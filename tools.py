# encoding: utf-8
# This file is part account_payment_gateway module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unicodedata

SRC_CHARS = u"""/*+?¿!&$[]{}@#`^<>=~%|\\"""


def unaccent(text):
    if not text:
        return ''
    for c in range(len(SRC_CHARS)):
        text = text.replace(SRC_CHARS[c], '')
    text = text.replace('º', '. ')
    text = text.replace('ª', '. ')
    text = text.replace('  ', ' ')
    output = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')
    return output.decode('utf-8')
