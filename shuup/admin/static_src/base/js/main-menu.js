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

    $("#menu-button").click(function(event) {
        closeAllSubmenus();
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

    function closeAllSubmenus() {
        $(".category-submenu").each(function(idx, elem){
            $(elem).removeClass("open");
        });
    }
    $(document).on("click", "#main-menu ul.menu-list > li a", function(e) {
        e.preventDefault();
        const target_id = $(this).data("target-id");
        $(".category-submenu").each(function(idx, elem){
            if($(elem).attr("id") != target_id) {
                $(elem).removeClass("open");
            }
        });
        const $target = $("#" + target_id);
        if (!$target.length) {
            return;
        }
        const isOpen = $target.hasClass("open");
        $target.toggleClass("open", !isOpen);
    });
    $(document).ready(function(){
        loadMenu();
        if($(window).width() > 768) {
            openMainNav();
        }
    });
    $(document).on("click", ".category-menu-close", function(e){
        closeAllSubmenus();
    });
    window.onresize = (function() {
        if($(window).width() > 768) {
            openMainNav();
        }
        else {
            closeMainNav();
        }
    });
});
