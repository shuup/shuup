/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {combineReducers} from "redux";
import lines from "./lines";
import productData from "./productData";
import shop from "./shop";
import customer from "./customer";
import methods from "./methods";
import order from "./order";
import comment from "./comment";

const childReducer = combineReducers({lines, productData, shop, customer, methods, order, comment});

export default function(state, action) {
    if(action.type === "_replaceState") { // For debugging purposes.
        return action.payload;
    }
    state = childReducer(state, action);
    return state;
}
