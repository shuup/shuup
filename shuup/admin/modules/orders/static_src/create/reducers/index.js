/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {combineReducers} from "redux";
import lines from "./lines";
import productData from "./productData";
import shop from "./shop";
import customer from "./customer";
import customerData from "./customerData";
import customerDetails from "./customerDetails";
import methods from "./methods";
import order from "./order";
import comment from "./comment";
import quickAdd from "./quickAdd";

const childReducer = combineReducers({
    lines,
    productData,
    shop,
    customer,
    customerData,
    customerDetails,
    methods,
    order,
    comment,
    quickAdd
});

export default function(state, action) {
    if(action.type === "_replaceState") { // For debugging purposes.
        return action.payload;
    }
    state = childReducer(state, action);
    return state;
}
