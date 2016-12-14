# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from collections import OrderedDict

import pytest

from shuup.admin.dashboard.charts import BarChart, Chart, ChartType, MixedChart


def test_chart_is_abstract_enough():
    with pytest.raises(TypeError):
        Chart("Derp").get_config()


def test_bar_chart():
    labels = ["One", "Two", "Three"]
    chart = BarChart("ma biultiful xart", labels)

    # add line data here
    with pytest.raises(AssertionError):
        chart.add_data("some lines", [1, 2, 3], ChartType.LINE)

    dataset1 = OrderedDict({"type": ChartType.BAR, "label": "some bars #1", "data": [1, 2, 3]})
    dataset2 = OrderedDict({"type": ChartType.BAR, "label": "some bars #2", "data": [2, 3, 4]})

    chart.add_data(dataset1["label"], dataset1["data"], dataset1["type"])
    chart.add_data(dataset2["label"], dataset2["data"], dataset2["type"])

    chart_config = chart.get_config()
    assert chart_config["type"] == ChartType.BAR
    assert chart_config["data"]["labels"] == labels

    assert OrderedDict(chart_config["data"]["datasets"][0]) == dataset1
    assert OrderedDict(chart_config["data"]["datasets"][1]) == dataset2


def test_mixed_chart():
    labels = ["One", "Two", "Three"]
    chart = MixedChart("ma biultiful xart", labels)

    dataset1 = OrderedDict({"type": ChartType.BAR, "label": "some bars #1", "data": [1, 2, 3]})
    dataset2 = OrderedDict({"type": ChartType.BAR, "label": "some bars #2", "data": [2, 3, 4]})
    dataset3 = OrderedDict({"type": ChartType.LINE, "label": "some lines #1", "data": [5, 6, 7]})
    dataset4 = OrderedDict({"type": ChartType.LINE, "label": "some lines #2", "data": [8, 9, 10]})
    datasets = [dataset1, dataset2, dataset3, dataset4]

    for dataset in datasets:
        chart.add_data(dataset["label"], dataset["data"], dataset["type"])

    chart_config = chart.get_config()
    assert chart_config["type"] == "mixed"
    assert chart_config["labels"] == labels

    for ix in range(len(datasets)):
        assert OrderedDict(chart_config["data"][ix]) == datasets[ix]
