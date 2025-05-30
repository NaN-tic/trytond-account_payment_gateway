# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from uuid import uuid4
from datetime import datetime
from trytond.model import ModelSQL, ModelView, Workflow, DeactivableMixin, fields
from trytond.pool import Pool
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['AccountPaymentGateway', 'AccountPaymentGatewayTransaction']

READONLY_IF_NOT_DRAFT = {'readonly': Eval('state') != 'draft'}


class AccountPaymentGateway(DeactivableMixin, ModelSQL, ModelView):
    "Account Payment Gateway"
    __name__ = 'account.payment.gateway'
    name = fields.Char('Name', required=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        readonly=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', 0)),
            ])
    method = fields.Selection('get_methods', 'Method', required=True)
    mode = fields.Selection([
        ('live', 'Live'),
        ('sandbox', 'Sandbox'),
        ], 'Mode', required=True)
    journal = fields.Many2One('account.journal', 'Journal', required=True,
        context={
            'company': Eval('company', -1),
        }, depends=['company'])
    journal_writeoff = fields.Many2One('account.journal', 'Write Off Journal',
        required=True, context={
            'company': Eval('company', -1),
        }, depends=['company'])
    writeoff_amount_percent = fields.Numeric('Write Off (%)', digits=(8, 4),
        required=True)
    from_transactions = fields.DateTime('From Transactions',
        help='This date is last import (filter)', required=True)
    to_transactions = fields.DateTime('To Transactions',
        help='This date is to import (filter)')
    scheduler = fields.Boolean('Scheduler',
        help='Import transactions from Gateway')

    @classmethod
    def __setup__(cls):
        super(AccountPaymentGateway, cls).__setup__()
        cls._buttons.update({
                'import_transactions': {},
                })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_from_transactions():
        return datetime.now()

    @classmethod
    def get_methods(cls):
        return []

    @staticmethod
    def default_mode():
        return 'live'

    @classmethod
    @ModelView.button
    def import_transactions(self, gateways):
        """
        Import Transactions from Gateway APP
        """
        for gateway in gateways:
            import_transaction = getattr(gateway, 'import_transactions_%s' %
                gateway.method)
            import_transaction()

    @classmethod
    def import_gateway(cls):
        """
        Import gateways transactions:
        """
        gateways = cls.search([
            ('scheduler', '=', True),
            ])
        cls.import_transactions(gateways)
        return True


