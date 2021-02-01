/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import Shepherd from "shepherd.js";

((($) => {
    function getTourMenuSteps() {
        const tippyOptions = {
            boundary: "offsetParent"
        };

        const steps = [];
        if (!$("body").hasClass("desktop-menu-closed")) {
            if ($("li a[data-target-id='quicklinks']").length > 0) {
                steps.push({
                    title: gettext("Quick Links"),
                    text: [
                        gettext("Quick Links to your most used features.")
                    ],
                    attachTo: "li a[data-target-id='quicklinks'] right",
                    scrollTo: false
                });
            }
            if ($("li a[data-target-id='category-1']").length > 0) {
                steps.push({
                    title: gettext("Orders"),
                    text: [
                        gettext("Track and filter your customers’ orders here."),
                    ],
                    attachTo: "li a[data-target-id='category-1'] right",
                    scrollTo: false,
                    tippyOptions
                });
            }
            if ($("li a[data-target-id='category-2']").length > 0) {
                steps.push({
                    title: gettext("Products"),
                    text: [
                        gettext("All your exciting products and features are located here.")
                    ],
                    attachTo: "li a[data-target-id='category-2'] right",
                    scrollTo: false,
                    tippyOptions
                });
            }
            if ($("li a[data-target-id='category-3']").length > 0) {
                steps.push({
                    title: gettext("Contacts"),
                    text: [
                        gettext("All your customer data is located here. Target and organize your clients details your way!")
                    ],
                    attachTo: "li a[data-target-id='category-3'] right",
                    scrollTo: false,
                    tippyOptions
                });
            }

            if ($("li a[data-target-id='category-5']").length > 0) {
                steps.push({
                    title: gettext("Campaigns"),
                    text: [gettext("Great loyalty tool for creating marketing, campaigns, special offers and coupons to entice your shoppers!"), gettext("Set offers based on their previous purchase behavior to up- and cross sale your inventory.")],
                    attachTo: "li a[data-target-id='category-5'] right",
                    tippyOptions
                });
            }

            if ($("li a[data-target-id='category-9']").length > 0) {
                steps.push({
                    title: gettext("Content"),
                    text: [gettext("The make-over tool to customize you site themes, add pages and product carousels. Incorporate any media to make your store pop!")],
                    attachTo: "li a[data-target-id='category-9'] right",
                    tippyOptions
                });
            }

            if ($("li a[data-target-id='category-4']").length > 0) {
                steps.push({
                    title: gettext("Reports"),
                    text: [gettext("Your reporting tool to build and analyze your consumer behavior information that can assist with your business decisions.")],
                    attachTo: "li a[data-target-id='category-4'] right",
                    tippyOptions
                });
            }

            if ($("li a[data-target-id='category-6']").length > 0) {
                steps.push({
                    title: gettext("Shops"),
                    text: [gettext("Place for your Shop specific settings. You can customize taxes, currencies, customer groups, and many other things in this menu.")],
                    attachTo: "li a[data-target-id='category-6'] right",
                    tippyOptions
                });
            }

            if ($("li a[data-target-id='category-7']").length > 0) {
                steps.push({
                    title: gettext("Addons"),
                    text: [gettext("This is your connection interface. Addons and other systems you use can be attached to your store through powerful data connections."), gettext("Supercharge your site and gather crazy amounts of data with integrations to CRMs and ERPs, POS’s and PIM’s, or any other acronym you can think of.")],
                    attachTo: "li a[data-target-id='category-7'] right",
                    tippyOptions,
                    when: {
                        show() {
                            $("ul.menu-list").addClass("pb-5");
                        },
                        hide() {
                            $("ul.menu-list").removeClass("pb-5");
                        }
                    }
                });
            }

            if ($("li a[data-target-id='category-8']").length > 0) {
                steps.push({
                    title: gettext("Settings"),
                    text: [
                        gettext("The nuts and bolts of your store are found here. From individual country tax-regulations to your contact details.")
                    ],
                    attachTo: "li a[data-target-id='category-8'] right",
                    scrollTo: true,
                    tippyOptions,
                    when: {
                        show() {
                            $("ul.menu-list").addClass("pb-5");
                        },
                        hide() {
                            $("ul.menu-list").removeClass("pb-5");
                        }
                    }
                });
            }
        }

        if ($("#site-search").length > 0 && $("#site-search").is(":visible")) {
            steps.push({
                title: gettext("Search"),
                text: [
                    gettext("Lost and cannot find your way? No worries, you can search contacts, settings, add-ons and more features from here.")
                ],
                attachTo: "#site-search bottom"
            });
        }
        if ($(".shop-btn.visit-store").length > 0) {
            steps.push({
                title: gettext("View your storefront"),
                text: [
                    gettext("Preview your shop and all the cool features you have created!")
                ],
                attachTo: ".shop-btn.visit-store bottom"
            });
        }

        steps.push({
            title: gettext("We're done!"),
            text: [
                gettext("It was nice to show you around!"),
                gettext("If you need to run it again, fire it up from the menu in the top right.")
            ]
        });
        return steps;
    }

    function getTextLines(tour, text) {
        let content = "";
        for (let i = 0; i < text.length; i += 1) {
            content += "<p>" + text[i] + "</p>";
        }
        return content;
    }

    function getHelpButton(tour, page) {
        let content = "";
        if (page) {
            const helpUrl = window.ShuupAdminConfig.docsPage + page;
            content += "<br>";
            content += "<p class='text-center'>";
            content += "<a href='" + helpUrl + "' class='btn btn-inverse btn-default', target='_blank'>";
            content += "<i class='fa fa-info-circle'></i> " + gettext("Learn more at the Shuup Help Center");
            content += "</a>";
            content += "</p>";
        }
        return content;

    }

    function getTourButtons(tour, type) {
        const buttons = [];
        if (type !== "first" && type !== "last") {
            buttons.push({
                text: "Previous",
                classes: "btn btn-primary",
                action: tour.back
            });
        }

        if (type === "last") {
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

    function initalizeAndRunTour(config) {
        const tour = new Shepherd.Tour({
            defaultStepOptions: {
                classes: "shepherd-theme-arrows",
                scrollTo: true,
                showCancelLink: true
            }
        });

        let steps = (config.initialSteps || []);
        if (config.showMenuSteps) {
            steps = steps.concat(getTourMenuSteps(config.tourKey));
        }
        $.each(steps, (idx, step) => {
            var buttonType = null;
            if (idx === 0) {
                buttonType = "first";
            }
            if (idx === steps.length - 1) {
                buttonType = "last";
            }
            step = $.extend({}, step, { buttons: getTourButtons(tour, buttonType) });
            let content = "";
            if (step.icon) {
                content += "<div class='step-with-icon'>";
                content += "<div class='icon'>";
                content += "<img src='" + step.icon + "' />";
                content += "</div>";
                content += "<div class='text'>";
                content += getTextLines(tour, step.text);
                content += getHelpButton(tour, step.helpPage);
                content += "</div>";
                content += "</div>";
            } else if (step.banner) {
                content += "<div>";
                content += "<div class='banner'>";
                content += "<img src='" + step.banner + "' />";
                content += "</div>";
                content += "<div class='step-with-banner'>";
                content += getTextLines(tour, step.text);
                content += getHelpButton(tour, step.helpPage);
                content += "</div>";
                content += "</div>";
            } else {
                content += getTextLines(tour, step.text);
                content += getHelpButton(tour, step.helpPage);
            }
            step.text = content;
            tour.addStep("step-" + idx, step);
        });

        if (!config.forceRun && config.tourKey && config.url && window.ShuupAdminConfig.csrf) {
            tour.on("cancel", () => {
                $.post(
                    config.url,
                    {
                        "csrfmiddlewaretoken": window.ShuupAdminConfig.csrf,
                        "tourKey": config.tourKey
                    }
                );
            });
        }

        tour.start();
    }

    window.runTour = function runTour(forceRun = false) {
        const menu = $("#main-menu");
        let config = (window.tourConfig || {});
        if (!config.tourKey) {
            // Let's do fallback config here
            config = { tourComplete: true, tourKey: "menuOnly", showMenuSteps: true };
        }
        config.forceRun = forceRun;
        if (config.showMenuSteps && menu && menu.position() && menu.position().left !== 0) {
            return;  // don't show tour when menu steps included and menu closed
        } else if ($(window).width() < 977) {
            return;  // don't show tour for mobile
        } else if (config.tourComplete && !forceRun) {
            return;  // tour completed so no run without force
        } else {
            initalizeAndRunTour(config);
        }
    }

    $(".show-tour").on("click", (e) => {
        e.stopImmediatePropagation();
        e.preventDefault();
        window.runTour(true);
    });
})(jQuery));
