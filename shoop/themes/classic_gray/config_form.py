# -*- coding: utf-8 -*-
import itertools

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.xtheme.forms import GenericThemeForm


class ClassicGrayConfigForm(GenericThemeForm):
    def __init__(self, **kwargs):
        super(ClassicGrayConfigForm, self).__init__(**kwargs)
        self._populate_footer_column_order_choices()

    def _populate_footer_column_order_choices(self):
        column_mnemonics_to_labels = {
            "cms": _("CMS Page Links"),
            "html": _("Custom HTML"),
            "links": _("Footer Links"),
        }
        column_orders = []
        for x in range(len(column_mnemonics_to_labels)):
            column_orders.extend(itertools.permutations(column_mnemonics_to_labels, x + 1))
        footer_column_order_choices = sorted([
            (
                ",".join(column_order),
                (" / ".join(force_text(column_mnemonics_to_labels[mnem]) for mnem in column_order))
            ) for column_order in column_orders
        ])
        footer_column_order_choices.insert(0, ("", _("None")))
        order_field = self.fields["footer_column_order"]
        order_field.choices = order_field.widget.choices = footer_column_order_choices
