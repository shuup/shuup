/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    var menuLoaded = false;

    function openMainNav() {
        $(document.body).addClass("menu-open");
    }

    function closeMainNav() {
        $(document.body).removeClass("menu-open");
    }

    function mainNavIsOpen() {
        return $(document.body).hasClass("menu-open");
    }

    function loadMenu(force) {
        if (!menuLoaded || force) {
            $("#main-menu").empty().load(window.ShuupAdminConfig.menuUrl, function() {
                $("#main-menu .scroll-inner-content").scrollbar("init", {
                    disableBodyScroll: true
                });
            });
            menuLoaded = true;
        }
    }

    $(document).click(function(e) {
        if (mainNavIsOpen() && !$(e.target).closest("#main-menu").length) {
            closeMainNav();
        }
    });

    $("#menu-button").click(function(event) {
        loadMenu();
        $("#site-search.mobile").removeClass("open"); // Close search if open on mobile
        event.stopPropagation();
        if (mainNavIsOpen()) {
            closeMainNav();
        } else {
            openMainNav();
        }
    }).hover(function() {
        // Start pre-emptively loading the contents of the main menu when the user seems he's about to open it.
        loadMenu();
    });

    $(document).on("click", "#main-menu ul.menu-list > li a", function(e) {
        if (!$(this).siblings("ul").length) {
            return;
        }
        e.preventDefault();
        const $currentListItem = $(this).parent("li");
        const isOpen = $currentListItem.hasClass("open");
        $(this).siblings("ul").slideToggle();
        $currentListItem.toggleClass("open", !isOpen);
    });

});
