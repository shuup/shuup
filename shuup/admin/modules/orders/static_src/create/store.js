/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {compose, createStore, applyMiddleware} from "redux";
import {autoRehydrate} from "redux-persist";
import reducer from "./reducers";

const thunk = function ({ dispatch, getState }) {
    // h/t redux-thunk :)
    return next => action =>
        typeof action === "function" ?
            action(dispatch, getState) :
            next(action);
};

const createLoggedStore = compose(autoRehydrate(), applyMiddleware(thunk))(createStore);
const store = createLoggedStore(reducer);

export default store;
