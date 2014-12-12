# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView,  Workflow, fields
from trytond.pool import Pool
from trytond.pyson import Eval, If, Bool
from trytond.transaction import Transaction
from trytond.cache import Cache
import re
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

__all__ = ['AccountPaymentGateway', 'AccountPaymentGatewayTransaction']
READONLY_IF_NOT_DRAFT = {'readonly': Eval('state') != 'draft'}


class AccountPaymentGateway(ModelSQL, ModelView):
    "Account Payment Gateway"
    __name__ = 'account.payment.gateway'
    name = fields.Char('Name', required=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, readonly=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', 0)),
            ])
    active = fields.Boolean('Active')
    method = fields.Selection('get_methods', 'Method', required=True)
    journal = fields.Many2One('account.journal', 'Journal', required=True)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_active():
        return True

    @classmethod
    def get_methods(cls):
        res = [(None, '')]
        return res


class AccountPaymentGatewayTransaction(Workflow, ModelSQL, ModelView):
    '''Account Payment Gateway Transaction'''
    __name__ = 'account.payment.gateway.transaction'
    _rec_name = 'uuid'
    uuid = fields.Char('UUID', required=True, readonly=True)
    description = fields.Char('Description', states=READONLY_IF_NOT_DRAFT,
        depends=['state'])
    origin = fields.Reference('Origin', selection='get_origin', select=True,
        states=READONLY_IF_NOT_DRAFT, depends=['state'])
    gateway = fields.Many2One('account.payment.gateway', 'Gateway', required=True,
        states=READONLY_IF_NOT_DRAFT, depends=['state'], ondelete='RESTRICT')
    reference_gateway = fields.Char('Reference Gateway',
        states=READONLY_IF_NOT_DRAFT, depends=['state'])
    authorisation_code = fields.Char('Authorisation Code',
        states=READONLY_IF_NOT_DRAFT, depends=['state'])
    date = fields.Date('Date', required=True,
        states=READONLY_IF_NOT_DRAFT, depends=['state'])
    company = fields.Many2One('company.company', 'Company', required=True,
        states=READONLY_IF_NOT_DRAFT, select=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
        ], depends=['state'])
    party = fields.Many2One('party.party', 'Party', ondelete='RESTRICT',
        depends=['state'], states=READONLY_IF_NOT_DRAFT)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        required=True, depends=['state', 'currency_digits'],
        states=READONLY_IF_NOT_DRAFT)
    currency = fields.Many2One('currency.currency', 'Currency',
        required=True, depends=['state'], states=READONLY_IF_NOT_DRAFT)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    method = fields.Function(fields.Char('Payment Gateway Method'), 'get_method')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('failed', 'Failed'),
        ('authorized', 'Authorized'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
        ], 'State', readonly=True)
    log = fields.Text("Log", depends=['state'], states=READONLY_IF_NOT_DRAFT)

    @classmethod
    def __setup__(cls):
        super(AccountPaymentGatewayTransaction, cls).__setup__()
        cls._order.insert(0, ('date', 'DESC'))
        cls._error_messages.update({
                'missing_debit_account': 'Journal "%s" has not got a debit '
                    'account',
                'delete_cancel': ('Transaction "%s" must be cancelled before '
                    'deletion.'),
                })
        cls._transitions |= set((
                ('draft', 'cancel'),
                ('draft', 'failed'),
                ('draft', 'authorized'),
                ('draft', 'done'),
                ('cancel', 'draft'),
                ('failed', 'draft'),
                ('authorized', 'cancel'),
                ('authorized', 'done'),
                ('done', 'cancel'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft', 'failed', 'done']),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancel']),
                    },
                'confirm': {
                    'invisible': ~Eval('state').in_(['draft', 'authorized']),
                    },
                })

    @staticmethod
    def default_uuid():
        return unicode(uuid4())

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
        models = IrModel.search([('model', 'in', models)])
        return [(None, '')] + [(m.model, m.name) for m in models]

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
            if transaction.state != 'cancel':
                cls.raise_user_error('delete_cancel', (transaction.rec_name,))
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
    @Workflow.transition('cancel')
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
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def confirm(cls, transactions):
        for transaction in transactions:
            method_name = 'confirm_%s' % transaction.gateway.method
            if hasattr(transaction, method_name):
                getattr(transaction, method_name)()
        pass
