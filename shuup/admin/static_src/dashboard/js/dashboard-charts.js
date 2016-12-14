/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.DashboardCharts = (function(Chart) {
    // colors from shuup/admin/static_src/base/less/variables.less
    let colorPallete = [
        "#429AAF",
        "#C54141",
        "#D16B2C",
        "#555555",
        "#7F5C99",
        "#409AAF",
        "#94B933",
        "#CFBE00",
        "#41589B"
    ];
    let nextColorIndex = 0;

    function getNextColorFromPallete (){
        return colorPallete[nextColorIndex++ % colorPallete.length];
    }
    function configureChartData(chartData){
        let color = getNextColorFromPallete();
        chartData.backgroundColor = color;

        if (chartData.type == "line"){
            chartData.borderColor = color;
            chartData.fill = false;
        }
    }
    function activate(config, id) {
        const context = $("#chart-" + id);

        if (!context) {
            return;
        }

        let chartData = {};
        if (config.type == "mixed"){
            _.each(config.data, configureChartData);

            chartData = {
                type: "bar",
                data: {
                    labels: config.labels,
                    datasets: config.data,
                    options: config.options
                }
            }
        }else{
            _.each(config.data.datasets, configureChartData);
            chartData = {
                type: config.type,
                data: config.data,
                options: config.options
            };
        }
        const chart = new Chart(context, chartData);
    }
    return {
        init: function init() {
            _.each(window.CHART_CONFIGS || {}, function(config, id) {
                activate(config, id);
            });
        }
    };
}(window.Chart));
