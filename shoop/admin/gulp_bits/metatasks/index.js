/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var _ = require("lodash");
var cssMetatask = require("./css-metatask");
var cssPackages = require("../css-packages");
var gulp = require("gulp");
var jsMetatask = require("./js-metatask");
var jsPackages = require("../js-packages");

module.exports.CSS_TASK_NAMES = _.map(cssPackages, cssMetatask);
module.exports.JS_TASK_NAMES = _.map(jsPackages, jsMetatask);

function installTasks() {
    var taskNames = _([]).
        concat(module.exports.CSS_TASK_NAMES).
        concat(module.exports.JS_TASK_NAMES).
        value();
    var tasksByPrefix = _(taskNames).uniq().groupBy(function(p) {
        return p.split(":")[0];
    }).value();
    _.each(tasksByPrefix, function(tasks, prefix) {
        gulp.task(prefix, tasks);
    });
    gulp.task("build", _.keys(tasksByPrefix));
}

module.exports.installTasks = installTasks;
