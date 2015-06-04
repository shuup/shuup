# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


class LineTax(object):
    """
    Tax of some line.

    :ivar tax: The tax that this line is about.
    :type tax: shoop.core.models.Tax
    :ivar name: Name of the tax.
    :type name: six.text_type
    :ivar amount: Tax amount.
    :type amount: decimal.Decimal
    :ivar base_amount: Amount that this tax is calculated from.
    :type base_amount: decimal.Decimal
    """
    @property
    def rate(self):
        return (self.amount / self.base_amount)

    @classmethod
    def from_tax(cls, tax, base_amount):
        return cls(
            tax=tax,
            name=tax,
            base_amount=base_amount,
            amount=tax.calculate_amount(base_amount)
        )


class SourceLineTax(LineTax):
    def __init__(self, tax, name, amount, base_amount):
        """
        Initialize line tax from given values.

        :type tax: shoop.core.models.Tax
        :type name: six.text_type
        :type amount: decimal.Decimal
        :type base_amount: decimal.Decimal
        """
        self.tax = tax
        self.name = name
        self.amount = amount
        self.base_amount = base_amount

    def __repr__(self):
        return '%s(%r, %r, %r, %r)' % (
            type(self).__name__,
            self.tax, self.name, self.amount, self.base_amount)
