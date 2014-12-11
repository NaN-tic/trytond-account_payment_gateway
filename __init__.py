# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .gateway import *
from .payment_type import *

def register():
    Pool.register(
        AccountPaymentGateway,
        AccountPaymentGatewayTransaction,
        PaymentType,
        module='account_payment_gateway', type_='model')
