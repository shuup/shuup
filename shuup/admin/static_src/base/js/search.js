/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    var searchResultController = null;

    function getShortcutFinder() {
        const usedShortcuts = {"s": true};
        const firstChoices = "123456789";
        const lastChoices = "abcdefghijklmnopqrstuvwxyz";
        return function(text) {
            const keys = (
                firstChoices +
                text.toLowerCase().replace(/[^a-z0-9]+/g, "") +
                lastChoices
            ).split("");
            const key = _.find(keys, (possibleKey) => !usedShortcuts[possibleKey]);
            if (key !== null) {
                usedShortcuts[key] = true;
            }
            return key;
        };
    }

    function resultView(ctrl) {
        const results = ctrl.results();
        if (results !== null && results.length === 0) {
            return m("div", gettext("No results."));
        }
        const showShortcuts = !!ctrl.showShortcuts();
        const [actionResults, standardResults] = _.partition(results, "isAction");
        const getShortcut = getShortcutFinder();

        const singleResultLi = function(result, linkClass) {
            const key = (showShortcuts ? getShortcut(result.text) : null);
            var attrs = {href: result.url, accesskey: key}
            if(result.target){
                attrs["target"] = result.target;
            }
            return m("li", {key: result.url},
                m(linkClass, attrs, [
                    (result.icon ? m("i." + result.icon) : null),
                    result.text,
                    (key ? m("span.key", key.toUpperCase()) : null)
                ])
            );
        };

        const standardResultContents = m("div",
            _(standardResults).groupBy("category").map(function(groupResults, category) {
                return m("div.result-category", [
                    m("h3.divider", ["" + category]),
                    m("ul", _.map(groupResults, (result) => singleResultLi(result, "a.result")))
                ]);
            }).value()
        );

        const actionResultContents = m("div",
            m("ul", _.map(actionResults, (result) => singleResultLi(result, "a.btn.btn-label")))
        );

        return m("div.container-fluid",
            m("div.results", {id: "site-search-standard-results"}, standardResultContents),
            m("div.additional", {id: "site-search-action-results"}, actionResultContents)
        );
    }

    function searchCtrl() {
        const ctrl = this;
        ctrl.results = m.prop(null);
        ctrl.showShortcuts = m.prop(false);
        this.doSearch = function(query) {
            if (!query) {
                ctrl.results([]);
                m.redraw();
                return;
            }
            $.ajax({
                url: window.ShuupAdminConfig.searchUrl,
                data: {"q": query}
            }).done(function(data) {
                ctrl.results(data.results);
                m.redraw();
            });
        };
        const setShowShortcuts = function(event) {
            if (event.keyCode === 18) { // 18 = alt
                ctrl.showShortcuts(event.type === "keydown");
                m.redraw();
            }
        };
        document.addEventListener("keydown", setShowShortcuts, false);
        document.addEventListener("keyup", setShowShortcuts, false);
    }

    var doSearch = function(query) {
        if (!searchResultController) {
            const container = document.getElementById("site-search-results");
            searchResultController = m.mount(container, {controller: searchCtrl, view: resultView});
        }
        searchResultController.doSearch(query);
    };

    const doSearchDebounced = _.debounce(doSearch, 500);

    $(document).click(function(e) {
        if (!$(e.target).closest("#site-search").length) {
            $("#site-search-results").slideUp(400, "easeOutCubic");
        }
    });

    // Disable default behaviour on mobile for the search dropdown.
    // The dropdown now stays open if clicked into the input field
    $(".mobile-search-dropdown").click(function(e) {
        e.stopPropagation();
    });

    // Hide search results if results are open and search parent element is clicked
    $("#site-search").find(".mobile").click(function() {
        if ($(this).hasClass("open")) {
            $("#site-search-results").slideUp(400, "easeOutCubic");
        }
    });

    function closeMobileSearchResults() {
        var windowWidth = $(window).outerWidth(true);
        var $siteSearchResults = $("#site-search-results");
        if ($siteSearchResults.is(":visible") && windowWidth < 768) {
            $siteSearchResults.slideUp(400, "easeOutCubic");
        }
    }

    $(window).resize(_.debounce(closeMobileSearchResults, 100));

    const $searchInputs = $("#site-search-input, #site-search-input-mobile");

    $searchInputs.on("keyup", function() {
        var query = $(this).val();
        if (query.length > 0) {
            $("#site-search-results").slideDown(300, "easeInSine");
            doSearchDebounced(query);
        } else {
            $("#site-search-results").slideUp(400, "easeOutSine");
        }
    });
    $searchInputs.on("focus", function() {
        if ($(this).val().length > 0) {
            $("#site-search-results").slideDown(300, "easeInSine");
        }
    });

    $(window).on('scroll', () => {
      if (window.scrollY > 0) {
        $('.site-search-nav').addClass('site-scrolling');
      } else {
        $('.site-search-nav').removeClass('site-scrolling');
      }
    });
});
