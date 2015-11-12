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
    setShopId: ((state, {payload}) => _.assign(state, {id: payload})),
    setShopChoices: ((state, {payload}) => _.assign(state, {choices: payload})),
}, {choices: [], id: null});
