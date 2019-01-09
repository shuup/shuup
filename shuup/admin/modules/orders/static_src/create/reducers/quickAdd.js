/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

export default handleActions({
    setAutoAdd: ((state, {payload}) => _.assign(state, {autoAdd: payload})),
    setQuickAddProduct: ((state, {payload}) => _.assign(state, {product: payload})),
    clearQuickAddProduct: ((state) => _.assign(state, {product: {id: "", text: ""}})),
    setFocusOnQuickAdd: ((state, {payload}) => _.assign(state, {focus: payload}))
}, {
    autoAdd: true,
    focus: false,
    product: {
        id: "",
        text: ""
    }
});
