/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";

    function openMainNav() {
        $(document.body).addClass("menu-open");
    }

    function closeMainNav() {
        $(document.body).removeClass("menu-open");
    }

    function mainNavIsOpen() {
        return $(document.body).hasClass("menu-open");
    }

    $("#menu-button").click(function(event) {
        closeAllSubmenus();
        $("#site-search.mobile").removeClass("open"); // Close search if open on mobile
        event.stopPropagation();
        if (mainNavIsOpen()) {
            closeMainNav();
        } else {
            openMainNav();
        }
    });

    function closeAllSubmenus() {
        $(".category-submenu").each(function(idx, elem){
            $(elem).removeClass("open");
        });
    }
    $(document).on("click", "#main-menu ul.menu-list > li a", function(e) {
        e.preventDefault();
        e.stopPropagation();  // do not close submenus
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

    $(window).click(function() {
        closeAllSubmenus();
    });

    $('.category-submenu').click(function(event){
        event.stopPropagation();
        if($(event.target).hasClass("fa-close")) {
            closeAllSubmenus();
        }
    });

    window.onresize = (function() {
        closeAllSubmenus();
        if($(window).width() < 768) {
            closeMainNav();
        }
    });
    if (window.Masonry) {
        const Masonry = window.Masonry;
        $(".category-menu-content").each(function(idx, elem) {
            const msnry = new Masonry(elem, {
                itemSelector: '.submenu-container',
                columnWidth: '.submenu-container',
                percentPosition: true
            });
        });
    }
});
