/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import RegionsMap from "./data";


const handleRegionFields = (countryRegions, regionCodeFieldSelector, regionFieldSelector = null) => {
    const regionField = $(regionFieldSelector) || null;
    let regionCodeField = $(regionCodeFieldSelector);

    if (countryRegions) {
        if (regionField) {
            regionField.closest(".form-group").hide();
        }
        regionCodeField.closest(".form-group").show();

        const regionValue = regionCodeField.val();
        const emptyOption = $("<option/>", { value: "", text: "---------" });

        if (regionCodeField.is("select")) {
            regionCodeField.empty();
        } else {
            const newRegionField = $("<select/>", {
                id: regionCodeField.attr("id"),
                name: regionCodeField.attr("name"),
                class: "form-control"
            });
            regionCodeField.off("*"); // remove all event listeners before removing the field
            regionCodeField.replaceWith(newRegionField);
            regionCodeField = newRegionField;
        }
        regionCodeField.append(emptyOption);
        countryRegions.forEach((region) => {
            const option = $("<option/>", {
                value: region.code,
                text: region.name,
                selected: ((regionValue === region.code) ? true : false)
            });
            regionCodeField.append(option);
        });
        if (regionField) {
            regionField.val("");
        }
        // warn that field was initialized
        const event = new CustomEvent("regionFieldInitialized", { detail: { field: regionCodeField[0] } });
        document.dispatchEvent(event);
    } else {
        if (regionField) {
            regionField.closest(".form-group").show();
        }
        regionCodeField.val("");
        regionCodeField.closest(".form-group").hide();
    }
};

const updateRegion = (countryFieldSelector, regionCodeFieldSelector, regionFieldSelector = null) => {
    const country = $(countryFieldSelector).val();
    const countryRegions = RegionsMap[country];
    handleRegionFields(countryRegions, regionCodeFieldSelector, regionFieldSelector);
};

// expose to the world!
window.initializeRegionFields = function (countryFieldSelector, regionCodeFieldSelector, regionFieldSelector = null) {
    updateRegion(countryFieldSelector, regionCodeFieldSelector, regionFieldSelector);

    $(countryFieldSelector).on("change", function () {
        updateRegion(countryFieldSelector, regionCodeFieldSelector, regionFieldSelector);
    });
};
window.REGIONS = RegionsMap;
