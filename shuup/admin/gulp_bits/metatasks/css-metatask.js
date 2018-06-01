/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var autoprefixer = require("gulp-autoprefixer");
var basifyFile = require("../util").basifyFile;
var concat = require("gulp-concat");
var gulp = require("gulp");
var gutil = require("gulp-util");
var less = require("gulp-less");
var cssnano = require("gulp-cssnano");
var plumber = require("gulp-plumber");
var settings = require("../settings");
var size = require("gulp-size");
var sourcemaps = require("gulp-sourcemaps");
var watchPaths = require("./watch-paths");

module.exports = function(spec, name) {
    var taskName = "css:" + name;
    var destDir = settings.DEST_DIR + "/css";
    var watcher = null;

    gulp.task(taskName, function() {
        if (settings.WATCH && !watcher) {
            var watches = (spec.watches || [spec.entrypoint]).map(basifyFile.bind(null, spec));
            watcher = watchPaths(watches, [taskName]);
        }
        return gulp.src(basifyFile(spec, spec.entrypoint))
            .pipe(plumber())
            .pipe(sourcemaps.init())
            .pipe(less({strictImports: true}))
            .pipe(autoprefixer({
                browsers: ["last 2 versions"],
                cascade: false
            }))
            .pipe(concat(name + ".css"))
            .pipe((settings.PRODUCTION ? cssnano() : gutil.noop()))
            .pipe(sourcemaps.write("."))
            .pipe(size({title: taskName}))
            .pipe(gulp.dest(destDir));
    });

    return taskName;
};
