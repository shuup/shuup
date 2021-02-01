# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import abc
import json

import six
from babel.numbers import format_decimal, format_percent

from shuup.utils.i18n import format_money, get_current_babel_locale
from shuup.utils.money import Money
from shuup.utils.serialization import ExtendedJSONEncoder


class ChartType(object):
    """ Type of a chart """
    BAR = "bar"
    LINE = "line"


class ChartDataType(object):
    """ Data type of datasets """
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENT = "percent"


class Chart(six.with_metaclass(abc.ABCMeta)):
    supported_chart_types = []   # list[ChartType]

    def __init__(self, title, data_type=ChartDataType.NUMBER, locale=None, currency=None, options=None):
        """
        :param str title: the title of the chart

        :param ChartDataType data_type: the data type of values
            The chart will format the output labels according to this parameter

        :param str locale: the locale to render values
            If not set, the locale will be fetched from Babel

        :param str currency: the ISO-4217 code for the currency
            This is necessary when the data_type is CURRENCY

        :param dict options: a dicionaty with options for Chartjs
        """
        self.title = title
        self.datasets = []
        self.options = options
        self.data_type = data_type
        self.currency = currency

        if locale:
            self.locale = locale
        else:
            self.locale = get_current_babel_locale()

        if data_type == ChartDataType.CURRENCY and not currency:
            raise AttributeError("You should also set currency for this data type")

    @abc.abstractmethod
    def get_config(self):
        """
        Get a JSONable dictionary of configuration data for this chart.
        This is passed on as `CHART_CONFIGS` in the JS environment and eventually
        processed by `dashboard-charts.js`.

        :return: Dict of configuration
        :rtype: dict
        """
        return {}  # Implement me in a subclass, please.

    def get_config_json(self):
        return json.dumps(self.get_config(), cls=ExtendedJSONEncoder, separators=',:')

    def add_data(self, name, data, chart_type):
        """
        Add data to this chart.

        :param name: the name of the dataset
        :type name: str
        :param data: the list of data
        :type data: list[int|float|Decimal]
        :param chart_type: the chart type - tells how data should be rendered.
            This data type must be available in the `supported_chart_type` attribute of this instance
        :type chart_type: ChartType
        """
        assert chart_type in self.supported_chart_types
        formatted_data = []

        # format value for each data point
        if self.data_type == ChartDataType.CURRENCY:
            for value in data:
                formatted_data.append(format_money(Money(value, currency=self.currency).as_rounded()))

        elif self.data_type == ChartDataType.PERCENT:
            for value in data:
                formatted_data.append(format_percent(value, locale=self.locale))

        # self.data_type == ChartDataType.NUMBER
        else:
            for value in data:
                formatted_data.append(format_decimal(value, locale=self.locale))

        self.datasets.append({"type": chart_type, "label": name, "data": data, "formatted_data": formatted_data})


class BarChart(Chart):
    supported_chart_types = [ChartType.BAR]

    def __init__(self, title, labels, data_type=ChartDataType.NUMBER, **kwargs):
        super(BarChart, self).__init__(title, data_type=data_type, **kwargs)
        self.labels = labels

    def get_config(self):
        return {
            "type": ChartType.BAR,
            "data": {
                "labels": self.labels,
                "datasets": self.datasets
            },
            "options": self.options
        }


class MixedChart(Chart):
    """
    This chart supports both Bars and Lines.
    """
    supported_chart_types = [ChartType.BAR, ChartType.LINE]

    def __init__(self, title, labels, data_type=ChartDataType.NUMBER, **kwargs):
        super(MixedChart, self).__init__(title, data_type=data_type, **kwargs)
        self.labels = labels

    def get_config(self):
        return {
            "type": "mixed",
            "labels": self.labels,
            "data": self.datasets,
            "options": self.options
        }
