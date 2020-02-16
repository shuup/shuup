/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

export default handleActions({
    setShippingMethod: ((state, {payload}) => _.assign(state, {shippingMethod: payload})),
    setShippingMethodChoices: ((state, {payload}) => _.assign(state, {shippingMethodChoices: payload})),
    setPaymentMethod: ((state, {payload}) => _.assign(state, {paymentMethod: payload})),
    setPaymentMethodChoices: ((state, {payload}) => _.assign(state, {paymentMethodChoices: payload}))
}, {
    shippingMethodChoices: [],
    shippingMethod: null,
    paymentMethodChoices: [],
    paymentMethod: null
});
