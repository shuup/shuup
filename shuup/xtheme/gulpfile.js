/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var apfx = require("gulp-autoprefixer");
var gtools = require("./gulp-tools");
var gulp = require("gulp");
var gutil = require("gulp-util");
var less = require("gulp-less");
var nano = require("gulp-cssnano");
var path = require("path");
var ren = require("gulp-rename");
var webpack = require("webpack");

var PRODUCTION = gtools.PRODUCTION;  // --production works in place of the environment variable

gtools.webpackTasks("injection", gtools.buildWebpackConfig(
    "./injection/index.js",
    "editor-injection.js"
));

gtools.webpackTasks("editor-js", gtools.buildWebpackConfig(
    [
        "./editor/index.js",
        "../../admin/static_src/base/js/browse-widget.js"
    ],
    "editor.js"
));

gulp.task("editor-style", function() {
    return gulp.src(["static_src/editor/style.less"])
        .pipe(less())
        .pipe(apfx())
        .pipe(PRODUCTION ? nano() : gutil.noop())
        .pipe(ren("editor.css"))
        .pipe(gulp.dest("static/xtheme"));
});

gtools.registerWatchTask(["editor-style"], function() {
    gulp.watch("static_src/editor/*.*", ["editor-style"]);
});

gulp.task("admin-style", function() {
    return gulp.src(["static_src/admin/css/style.less"])
        .pipe(less())
        .pipe(apfx())
        .pipe(PRODUCTION ? nano() : gutil.noop())
        .pipe(ren("xtheme_admin.css"))
        .pipe(gulp.dest("static/xtheme/admin"));
});

gtools.webpackTasks("admin-js", gtools.buildWebpackConfig(
    [
        "./admin/js/script.js"
    ],
    "admin/admin.js"
));

gulp.task("default", gulp.parallel(["editor-style", "injection", "editor-js", "admin-style", "admin-js"]));
