/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var _ = require("lodash");

module.exports.DEST_DIR = "./static/shoop_admin";
module.exports.PRODUCTION = (process.env.NODE_ENV === "production");

var watchRules = [];

module.exports.getWatchRules = function() {
    return watchRules;
};

module.exports.addWatchRule = function(tasks, paths, func) {
    if (!_.isArray(tasks)) tasks = [tasks];
    watchRules.push({tasks: tasks, paths: paths, func: func});
};
