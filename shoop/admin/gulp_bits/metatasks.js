/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var _ = require("lodash");
var autoprefixer = require("gulp-autoprefixer");
var concat = require("gulp-concat");
var cssPackages = require("./css-packages");
var gulp = require("gulp");
var gutil = require("gulp-util");
var jsPackages = require("./js-packages");
var less = require("gulp-less");
var mincss = require("gulp-minify-css");
var path = require("path");
var plumber = require("gulp-plumber");
var settings = require("./settings");
var size = require("gulp-size");
var sourcemaps = require("gulp-sourcemaps");
var babel = require('gulp-babel');
var uglify = require("gulp-uglify");
var webpack = require("webpack");

function basifyFile(spec, file) {
    if(!spec.base) return file;
    return path.join(spec.base, file);
}

function basifyFiles(spec) {
    return spec.files.map(basifyFile.bind(null, spec));
}

module.exports.CSS_TASK_NAMES = _.map(cssPackages, function(spec, name) {
    var taskName = "css:" + name;
    gulp.task(taskName, function() {
        return gulp.src(basifyFile(spec, spec.entrypoint))
            .pipe(plumber())
            .pipe(sourcemaps.init())
            .pipe(less({strictImports: true}))
            .pipe(autoprefixer({
                browsers: ["last 2 versions"],
                cascade: false
            }))
            .pipe(concat(name + ".css"))
            .pipe((settings.PRODUCTION ? mincss({keepBreaks: true}) : gutil.noop()))
            .pipe((settings.PRODUCTION ? gutil.noop() : sourcemaps.write()))
            .pipe(size({title: taskName}))
            .pipe(gulp.dest(settings.DEST_DIR + "/css"));
    });
    if(!spec.watches) spec.watches = [spec.entrypoint];
    var watches = spec.watches.map(basifyFile.bind(null, spec));
    settings.addWatchRule(taskName, watches);

    return taskName;
});

function normalJsBundle(spec, name) {
    var paths = spec.files.map(basifyFile.bind(null, spec));
    var taskName = "js:" + name;
    gulp.task(taskName, function() {
        return gulp.src(paths)
            .pipe(plumber())
            .pipe(sourcemaps.init())
            .pipe((!!spec.es6 ? babel() : gutil.noop()))
            .pipe(concat(name + ".js"))
            .pipe((settings.PRODUCTION ? uglify() : gutil.noop()))
            .pipe((settings.PRODUCTION ? gutil.noop() : sourcemaps.write()))
            .pipe(size({title: taskName}))
            .pipe(gulp.dest(settings.DEST_DIR + "/js"));
    });

    settings.addWatchRule(taskName, paths);

    return taskName;
}

function webpackJsBundle(spec, name) {
    var taskName = "js:" + name;
    if(_.isString(spec.webpack)) {  // Allow loading webpack configuration from file
        spec.webpack = require(spec.webpack);
    }
    spec.webpack.output = _.extend(spec.webpack.output || {}, {
        path: settings.DEST_DIR + "/js",
        filename: name + ".js"
    });
    if(settings.PRODUCTION) {
        spec.webpack.plugins = [
            new webpack.optimize.UglifyJsPlugin(),
            new webpack.optimize.DedupePlugin(),
        ];
    }
    var packer = webpack(spec.webpack);

    var complete = function(err, stats) {
        if(err) throw new gutil.PluginError(taskName, err);
        gutil.log(taskName, stats.toString({colors: true}));
    };

    gulp.task(taskName, function(callback) {
        packer.run(function(err, stats) {
            complete(err, stats);
            callback();
        });
    });
    if (spec.watch) {
        // TODO: Webpack's watch doesn't seem to work reliably, use this...
        settings.addWatchRule(taskName, spec.watch);
    }
    return taskName;
}

module.exports.JS_TASK_NAMES = _.map(jsPackages, function(spec, name) {
    if (spec.webpack) {
        return webpackJsBundle(spec, name);
    }
    return normalJsBundle(spec, name);
});

function installTasks() {
    var watchRules = settings.getWatchRules();
    var taskNames = _(watchRules).
        pluck("tasks").
        flatten().
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
    gulp.task("watch", ["bower"], function() {
        _.each(watchRules, function(r) {
            if (r.paths) {
                gulp.watch(r.paths, r.tasks);
                console.log("Watch:" + gutil.colors.green(r.tasks) + " <= " + gutil.colors.yellow(r.paths));
            }
            if (r.func) r.func();
        });
    });
}

module.exports.installTasks = installTasks;
