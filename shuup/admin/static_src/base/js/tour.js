/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function($) {
    function getAppChromeSteps(key) {
        if(key !== "home" && typeof(key) !== "undefined") {
            return [];
        }
        if($("#main-menu").position().left !== 0) {
            // don't show chrome tour on mobile
            return [];
        }
        let steps = [];
        steps = steps.concat([
            {
                title: gettext("Quicklinks"),
                text: [
                    gettext("Quick Links to your most used features.")
                ],
                attachTo: "li a[data-target-id='quicklinks'] right"
            }, {
                title: gettext("Orders"),
                text: [
                    gettext("Here you can track your orders and shoppers’ carts."),
                    gettext("Filters are setup to find the orders or shopping carts you are looking for, based on anything. There are order filters like customer’s name, date range, if it has been shipped or paid, and basket filters like how many products are in the basket or if the cart was abandoned.")
                ],
                attachTo: "li a[data-target-id='category-1'] right"
            }, {
                title: gettext("Products"),
                text: [
                    gettext("All your products and product options are in here, there’s a bunch. Manufacturers, suppliers, and your inventory and stock management are inside. You can add more products and categories here too.")
                ],
                attachTo: "li a[data-target-id='category-2'] right"
            }, {
                title: gettext("Contacts"),
                text: [
                    gettext("All your shopper data is inside. Check out your best customers, setup special user groups, and get info to target them so that they want to buy.")
                ],
                attachTo: "li a[data-target-id='category-3'] right"
            }
        ]);

        if($("li a[data-target-id='category-4']").length > 0) {
            steps.push({
                title: gettext("Reports"),
                text: [
                    gettext("Here you can create all types of reports and export them in multiple formats. Get the sales data you need and see how and where you are making money.")
                ],
                attachTo: "li a[data-target-id='category-4'] right"
            });
        }

        if($("li a[data-target-id='category-5']").length > 0) {
            steps.push({
                title: gettext("Campaigns"),
                text: [
                    gettext("Here you can create sales, coupons, and marketing campaigns that entice your shoppers. Set them up based on catalog or basket and make recommended product upsells and crossells. Or do something unique that will create loyalty and happy shoppers.")
                ],
                attachTo: "li a[data-target-id='category-5'] right"
            });
        }

        steps.push({
            title: gettext("Storefront"),
            text: [
                gettext("This is the place to customize your site and add pages, shops, and sales carousels. You can add media like photos and videos or completely change the look of your store. It’s super customizable to make it exactly how you want.")
            ],
            attachTo: "li a[data-target-id='category-6'] right"
        });

        if($("li a[data-target-id='category-7']").length > 0){
            steps.push({
                title: gettext("Addons"),
                text: [
                    gettext("This is your connection interface. Addons and other systems you use can be attached to your store through powerful data connections. Supercharge your site and gather crazy amounts of data with integrations to CRMs and ERPs, POS’s and PIM’s, or any other acronym you can think of.")
                ],
                attachTo: "li a[data-target-id='category-7'] right"
            });
        }

        steps = steps.concat([{
            title: gettext("Settings"),
            text: [
                gettext("Here are the main options for your store. Its got everything from taxes and tax rules, payment and shipping methods, to notification settings. Tweak away.")
            ],
            attachTo: "li a[data-target-id='category-8'] right"
        }, {
            title: gettext("Search"),
            text: [
                gettext("Find anything that is inside your store. This includes settings, products, users, and addons.")
            ],
            attachTo: "#site-search bottom"
        }, {
            title: gettext("View your storefront"),
            text: [
                gettext("Check out your shop and all the cool changes you’ve made.")
            ],
            attachTo: ".shop-btn left"
        }, {
            title: gettext("We're done!"),
            text: [
                gettext("You have completed the tutorial."),
                gettext("If you need to run it again, fire it up from the menu in the top right.")
            ]
        }]);
        return steps;
    }

    $(document).ready(function() {
        $("#top-header .show-tour-li").on("click", "a", function(e){
            e.preventDefault();
            $.tour();
        });
    });

    $.tour = function(config={}, params) {
        if(config === "setPageSteps") {
            this.pageSteps = params;
            return;
        }
        let tour = new Shepherd.Tour({
            defaults: {
                classes: "shepherd-theme-arrows",
                scrollTo: true,
                showCancelLink: true
            }
        });

        var steps = [];
        if (this.pageSteps && this.pageSteps.length > 1) {
            steps = this.pageSteps;
        }
        else {
            steps = (this.pageSteps || []).concat(getAppChromeSteps(config.tourKey));
        }

        $.each(steps, (idx, step) => {
            var buttonType = null;
            if(idx === 0) {
                buttonType = "first";
            }
            if(idx === steps.length - 1) {
                buttonType = "last";
            }
            step = $.extend({}, step, {buttons: getTourButtons(buttonType)});
            let content = "";
            if(step.icon) {
                content += "<div class='clearfix'>";
                content += "<div class='pull-left'>";
                content += "<div class='icon'>";
                content += "<img src='" + step.icon + "' />";
                content += "</div>";
                content += "</div>";
                content += "<div class='step-with-icon'>";
                content += getTextLines(step.text);
                content += getHelpButton(step.helpPage);
                content += "</div>";
                content += "</div>";
            } else {
                content += getTextLines(step.text);
                content += getHelpButton(step.helpPage);
            }
            step.text = content;
            tour.addStep("step-" + idx, step);
        });

        function getTextLines(text) {
            let content = "";
            for(let i = 0; i < text.length; i++) {
                content += "<p class='lead'>" + text[i] + "</p>";
            }
            return content;
        }

        function getHelpButton(page) {
            let content = "";
            if(page) {
                let helpUrl = "http://shuup-guide.readthedocs.io/en/latest/" + page;
                content += "<br>";
                content += "<p class='text-center'>";
                content += "<a href='" + helpUrl + "' class='btn btn-inverse btn-default', target='_blank'>";
                content += "<i class='fa fa-info-circle'></i> " + gettext("Learn more at the Shuup Help Center");
                content += "</a>";
                content += "</p>";
            }
            return content;

        }
        function getTourButtons(type) {
            let buttons = [];
            if(type !== "first" && type !== "last") {
                buttons.push({
                    text: "Previous",
                    classes: "btn shepherd-button-secondary",
                    action: tour.back
                });
            }

            if(type == "last") {
                buttons.push({
                    text: "OK",
                    classes: "btn btn-primary",
                    action: tour.cancel
                });
            } else {
                buttons.push({
                    text: "Next",
                    classes: "btn btn-primary",
                    action: tour.next
                });
            }

            return buttons;
        }

        if(config.tourKey) {
            tour.on("cancel", () => {
                $.post("/sa/tour/", {"csrfmiddlewaretoken": window.ShuupAdminConfig.csrf, "tourKey": config.tourKey});
            });
        }
        tour.start();
        return tour;
    };
}(jQuery));
