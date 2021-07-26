/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import $ from 'jquery';
import select2 from 'select2';
select2($);

export function activateSelect($select, model, searchMode, extraFilters = null, noExpand = false, attrs = {}, isObjectSelector = false) {
    if (!noExpand) {
        // make sure to expand the select2 to use all the available space
        $select.width("100%");
    }

    const language = {
        errorLoading: function () {
            return gettext("The results could not be loaded");
        },
        inputTooLong: function (args) {
            var overChars = args.input.length - args.maximum;
            var message = ngettext(
                "Please delete %s character",
                "Please delete %s characters", overChars
            );
            return interpolate(message, [overChars]);
        },
        inputTooShort: function (args) {
            var remainingChars = args.minimum - args.input.length;
            return interpolate(gettext("Please enter %s or more characters"), [remainingChars]);
        },
        loadingMore: function () {
            return gettext("Loading more results...");
        },
        maximumSelected: function (args) {
            var message = ngettext(
                "You can only select %s item",
                "You can only select %s items", args.maximum
            );
            return interpolate(message, [args.maximum]);
        },
        noResults: function () {
            return gettext("No results found");
        },
        searching: function () {
            return gettext("Searching...");
        }
    };

    if (!model) {
        return $select.select2({
            ...attrs,
            language,
        });
    }
    let url = null;
    if (isObjectSelector) {
        url = window.ShuupAdminConfig.browserUrls.object_selector;
    } else {
        url = window.ShuupAdminConfig.browserUrls.select;
    }
    
    return $select.select2(Object.assign({
        language,
        minimumInputLength: window.ShuupAdminConfig.settings.minSearchInputLength,
        ajax: {
            url: url,
            dataType: "json",
            data: function (params) {
                // extraFilters is a fn that returns extra params for the query
                let data = null;
                if (isObjectSelector) {
                    data = {
                        selector: model,
                        q: params.term,
                        searchMode: searchMode,
                    };
                } else {
                    data = {
                        model: model,
                        searchMode: searchMode,
                        search: params.term,
                    };
                }
                if (extraFilters) {
                    Object.assign(data, extraFilters(params));
                }
                return data;
            },
            processResults: function (data) {
                return {
                    results: $.map(data.results, function (item) {
                        return { text: item.name, id: item.id };
                    })
                };
            }
        }
    }, attrs));
}

export function activateSelects() {
    $("select").each(function (idx, object) {
        const select = $(object);
        // only activate selects that aren't already select2 inputs
        if (!select.hasClass("select2-hidden-accessible") && !select.hasClass("no-select2")) {
            const model = select.data("model");
            const searchMode = select.data("search-mode");
            const noExpand = select.data("no-expand");
            const placeholderText = select.data("placeholder");
            let placeholder = null;

            if (placeholderText) {
                placeholder = {
                    id: null,
                    text: placeholderText
                };
            }

            // do not set clear when there is no placeholder to use
            const allowClear = placeholder ? select.data("allow-clear") : null;
            const attrs = {
                placeholder,
                allowClear
            };
            const isObjectSelector = select.hasClass("object-selector")
            activateSelect(select, model, searchMode, null, noExpand, attrs, isObjectSelector);
        }
    });
}

window.activateSelects = activateSelects;
activateSelects();
