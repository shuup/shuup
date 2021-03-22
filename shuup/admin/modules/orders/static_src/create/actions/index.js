/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {createAction} from "redux-actions";
import {get, post} from "../api";
import _ from "lodash";

// Shops actions
export const setShop = createAction("setShop");
export const setShopChoices = createAction("setShopChoices");
export const setCountries = createAction("setCountries");
// Lines actions
export const addLine = createAction("addLine");
export const deleteLine = createAction("deleteLine");
export const updateLineFromProduct = createAction("updateLineFromProduct");
export const setLineProperty = createAction("setLineProperty", (id, property, value) => ({id, property, value}));
export const setLines = createAction("setLines");
// Customers actions
export const clearExistingCustomer = createAction("clearExistingCustomer");
export const setAddressProperty = createAction("setAddressProperty", (type, field, value) => ({type, field, value}));
export const setAddressSavingOption = createAction("setAddressSavingOption");
export const setShipToBillingAddress = createAction("setShipToBillingAddress");
export const setIsCompany = createAction("setIsCompany");
export const setCustomer = createAction("setCustomer");
export const showCustomerModal = createAction("showCustomerModal");
// Methods actions
export const setShippingMethodChoices = createAction("setShippingMethodChoices");
export const setShippingMethod = createAction("setShippingMethod");
export const setPaymentMethodChoices = createAction("setPaymentMethodChoices");
export const setPaymentMethod = createAction("setPaymentMethod");
// Orders actions
export const updateTotals = createAction("updateTotals");
export const setOrderSource = createAction("setOrderSource");
export const clearOrderSourceData = createAction("clearOrderSourceData");
export const setOrderId = createAction("setOrderId");
const beginCreatingOrder = createAction("beginCreatingOrder");
const endCreatingOrder = createAction("endCreatingOrder");
// Comment action
export const setComment = createAction("setComment");
// Quick add actions
export const setAutoAdd = createAction("setAutoAdd");
export const clearQuickAddProduct = createAction("clearQuickAddProduct");
export const setQuickAddProduct = createAction("setQuickAddProduct");

export const retrieveProductData = function ({id, forLine, quantity}) {
    return (dispatch, getState) => {
        const {customer, lines, shop} = getState();
        const prodsAlreadyInLinesQty = _.reduce(lines, function(sum, line) {
            if (line.id !== forLine && line.product && line.product.id === id) {
                return sum + parseFloat(line.quantity);
            }
            return sum;
        }, 0);
        get("product_data", {
            id,
            "shop_id": shop.selected.id,
            "customer_id": _.get(customer, "id"),
            "quantity": quantity,
            "already_in_lines_qty": prodsAlreadyInLinesQty
        }).then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            dispatch(receiveProductData({id, data}));
            if (forLine) {
                dispatch(updateLineFromProduct({id: forLine, product: data}));
                dispatch(updateTotals(getState));
            }
        });
    };
};

export const retrieveCustomerData = function({id}) {
    return (dispatch) => {
        get("customer_data", {
            id
        }).then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            dispatch(receiveCustomerData({id, data}));
            dispatch(setCustomer(data));
            dispatch(updateLines());
        });
    };
};

export const retrieveCustomerDetails = function({id}) {
    return (dispatch) => {
        return get("customer_details", {
            id
        }).then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            dispatch(receiveCustomerDetails({ id, data }));
        });
    };
};

export const retrieveOrderSourceData = function () {
    return (dispatch, getState) => {
        dispatch(beginCreatingOrder());
        const state = getState();
        post("source_data", {state}).then((data) => {
            dispatch(receiveOrderSourceData({data}));
            dispatch(setOrderSource(data));
            dispatch(endCreatingOrder());
        }, (data) => {  // error handler
            dispatch(endCreatingOrder());
            const {Messages} = window;
            if (Messages) {
                Messages.enqueue({type: "error", text: data.errorMessage});
            } else {
                alert(data.errorMessage);
            }
        });
    };
};

export const updateLines = () => {
    return (dispatch, getState) => {
        getState().lines.forEach((line) => {
            if (line.product) {
                dispatch(retrieveProductData({id: line.product.id, forLine: line.id, quantity: line.quantity}));
            }
        });
    };
};

export const receiveProductData = createAction("receiveProductData");
export const receiveCustomerData = createAction("receiveCustomerData");
export const receiveCustomerDetails = createAction("receiveCustomerDetails");
export const receiveOrderSourceData = createAction("receiveOrderSourceData");
export const endFinalizingOrder = createAction("endFinalizingOrder");

function handleFinalizeResponse(dispatch, data) {
    const {success, errorMessage, orderIdentifier, url} = data;
    if (success) {
        window.localStorage.setItem("resetSavedOrder", "true");
        if (url) {
            location.href = url;
        } else {
            // Very, very unlikely that we'd ever get here
            alert(interpolate(gettext("Success! Order %s was created."), [orderIdentifier]));
        }
        return;
    }
    dispatch(endCreatingOrder());
    dispatch(endFinalizingOrder());  // Only flag end if something went awry
    if (errorMessage) {
        const {Messages} = window;
        if (Messages) {
            Messages.enqueue({type: "error", text: errorMessage});
        } else {
            alert(errorMessage);
        }
        return;
    }
    alert(gettext("Error! An unspecified error occurred.\n") + data);
}

export const beginFinalizingOrder = function () {
    return (dispatch, getState) => {
        dispatch(beginCreatingOrder());
        const state = _.assign({}, getState(), {productData: null, order: null, quickAdd: null}); // We don't care about that substate
        post("finalize", {state}).then((data) => {
            handleFinalizeResponse(dispatch, data);
        }, (data) => {  // error handler
            handleFinalizeResponse(dispatch, data);
        });
        dispatch(createAction("beginFinalizingOrder")());
    };
};


export const addProduct = function(product) {
    return (dispatch, getState) => {
        const {lines} = getState();
        var line = _.find(lines, function(o) { return (o.product && o.product.id === parseInt(product.id));});
        if (line === undefined) {
            dispatch(addLine());
            dispatch(retrieveProductData({id: product.id, forLine: _.last(getState().lines).id}));
        }
        else {
            dispatch(setLineProperty(line.id, "quantity", parseFloat(line.quantity) + 1));
        }
    };
};
