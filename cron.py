# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['Cron']


class Cron(metaclass=PoolMeta):
    __name__ = "ir.cron"

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.extend([
            ('account.payment.gateway|import_gateway',
                'Payment Gateway - Import Transactions'),
        ])
