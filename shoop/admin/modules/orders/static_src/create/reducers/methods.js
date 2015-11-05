/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

export default handleActions({
    setShippingMethodId: ((state, {payload}) => _.assign(state, {shippingMethodId: payload})),
    setShippingMethodChoices: ((state, {payload}) => _.assign(state, {shippingMethodChoices: payload})),
    setPaymentMethodId: ((state, {payload}) => _.assign(state, {paymentMethodId: payload})),
    setPaymentMethodChoices: ((state, {payload}) => _.assign(state, {paymentMethodChoices: payload})),
}, {
    shippingMethodChoices: [],
    shippingMethodId: null,
    paymentMethodChoices: [],
    paymentMethodId: null,
});
