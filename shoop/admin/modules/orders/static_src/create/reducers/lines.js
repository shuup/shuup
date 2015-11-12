/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

function newLine() {
    return {
        id: (+new Date() * 10000).toString(36),
        type: "product",
        product: null,
        sku: null,
        text: null,
        quantity: 1,
        unitPrice: 0,
        unitPriceIncludesTax: false
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

function updateLineFromProduct(state, {payload}) {
    const {id, product} = payload;
    const line = _.detect(state, (sLine) => sLine.id === id);
    if (!line) {
        return state;
    }
    const updates = {};
    if (line.unitPrice === 0) {
        updates.unitPrice = product.unitPrice.value;
        updates.unitPriceIncludesTax = product.unitPrice.includesTax;
    }
    updates.sku = product.sku;
    updates.text = product.name;
    return setLineProperties(state, id, updates);
}

function setLineProperty(state, {payload}) {
    const {id, property, value} = payload;
    const line = _.detect(state, (sLine) => sLine.id === id);
    const updates = {};
    if (line) {
        switch (property) {
            case "product":
                const product = value;
                updates.product = product;
                updates.type = "product";
                break;
            case "text":
                updates.text = value;
                break;
            case "type":
                updates.type = value;
                if (value === "other" || value === "text") {
                    updates.product = null;
                    updates.sku = null;
                }
                if (value === "text") {
                    updates.unitPrice = 0;
                    updates.quantity = 0;
                }
                break;
            case "quantity":
                updates.quantity = Math.max(0, parseFloat(value));
                break;
            case "unitPrice":
                updates.unitPrice = Math.max(0, parseFloat(value));
                break;
        }
    }
    return setLineProperties(state, id, updates);
}

export default handleActions({
    addLine: ((state) => [].concat(state, newLine())),
    deleteLine: ((state, {payload}) => _.reject(state, (line) => line.id === payload)),
    updateLineFromProduct,
    setLineProperty
}, []);
