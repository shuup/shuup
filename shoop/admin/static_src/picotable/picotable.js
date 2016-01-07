/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-plusplus, prefer-const, curly, no-bitwise */
/* exported Picotable */
/* global alert, require */
const Picotable = (function(m, storage) {
    "use strict";
    m = m || require("mithril");

    const Util = (function() {
        function property(propertyName) {
            return function(obj) {
                return obj[propertyName];
            };
        }

        function map(obj, callback) {
            if (Array.isArray(obj)) {
                return obj.map(callback);
            }
            return Object.keys(obj).map(function(key) {
                return callback(obj[key], key, obj);
            });
        }

        function any(obj, callback) {
            if (Array.isArray(obj)) {
                return obj.some(callback);
            }
            return Object.keys(obj).some(function(key) {
                return callback(obj[key], key, obj);
            });
        }

        function extend(/*...*/) {
            const target = arguments[0];
            for (var i = 1; i < arguments.length; i++) {
                for (var key in arguments[i]) {
                    if (arguments[i].hasOwnProperty(key)) {
                        target[key] = arguments[i][key];
                    }
                }
            }
            return target;
        }

        function trim(value) {
            return ("" + value).replace(/^\s+|\s+$/g, "");
        }

        function omitNulls(object) {
            const outputObject = {};
            map(object, function(value, key) {
                if (value !== null) {
                    outputObject[key] = value;
                }
            });
            return outputObject;
        }

        function debounce(func, wait, immediate) {
            var timeout;

            function cancel() {
                clearTimeout(timeout);
                timeout = null;
            }

            const debounced = function() {
                const context = this, args = arguments;
                const later = function() {
                    cancel();
                    if (!immediate) {
                        func.apply(context, args);
                    }
                };
                const callNow = immediate && !timeout;
                cancel();
                timeout = setTimeout(later, wait);
                if (callNow) {
                    func.apply(context, args);
                }
            };
            debounced.cancel = cancel;
            return debounced;
        }

        function stringValue(obj) {
            if (obj === null || obj === undefined) {
                return "";
            }
            if (Array.isArray(obj) && obj.length === 0) {
                return "";
            }
            return "" + obj;
        }

        function isEmpty(obj) {
            if (obj.length) {
                return false;
            }
            for (var k in obj) {
                if (obj.hasOwnProperty(k)) {
                    return false;
                }
            }
            return true;
        }

        function boundPartial(thisArg, func/*, args */) {
            const partialArgs = [].slice.call(arguments, 2);
            return function(/* args */) {
                const fArgs = partialArgs.concat([].slice.call(arguments));
                return func.apply(thisArg, fArgs);
            };
        }

        return {
            property: property,
            map: map,
            any: any,
            extend: extend,
            trim: trim,
            omitNulls: omitNulls,
            debounce: debounce,
            stringValue: stringValue,
            isEmpty: isEmpty,
            boundPartial: boundPartial
        };
    }());

    const lang = {
        "RANGE_FROM": gettext("From"),
        "RANGE_TO": gettext("To"),
        "ITEMS_PER_PAGE": gettext("Items per page"),
        "RESET_FILTERS": gettext("Reset filters"),
        "RESET": gettext("Reset"),
        "SORT_BY": gettext("Sort by"),
        "SORT_ASC": gettext("ascending"),
        "SORT_DESC": gettext("descending"),
        "SORT_DEFAULT": gettext("Default sorting")
    };

    const cx = function generateClassName(classSet) {
        var classValues = [];
        Util.map((classSet || {}), function(flag, key) {
            var className = null;
            if (key === "") { // The empty string as a class set means the entire value is used if not empty
                className = (flag && flag.length ? "" + flag : null);
            } else {
                className = flag ? key : null;
            }
            if (className) classValues.push(className);
        });
        return classValues.join(" ");
    };

    function addDummies(pageLinks) {
        var nDummy = 0;
        for (var i = 1; i < pageLinks.length; i++) {
            if (pageLinks[i]._page !== pageLinks[i - 1]._page + 1) {
                const li = m("li", {key: "dummy" + (nDummy++), className: "disabled"}, m("a", {href: "#"}, "\u22EF"));
                pageLinks.splice(i, 0, li);
                i++;
            }
        }
    }

    function paginator(paginationData, setPage) {
        if (paginationData.nItems === 0) return m("nav");
        var callback = m.withAttr("rel", setPage);
        var currentPage = paginationData.pageNum;
        var pageLinks = [];
        var pageLink = function(page, title) {
            return m("a", {rel: page, href: "#", onclick: callback}, title || page);
        };
        for (var page = 1; page <= paginationData.nPages; page++) {
            if (page === 1 || page === paginationData.nPages || Math.abs(page - currentPage) <= 4 || page % 10 === 0) {
                var li = m("li", {key: page, className: cx({active: currentPage === page})}, pageLink(page));
                li._page = page;
                pageLinks.push(li);
            }
        }
        addDummies(pageLinks);
        var prevLink = m("li", {
            key: "previous",
            className: cx({disabled: currentPage === 1})
        }, pageLink(currentPage - 1, gettext("Previous")));
        var nextLink = m("li", {
            key: "next",
            className: cx({disabled: currentPage === paginationData.nPages})
        }, pageLink(currentPage + 1, gettext("Next")));
        return m("nav", m("ul.pagination", prevLink, pageLinks, nextLink));
    }

    function debounceChangeConfig(timeout) {
        return function(el, isInit, context) {
            if (!isInit) {
                el.oninput = context.debouncedOnInput = Util.debounce(el.onchange, timeout);
                context.onunload = function() {
                    if (context.debouncedOnInput) {
                        context.debouncedOnInput.cancel();
                        context.debouncedOnInput = null;
                    }
                };
            }
        };
    }

    function buildColumnChoiceFilter(ctrl, col, value) {
        var setFilterValueFromSelect = function() {
            var valueJS = JSON.parse(this.value);
            ctrl.setFilterValue(col.id, valueJS);
        };
        var select = m("select.form-control", {
            value: JSON.stringify(value),
            onchange: setFilterValueFromSelect
        }, Util.map(col.filter.choices, function(choice) {
            return m("option", {value: JSON.stringify(choice[0]), key: choice[0]}, choice[1]);
        }));
        return m("div.choice-filter", select);

    }

    function buildColumnRangeFilter(ctrl, col, value) {
        var setFilterValueFromInput = function(which) {
            const filterObj = Util.extend({}, ctrl.getFilterValue(col.id) || {}); // Copy current filter object
            var newValue = this.value;
            if (!Util.trim(newValue)) {
                newValue = null;
            }
            filterObj[which] = newValue;
            ctrl.setFilterValue(col.id, filterObj);
        };
        var attrs = {"type": col.filter.range.type || "text"};
        Util.map(["min", "max", "step"], function(key) {
            var val = col.filter.range[key];
            if (!(val === undefined || val === null)) {
                attrs[key] = val;
                attrs.type = "number";  // Any of these set means we're talking about numbers
            }
        });
        value = value || {};
        var minInput = m("input.form-control", Util.extend({}, attrs, {
            value: Util.stringValue(value.min),
            placeholder: lang.RANGE_FROM,
            onchange: function() {
                setFilterValueFromInput.call(this, "min");
            },
            config: debounceChangeConfig(500)
        }));
        var maxInput = m("input.form-control", Util.extend({}, attrs, {
            value: Util.stringValue(value.max),
            placeholder: lang.RANGE_TO,
            onchange: function() {
                setFilterValueFromInput.call(this, "max");
            },
            config: debounceChangeConfig(500)
        }));
        return m("div.range-filter", [
            m("div.input-wrapper.min", {key: "min"}, minInput),
            m("div.input-wrapper.max", {key: "max"}, maxInput)
        ]);
    }

    function buildColumnTextFilter(ctrl, col, value) {
        var setFilterValueFromInput = function() {
            ctrl.setFilterValue(col.id, this.value);
        };
        var input = m("input.form-control", {
            type: col.filter.text.type || "text",
            value: Util.stringValue(value),
            placeholder: col.filter.placeholder || "Filter by " + col.title,
            onchange: setFilterValueFromInput,
            config: debounceChangeConfig(500)
        });
        return m("div.text-filter", input);
    }

    function buildColumnFilter(ctrl, col) {
        var value = ctrl.getFilterValue(col.id);
        if (col.filter.choices) {
            return buildColumnChoiceFilter(ctrl, col, value);
        }
        if (col.filter.range) {
            return buildColumnRangeFilter(ctrl, col, value);
        }
        if (col.filter.text) {
            return buildColumnTextFilter(ctrl, col, value);
        }
    }

    function buildColumnHeaderCell(ctrl, col) {
        var sortIndicator = null;
        var classSet = {"": col.className};
        var columnOnClick = null;
        if (col.sortable) {
            var currentSort = ctrl.vm.sort();
            var thisColSort = null;
            if (currentSort === "+" + col.id) {
                thisColSort = "asc";
            }
            if (currentSort === "-" + col.id) {
                thisColSort = "desc";
            }
            var sortIcon = "fa-sort" + (thisColSort ? "-" + thisColSort : "");
            sortIndicator = m("i.fa." + sortIcon);
            classSet.sortable = true;
            if (thisColSort) {
                classSet["sorted-" + thisColSort] = true;
            }
            columnOnClick = function() {
                ctrl.setSortColumn(col.id);
            };
        }
        return m("th", {key: col.id, className: cx(classSet), onclick: columnOnClick}, [sortIndicator, " ", col.title]);
    }

    function buildColumnFilterCell(ctrl, col) {
        var filterControl = null;
        if (col.filter) {
            filterControl = buildColumnFilter(ctrl, col);
        }
        return m("th", {key: col.id, className: col.className || ""}, [filterControl]);
    }

    function renderTable(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) {  // Not loaded, don't return anything
            return;
        }

        // Build header
        var columnHeaderCells = Util.map(data.columns, function(col) {
            return buildColumnHeaderCell(ctrl, col);
        });
        var columnFilterCells = (
            Util.any(data.columns, Util.property("filter")) ?
            Util.map(data.columns, function(col) {
                return buildColumnFilterCell(ctrl, col);
            }) : null
        );
        var thead = m("thead", [
            m("tr.headers", columnHeaderCells),
            (columnFilterCells ? m("tr.filters", columnFilterCells) : null)
        ]);

        // Build footer
        var footColspan = data.columns.length;
        var footCell = m("td", {colspan: footColspan}, paginator(data.pagination, ctrl.setPage));
        var tfoot = m("tfoot", [m("tr", footCell)]);

        // Build body
        var isPick = !!ctrl.vm.pickId();
        var rows = Util.map(data.items, function(item) {
            return m("tr", {key: "item-" + item._id}, Util.map(data.columns, function(col) {
                var content = item[col.id] || "";
                if (col.raw) content = m.trust(content);
                if (col.linked) {
                    if (isPick) {
                        content = m("a", {
                            href: "#",
                            onclick: Util.boundPartial(ctrl, ctrl.pickObject, item)
                        }, content);
                    } else if (item._url) {
                        content = m("a", {href: item._url}, content);
                    }
                }
                return m("td", {key: "col-" + col.id, className: col.className || ""}, [content]);
            }));
        });
        var tbody = m("tbody", rows);
        return m("table.table.table-striped.picotable-table", [thead, tfoot, tbody]);
    }

    function getMobileFilterModal(ctrl) {
        var data = ctrl.vm.data();
        var filters = Util.map(data.columns, function(col) {
            if (!col.filter) return null;
            return m("div.single-filter",
                m("h3", col.title),
                buildColumnFilter(ctrl, col)
            );
        });
        return m("div.mobile-filters.shoop-modal-bg", {key: "mobileFilterModal"}, [
            m("div.shoop-modal-container", [
                m("div.shoop-modal-header", [
                    m("h2.pull-left", [m("i.fa.fa-filter")], gettext("Filters")),
                    m("button.btn.btn-success.pull-right", {
                        onclick: function() {
                            ctrl.vm.showMobileFilterSettings(false);
                        }
                    }, "Done"),
                    m(
                        "button.btn.btn-gray.btn-inverse.pull-right",
                        {
                            onclick: ctrl.resetFilters,
                            disabled: Util.isEmpty(ctrl.vm.filterValues())
                        },
                        lang.RESET
                    )
                ]),
                m("div.mobile-filters-content", filters)
            ])
        ]);
    }

    function getMobileSortSelect(ctrl) {
        var data = ctrl.vm.data();
        var sortOptions = [];
        Util.map(data.columns, function(col) {
            if (col.sortable) {
                sortOptions.push({
                    value: "+" + col.id,
                    text: "" + lang.SORT_BY + " " + col.title + " " + lang.SORT_ASC
                });
                sortOptions.push({
                    value: "-" + col.id,
                    text: "" + lang.SORT_BY + " " + col.title + " " + lang.SORT_DESC
                });
            }
        });
        if (!sortOptions.length) return;
        sortOptions.unshift({value: "", text: lang.SORT_DEFAULT});

        return m("select.picotable-mobile-sort.form-control",
            {
                id: "mobile-sort-select",
                value: (ctrl.vm.sort() || ""),
                onchange: m.withAttr("value", function(value) {
                    ctrl.setSortColumn(value);
                    ctrl.refreshSoon();
                })
            },
            Util.map(sortOptions, function(so) {
                return m("option", {value: so.value}, so.text);
            })
        );
    }

    function renderMobileTable(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) return; // Not loaded, don't return anything
        var isPick = !!ctrl.vm.pickId();
        var listItems = Util.map(data.items, function(item) {
            var content = null;
            if (item._abstract && item._abstract.length) {
                content = Util.map(item._abstract, function(line) {
                    if (!line) return;
                    if (typeof line === "string") line = {text: line};
                    if (!line.text) return;
                    if (line.raw) line.text = m.trust(line.raw);
                    var rowClass = "div.inner-row." +
                        (line.title ? "with-title" : "") +
                        (line.class ? "." + line.class : "");
                    return m(rowClass, [
                        (line.title ? m("div.column.title", line.title) : null),
                        m("div.column", line.text)
                    ]);
                });
                if (!Util.any(content, function(v) {
                        return !!v;
                    })) {
                    // Not a single valid line
                    content = null;
                }
            }
            if (content === null) {
                content = Util.map(data.columns, function(col) {
                    var colContent = item[col.id] || "";
                    if (col.raw) colContent = m.trust(colContent);
                    return m("div.inner-row.with-title", [
                        m("div.column.title", col.title),
                        m("div.column", colContent)
                    ]);
                });
            }
            var linkAttrs = {href: item._url};
            if (isPick) {
                linkAttrs.onclick = Util.boundPartial(ctrl, ctrl.pickObject, item);
                linkAttrs.href = "#";
            }
            return m("div.list-element", m("a.inner", linkAttrs, content));
        });
        return m("div.mobile", [
            m("div.row.mobile-header", [
                m("div.col-sm-6", [
                    m("button.btn.btn-info.btn-block.toggle-btn",
                        {
                            onclick: function() {
                                ctrl.vm.showMobileFilterSettings(true);
                            }
                        },
                        [m("i.fa.fa-filter")], "Show filters"
                    )
                ]),
                m("div.col-sm-6", [
                    m("div.mobile-sort", getMobileSortSelect(ctrl))
                ])
            ]),
            (ctrl.vm.showMobileFilterSettings() ? getMobileFilterModal(ctrl) : null),
            m("hr"),
            m("div.mobile-items", listItems),
            paginator(data.pagination, ctrl.setPage)
        ]);
    }

    function renderHeader(ctrl) {
        var itemInfo = (ctrl.vm.data() ? ctrl.vm.data().itemInfo : null);
        return m("div.picotable-header", [
            m("div.picotable-items-per-page-ctr", [
                m("label", {"for": "pipps" + ctrl.id}, lang.ITEMS_PER_PAGE),
                m("select.picotable-items-per-page-select.form-control",
                    {
                        id: "pipps" + ctrl.id,
                        value: ctrl.vm.perPage(),
                        onchange: m.withAttr("value", function(value) {
                            ctrl.vm.perPage(value);
                            ctrl.refreshSoon();
                        })
                    },
                    Util.map(ctrl.vm.perPageChoices(), function(value) {
                        return m("option", {value: value}, value);
                    })
                )
            ]),
            m("div.picotable-item-info", itemInfo),
            m("div.picotable-reset-filters-ctr",
                m(
                    "button.picotable-reset-filters-btn.btn.btn-gray.btn-inverse",
                    {
                        onclick: ctrl.resetFilters,
                        disabled: Util.isEmpty(ctrl.vm.filterValues())
                    },
                    lang.RESET_FILTERS
                )
            )
        ]);
    }

    function PicotableView(ctrl) {
        return m("div.table-view", [
            (ctrl.vm.showHeader() ? renderHeader(ctrl) : null),
            (ctrl.vm.renderMode() === "mobile" ? renderMobileTable(ctrl) : renderTable(ctrl))
        ]);
    }

    function PicotableController() {
        var ctrl = this;
        ctrl.id = "" + 0 | (Math.random() * 0x7FFFFFF);
        ctrl.vm = {
            url: m.prop(null),
            sort: m.prop(null),
            filterEnabled: m.prop({}),
            filterValues: m.prop({}),
            page: m.prop(1),
            perPage: m.prop(20),
            perPageChoices: m.prop([20, 50, 100, 200]),
            showHeader: m.prop(true),
            data: m.prop(null),
            renderMode: m.prop("normal"),
            showMobileFilterSettings: m.prop(false),
            pickId: m.prop(null)
        };
        ctrl.setRenderMode = function(mode) {
            var oldMode = ctrl.vm.renderMode();
            ctrl.vm.renderMode(mode);
            if (mode !== oldMode) ctrl.refreshSoon();
        };
        ctrl.adaptRenderMode = function() {
            var width = window.innerWidth;
            ctrl.setRenderMode(width < 992 ? "mobile" : "normal");
        };
        ctrl.setSource = function(url) {
            ctrl.vm.url(url);
            ctrl.refreshSoon();
        };
        ctrl.setSortColumn = function(colId) {
            var sortValue = null;
            if (colId && colId.length && colId !== "null") {
                if (/^[+-]/.test(colId)) {
                    sortValue = colId;
                } else {
                    var currentSort = ctrl.vm.sort();
                    if (currentSort === "+" + colId) sortValue = "-" + colId;
                    else if (currentSort === "-" + colId) sortValue = null;
                    else sortValue = "+" + colId;
                }
            }
            ctrl.vm.sort(sortValue);
            ctrl.refreshSoon();
        };
        ctrl.getFilterValue = function(colId) {
            return ctrl.vm.filterValues()[colId];
        };
        ctrl.setFilterValue = function(colId, value) {
            var filters = ctrl.vm.filterValues();
            if (typeof value === "string" && Util.trim(value) === "") {
                // An empty string is invalid for filtering
                value = null;
            }
            filters[colId] = value;
            filters = Util.omitNulls(filters);
            ctrl.vm.filterValues(filters);
            ctrl.refreshSoon();
        };
        ctrl.resetFilters = function() {
            ctrl.vm.filterValues({});
            ctrl.refreshSoon();
        };
        ctrl.setPage = function(newPage) {
            newPage = 0 | newPage;
            if (isNaN(newPage) || newPage < 1) newPage = 1;
            ctrl.vm.page(newPage);
            ctrl.refreshSoon();
        };
        var refreshTimer = null;
        ctrl.refresh = function() {
            clearTimeout(refreshTimer);
            refreshTimer = null;
            var url = ctrl.vm.url();
            if (!url) return;
            var data = {
                sort: ctrl.vm.sort(),
                perPage: 0 | ctrl.vm.perPage(),
                page: 0 | ctrl.vm.page(),
                filters: ctrl.vm.filterValues()
            };
            const params = m.route.parseQueryString(decodeURI(location.search));
            params.jq = JSON.stringify(data);
            m.request({
                method: "GET",
                url: url,
                data: params
            }).then(ctrl.vm.data, function() {
                alert("An error occurred.");
            });
            ctrl.saveSettings();
        };
        ctrl.refreshSoon = function() {
            if (refreshTimer) return;
            refreshTimer = setTimeout(function() {
                ctrl.refresh();
            }, 20);
        };
        ctrl.saveSettings = function() {
            if (!storage) return;
            storage.setItem("picotablePerPage", ctrl.vm.perPage());
        };
        ctrl.loadSettings = function() {
            if (!storage) return;
            var perPage = 0 | storage.getItem("picotablePerPage");
            if (perPage > 1) ctrl.vm.perPage(perPage);

            // See if we're in pick mode...
            var pickMatch = /pick=([^&]+)/.exec(location.search);
            ctrl.vm.pickId(pickMatch ? pickMatch[1] : null);
        };
        ctrl.pickObject = function(object) {
            var opener = window.opener;
            if (!opener) {
                alert("Window has no opener. Can't pick object.");
                return;
            }
            var text = null;  // Try to figure out a name for the object
            Util.map(["_text", "_name", "title", "name", "text"], function(prop) {
                if (!text && object[prop]) text = object[prop];
            });
            if (!text && object._abstract && object._abstract.length > 0) {
                text = object._abstract[0];
                if (text.text) text = text.text; // Unwrap possible abstract text
            }
            if (!text) text = "#" + object._id;
            opener.postMessage({
                "pick": {
                    "id": ctrl.vm.pickId(),
                    "object": {
                        "id": object._id,
                        "text": text,
                        "url": object._url
                    }
                }
            }, "*");
            event.preventDefault();
        };
        ctrl.loadSettings();
        ctrl.adaptRenderMode();
        window.addEventListener("resize", Util.debounce(ctrl.adaptRenderMode, 100));

        // Replace Mithril's deferred error monitor with one that can ignore JSON-parsing syntax errors.
        // See https://lhorie.github.io/mithril/mithril.deferred.html#the-exception-monitor
        m.deferred.onerror = function(e) {
            if (e.toString().match(/^SyntaxError/)) return;

            // Original onerror behavior below.
            if ({}.toString.call(e) === "[object Error]" && !e.constructor.toString().match(/ Error/)) throw e;
        };
    }

    var generator = function(container, dataSourceUrl) {
        this.ctrl = m.mount(container, {view: PicotableView, controller: PicotableController});
        this.ctrl.setSource(dataSourceUrl);
    };
    generator.lang = lang;
    return generator;
}(window.m, window.localStorage));
/* eslint-disable */
if (typeof module !== "undefined" && module !== null && module.exports) module.exports = Picotable;
else if (typeof define === "function" && define.amd) define(function() {
    return Picotable;
});
