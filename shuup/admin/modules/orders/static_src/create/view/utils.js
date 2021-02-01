/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";

import { activateSelect } from '../../../../../static_src/base/js/select.js';

export const LINE_TYPES = [
    {id: "product", name: gettext("Product")},
    {id: "other", name: gettext("Other")},
    {id: "text", name: gettext("Text/Comment")}
];

// ensure address types are translated
gettext("billing");
gettext("shipping");

export const ADDRESS_FIELDS = [
    {key: "name", label: gettext("Name"), "required": true, helpText: gettext("Enter the name for the %s address.")},
    {key: "tax_number", label: gettext("Tax number"), "required": false, helpText: gettext("Enter the company tax (ID) number.")},
    {key: "phone", label: gettext("Phone"), "required": false, helpText: gettext("Enter the best %s contact phone number.")},
    {key: "email", label: gettext("Email"), "required": false, helpText: gettext("Enter the %s email address for transaction receipts and communications.")},
    {key: "street", label: gettext("Street"), "required": true, helpText: gettext("Enter the %s street address.")},
    {key: "street2", label: gettext("Street (2)"), "required": false, helpText: gettext("Enter the %s street address (2).")},
    {key: "postal_code", label: gettext("ZIP / Postal code"), "required": false, helpText: gettext("Enter the zip or postal code of the %s address.")},
    {key: "city", label: gettext("City"), "required": true, helpText: gettext("Enter the city of the %s address.")},
    {key: "region", label: gettext("Region"), "required": false, helpText: gettext("Enter the region, state, or province of the %s address.")},
    {key: "region_code", label: gettext("Region"), "required": false, helpText: gettext("Enter the region, state, or province of the %s address.")},
    {key: "country", label: gettext("Country"), "required": true, helpText: gettext("Enter the country of the %s address.")}
];

export function selectBox(
    value, onchange, choices, valueGetter = "id", nameGetter = "name", name = "", emptyValue = null) {
    if (_.isString(valueGetter)) {
        valueGetter = _.partialRight(_.get, valueGetter);
    }
    if (_.isString(nameGetter)) {
        nameGetter = _.partialRight(_.get, nameGetter);
    }
    return m("select.form-control.no-select2", {value, onchange, name}, [
        emptyValue ? m("option", {value: valueGetter(emptyValue)}, nameGetter(emptyValue)) : null,
        choices.map(
            (obj) => m("option", {value: valueGetter(obj)}, nameGetter(obj))
        )
    ]);
}

export function contentBlock(icon, title, view, header = "h2") {
    return m("div.content-block",
        m("div.title",
            m(header + ".block-title.d-flex.align-items-center", m(icon), " " + title),
            m("a.toggle-contents", {
                onclick: (event) => {
                    const $collapseElement = $(event.target).closest(".content-block").find(".content-wrap");
                    event.preventDefault();

                    // Checks if the bootstrap collapse animation is not ongoing
                    if (!$collapseElement.hasClass("collapsing")) {
                        $collapseElement.collapse("toggle");
                        $(this).closest(".title").toggleClass("open");
                    }
                }
            }, m("i.fa.fa-chevron-right"))
        ),
        m("div.content-wrap.collapse",
            m("div.content", view)
        )
    );
}

export function infoRow(header, value, klass) {
    if(value && value !== ""){
        return m("div", [
            m("dt", header),
            m("dd" + (klass? klass : ""), value)
        ]);
    }
}

export function table({columns, data=[], tableClass="", emptyMsg=gettext("No records found.")}) {
    return m("table", {class: "table " + tableClass},
        m("thead",
            m("tr", columns.map(col => m("th", col.label)))
        ),
        m("tbody",
            (data.length > 0?
            data.map(row => m("tr", columns.map(col => m("td", row[col.key])))):
            m("tr", m("td[colspan='" + columns.length + "'].text-center", m("i", emptyMsg))))
        )
    );
}

export function modal({show=false, sizeClass="", title, body, footer, close}) {
    if(show){
        $("body").append("<div class='modal-backdrop show'></div>").addClass("modal-open");
    } else {
        $("body").removeClass("modal-open").find(".modal-backdrop").remove();
    }

    return (
        m("div.modal" + (show ? " d-block fade show": " d-none"),
            m("div.modal-dialog", {class: sizeClass},
                m("div.modal-content",
                    m("div.modal-header",
                        title,
                        m("button.close", {
                            onclick: () => close()
                        }, m("span", m.trust("&times;")))
                    ),
                    m("div.container.p-4", body),
                    m("div.modal-footer", footer)
                )
            )
        )
    );
}

export const Select2 = {
    view: function(ctrl, attrs) {
        return m("select", {
            name: attrs.name,
            config: Select2.config(attrs)
        });
    },
    config: function(attrs) {
        return function(element, isInitialized) {
            if(typeof jQuery !== "undefined" && typeof jQuery.fn.select2 !== "undefined") {
                const $el = $(element);
                if (!isInitialized) {
                    activateSelect($el, attrs.model, attrs.searchMode, attrs.extraFilters, false, attrs.attrs).on("change", () => {
                        // note: data is only populated when an element is actually clicked or enter is pressed
                        const data = $el.select2("data");
                        attrs.onchange(data);
                        if(attrs.focus && attrs.focus()){
                            // close it first to clear the search box...
                            $el.select2("close");
                            $el.select2("open");
                        }
                    });
                } else {
                    // this doesn't actually set the value for ajax autoadd
                    if(attrs.value) {
                        $el.val(attrs.value().id).trigger("change");
                    }

                    if(attrs.clear) {
                        $el.select2("val", "");
                    }

                    // trigger select2 dropdown repositioning
                    $(window).scroll();
                }

            } else {
                alert(gettext("Warning! Missing JavaScript dependencies detected."));
            }
        };
    }
};

export const HelpPopover = {
    view: function(ctrl, attrs) {
        return m("div.help-popover-btn", [
            m("a.btn", {
                role: "button",
                config: HelpPopover.config(attrs),
                // tabindex is required for popover to work but we don't want to actually tab the popover
                tabindex: 50000
            }, [
                m("i.fa.fa-question-circle")
            ])
        ]);
    },
    config: function(attrs) {
        return function(element, isInitialized) {
            const $el = $(element);
            if(!isInitialized) {
                const defaults = {
                    "placement": "bottom",
                    "container": "body",
                    "trigger": "focus"
                };

                $el.popover($.extend({}, defaults, attrs));
            }
        };
    }
};
