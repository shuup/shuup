# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import abc
import json

import six

from shuup.utils.serialization import ExtendedJSONEncoder


class ChartType(object):
    """ Type of a chart """
    BAR = "bar"
    LINE = "line"


class Chart(six.with_metaclass(abc.ABCMeta)):
    supported_data_types = []   # list[ChartType]

    def __init__(self, title):
        self.title = title
        self.datasets = []

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

    def add_data(self, name, data, data_type):
        """
        Add data to this chart
        :param name: the name of the dataset
        :type name: str
        :param data: the list of data
        :type data: list[int|float|Decimal]
        :param data_type: the cart type of this data - tells how data should be rendered.
            This data type must be available in the `supported_data_types` attribute of this instance
        :type data_type: ChartType
        """
        assert data_type in self.supported_data_types
        self.datasets.append({"type": data_type, "label": name, "data": data})


class BarChart(Chart):
    supported_data_types = [ChartType.BAR]

    def __init__(self, title, labels):
        super(BarChart, self).__init__(title)
        self.labels = labels

    def get_config(self):
        return {
            "type": ChartType.BAR,
            "data": {
                "labels": self.labels,
                "datasets": self.datasets
            }
        }


class MixedChart(Chart):
    """
    This chart supports both Bars and Lines
    """
    supported_data_types = [ChartType.BAR, ChartType.LINE]

    def __init__(self, title, labels):
        super(MixedChart, self).__init__(title)
        self.labels = labels

    def get_config(self):
        return {
            "type": "mixed",
            "labels": self.labels,
            "data": self.datasets
        }
