/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-plusplus, prefer-const, curly, no-bitwise */
/* exported Picotable */
/* global alert, require */

const Picotable = (function (m, storage) {
    "use strict";
    m = m || require("mithril");

    const Util = (function () {
        function property(propertyName) {
            return function (obj) {
                return obj[propertyName];
            };
        }

        function map(obj, callback) {
            if (Array.isArray(obj)) {
                return obj.map(callback);
            }
            return Object.keys(obj).map(function (key) {
                return callback(obj[key], key, obj);
            });
        }

        function any(obj, callback) {
            if (Array.isArray(obj)) {
                return obj.some(callback);
            }
            return Object.keys(obj).some(function (key) {
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
            map(object, function (value, key) {
                if (value !== null) {
                    outputObject[key] = value;
                }
            });
            return outputObject;
        }

        function debounce(func, wait, immediate = false) {
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
            return function (/* args */) {
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
        "APPLY_FILTERS": gettext("Apply filters"),
        "SORT_BY": gettext("Sort by"),
        "SORT_ASC": gettext("ascending"),
        "SORT_DESC": gettext("descending"),
        "SORT_DEFAULT": gettext("Default sorting")
    };

    const cx = function generateClassName(classSet) {
        var classValues = [];
        Util.map((classSet || {}), function (flag, key) {
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
                const li = m("li", { key: "dummy" + (nDummy++), className: "disabled" }, m("a", { href: "#" }, "\u22EF"));
                pageLinks.splice(i, 0, li);
                i++;
            }
        }
    }

    function paginator(paginationData, setPage, extraClass) {
        if (paginationData.nItems === 0) return m("nav");

        var callback = m.withAttr("rel", setPage);
        var currentPage = paginationData.pageNum;
        var pageLinks = [];
        var pageLink = function (page, title) {
            return m("a.page-link", { rel: page, href: "#", onclick: callback }, title || page);
        };

        for (var page = 1; page <= paginationData.nPages; page++) {
            if (page === 1 || page === paginationData.nPages || Math.abs(page - currentPage) <= 2) {
                var li = m("li.page-item", { key: page, className: cx({ active: currentPage === page }) }, pageLink(page));
                li._page = page;
                pageLinks.push(li);
            }
        }

        addDummies(pageLinks);

        var prevLink = m("li.page-item", {
            key: "previous",
            className: cx({ disabled: currentPage === 1 })
        }, pageLink(currentPage - 1, gettext("Previous")));

        var nextLink = m("li.page-item", {
            key: "next",
            className: cx({ disabled: currentPage === paginationData.nPages })
        }, pageLink(currentPage + 1, gettext("Next")));

        let css = '';

        if (typeof extraClass !== 'undefined') {
            css = `.${extraClass}`;
        }

        return m("nav" + css, m("ul.pagination", prevLink, pageLinks, nextLink));
    }

    function debounceChangeConfig(timeout) {
        return function (el, isInit, context) {
            if (!isInit) {
                el.oninput = context.debouncedOnInput = Util.debounce(el.onchange, timeout);
            }
        };
    }

    function buildColumnChoiceFilter(ctrl, col, value) {
        var setFilterValueFromSelect = function () {
            var valueJS = JSON.parse(this.value);
            ctrl.setFilterValue(col.id, valueJS);
        };
        var select2Config = function () {
            return function (el, isInit) {
                if (!isInit) {
                    $(el).select2({
                        dropdownParent: $(el).parent()
                    });

                    const body = $('body').find('.select2-search-input');
                    const select2Span = $(el).next();
                    const elements = [select2Span, body];

                    elements.map(el => el.on('click', e => preventSelect(e)));

                }
            };
        };

        var select = m("select.form-control", {
            config: (col.filter.select2) ? select2Config() : null,
            value: JSON.stringify(value),
            onchange: setFilterValueFromSelect,
            onclick: preventSelect,
        }, Util.map(col.filter.choices, function (choice) {
            return m("option", {
                value: JSON.stringify(choice[0]),
                key: choice[0]
            },
                choice[1]);
        })
        );

        const label = m("h6", col.title);
        return m("div.choice-filter", [label, select]);
    }

    function getDefaultValues(ctrl) {
        const data = ctrl.vm.data();
        const filters = {};
        for (var i = 0; i < data.columns.length; i++) {
            if (data.columns[i].filter) {
                var value = data.columns[i].filter.defaultChoice;
                if (value) {
                    filters[data.columns[i].id] = value;
                }
            }
        }

        return filters;
    }

    function buildColumnRangeFilter(ctrl, col, value) {
        var setFilterValueFromInput = function (which) {
            const filterObj = Util.extend({}, ctrl.getFilterValue(col.id) || {}); // Copy current filter object
            var newValue = this.value;
            if (!Util.trim(newValue)) {
                newValue = null;
            }
            filterObj[which] = newValue;
            ctrl.setFilterValue(col.id, filterObj);
        };
        var attrs = { "type": col.filter.range.type || "text" };
        var useDatepicker = false;

        if (attrs.type === "date") {
            // use a normal text input since mixing a date input and the datepicker together works weird in chrome
            useDatepicker = true;
            attrs.type = "text";
        }

        Util.map(["min", "max", "step"], function (key) {
            var val = col.filter.range[key];
            if (!(val === undefined || val === null)) {
                attrs[key] = val;
                attrs.type = "number";  // Any of these set means we're talking about numbers
            }
        });

        value = value || {};

        var minInput = m("input.form-control", Util.extend({}, attrs, {
            key: "min",
            value: Util.stringValue(value.min),
            placeholder: lang.RANGE_FROM,
            onchange: function (e) {
                if (value.min !== e.target.value) {
                    setFilterValueFromInput.call(this, "min");
                }
            },
            config: useDatepicker ? ctrl.datePicker() : debounceChangeConfig(500)
        }));

        var maxInput = m("input.form-control", Util.extend({}, attrs, {
            key: "max",
            value: Util.stringValue(value.max),
            placeholder: lang.RANGE_TO,
            onchange: function (e) {
                if (value.max !== e.target.value) {
                    setFilterValueFromInput.call(this, "max");
                }
            },
            config: useDatepicker ? ctrl.datePicker() : debounceChangeConfig(500)
        }));

        const label = m("h6", col.title);

        return m("div.range-filter", [
            label,
            m("div.input-group", [minInput, maxInput])
        ]);
    }

    function buildColumnTextFilter(ctrl, col, value) {
        var setFilterValueFromInput = function () {
            ctrl.setFilterValue(col.id, this.value);
        };

        const label = m("h6", col.title);

        var input = m("input.form-control", {
            type: col.filter.text.type || "text",
            value: Util.stringValue(value),
            placeholder: col.filter.placeholder || interpolate(gettext("Filter by %s"), [col.title]),
            onchange: setFilterValueFromInput,
            config: debounceChangeConfig(500)
        });
        return m("div.text-filter", [label, input]);
    }

    // Check to see if it's any of the types of filters that
    // we want to highlight by placing it at the top of the table
    // FIXME: remove fixed col names from here and bring from col definition
    function isLiftFilter(col) {
        return (col.allowHighlight && ["name", "customer", "title", "code"].includes(col.id));
    }

    function buildNameFilter(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) return; // Not loaded, don't return anything

        const [col] = data.columns.filter(column => isLiftFilter(column));

        if (col !== undefined && col.filter) {
            var value = ctrl.getFilterValue(col.id);

            var setFilterValueFromInput = function () {
                ctrl.setFilterValue(col.id, this.value);
            };

            var input = m("input.form-control", {
                type: "text",
                value: Util.stringValue(value),
                placeholder: col.filter.placeholder || interpolate(gettext("Filter by %s"), [col.title]),
                onchange: setFilterValueFromInput,
                config: debounceChangeConfig(500)
            });

            var filterByNameContainer = m("div.input-group", [
                input,
                m("div.input-group-append", [
                    m(
                        "button.btn.btn-primary",
                        {
                            onclick: () => {
                                ctrl.saveFilters();
                                ctrl.refresh();
                            }
                        },
                        lang.APPLY_FILTERS
                    ),
                ]),
            ])

            return m('div.picotable-filter-name.ml-2.mr-2', filterByNameContainer);
        }
    }

    function buildColumnHeaderCell(ctrl, col, columnNumber) {
        var sortIndicator = null;
        var classSet = { "": col.className };
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
            columnOnClick = function () {
                ctrl.setSortColumn(col.id);
            };
        }
        var columnSettings = { key: col.id, className: cx(classSet), onclick: columnOnClick };
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        if (massActions.length) {
            if ((col.id === "primary_image") || (columnNumber === 0)) {
                columnSettings.className += " hidden-cell";
            }
        }
        return m("th", columnSettings, [m("span", "", col.title), " ", sortIndicator]);
    }

    function renderFooter(ctrl) {
        var data = ctrl.vm.data();

        if (data === null) {  // Not loaded, don't return anything
            return;
        }

        var itemInfo = (ctrl.vm.data() ? ctrl.vm.data().itemInfo : null);

        // Build footer
        const PageSizeSelector = {
            view: function () {
                return m("div.btn-group.dropup.picotable-items-per-page-ctr", [
                    m("button.btn.btn-default.dropdown-toggle",
                        {
                            type: "button",
                            id: "pipps" + ctrl.id + 1,
                            "data-toggle": "dropdown",
                            "aria-haspopup": "true",
                            "aria-expanded": "false",
                        }, `${ctrl.vm.perPage()} / ${lang.PAGE}`),
                    m("div.dropdown-menu", {
                        "aria-labelledby": "pipps" + ctrl.id + 1,
                    },
                        Util.map(ctrl.vm.perPageChoices(), function (value) {
                            return m("a.dropdown-item",
                                {
                                    href: "#",
                                    "data-value": value,
                                    onclick: m.withAttr("data-value", function (value) {
                                        ctrl.vm.perPage(value);
                                        ctrl.refresh(true);
                                    })
                                }, `${value} / ${lang.PAGE}`);
                        })
                    )
                ]);
            }
        };

        var FootCell = {
            view: function () {
                return paginator(data.pagination, ctrl.setPage, "d-none d-lg-flex");
            }
        };

        const selectoClasses = "d-flex pt-2 pb-2 justify-content-between align-items-center";
        return m("div", { class: selectoClasses }, [
            m.component(PageSizeSelector),
            m("div.picotable-item-info", itemInfo),
            m.component(FootCell),
        ]);
    }

    function renderTable(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) {  // Not loaded, don't return anything
            return;
        } else if (data.items.length === 0) {
            return;
        }

        // Set default filter values
        var defaultValues = Util.extend(getDefaultValues(ctrl), ctrl.vm.filterValues());
        ctrl.vm.filterValues(defaultValues);

        // Build header
        var columnHeaderCells = Util.map(data.columns, function (col, columnNumber) {
            return buildColumnHeaderCell(ctrl, col, columnNumber);
        });

        var thead = m("thead", [
            m("tr.headers", columnHeaderCells)
        ]);

        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);

        // Build body
        var isPick = !!ctrl.vm.pickId();
        var rows = Util.map(data.items, function (item) {
            var rowSettings = { key: "item-" + item._id };
            rowSettings.onclick = (function (e) {
                if (massActions.length) {
                    ctrl.saveCheck(item);
                } else if (item._url && e.target.className !== "row-selection") {
                    location.href = item._url;
                }
            });
            rowSettings.class = "";
            if (item._extra && item._extra.class) {
                rowSettings.class += item._extra.class;
            }
            if (ctrl.isChecked(item)) {
                rowSettings.class += " active";
            }
            return m("tr", rowSettings, Util.map(data.columns, function (col, idx) {
                var content;
                if (idx === 0 && massActions.length && (!item.hasOwnProperty("popup") || item.popup === false)) {
                    content = m("div.input-checkbox", { onclick: preventSelect }, [
                        m("input[type=checkbox]", {
                            id: item._id,
                            value: item.type + "-" + item._id,
                            class: "row-selection",
                            onclick: Util.boundPartial(ctrl, ctrl.saveCheck, item),
                            checked: ctrl.isChecked(item)
                        }),
                        m("label", { for: item._id, }),
                        (item._url ? m("a", {
                            href: item._url,
                            title: gettext("Edit")
                        }, m("i.fa.fa-edit")) : null),
                    ]);
                } else if (idx === 0 && massActions.length && item.popup === true) {
                    content = m("div.input-checkbox", { onclick: preventSelect }, [
                        m("button[type=button]", {
                            class: "browse-btn btn btn-primary btn-sm",
                            onclick: Util.boundPartial(ctrl, ctrl.pickObject, item)
                        }, [
                            m("i.fa.fa-folder"),
                            gettext(" Select")
                        ])
                    ]);
                } else {
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
                    } else if (item._url && (col.id === "name" || col.id === "title" || col.id === "username")) {
                        content = m("a", {
                            href: item._url,
                            className: "row-" + col.id,
                        }, content);
                    } else {
                        content = m("span", {
                            className: "row-" + col.id
                        }, content);
                    }
                }
                return m("td", { key: "col-" + col.id, className: col.className || "" }, [content]);
            }));
        });
        var tbody = m("tbody", rows);
        var massActionsClass = massActions.length ? ".has-mass-actions" : "";

        return m("table.table.picotable-table" + massActionsClass, [thead, tbody]);
    }

    function preventSelect(event) {
        event.stopPropagation();
    }

    function getMobileFilterModal(ctrl) {
        var data = ctrl.vm.data();
        var filters = Util.map(data.columns, function (col) {
            if (!col.filter) return null;
            return m("div.single-filter",
                buildColumnFilter(ctrl, col)
            );
        });
        return m("div.mobile-filters.shuup-modal-bg", { key: "mobileFilterModal" }, [
            m("div.shuup-modal-container", [
                m("div.shuup-modal-header.d-flex.align-items-center", [
                    m("h4.mr-auto", [m("i.fa.fa-filter")], gettext("Filters")),
                    m(
                        "button.btn.btn-inverse.mr-2",
                        {
                            onclick: ctrl.resetFilters,
                            disabled: Util.isEmpty(ctrl.vm.filterValues())
                        },
                        lang.RESET
                    ),
                    m("button.btn.btn-default", {
                        onclick: function () {
                            ctrl.vm.showMobileFilterSettings(false);
                        }
                    }, gettext("Close")),
                ]),
                m("div.mobile-filters-content", [
                    filters,
                    m("div.apply-filters", [
                        m(
                            "button.btn.btn-block.btn-primary",
                            {
                                onclick: () => {
                                    ctrl.saveFilters();
                                    ctrl.refresh();
                                }
                            },
                            lang.APPLY_FILTERS
                        ),
                    ]),
                ]),
            ])
        ]);
    }

    function getMobileSortSelect(ctrl) {
        var data = ctrl.vm.data();
        var sortOptions = [];
        Util.map(data.columns, function (col) {
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
        sortOptions.unshift({ value: "", text: lang.SORT_DEFAULT });

        return m("select.picotable-mobile-sort.form-control",
            {
                id: "mobile-sort-select",
                value: (ctrl.vm.sort() || ""),
                onchange: m.withAttr("value", function (value) {
                    ctrl.setSortColumn(value);
                    ctrl.refresh();
                })
            },
            Util.map(sortOptions, function (so) {
                return m("option", { value: so.value }, so.text);
            })
        );
    }

    function renderMobileTable(ctrl) {
        var data = ctrl.vm.data();
        if (data === null) return; // Not loaded, don't return anything

        // Set default filter values
        var defaultValues = Util.extend(getDefaultValues(ctrl), ctrl.vm.filterValues());
        ctrl.vm.filterValues(defaultValues);

        const filterCount = ctrl.getActiveFilterCount();

        var isPick = !!ctrl.vm.pickId();
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        var listItems = Util.map(data.items, function (item) {
            var content = null;
            if (item._abstract && item._abstract.length) {
                content = Util.map(item._abstract, function (line) {
                    if (!line) return;
                    if (typeof line === "string") line = { text: line };
                    if (!line.text) return;
                    if (line.raw) line.text = m.trust(line.raw);

                    const rowClasses = ["row", "mobile-row."];
                    if (line.title) rowClasses.push("with-title");
                    if (line.class) rowClasses.push(line.class);
                    if (item._extra && item._extra.class) {
                        rowClasses.push(...item._extra.class.split(" "));
                    }
                    return m("." + rowClasses.join("."), [
                        (line.class && massActions.length && (!item.hasOwnProperty("popup") || item.popup === false) ?
                            m("div.input-checkbox", { onclick: preventSelect }, [
                                m("input[type=checkbox]", {
                                    id: item._id,
                                    value: item.type + "-" + item._id,
                                    class: "row-selection",
                                    onclick: Util.boundPartial(ctrl, ctrl.saveCheck, item),
                                    checked: ctrl.isChecked(item)
                                }),
                                m("label", { for: item._id, }),
                                (item._url ? m("a.edit", {href: item._url}, m("i.fa.fa-edit")) : null)
                            ])
                        : (line.class && massActions.length && item.popup === true ?
                                m("div.input-checkbox", { onclick: preventSelect }, [
                                    m("button[type=button]", {
                                        class: "browse-btn btn btn-primary btn-sm",
                                        onclick: Util.boundPartial(ctrl, ctrl.pickObject, item)
                                    }, [
                                        m("i.fa.fa-folder"),
                                        gettext(" Select")
                                    ])
                                ])
                            : null)
                        ),
                        (line.title ? m(".col.title", line.title) : null),
                        m(".col.value", line.text)
                    ]);
                });
                if (!Util.any(content, function (v) {
                    return !!v;
                })) {
                    // Not a single valid line
                    content = null;
                }
            }
            if (content === null) {
                content = Util.map(data.columns, function (col) {
                    var colContent = item[col.id] || "";
                    if (col.raw) colContent = m.trust(colContent);
                    return m("div.mobile-row.row.with-title", [
                        m(".col.title", col.title),
                        m(".col.text-right", colContent)
                    ]);
                });
            }
            var linkAttrs = { href: item._url };
            if (isPick) {
                linkAttrs.onclick = Util.boundPartial(ctrl, ctrl.pickObject, item);
                linkAttrs.href = "#";
            }
            var element = null;
            if (massActions.length) {
                element = m("span.inner", {
                    class: "row-selection",
                    onclick: (e) => {
                        ctrl.saveCheck(item);
                    }
                }, content);
            } else {
                element = (item._linked_in_mobile ? m("a.inner", linkAttrs, content) : m("span.inner", content));
            }
            return m("div.list-element.col-12", element);
        });
        return m("div.mobile", [
            m("div.mobile-header.row", [
                m("div.col", [
                    m("button.btn.btn-default.btn-block.toggle-btn.position-relative",
                        {
                            onclick: function () {
                                ctrl.vm.showMobileFilterSettings(true);
                            }
                        },
                        [m("i.fa.fa-filter")], gettext("Show filters"),
                        (filterCount ?
                            m("span.badge.badge-pill.badge-dark.active-filter-counter",
                            filterCount
                        ) : null),
                    )
                ]),
                m("div.col-sm-6", [
                    m("div.mobile-sort", getMobileSortSelect(ctrl))
                ])
            ]),
            (ctrl.vm.showMobileFilterSettings() ? getMobileFilterModal(ctrl) : null),
            m("hr"),
            m("div.mobile-items.row ", listItems),
            paginator(data.pagination, ctrl.setPage, "mobile-pagination")
        ]);
    }

    function renderMassActions(ctrl) {
        var massActions = (ctrl.vm.data() ? ctrl.vm.data().massActions : null);
        if (massActions.length === 0) {
            return "";
        }

        var isPick = !!ctrl.vm.pickId();
        if (massActions === null || isPick) {
            return "";
        }
        var select2Config = function () {
            return function (el, isInit) {
                if (!isInit) {
                    $(el).select2().data('select2').$dropdown.addClass('mass-action-dropdown');
                }
            };
        };


        const totalItemCount = ctrl.vm.data().pagination.nItems;
        if (totalItemCount === 0) {
            return "";
        }

        const listedItemCount = ctrl.vm.data().items.length;
        const initialMassActions = [
            { key: 0, value: gettext("Select Action") },
            { key: "unselect_all", value: gettext("Clear Selections") },
            { key: "select_all", value: gettext("Select All") },
            { key: "select_listed", value: interpolate(gettext("Select All %s Items"), [listedItemCount]) },
        ];
        massActions = initialMassActions.concat(massActions);

        return m("div.picotable-mass-actions", [
            m("select.picotable-mass-action-select",
                {
                    id: "mass-action-select" + ctrl.id,
                    config: select2Config(),
                    value: 0,
                    onchange: m.withAttr("value", function (value) {
                        ctrl.doMassAction(value);
                    }),
                },
                Util.map(massActions, function (obj) {
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

    function buildColumnFilter(ctrl, col) {
        var value = ctrl.getFilterValue(col.id);
        if (col.filter.choices) {
            return buildColumnChoiceFilter(ctrl, col, value);
        }
        if (col.filter.range) {
            return buildColumnRangeFilter(ctrl, col, value);
        }
        if (col.filter.text && !isLiftFilter(col)) {
            return buildColumnTextFilter(ctrl, col, value);
        }
    }

    function buildColumnFilterCell(ctrl, col) {
        var filterControl = null;
        if (col.filter && !isLiftFilter(col)) {
            filterControl = buildColumnFilter(ctrl, col);
            var columnSettings = { key: col.id };
            return m("div.pt-2.pb-2", columnSettings, [filterControl]);
        }
    }

    function renderFilter(ctrl) {
        const data = ctrl.vm.data();
        if (data === null) return; // Not loaded, don't return anything

        const columnFilterCells = (
            data.columns.filter(col => col.filter) ?
                data.columns.map(col => {
                    if (!isLiftFilter(col)) {
                        return buildColumnFilterCell(ctrl, col);
                    }
                }) : null
        );

        function initSelect() {
            const filter = ctrl.vm.filterValues();
            return filter;
        }

        const dropdownButtonSettings = {
            "id": "dropdownFilter",
            "data-toggle": "dropdown",
            "aria-haspopup": "true",
            "aria-expanded": "false",
            onclick: initSelect,
        };

        const filterCount = ctrl.getActiveFilterCount();

        return m("div.picotable-filter.btn-group.d-none.d-lg-flex",
            m("button.btn.btn-default.btn-icon.dropdown-toggle",
                dropdownButtonSettings,
                m("i.fa.fa-filter"),
                gettext("Filters"),
                (filterCount > 0 ?
                    m("span.badge.badge-pill.badge-dark.active-filter-counter",
                    filterCount
                ) : null),
            ),
            m("div.dropdown-menu.dropdown-menu-right.pl-3.pr-3", {
                "aria-labelledby": "dropdownFilter"
            },
                (columnFilterCells ? m("div.filters.d-flex.flex-column", columnFilterCells) : null),
                m("div.picotable-reset-filters-ctr",
                    m(
                        "button.picotable-reset-filters-btn.btn.btn-block.btn-inverse",
                        {
                            onclick: ctrl.resetFilters,
                            disabled: Util.isEmpty(ctrl.vm.filterValues())
                        },
                        lang.RESET_FILTERS
                    )
                ),
                m("div.apply-filters", [
                    m(
                        "button.btn.btn-block.btn-primary",
                        {
                            onclick: () => {
                                ctrl.saveFilters();
                                ctrl.refresh();
                            }
                        },
                        lang.APPLY_FILTERS
                    ),
                ]),
            )
        );
    }

    function renderHeader(ctrl) {
        return m("div.picotable-header", [
            renderMassActions(ctrl),
            buildNameFilter(ctrl),
            renderFilter(ctrl)
        ]);
    }

    function buildEmptyState(ctrl) {
        const pageName = $('.main-header').text().toLocaleLowerCase();
        let title = "";
        if (pageName) {
            title = interpolate(gettext("There are no %s to show"), [pageName]);
        } else {
            title = gettext("There is no item to show");
        }
        if (Object.keys(ctrl.vm.filterValues()).length) {
            title = interpolate("%s %s", [title, gettext("with selected filters")]);
        }
        const button = $('.shuup-toolbar').find('.btn-primary');

        let buttonAttr;
        if (button.length > 0) {
            buttonAttr = {
                title: button.text(),
                href: button[0].pathname
            };
        }
        const markup = [
            m("h3", title),
            (buttonAttr ? m("p", gettext("How about creating a new entry?")) : null),
            (buttonAttr ? m("a.btn.btn-default", { href: buttonAttr.href }, buttonAttr.title) : null)
        ];

        const markupCss = "div.w-100.d-flex.flex-column.align-items-center.justify-content-center.text-center";
        return m(markupCss, markup);
    }

    function renderEmptyState(ctrl) {
        return m("div.picotable-empty", [buildEmptyState(ctrl)]);
    }

    function renderLoader() {
        return m("div.loader", [
            m("div.mt-4.mb-4.row", [
                m("div.btn.btn-default.pt-3.pb-3.mr-3", m("div.loader-block")),
                m("div.btn.btn-default.w-50.pt-3.pb-3.mr-auto"),
                m("div.btn.btn-default.pt-3.pb-3", m("div.loader-block")),
            ]),
            m("div.loader-content.row", [
                m("div.loader-content-header.col-12.w-100.ml-0", [
                    m("div.loader-block.w-100"),
                ]),
                m("div.d-flex.justify-content-center.h-50.col-12.pt-5.pb-5", [
                    m("div.loader-spinner")
                ])
            ])
        ]);
    }

    function PicotableView(ctrl) {
        const data = ctrl.vm.data();
        if (data === null) return;

        const showEmptyState = (ictrl) => {
            const content = [
                (ictrl.vm.renderMode() === "mobile" ? renderMobileTable(ictrl) : renderTable(ictrl)),
            ];
            if (data.items.length > 0) {
                content.push(renderFooter(ictrl));
            } else {
                content.push(renderEmptyState(ictrl));
            }
            return content;
        };

        return m("div.table-view", [
            (ctrl.vm.showHeader() ? renderHeader(ctrl) : null),
            (showEmptyState(ctrl)),
        ]);
    }

    function renderPicotable(ctrl) {
        return (ctrl.vm.isLoading) ? renderLoader() : PicotableView(ctrl);
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
            pickId: m.prop(null),
            isLoading: true
        };
        ctrl.setRenderMode = function (mode) {
            var oldMode = ctrl.vm.renderMode();
            ctrl.vm.renderMode(mode);
            if (mode !== oldMode) ctrl.refresh();
        };
        ctrl.adaptRenderMode = function () {
            var width = window.innerWidth;
            ctrl.setRenderMode(width < 992 ? "mobile" : "normal");
        };
        ctrl.setSource = function (url) {
            ctrl.vm.url(url);
            ctrl.refresh();
        };
        ctrl.setSortColumn = function (colId) {
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
        ctrl.getFilterValue = function (colId) {
            return ctrl.vm.filterValues()[colId];
        };
        ctrl.setFilterValue = function (colId, value) {
            var filters = ctrl.vm.filterValues();
            if (typeof value === "string" && Util.trim(value) === "") {
                // An empty string is invalid for filtering
                value = null;
            }
            filters[colId] = value;
            filters = Util.omitNulls(filters);
            ctrl.vm.filterValues(filters);
        };
        ctrl.getFilterKey = function () {
            var pieces = window.location.pathname.split("/").filter((piece) => piece.length);
            return interpolate("%s_filters", [pieces[pieces.length - 1]]);
        };
        ctrl.resetFilters = function () {
            ctrl.vm.filterValues({});
            storage.setItem(ctrl.getFilterKey(), JSON.stringify({}));
            ctrl.refresh();
        };
        ctrl.getFilters = function () {
            if (!storage) {
                return ctrl.vm.filterValues();
            }
            const filters = storage.getItem(ctrl.getFilterKey());
            return filters ? JSON.parse(filters) : {};
        };
        ctrl.getActiveFilterCount = function () {
            return Object.values(
                ctrl.getFilters()
            ).filter((value) => value && value !== "_all").length;
        }
        ctrl.saveFilters = function () {
            if (!storage) return;
            var filters = ctrl.vm.filterValues();
            storage.setItem(ctrl.getFilterKey(), JSON.stringify(filters));
        };
        ctrl.resetCheckboxes = function () {
            ctrl.vm.allItemsSelected(false);
            ctrl.vm.checkboxes([]);
        };
        ctrl.saveCheck = function (object) {
            var originalValues = ctrl.vm.checkboxes();
            var items = originalValues.filter(function (i) { return i !== object._id; });

            if (items.length < originalValues.length) {
                ctrl.vm.checkboxes(items);
            }
            else {
                originalValues.push(object._id);
                ctrl.vm.checkboxes(originalValues);
            }

            $(object).toggleClass("active");
        };
        ctrl.isChecked = function (object) {
            var originalValues = ctrl.vm.checkboxes();
            const checked = originalValues.filter(function (i) { return i === object._id; });
            return checked.length > 0;
        };
        ctrl.getMassActionResponse = function (xhr) {
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
                        var redirects = $("option[value=" + window.savedValue + "]").data("redirects");
                        if (redirects) {
                            window.location = $("option[value=" + window.savedValue + "]").data("redirect-url");
                        }
                        ctrl.resetCheckboxes();
                        $(".picotable-mass-action-select").val(0);
                        ctrl.refresh();
                        setTimeout(function () {
                            window.Messages.enqueue({ tags: "success", text: gettext("Success! Mass Action was completed.") });
                        }, 1000);
                    }
                    setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
                }
            } else {
                ctrl.resetCheckboxes();
                $(".picotable-mass-action-select").val(0);
                ctrl.refresh();
                setTimeout(function () {
                    window.Messages.enqueue({ tags: "error", text: gettext("Error! Something went wrong with the Mass Action.") });
                }, 1000);
            }
        };
        ctrl.doMassAction = function (value) {
            switch (value) {
                case "select_all":
                    ctrl.selectAllProducts();
                    const totalItemCount = ctrl.vm.data().pagination.nItems;
                    const selectAllMessage = interpolate(gettext("All %s Items Selected"), [totalItemCount]);
                    window.Messages.enqueue({ tags: "info", text: selectAllMessage });
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
                alert(gettext("Warning! You didn't select anything."));
                return;
            }
            if (value === 0) {
                return;
            }

            if (!confirm(gettext("Confirm action by clicking OK!"))) {
                $(".picotable-mass-action-select").val(0);
                ctrl.refresh();
                return;
            }

            var xhrConfig = function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.ShuupAdminConfig.csrf);
                xhr.setRequestHeader("Content-type", "application/json");
                xhr.responseType = "blob";
            };
            var payload = {
                "action": value,
                "values": (ctrl.vm.allItemsSelected() ? "all" : originalValues)
            };

            const callback = $("option[value=" + value + "]").data("callback");
            if (callback && window[callback]) {
                window[callback](payload.values);
            } else {
                m.request({
                    method: "POST",
                    url: window.location.pathname,
                    data: payload,
                    extract: ctrl.getMassActionResponse,
                    config: xhrConfig
                });
            }
        };
        ctrl.selectAllListedProducts = function () {
            ctrl.vm.allItemsSelected(false);
            ctrl.vm.checkboxes(ctrl.vm.data().items.map(item => item._id));
        };
        ctrl.selectAllProducts = function () {
            ctrl.selectAllListedProducts();
            ctrl.vm.allItemsSelected(true);
        };
        ctrl.setPage = function (newPage) {
            newPage = 0 | newPage;
            if (isNaN(newPage) || newPage < 1) newPage = 1;
            ctrl.vm.page(newPage);
            ctrl.refresh();
        };
        ctrl.refresh = function () {
            var url = ctrl.vm.url();

            ctrl.vm.isLoading = true;
            m.redraw();

            if (!url) return;
            if (!Object.keys(ctrl.vm.filterValues()).length) {
                ctrl.vm.filterValues(ctrl.getFilters());
            }
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
            }).then(ctrl.vm.data, function () {
                alert("Error! An error occurred.");
            }).then(function () {
                ctrl.vm.isLoading = false;
            });
            ctrl.saveSettings();
        };
        ctrl.saveSettings = function () {
            if (!storage) return;
            storage.setItem("picotablePerPage", ctrl.vm.perPage());
        };
        ctrl.loadSettings = function () {
            if (!storage) return;
            var perPage = 0 | storage.getItem("picotablePerPage");
            if (perPage > 1) {
                ctrl.vm.perPage(perPage);
            }

            // See if we're in pick mode...
            var pickMatch = /pick=([^&]+)/.exec(location.search);
            ctrl.vm.pickId(pickMatch ? pickMatch[1] : null);
        };
        ctrl.pickObject = function (object) {
            var opener = window.opener;
            if (!opener) {
                alert("Error! Window has no opener. Can't pick object.");
                return;
            }
            var text = null;  // Try to figure out a name for the object
            Util.map(["_text", "_name", "title", "name", "text"], function (prop) {
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
        ctrl.datePicker = function () {
            return function (el, isInitialized) {
                if (isInitialized) {
                    return;
                }

                $(el).datetimepicker({
                    format: window.ShuupAdminConfig.settings.datetimeInputFormat,
                    step: window.ShuupAdminConfig.settings.datetimeInputStep
                });
                jQuery.datetimepicker.setLocale(window.ShuupAdminConfig.settings.dateInputLocale);
            };
        };
        ctrl.loadSettings();
        ctrl.adaptRenderMode();
        window.addEventListener("resize", Util.debounce(ctrl.adaptRenderMode, 100));

        // Replace Mithril's deferred error monitor with one that can ignore JSON-parsing syntax errors.
        // See https://lhorie.github.io/mithril/mithril.deferred.html#the-exception-monitor
        m.deferred.onerror = function (e) {
            if (e.toString().match(/^SyntaxError/)) return;

            // Original onerror behavior below.
            if ({}.toString.call(e) === "[object Error]" && !e.constructor.toString().match(/ Error/)) throw e;
        };
    }

    var generator = function (container, dataSourceUrl) {
        this.ctrl = m.mount(container, { view: renderPicotable, controller: PicotableController });
        this.ctrl.setSource(dataSourceUrl);
    };
    generator.lang = lang;
    return generator;
}(window.m, window.localStorage));
/* eslint-disable */
if (typeof module !== "undefined" && module !== null && module.exports) {
    module.exports = Picotable;
}
else if (typeof define === "function" && define.amd) define(function () {
    return Picotable;
});

const picotableElement = document.getElementById("picotable");
if (picotableElement) {
   window.picotable = new Picotable(picotableElement, window.location.pathname);
}
