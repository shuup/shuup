/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {createAction} from "redux-actions";
import {get, post} from "../api";
import _ from "lodash";

export const setCustomer = createAction("setCustomer");
export const setComment = createAction("setComment");
export const setShopId = createAction("setShopId");
export const setShopChoices = createAction("setShopChoices");
export const setShippingMethodChoices = createAction("setShippingMethodChoices");
export const setShippingMethodId = createAction("setShippingMethodId");
export const addLine = createAction("addLine");
export const deleteLine = createAction("deleteLine");
export const updateLineFromProduct = createAction("updateLineFromProduct");
export const setLineProperty = createAction("setLineProperty", (id, property, value) => ({id, property, value}));

export const retrieveProductData = function ({id, forLine}) {
    return (dispatch, getState) => {
        const {customer, shop} = getState();
        get("product_data", {
            id,
            "shop_id": shop.id,
            "customer_id": _.get(customer, "id"),
        }).then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            dispatch(receiveProductData({id, data}));
            if (forLine) {
                dispatch(updateLineFromProduct({id: forLine, product: data}));
            }
        });
    };
};

export const receiveProductData = createAction("receiveProductData");
export const endCreatingOrder = createAction("endCreatingOrder");

function handleCreateResponse(dispatch, data) {
    const {success, errorMessage, orderIdentifier, url} = data;
    if (success) {
        if (url) {
            location.href = url;
        } else {
            // Very, very unlikely that we'd ever get here
            alert("Order" + orderIdentifier + " created.");
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
    alert("An unspecified error occurred.\n" + data);
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
