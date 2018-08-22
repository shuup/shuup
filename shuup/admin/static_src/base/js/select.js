/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import $ from 'jquery';
import select2 from 'select2';
select2($);

export function activateSelect($select, model, searchMode, attrs={}) {
    if(model === undefined) {
        return $select.select2($.extend(true, {
            language: "xx"
        }, attrs));
    }
    return $select.select2($.extend(true, {
        language: "xx",
        minimumInputLength: 3,
        ajax: {
            url: window.ShuupAdminConfig.browserUrls.select,
            dataType: "json",
            data: function(params) {
                return {model: model, searchMode: searchMode, search: params.term};
            },
            processResults: function (data) {
                return {
                    results: $.map(data.results, function (item) {
                        return {text: item.name, id: item.id};
                    })
                };
            }
        }
    }, attrs));
}

export function activateSelects() {
    $("select").each(function(idx, object) {
        const select = $(object);
        // only activate selects that aren't already select2 inputs
        if (!select.hasClass("select2-hidden-accessible") && !select.hasClass("no-select2")) {
            const model = select.data("model");
            const searchMode = select.data("search-mode");
            activateSelect(select, model, searchMode);
        }
    });
}

function select2Local() {
  // Handle localization with Django instead of using select2 localization files
  $.fn.select2.amd.define("select2/i18n/xx", [], function () {
      return {
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
  });
}

activateSelects();
select2Local();
