# This file is part of the account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class AccountPaymentGatewayTestCase(ModuleTestCase):
    'Test Account Payment Gateway module'
    module = 'account_payment_gateway'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountPaymentGatewayTestCase))
    return suite
