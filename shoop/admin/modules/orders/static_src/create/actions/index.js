/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
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
// Customers actions
export const clearExistingCustomer = createAction("clearExistingCustomer");
export const setAddressProperty = createAction("setAddressProperty", (type, field, value) => ({type, field, value}));
export const setAddressSavingOption = createAction("setAddressSavingOption");
export const setShipToBillingAddress = createAction("setShipToBillingAddress");
export const setIsCompany = createAction("setIsCompany");
export const setCustomer = createAction("setCustomer");
// Methods actions
export const setShippingMethodChoices = createAction("setShippingMethodChoices");
export const setShippingMethod = createAction("setShippingMethod");
export const setPaymentMethodChoices = createAction("setPaymentMethodChoices");
export const setPaymentMethod = createAction("setPaymentMethod");
// Orders actions
export const updateTotals = createAction("updateTotals");
export const setOrderSource = createAction("setOrderSource");
export const clearOrderSourceData = createAction("clearOrderSourceData");
// Comment action
export const setComment = createAction("setComment");

export const retrieveProductData = function ({id, forLine, quantity=1}) {
    return (dispatch, getState) => {
        const {customer, shop} = getState();
        get("product_data", {
            id,
            "shop_id": shop.selected.id,
            "customer_id": _.get(customer, "id"),
            "quantity": quantity
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
        });
    };
};

export const retrieveOrderSourceData = function () {
    return (dispatch, getState) => {
        const state = getState();
        post("source_data", {state}).then((data) => {
            dispatch(receiveOrderSourceData({data}));
            dispatch(setOrderSource(data));
        }, (data) => {  // error handler
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
export const receiveOrderSourceData = createAction("receiveOrderSourceData");
export const endCreatingOrder = createAction("endCreatingOrder");

function handleCreateResponse(dispatch, data) {
    const {success, errorMessage, orderIdentifier, url} = data;
    if (success) {
        if (url) {
            location.href = url;
        } else {
            // Very, very unlikely that we'd ever get here
            alert(interpolate(gettext("Order %s created."), [orderIdentifier]));
        }
        return;
    }
    dispatch(endCreatingOrder());  // Only flag end if something went awry
    if (errorMessage) {
        const {Messages} = window;
        if (Messages) {
            Messages.enqueue({type: "error", text: errorMessage});
        } else {
            alert(errorMessage);
        }
        return;
    }
    alert(gettext("An unspecified error occurred.\n") + data);
}

export const beginCreatingOrder = function () {
    return (dispatch, getState) => {
        const state = _.assign({}, getState(), {productData: null, order: null}); // We don't care about that substate
        post("create", {state}).then((data) => {
            handleCreateResponse(dispatch, data);
        }, (data) => {  // error handler
            handleCreateResponse(dispatch, data);
        });
        dispatch(createAction("beginCreatingOrder")());
    };
};
