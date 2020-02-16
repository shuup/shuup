/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { handleActions } from "redux-actions";

export default handleActions({
    setShopChoices: ((state, { payload }) => Object.assign({}, state, { choices: payload })),
    setCountries: ((state, { payload }) => Object.assign({}, state, { countries: payload })),
    setShop: ((state, { payload }) => Object.assign({}, state, { selected: payload }))
}, {
    choices: [],
    countries: [],
    selected: null
});
