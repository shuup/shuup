/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
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
    $("#site-search .mobile").click(function() {
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

    function renderResults(results) {

        var [actionResults, standardResults] = _.partition(results, "isAction");
        var standardResultContents = m("div",
            _(standardResults).groupBy("category").map(function(results, category) {
                return m("div.result-category", [
                    m("h3.divider", ["" + category]),
                    m("ul",
                        _.map(results, function(result) {
                            return m("li", {key: result.url},
                                m("a.result", {href: result.url}, [
                                    (result.icon ? m("i." + result.icon) : null),
                                    result.text
                                ])
                            );
                        })
                    )
                ]);
            }).value()
        );


        var actionResultContents = m("div", [
                m("ul",
                    _.map(actionResults, function(result) {
                        return m("li", {key: result.url},
                            m("a.btn.btn-gray", {href: result.url}, [
                                (result.icon ? m("i." + result.icon) : null),
                                result.text
                            ])
                        );
                    })
                )
            ]
        );

        var standardResultNode = document.getElementById("site-search-standard-results");
        var actionResultNode = document.getElementById("site-search-action-results");
        m.render(standardResultNode, standardResultContents);
        m.render(actionResultNode, actionResultContents);

    }

    var doSearch = function(query) {
        if (!query) {
            renderResults([]);
            return;
        }
        $.ajax({
            url: ShoopAdminConfig.searchUrl,
            data: {"q": query}
        }).done(function(data) {
            renderResults(data.results);
        }).fail(function(data) {
            $("#site-search-standard-results").text("An error occurred.");
        });
    };

    var doSearchDebounced = _.debounce(doSearch, 500);

    $("#site-search-input, #site-search-input-mobile").on("keyup", function() {
        var query = $(this).val();
        if (query.length > 0) {
            $("#site-search-results").slideDown(300, "easeInSine");
            doSearchDebounced(query);
        } else {
            $("#site-search-results").slideUp(400, "easeOutSine");
        }
    });
    $("#site-search-input, #site-search-input-mobile").on("focus", function() {
        if ($(this).val().length > 0) {
            $("#site-search-results").slideDown(300, "easeInSine");
        }
    });
});
