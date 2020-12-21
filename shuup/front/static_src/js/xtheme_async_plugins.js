/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(document).ready(function() {
    $('.async-xtheme-product-carousel-plugin').each(function(index, value) {
        const url = $(this).data("url");
        if (url) {
            $(this).find(
                '.ajax-content'
            ).html(
                '<div class="text-primary text-center spinner"><i class="fa fa-3x fa-spin fa-spinner"></i></div>'
            ).show();

            const that = $(this);
            $.ajax({
                url,
                method: "GET",
                success: function(data) {
                    that.find('.ajax-content').html(data).owlCarousel({
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
                                slideBy: 1
                            },
                            425: { // breakpoint from 425px up
                                items : 3,
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
                },
                error: function(error) {
                    that.find('.ajax-content').html("")
                }
            });
        }
    });
});
