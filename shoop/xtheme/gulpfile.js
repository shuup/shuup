/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
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

var PRODUCTION = gtools.PRODUCTION;  // --production works in place of the environment variable

gtools.webpackTasks("injection", gtools.buildWebpackConfig(
    "./injection/index.js",
    "editor-injection.js"
));

gtools.webpackTasks("editor-js", gtools.buildWebpackConfig(
    "./editor/index.js",
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

gulp.task("default", ["editor-style", "injection", "editor-js"]);
