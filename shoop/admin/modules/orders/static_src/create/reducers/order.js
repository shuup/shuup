/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";
import _ from "lodash";

function updateTotals(state, {payload}) {
    const updates = {};
    const {lines, methods} = payload();
    var total = 0;
    _.map(lines, (line) => {
        total += line.total;
    });
    updates.total = +total.toFixed(2);
    return _.assign({}, state, updates);
}

export default handleActions({
    beginCreatingOrder: ((state) => _.assign(state, {creating: true})),
    endCreatingOrder:  ((state) => _.assign(state, {creating: false})),
    updateTotals,
    setOrderSource: ((state, {payload}) => _.assign(state, {source: payload})),
    clearOrderSourceData: ((state) => _.assign(state, {source: null}))
}, {
    creating: false,
    source: null,
    total: 0
});
