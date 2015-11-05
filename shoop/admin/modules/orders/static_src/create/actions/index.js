/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {createAction} from "redux-actions";
import {get} from "../api";
import _ from "lodash";

export const setCustomer = createAction("setCustomer");
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

export const beginCreatingOrder = function () {
    return () => {
        // TODO: Send something
    };
};
