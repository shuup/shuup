/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var gulp = require("gulp");
var less = require("gulp-less");
var concat = require("gulp-concat");
var uglify = require("gulp-uglify");
var plumber = require("gulp-plumber");
var minifycss = require("gulp-cssnano");
var gutil = require("gulp-util");
var merge = require('merge-stream');
var PRODUCTION = gutil.env.production || process.env.NODE_ENV == "production";

var folders = ["blue", "pink"];

gulp.task("less", function() {
    var tasks = folders.map(function(folder){
        return gulp.src([
            "bower_components/owl.carousel/dist/assets/owl.carousel.css",
            "static_src/" + folder + "/less/style.less"
        ])
            .pipe(plumber({}))
            .pipe(less().on("error", function(err) {
                console.log(err.message);
                this.emit("end");
            }))
            .pipe(concat("style.css"))
            .pipe((PRODUCTION ? minifycss() : gutil.noop()))
            .pipe(gulp.dest("static/shuup/classic_gray/" + folder));
    });

    return merge(tasks);
});

gulp.task("less:watch", gulp.parallel(["less"]), function() {
    gulp.watch(["static_src/**/**/*.less"], ["less"]);
});

gulp.task("owl-assets", function() {
    var tasks = folders.map(function(folder) {
        return gulp.src([
            "bower_components/owl.carousel/dist/assets/owl.video.play.png"
        ]).pipe(gulp.dest("static/shuup/classic_gray/" + folder));
    });
    return merge(tasks);
});

gulp.task("default", gulp.parallel(["less", "owl-assets"]));
