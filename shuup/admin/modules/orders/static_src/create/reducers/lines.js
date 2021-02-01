/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { handleActions } from "redux-actions";
import _ from "lodash";
import ensureNumericValue  from "../utils/numbers";

function newLine() {
    return {
        id: (+new Date() * 10000).toString(36),
        type: "product",
        product: null,
        supplier: null,
        sku: null,
        text: null,
        errors: null,
        quantity: 1,
        step: "",
        baseUnitPrice: 0,
        unitPrice: 0,
        unitPriceIncludesTax: false,
        discountPercent: 0,
        discountAmount: 0,
        total: 0
    };
}

function setLineProperties(linesState, lineId, props) {
    return _.map(linesState, (line) => {
        if (line.id === lineId) {
            return _.assign({}, line, props);
        }

        return line;
    });
}

function getFormattedStockCounts(line) {
    const physicalCount = parseFloat(ensureNumericValue(line.physicalCount));
    const logicalCount = parseFloat(ensureNumericValue(line.logicalCount));



    return {
        physicalCount: physicalCount.toFixed(line.salesDecimals) + " " + line.salesUnit,
        logicalCount: logicalCount.toFixed(line.salesDecimals) + " " + line.salesUnit
    };
}

function getDiscountsAndTotal(quantity, baseUnitPrice, unitPrice, updateUnitPrice=false) {
    const updates = {};

    if (updateUnitPrice) {
        updates.unitPrice = unitPrice;
    }
    var totalBeforeDiscount = baseUnitPrice * quantity;
    var total = +(unitPrice * quantity);
    updates.total = total;
    if (baseUnitPrice < unitPrice || unitPrice < 0) {
        updates.discountPercent = 0;
        updates.discountAmount = 0;
        return updates;
    }
    var discountAmount = totalBeforeDiscount - total;
    if (isNaN(discountAmount)) {
        discountAmount = 0;
    }
    updates.discountAmount = discountAmount;
    updates.discountPercent = ((discountAmount / totalBeforeDiscount) * 100).toFixed(2);

    return updates;
}

function updateLineFromProduct(state, {payload}) {
    const {id, product} = payload;
    const line = _.find(state, (sLine) => sLine.id === id);
    if (!line) {
        return state;
    }
    var updates = {};
    if (!product.sku) {
        // error happened before getting actual product information
        updates.errors = product.errors;
        return setLineProperties(state, id, updates);
    }

    const baseUnitPrice = ensureNumericValue(product.baseUnitPrice.value);
    const unitPrice = ensureNumericValue(product.unitPrice.value);
    updates = getDiscountsAndTotal(
        ensureNumericValue(product.quantity),
        baseUnitPrice,
        unitPrice
    );
    updates.baseUnitPrice = baseUnitPrice;
    updates.unitPrice = unitPrice;
    updates.unitPriceIncludesTax = product.unitPrice.includesTax;
    updates.sku = product.sku;
    updates.text = product.name;
    updates.quantity = product.quantity;
    updates.step = product.purchaseMultiple;
    updates.errors = product.errors;
    updates.product = product.product;
    updates.supplier = product.supplier;
    updates = _.merge(updates, getFormattedStockCounts(product));
    return setLineProperties(state, id, updates);
}

function setLineProperty(state, {payload}) {
    const {id, property, value} = payload;
    const line = _.find(state, (sLine) => sLine.id === id);
    var updates = {};
    if (line) {
        switch (property) {
            case "product": {
                const product = value;
                updates.product = product;
                updates.type = "product";
                break;
            }
            case "supplier": {
                updates.supplier = value;
            }
            case "text": {
                updates.text = value;
                break;
            }
            case "type": {
                updates.type = value;
                updates.errors = null;
                if (value === "other" || value === "text") {
                    updates.product = null;
                    updates.sku = null;
                }
                if (value === "text") {
                    updates = getDiscountsAndTotal(0, line.baseUnitPrice, 0);
                    updates.unitPrice = 0;
                    updates.quantity = 0;
                }
                updates.type = value;
                break;
            }
            case "quantity": {
                const quantity = Math.max(0, ensureNumericValue(value, 1, true));
                updates = getDiscountsAndTotal(quantity, line.baseUnitPrice, line.unitPrice);
                updates.quantity = quantity;
                break;
            }
            case "unitPrice": {
                updates = getDiscountsAndTotal(
                    line.quantity,
                    line.baseUnitPrice,
                    ensureNumericValue(value, line.baseUnitPrice),
                    true
                );
                break;
            }
            case "discountPercent": {
                const discountPercent = Math.min(100, Math.max(0, ensureNumericValue(value)));
                updates = getDiscountsAndTotal(
                    line.quantity, line.baseUnitPrice, (line.baseUnitPrice * (1 - (discountPercent / 100))), true
                );
                break;
            }
            case "discountAmount": {
                const newDiscountAmount = Math.max(0, ensureNumericValue(value));
                updates = getDiscountsAndTotal(
                    line.quantity,
                    line.baseUnitPrice,
                    (line.baseUnitPrice -  newDiscountAmount / line.quantity),
                    true
                );
                updates.discountAmount = newDiscountAmount;
                break;
            }
            case "total": {
                const calculatedTotal = line.quantity * line.baseUnitPrice;
                // TODO: change the hardcoded rounding when doing SHUUP-1912
                const total = +ensureNumericValue(value, calculatedTotal);
                updates = getDiscountsAndTotal(
                    line.quantity,
                    line.baseUnitPrice,
                    (total / line.quantity),
                    true
                );
                break;
            }
        }
    }
    return setLineProperties(state, id, updates);
}

function setLines(state, {payload}) {
    var lines = [];
    _.map(payload, (line) => {
        _.merge(
            line,
            getFormattedStockCounts(line),
            getDiscountsAndTotal(
                ensureNumericValue(line.quantity, 0, true),
                ensureNumericValue(line.baseUnitPrice),
                ensureNumericValue(line.unitPrice)
            )
        );
        lines.push(line);
    });
    return _.assign([], state, lines);
}

export default handleActions({
    addLine: ((state) => [].concat(state, newLine())),
    deleteLine: ((state, {payload}) => _.reject(state, (line) => line.id === payload)),
    updateLineFromProduct,
    setLineProperty,
    setLines
}, []);
