/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var gulp = require("gulp");
var less = require("gulp-less");
var concat = require("gulp-concat");
var uglify = require("gulp-uglify");
var plumber = require("gulp-plumber");
var minifycss = require("gulp-cssnano");
var gutil = require("gulp-util");
var PRODUCTION = gutil.env.production || process.env.NODE_ENV == "production";

gulp.task("less", function() {
    return gulp.src([
        "bower_components/owl.carousel/dist/assets/owl.carousel.css",
        "static_src/less/style.less"
    ])
        .pipe(plumber({}))
        .pipe(less().on("error", function(err) {
            console.log(err.message);
            this.emit("end");
        }))
        .pipe(concat("style.css"))
        .pipe((PRODUCTION ? minifycss() : gutil.noop()))
        .pipe(gulp.dest("static/shuup/front/css/"));
});

gulp.task("less:watch", ["less"], function() {
    gulp.watch(["static_src/less/**/*.less"], ["less"]);
});

gulp.task("js", function() {
    return gulp.src([
        "bower_components/jquery/dist/jquery.js",
        "bower_components/bootstrap/dist/js/bootstrap.js",
        "bower_components/bootstrap-select/dist/js/bootstrap-select.js",
        "bower_components/jquery.easing/js/jquery.easing.js",
        "bower_components/owl.carousel/dist/owl.carousel.js",
        "static_src/js/vendor/imagelightbox.js",
        "static_src/js/custom.js"
    ])
        .pipe(plumber({}))
        .pipe(concat("scripts.js"))
        .pipe((PRODUCTION ? uglify() : gutil.noop()))
        .pipe(gulp.dest("static/shuup/front/js/"));
});

gulp.task("js:watch", ["js"], function() {
    gulp.watch(["static_src/js/**/*.js"], ["js"]);
});

gulp.task("copy_fonts", function() {
    return gulp.src([
        "bower_components/bootstrap/fonts/*",
        "bower_components/font-awesome/fonts/*"
    ]).pipe(gulp.dest("static/shuup/front/fonts/"));
});

gulp.task("default", ["js", "less", "copy_fonts"]);

gulp.task("watch", ["js:watch", "less:watch"], function() {
});
