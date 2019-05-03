# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import cron
from . import gateway
from . import payment_type
from . import party


def register():
    Pool.register(
        cron.Cron,
        gateway.AccountPaymentGateway,
        gateway.AccountPaymentGatewayTransaction,
        payment_type.PaymentType,
        module='account_payment_gateway', type_='model')
    Pool.register(
        party.PartyReplace,
        module='account_payment_gateway', type_='wizard')
