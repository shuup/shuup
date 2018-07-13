/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
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

        function debounce(func, wait, immediate=false) {
            let context, args, timestamp, timeout, result;

            function debounced() {
                context = this;
                args = arguments;
                timestamp = new Date().getTime();

                if (!timeout) {
                    m.startComputation();

                    timeout = setTimeout(later, wait);

                    if (immediate) {
                        result = func.apply(context, args);
                        context = args = null;
                    }
                }
                return result;
            }

            function later() {
                const elapsed = new Date().getTime() - timestamp;

                if (elapsed < wait && elapsed > 0) {
                    timeout = setTimeout(later, wait - elapsed);
                } else {
                    timeout = null;

                    if (!immediate) {
                        result = func.apply(context, args);
                        context = args = null;
                    }
                    m.endComputation();
                }
            }

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
        "MASS_ACTIONS": gettext("Mass actions"),
        "RANGE_FROM": gettext("From"),
        "RANGE_TO": gettext("To"),
        "ITEMS_PER_PAGE": gettext("Items per page"),
        "PAGE": gettext("Page"),
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
            if (page === 1 || page === paginationData.nPages || Math.abs(page - currentPage) <= 2) {
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
            }
        };
    }

    function buildColumnChoiceFilter(ctrl, col, value) {
        var setFilterValueFromSelect = function() {
            var valueJS = JSON.parse(this.value);
            ctrl.setFilterValue(col.id, valueJS);
        };
        var select2Config = function() {
            return function(el, isInit) {
                if(!isInit) {
                    $(el).select2();
                }
            };
        };

        var select = m("select.form-control", {
            config: col.filter.select2? select2Config(): null,
            value: JSON.stringify(value),
            onchange: setFilterValueFromSelect
        }, Util.map(col.filter.choices, function(choice) {
            return m("option", {value: JSON.stringify(choice[0]), key: choice[0]}, choice[1]);
        }));
        return m("div.choice-filter", select);
    }

    function getDefaultValues(ctrl) {
        const data = ctrl.vm.data();
        const filters = {};
        for (var i = 0; i < data.columns.length; i++) {
            if (data.columns[i].filter){
                var value = data.columns[i].filter.defaultChoice;
                if (value) {
                    filters[data.columns[i].id] = value;
                }
            }
        }

        return filters;
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
        var useDatepicker = false;
        if(attrs.type === "date") {
            // use a normal text input since mixing a date input and the datepicker together works weird in chrome
            useDatepicker = true;
            attrs.type = "text";
        }
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
            config: useDatepicker? ctrl.datePicker() : debounceChangeConfig(500)
        }));
        var maxInput = m("input.form-control", Util.extend({}, attrs, {
            value: Util.stringValue(value.max),
            placeholder: lang.RANGE_TO,
            onchange: function() {
                setFilterValueFromInput.call(this, "max");
            },
            config: useDatepicker? ctrl.datePicker() : debounceChangeConfig(500)
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
            placeholder: col.filter.placeholder || interpolate(gettext("Filter by %s"), [col.title]),
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

    function buildColumnHeaderCell(ctrl, col, columnNumber) {
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
        var columnSettings = {key: col.id, className: cx(classSet), onclick: columnOnClick};
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        if (massActions.length) {
            if (columnNumber === 0) {
                columnSettings.className += " hidden";
            }
            if (columnNumber === 1) {
                columnSettings.colspan = 2;
            }
        }
        return m("th", columnSettings, [sortIndicator, " ", col.title]);
    }

    function buildColumnFilterCell(ctrl, col, columnNumber) {
        var filterControl = null;
        if (col.filter) {
            filterControl = buildColumnFilter(ctrl, col);
        }
        var columnSettings = {key: col.id, className: col.className || ""};
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        if (massActions.length) {
            if (columnNumber === 0) {
                columnSettings.className += " hidden";
            }
            if (columnNumber === 1) {
                columnSettings.colspan = 2;
            }
        }
        return m("th", columnSettings, [filterControl]);
    }

    function renderTable(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) {  // Not loaded, don't return anything
            return;
        }

        // Set default filter values
        var defaultValues = Util.extend(getDefaultValues(ctrl), ctrl.vm.filterValues());
        ctrl.vm.filterValues(defaultValues);

        // Build header
        var columnHeaderCells = Util.map(data.columns, function(col, columnNumber) {
            return buildColumnHeaderCell(ctrl, col, columnNumber);
        });
        var columnFilterCells = (
            Util.any(data.columns, Util.property("filter")) ?
            Util.map(data.columns, function(col, columnNumber) {
                return buildColumnFilterCell(ctrl, col, columnNumber);
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

        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);

        // Build body
        var isPick = !!ctrl.vm.pickId();
        var rows = Util.map(data.items, function(item) {
            var rowSettings = {key: "item-" + item._id};
            if (massActions.length) {
                rowSettings.onclick = (function() {
                    ctrl.saveCheck(item);
                });
                rowSettings.class = ctrl.isChecked(item) ? "active" : "";
            }
            return m("tr", rowSettings, Util.map(data.columns, function(col, idx) {
                var content;
                if (idx === 0 && massActions.length) {
                    content = m("input[type=checkbox]", {
                        value: item.type + "-" + item._id,
                        class: "row-selection",
                        onclick: Util.boundPartial(ctrl, ctrl.saveCheck, item),
                        checked: ctrl.isChecked(item)
                    });
                }
                else {
                    content = item[col.id] || "";
                }
                if (col.raw) {
                    content = m.trust(content);
                }
                if (col.linked) {
                    if (isPick) {
                        content = m("a", {
                            href: "#",
                            onclick: Util.boundPartial(ctrl, ctrl.pickObject, item)
                        }, content);
                    } else if (item._url) {
                        content = m("a", {href: item._url, onclick:preventSelect}, content);
                    }
                }
                return m("td", {key: "col-" + col.id, className: col.className || ""}, [content]);
            }));
        });
        var tbody = m("tbody", rows);
        var massActionsClass = massActions.length ? ".has-mass-actions" : "";
        return m("table.table.table-striped.picotable-table" + massActionsClass, [thead, tfoot, tbody]);
    }

    function preventSelect(event) {
        event.stopPropagation();
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
        return m("div.mobile-filters.shuup-modal-bg", {key: "mobileFilterModal"}, [
            m("div.shuup-modal-container", [
                m("div.shuup-modal-header", [
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
                    ctrl.refresh();
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

        // Set default filter values
        var defaultValues = Util.extend(getDefaultValues(ctrl), ctrl.vm.filterValues());
        ctrl.vm.filterValues(defaultValues);

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
            var element = (item._linked_in_mobile ? m("a.inner", linkAttrs, content) : m("span.inner", content));
            return m("div.list-element", element);
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

    function renderMassActions(ctrl) {
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        var isPick = !!ctrl.vm.pickId();
        if (massActions === null || isPick) {
            return "";
        }
        var select2Config = function() {
            return function(el, isInit) {
                if(!isInit) {
                    $(el).select2();
                }
            };
        };

        const totalItemCount = ctrl.vm.data().pagination.nItems;
        if (totalItemCount === 0) {
            return "";
        }
        const listedItemCount = ctrl.vm.data().items.length;
        const initialMassActions = [
            {key: 0, value: gettext("Select Action")},
            {key: "unselect_all", value: gettext("Clear Selections")},
            {key: "select_all", value: gettext("Select All")},
            {key: "select_listed", value: interpolate(gettext("Select All %s Items"), [listedItemCount])},
        ];
        massActions = initialMassActions.concat(massActions);

        return m("div.picotable-mass-actions", [
            (ctrl.vm.allItemsSelected() ? m("p", interpolate(gettext("All %s Items Selected"), [totalItemCount])) : null),
            m("select.picotable-mass-action-select.form-control",
                {
                    id: "mass-action-select" + ctrl.id,
                    config: select2Config(),
                    value: 0,
                    onchange: m.withAttr("value", function(value) {
                        ctrl.doMassAction(value);
                    })
                },
                Util.map(massActions, function(obj) {
                    const defaultKeys = ["key", "value"];
                    const data = {
                        value: obj.key
                    };
                    Object.keys(obj).forEach((key) => {
                        if (!defaultKeys.includes(defaultKeys)) {
                            const dataKey = key.replace("_", "-");
                            data["data-" + dataKey] = obj[key];
                        }
                    });
                    return m("option", data, obj.value);
                })
            ),
        ]);
    }

    function renderHeader(ctrl) {
        var itemInfo = (ctrl.vm.data() ? ctrl.vm.data().itemInfo : null);
        return m("div.picotable-header", [
            renderMassActions(ctrl),
            m("div.picotable-items-per-page-ctr", [
                m("select.picotable-items-per-page-select.form-control",
                    {
                        id: "pipps" + ctrl.id,
                        value: ctrl.vm.perPage(),
                        onchange: m.withAttr("value", function(value) {
                            ctrl.vm.perPage(value);
                            ctrl.refresh();
                        })
                    },
                    Util.map(ctrl.vm.perPageChoices(), function(value) {
                        return m("option", { value: value }, `${value} / ${lang.PAGE}`);
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

    function PicotableController(ctrl) {
        var ctrl = this;
        ctrl.id = "" + 0 | (Math.random() * 0x7FFFFFF);
        ctrl.vm = {
            url: m.prop(null),
            sort: m.prop(null),
            filterEnabled: m.prop({}),
            filterValues: m.prop({}),
            checkboxes: m.prop([]),
            allItemsSelected: m.prop(false),
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
            if (mode !== oldMode) ctrl.refresh();
        };
        ctrl.adaptRenderMode = function() {
            var width = window.innerWidth;
            ctrl.setRenderMode(width < 992 ? "mobile" : "normal");
        };
        ctrl.setSource = function(url) {
            ctrl.vm.url(url);
            ctrl.refresh();
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
            ctrl.refresh();
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
            ctrl.refresh();
        };
        ctrl.resetFilters = function() {
            ctrl.vm.filterValues({});
            ctrl.refresh();
        };
        ctrl.resetCheckboxes = function() {
            ctrl.vm.allItemsSelected(false);
            ctrl.vm.checkboxes([]);
        };
        ctrl.saveCheck = function(object) {
            var originalValues = ctrl.vm.checkboxes();
            var items = originalValues.filter(function(i) { return i !== object._id; });

            if (items.length < originalValues.length) {
                ctrl.vm.checkboxes(items);
            }
            else {
                originalValues.push(object._id);
                ctrl.vm.checkboxes(originalValues);
            }

            $(object).toggleClass("active");
        };
        ctrl.isChecked = function(object) {
            var originalValues = ctrl.vm.checkboxes();
            const checked = originalValues.filter(function(i) { return i === object._id; });
            return checked.length > 0;
        };
        ctrl.getMassActionResponse = function(xhr) {
            if (xhr.status === 200) {
                var filename = "";
                var disposition = xhr.getResponseHeader("Content-Disposition");
                if (disposition && disposition.indexOf("attachment") !== -1) {
                    var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    var matches = filenameRegex.exec(disposition);
                    if (matches !== null && matches[1]) filename = matches[1].replace(/['"]/g, "");
                }
                var type = xhr.getResponseHeader("Content-Type");

                var blob = new Blob([xhr.response], { type: type });
                if (typeof window.navigator.msSaveBlob !== "undefined") {
                    // IE workaround for "HTML7007: One or more blob URLs
                    // were revoked by closing the blob for which they were
                    // created. These URLs will no longer resolve as the data
                    // backing the URL has been freed."
                    window.navigator.msSaveBlob(blob, filename);
                }
                else {
                    var URL = window.URL || window.webkitURL;
                    var downloadUrl = URL.createObjectURL(blob);

                    if (filename) {
                        // use HTML5 a[download] attribute to specify filename
                        var a = document.createElement("a");
                        // safari doesn't support this yet
                        if (typeof a.download === "undefined") {
                            window.location = downloadUrl;
                        } else {
                            a.href = downloadUrl;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                        }
                    }
                    else {
                        var redirects = $("option[value="+window.savedValue+"]").data("redirects");
                        if (redirects) {
                            window.location = $("option[value="+window.savedValue+"]").data("redirect-url");
                        }
                        ctrl.resetCheckboxes();
                        $(".picotable-mass-action-select").val(0);
                        ctrl.refresh();
                        setTimeout(function() {
                            window.Messages.enqueue({tags: "success", text: gettext("Mass Action complete.")});
                        }, 1000);
                    }
                    setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
                }
            } else {
                ctrl.resetCheckboxes();
                $(".picotable-mass-action-select").val(0);
                ctrl.refresh();
                setTimeout(function() {
                    window.Messages.enqueue({tags: "error", text: gettext("Something went wrong.")});
                }, 1000);
            }
        };
        ctrl.doMassAction = function(value) {
            switch (value) {
                case "select_all":
                    ctrl.selectAllProducts();
                    return;
                case "select_listed":
                    ctrl.selectAllListedProducts();
                    return;
                case "unselect_all":
                    ctrl.resetCheckboxes();
                    return;
            }

            var originalValues = ctrl.vm.checkboxes();
            window.savedValue = value;
            if (originalValues.length === 0) {
                alert(gettext("You haven't selected anything"));
                return;
            }
            if(value === 0) {
                return;
            }

            if (!confirm(gettext("Confirm action by clicking OK!"))) {
                $(".picotable-mass-action-select").val(0);
                ctrl.refresh();
                return;
            }

            var xhrConfig = function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.ShuupAdminConfig.csrf);
                xhr.setRequestHeader("Content-type", "application/json");
                xhr.responseType = "blob";
            };
            var payload = {
                "action": value,
                "values": (ctrl.vm.allItemsSelected() ? "all" : originalValues)
            };

            const callback = $("option[value="+value+"]").data("callback");
            if (callback && window[callback]) {
                window[callback](payload.values);
            } else {
                m.request({
                    method: "POST",
                    url: window.location.pathname,
                    data: payload,
                    extract:ctrl.getMassActionResponse,
                    config: xhrConfig
                });
            }
        };
        ctrl.selectAllListedProducts = function() {
            ctrl.vm.allItemsSelected(false);
            ctrl.vm.checkboxes(ctrl.vm.data().items.map(item => item._id));
        };
        ctrl.selectAllProducts = function() {
            ctrl.selectAllListedProducts();
            ctrl.vm.allItemsSelected(true);
        };
        ctrl.setPage = function(newPage) {
            newPage = 0 | newPage;
            if (isNaN(newPage) || newPage < 1) newPage = 1;
            ctrl.vm.page(newPage);
            ctrl.refresh();
        };
        ctrl.refresh = function() {
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
        ctrl.saveSettings = function() {
            if (!storage) return;
            storage.setItem("picotablePerPage", ctrl.vm.perPage());
        };
        ctrl.loadSettings = function() {
            if (!storage) return;
            var perPage = 0 | storage.getItem("picotablePerPage");
            if (perPage > 1) {
                ctrl.vm.perPage(perPage);
            }

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
        ctrl.datePicker = function() {
            return function(el, isInitialized) {
                if(isInitialized) {
                    return;
                }

                $(el).datetimepicker({
                    format: "yyyy-mm-dd",
                    autoclose: true,
                    todayBtn: true,
                    todayHighlight: true,
                    fontAwesome: true,
                    minView: 2
                });
            }
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
if (typeof module !== "undefined" && module !== null && module.exports) {
    module.exports = Picotable;
}
else if (typeof define === "function" && define.amd) define(function() {
    return Picotable;
});
