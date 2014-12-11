# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView,  Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If, Bool
from trytond.transaction import Transaction

__all__ = ['PaymentType']
__metaclass__ = PoolMeta


class PaymentType:
    __name__ = 'account.payment.type'
    gateway = fields.Many2One('account.payment.gateway', 'Gateway')
