/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {createStore, applyMiddleware} from "redux";
import reducer from "./reducers";

const logger = ({ getState }) => (next) => (action) => {
    // h/t redux-logger :)
    const console = window.console;
    next(action);
    if (console !== undefined) {
        console.log("%c Action", "color: #995EEA", action);  // eslint-disable-line no-console
        console.log("%c State", "color: #995EEA", getState());  // eslint-disable-line no-console
    }
};

const thunk = function ({ dispatch, getState }) {
    // h/t redux-thunk :)
    return next => action =>
        typeof action === "function" ?
            action(dispatch, getState) :
            next(action);
};

const createLoggedStore = applyMiddleware(thunk, logger)(createStore);
const store = createLoggedStore(reducer);

export default store;
