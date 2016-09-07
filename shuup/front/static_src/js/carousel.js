/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".carousel-plugin.one").each(function () {
        var autoplay = JSON.parse($(this).data("autoplay"));
        var interval = JSON.parse($(this).data("interval"));
        var arrowsVisible = JSON.parse($(this).data("arrows-visible").toLowerCase());
        var pauseOnHover = JSON.parse($(this).data("pause-on-hover").toLowerCase());
        var useDotNavigation = JSON.parse($(this).data("use-dot-navigation").toLowerCase());
        $(this).owlCarousel({
            loop: true,
            autoplay: autoplay,
            autoplayTimeout: interval,
            autoplayHoverPause: pauseOnHover,
            nav: arrowsVisible,
            navText: [
                '<i class="fa fa-angle-left .carousel-control .icon-prev"></i>',
                '<i class="fa fa-angle-right .carousel-control .icon-prev"></i>'
            ],
            dots: useDotNavigation,
            items: 1
        });
    });

    $(".carousel-plugin.four").each(function () {
        var arrowsVisible = JSON.parse($(this).data("arrows-visible").toLowerCase());
        $(this).owlCarousel({
            margin: 30,
            nav: arrowsVisible,
            navText: [
                '<i class="fa fa-angle-left .carousel-control .icon-prev"></i>',
                '<i class="fa fa-angle-right .carousel-control .icon-prev"></i>'
            ],
            responsiveClass: true,
            responsive: {
                0: { // breakpoint from 0 up
                    items: 2
                },
                640: { // breakpoint from 640 up
                    items: 2
                },
                992: { // breakpoint from 992 up
                    items: 4
                }
            }
        });
    });
});
