# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['PaymentType']


class PaymentType(metaclass=PoolMeta):
    __name__ = 'account.payment.type'
    gateway = fields.Many2One('account.payment.gateway', 'Gateway')
