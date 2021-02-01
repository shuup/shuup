/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
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
            navElement: "span",
            navText: [
                '<span type="button" role="presentation" class="owl-prev"><i class="fa carousel fa-angle-left .carousel-control .icon-prev"></i></span>',
                '<span type="button" role="presentation" class="owl-next"><i class="fa carousel fa-angle-right .carousel-control .icon-next"></i></span>'
            ],
            dots: useDotNavigation,
            items: 1
        });
    });

    var slideCountToResponsiveData = {
        2: {0: {items: 1}, 640: {items: 2}, 992: {items: 2}},
        3: {0: {items: 2}, 640: {items: 2}, 992: {items: 3}},
    };

    $(".carousel-plugin.banner").each(function () {
        var slideCount = JSON.parse($(this).data("slide-count"));
        var arrowsVisible = JSON.parse($(this).data("arrows-visible").toLowerCase());
        var responsiveConfigure = slideCountToResponsiveData[slideCount];
        $(this).owlCarousel({
            margin: 30,
            nav: arrowsVisible,
            navElement: "span",
            navText: [
                '<span type="button" role="presentation" class="owl-prev"><i class="fa fa-angle-left .carousel-control .icon-prev"></i></span>',
                '<span type="button" role="presentation" class="owl-next"><i class="fa fa-angle-right .carousel-control .icon-next"></i></span>'
            ],
            responsiveClass: true,
            responsive: (responsiveConfigure ? responsiveConfigure : {0: {items: 2}, 640: {items: 2}, 992: {items: 4}})
        });
    });

    // Set up owl carousel for product list and make sure they have the owl-carousel styles
    $(".product-carousel.carousel-items").owlCarousel({
        margin: 20,
        nav: true,
        navText: [
            "<i class='fa fa-angle-left'></i>",
            "<i class='fa fa-angle-right'></i>"
        ],
        responsiveClass: true,
        responsive: {
            0: { // breakpoint from 0 up
                items : 2,
                slideBy: 2
            },
            640: { // breakpoint from 640 up
                items : 4,
                slideBy: 2
            },
            1200: { // breakpoint from 992 up
                items : 5,
                slideBy: 3
            }
        }
    });
});
