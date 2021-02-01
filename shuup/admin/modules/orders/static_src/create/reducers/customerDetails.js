/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

export default handleActions({
    retrieveCustomerDetails: _.identity,
    receiveCustomerDetails: (state, {payload}) => {
        return _.assign(state, {
            customerInfo: payload.data.customer_info,
            orderSummary: payload.data.order_summary,
            recentOrders: payload.data.recent_orders
        });
    },
    showCustomerModal: ((state, {payload}) => _.assign(state, {showCustomerModal: payload}))
}, {});
