# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json
import abc
from shoop.utils.serialization import ExtendedJSONEncoder
import six


class Chart(six.with_metaclass(abc.ABCMeta)):
    def __init__(self, title):
        self.title = title

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


class BarChart(Chart):
    def __init__(self, title, labels):
        super(BarChart, self).__init__(title)
        self.labels = labels
        self.series = []

    def add_data(self, name, data):
        assert len(data) == len(self.labels)
        self.series.append({"name": name, "data": data})

    def get_config(self):
        return {
            "type": "bar",
            "data": {
                "labels": self.labels,
                "series": self.series,
            },
            "options": {
                "seriesBarDistance": 3
            }
        }
