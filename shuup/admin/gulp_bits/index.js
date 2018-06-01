/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-console */
var gulp = require("gulp");
var gutil = require("gulp-util");
var settings = require("./settings");

require("./bower-install-task");  // Installs the `bower` task.

if (process.argv.indexOf("bower") === -1) {
    // If `bower` exists on the command line, it should be run by itself in any case (because Gulp/
    // Orchestrator attempts to run tasks with maximum parallelisation), so when that occurs,
    // we don't need to load the regular tasks (nor the whole metatask hierarchy).  This makes loading
    // a little faster, too.
    // As a side effect, this squelches errors from main-bower-files.
    require("./metatasks").installTasks();
}

gulp.task("default", function() {
    console.log(gutil.colors.cyan.bold(
        "*** Please use `npm run build` instead of running `gulp` directly!\n" +
        "  * Using `npm run build` will ensure Bower prerequisites are installed before\n" +
        "  * Gulp tasks are run.  Alternately, use `gulp bower`, then `gulp build` (or `gulp --watch`)."
    ));
});

gulp.task("watch", function() {
    console.log(gutil.colors.cyan.bold(
        "*** Please use `gulp [task ...] --watch` instead of `gulp watch`!\n" +
        "  * That is, `gulp css:base --watch` for instance.\n"
    ));
});

if (settings.PRODUCTION) {
    gutil.log("Production mode enabled.");
}
