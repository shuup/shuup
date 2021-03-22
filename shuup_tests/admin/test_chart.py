# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from babel.numbers import format_decimal, format_percent
from collections import OrderedDict

from shuup.admin.dashboard.charts import BarChart, Chart, ChartDataType, ChartType, MixedChart
from shuup.utils.i18n import format_money
from shuup.utils.money import Money


def test_chart_is_abstract_enough():
    with pytest.raises(TypeError):
        Chart("Derp").get_config()


@pytest.mark.django_db
def test_bar_chart():
    labels = ["One", "Two", "Three"]
    locale = "pt_br"
    chart = BarChart("ma biultiful xart", labels, data_type=ChartDataType.NUMBER, locale=locale)

    # add line data here
    with pytest.raises(AssertionError):
        chart.add_data("some lines", [1, 2, 3], ChartType.LINE)

    dataset1 = OrderedDict({"type": ChartType.BAR, "label": "some bars #1", "data": [1, 2, 3]})
    dataset2 = OrderedDict({"type": ChartType.BAR, "label": "some bars #2", "data": [2, 3, 4]})
    datasets = [dataset1, dataset2]

    chart.add_data(dataset1["label"], dataset1["data"], dataset1["type"])
    chart.add_data(dataset2["label"], dataset2["data"], dataset2["type"])

    chart_config = chart.get_config()
    assert chart_config["type"] == ChartType.BAR
    assert chart_config["data"]["labels"] == labels

    for i in range(len(chart_config["data"]["datasets"])):
        for j in range(len(chart_config["data"]["datasets"][i]["data"])):
            assert chart_config["data"]["datasets"][i]["data"][j] == datasets[i]["data"][j]

            formatted_data = chart_config["data"]["datasets"][i]["formatted_data"][j]
            assert formatted_data == format_decimal(datasets[i]["data"][j], locale=locale)


@pytest.mark.django_db
def test_bar_chart_percent():
    labels = ["One", "Two", "Three"]
    locale = "pt_br"
    chart = BarChart("ma biultiful xart %", labels, data_type=ChartDataType.PERCENT, locale=locale)

    dataset1 = OrderedDict({"type": ChartType.BAR, "label": "some bars #1", "data": [0.1, 0.2, 0.3]})
    dataset2 = OrderedDict({"type": ChartType.BAR, "label": "some bars #2", "data": [0.45, 0.55, 0.999]})
    datasets = [dataset1, dataset2]

    chart.add_data(dataset1["label"], dataset1["data"], dataset1["type"])
    chart.add_data(dataset2["label"], dataset2["data"], dataset2["type"])

    chart_config = chart.get_config()
    assert chart_config["type"] == ChartType.BAR
    assert chart_config["data"]["labels"] == labels

    for i in range(len(chart_config["data"]["datasets"])):
        for j in range(len(chart_config["data"]["datasets"][i]["data"])):
            assert chart_config["data"]["datasets"][i]["data"][j] == datasets[i]["data"][j]

            formatted_data = chart_config["data"]["datasets"][i]["formatted_data"][j]
            assert formatted_data == format_percent(datasets[i]["data"][j], locale=locale)


@pytest.mark.django_db
def test_mixed_chart():
    labels = ["One", "Two", "Three"]
    locale = "pt_br"
    currency = "BRL"
    chart = MixedChart("ma biultiful xart", labels, data_type=ChartDataType.CURRENCY, locale=locale, currency=currency)

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

    for i in range(len(chart_config["data"])):
        for j in range(len(chart_config["data"][i]["data"])):
            assert chart_config["data"][i]["data"][j] == datasets[i]["data"][j]

            formatted_data = chart_config["data"][i]["formatted_data"][j]
            assert formatted_data == format_money(Money(datasets[i]["data"][j], currency=currency).as_rounded())
