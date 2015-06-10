/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.DashboardCharts = (function(Chartist) {
    var chartTypeInfo = {
        "bar": {
            "factory": Chartist.Bar,
            "elementSelector": ".ct-bar"
        }
    };
    function activate(config, id) {
        var parent = Chartist.querySelector("#chart-" + id);
        if(!parent) return;
        var typeInfo = chartTypeInfo[config.type];
        if (!typeInfo) {
            console.log("Unable to initialize chart - no type info", config);
            return;
        }
        var chartElement = document.createElement("div");
        chartElement.className = "ct-chart " + (config.aspect || "ct-major-twelfth");

        parent.appendChild(chartElement);
        var factory = typeInfo.factory;
        config.instance = new factory(chartElement, config.data, config.options);
        if(typeInfo.elementSelector) setupTooltips(chartElement, typeInfo.elementSelector);
    }

    function setupTooltips(chart, elementSelector) {
        var $chart = $(chart);

        var $toolTip = $chart
            .append('<div class="ct-tooltip"></div>')
            .find('.ct-tooltip')
            .hide();

        $chart.on('mouseenter', elementSelector, function() {
            var $point = $(this),
                value = $point.attr('ct:value'),
                seriesName = $point.parent().attr('ct:series-name');
            $toolTip.html(seriesName + '<br>' + value).show();
        });

        $chart.on('mouseleave', elementSelector, function() {
            $toolTip.hide();
        });

        $chart.on('mousemove', function(event) {
            $toolTip.css({
                left: (event.offsetX || event.originalEvent.layerX) - $toolTip.width() / 2 - 10,
                top: (event.offsetY || event.originalEvent.layerY) - $toolTip.height() - 40
            });
        });
    }
    return {
        init: function init() {
            _.each(window.CHART_CONFIGS || {}, function(config, id) {
                activate(config, id);
            });
        }
    }
}(window.Chartist));