class AccountPaymentGatewayTransaction(Workflow, ModelSQL, ModelView):
    '''Account Payment Gateway Transaction'''
    __name__ = 'account.payment.gateway.transaction'
    _rec_name = 'uuid'
    uuid = fields.Char('UUID', required=True, readonly=True)
    description = fields.Char('Description', states=READONLY_IF_NOT_DRAFT)
    origin = fields.Reference('Origin', selection='get_origin',
        states=READONLY_IF_NOT_DRAFT)
    gateway = fields.Many2One('account.payment.gateway', 'Gateway',
        required=True, states=READONLY_IF_NOT_DRAFT,
        ondelete='RESTRICT')
    reference_gateway = fields.Char('Reference Gateway',
        states=READONLY_IF_NOT_DRAFT)
    authorisation_code = fields.Char('Authorisation Code',
        states=READONLY_IF_NOT_DRAFT)
    date = fields.Date('Date', required=True,
        states=READONLY_IF_NOT_DRAFT)
    company = fields.Many2One('company.company', 'Company', required=True,
        states=READONLY_IF_NOT_DRAFT,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
        ])
    party = fields.Many2One('party.party', 'Party', ondelete='RESTRICT',
        context={
            'company': Eval('company', -1),
        }, depends=['company'], states=READONLY_IF_NOT_DRAFT)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        required=True,
        states=READONLY_IF_NOT_DRAFT)
    currency = fields.Many2One('currency.currency', 'Currency',
        required=True, states=READONLY_IF_NOT_DRAFT)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    method = fields.Function(fields.Char('Payment Gateway Method'),
        'get_method')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('authorized', 'Authorized'),
        ('done', 'Done'),
        ('cancelled', "Cancelled"),
        ('refunded', 'Refunded'),
        ], 'State', readonly=True)
    gateway_log = fields.Text("Gateway Log", states=READONLY_IF_NOT_DRAFT)

    @classmethod
    def __setup__(cls):
        super(AccountPaymentGatewayTransaction, cls).__setup__()
        cls._order.insert(0, ('date', 'DESC'))
        cls._transitions |= set((
                ('draft', 'cancelled'),
                ('draft', 'pending'),
                ('draft', 'failed'),
                ('draft', 'authorized'),
                ('draft', 'done'),
                ('cancelled', 'draft'),
                ('failed', 'draft'),
                ('pending', 'cancelled'),
                ('pending', 'authorized'),
                ('pending', 'done'),
                ('authorized', 'cancelled'),
                ('authorized', 'done'),
                ('authorized', 'refunded'),
                ('done', 'cancelled'),
                ('done', 'refunded'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_([
                        'draft', 'pending', 'failed', 'authorized', 'done',
                        ]),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancelled']),
                    },
                'pending': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                'authorized': {
                    'invisible': ~Eval('state').in_(['draft', 'pending']),
                    },
                'confirm': {
                    'invisible': ~Eval('state').in_([
                        'draft', 'pending', 'authorized',
                        ]),
                    },
                'refund': {
                    'invisible': ~Eval('state').in_([
                        'authorized', 'done',
                        ]),
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        table = cls.__table_handler__(module_name)
        sql_table = cls.__table__()

        # Migration from 6.8: rename log to gateway_log
        if (table.column_exist('log')
                and not table.column_exist('gateway_log')):
            table.column_rename('log', 'gateway_log')

        super(AccountPaymentGatewayTransaction, cls).__register__(module_name)

        # Migration from 5.6: rename state cancel to cancelled
        cursor.execute(*sql_table.update(
                [sql_table.state], ['cancelled'],
                where=sql_table.state == 'cancel'))

    @staticmethod
    def default_uuid():
        return '%s' % uuid4()

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.id

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def _get_origin(cls):
        'Return list of Model names for origin Reference'
        return []

    @classmethod
    def get_origin(cls):
        IrModel = Pool().get('ir.model')
        models = cls._get_origin()
        models = IrModel.search([('name', 'in', models)])
        return [(None, '')] + [(m.name, m.string) for m in models]

    @classmethod
    def copy(cls, transactions, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['uuid'] = cls.default_uuid()
        return super(AccountPaymentGatewayTransaction, cls).copy(
            transactions, default=default)

    @classmethod
    def delete(cls, transactions):
        # Cancel before delete
        cls.cancel(transactions)
        for transaction in transactions:
            if transaction.state != 'cancelled':
                raise UserError(gettext('account_payment_gateway.delete_cancel',
                    transaction=transaction.rec_name))
        super(AccountPaymentGatewayTransaction, cls).delete(transactions)

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    def get_method(self, name=None):
        'Return the method based on the gateway'
        return self.gateway.method

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, transactions):
        for transaction in transactions:
            method_name = 'cancel_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, transactions):
        for transaction in transactions:
            method_name = 'draft_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()

    @classmethod
    @ModelView.button
    @Workflow.transition('pending')
    def pending(cls, transactions):
        for transaction in transactions:
            method_name = 'pending_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()

    @classmethod
    @ModelView.button
    @Workflow.transition('authorized')
    def authorized(cls, transactions):
        for transaction in transactions:
            method_name = 'authorized_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def confirm(cls, transactions):
        for transaction in transactions:
            method_name = 'confirm_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()

    @classmethod
    @ModelView.button
    @Workflow.transition('refunded')
    def refund(cls, transactions):
        for transaction in transactions:
            method_name = 'refund_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()
