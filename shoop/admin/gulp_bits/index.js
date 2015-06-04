/**
* This file is part of Shoop.
*
* Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
*
* This source code is licensed under the AGPLv3 license found in the
* LICENSE file in the root directory of this source tree.
 */
var _ = require("lodash");
var gulp = require('gulp');
var gutil = require("gulp-util");
var settings = require("./settings");
var metatasks = require("./metatasks");
require("./bower-install-task");
var watchRules = settings.getWatchRules();
var noop = function(complete) { complete(); };
var taskNames = _(watchRules).pluck("tasks").flatten().concat(metatasks.CSS_TASK_NAMES).concat(metatasks.JS_TASK_NAMES).value();
var tasksByPrefix = _(taskNames).uniq().groupBy(function (p) { return p.split(":")[0]; }).value();
_.each(tasksByPrefix, function(tasks, prefix) { gulp.task(prefix, tasks, noop); });
gulp.task('build', _.keys(tasksByPrefix), noop);
gulp.task('watch', ["bower"], function() {
    _.each(watchRules, function(r) {
        if(r.paths) {
            gulp.watch(r.paths, r.tasks);
            console.log("Watch:" + gutil.colors.green(r.tasks) + " <= " + gutil.colors.yellow(r.paths));
        }
        if(r.func) r.func();
    });
});
gulp.task('default', function() {
    console.log(gutil.colors.cyan.bold(
        "*** Please use `npm run build` instead of running `gulp` directly!\n" +
        "  * Using `npm run build` will ensure Bower prerequisites are installed before\n" +
        "  * Gulp tasks are run.  Alternately, use `gulp bower`, then `gulp build` (or `gulp watch`)."
    ));
});
if(settings.PRODUCTION) {
    gutil.log("Production mode enabled.");
}
