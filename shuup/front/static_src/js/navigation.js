/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $("#search-modal").on("show.bs.modal", function() {
        setTimeout(function() {
            $("#site-search").focus();
        }, 300);
    });

    function openMobileNav() {
        $(document.body).addClass("menu-open");
    }

    function closeMobileNav() {
        $(document.body).removeClass("menu-open");
    }

    function mobileNavIsOpen() {
        return $(document.body).hasClass("menu-open");
    }

    $(".toggle-mobile-nav").click(function(e) {
        e.stopPropagation();
        if (mobileNavIsOpen()) {
            closeMobileNav();
        } else {
            openMobileNav();
        }
    });

    $(document).click(function(e) {
        if (mobileNavIsOpen() && !$(e.target).closest(".pages .nav-collapse").length) {
            closeMobileNav();
        }

    });

    $(".main-nav .dropdown-menu").click(function(e) {
        e.stopPropagation();
    });

    // Add proper classes to category navigation based on current-page class
    var $currentlySelectedPage = $(".current-page");
    if ($currentlySelectedPage.length > 0) {
        $currentlySelectedPage.addClass("current");
        $currentlySelectedPage.parents("li").addClass("current");
    }
});
