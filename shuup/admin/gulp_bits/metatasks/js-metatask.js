/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var _ = require("lodash");
var babel = require("gulp-babel");
var basifyFile = require("../util").basifyFile;
var concat = require("gulp-concat");
var gulp = require("gulp");
var gutil = require("gulp-util");
var plumber = require("gulp-plumber");
var settings = require("../settings");
var size = require("gulp-size");
var sourcemaps = require("gulp-sourcemaps");
var uglify = require("gulp-uglify");
var webpack = require("webpack");
var watchPaths = require("./watch-paths");
var gulpif = require("gulp-if");

function normalJsBundle(spec, name) {
    var paths = spec.files.map(basifyFile.bind(null, spec));
    var taskName = "js:" + name;
    var destDir = settings.DEST_DIR + "/js";
    var watcher = null;
    var transpiler = gutil.noop();
    if (spec.es6) {
        // Don't transpile Bower components.
        transpiler = gulpif(function(file) { return /bower_components/.test(file.path); }, gutil.noop(), babel({ presets: ['env'] }));
    }
    gulp.task(taskName, function () {
        if (settings.WATCH && !watcher) {
            watcher = watchPaths(paths, [taskName]);
        }

        return gulp.src(paths)
            .pipe(plumber())
            .pipe(sourcemaps.init())
            .pipe(transpiler)
            .pipe(concat(name + ".js"))
            .pipe((settings.PRODUCTION ? uglify() : gutil.noop()))
            .pipe(sourcemaps.write("."))
            .pipe(size({title: taskName}))
            .pipe(gulp.dest(destDir));
    });

    return taskName;
}

function getWebpackConfig(specWebpack, name) {
    if (_.isString(specWebpack)) {  // Allow loading webpack configuration from file
        specWebpack = require(specWebpack);
    }
    specWebpack.output = _.extend(specWebpack.output || {}, {
        path: settings.DEST_DIR + "/js",
        filename: name + ".js"
    });
    if (settings.PRODUCTION) {
        if(!Array.isArray(specWebpack.plugins)) {
            specWebpack.plugins = [];
        }
        specWebpack.plugins = specWebpack.plugins.concat([
            new webpack.optimize.UglifyJsPlugin(),
            new webpack.optimize.DedupePlugin()
        ]);
    }
    if (!specWebpack.devtool) {
        specWebpack.devtool = (settings.PRODUCTION ? "source-map" : "cheap-module-source-map");
    }
    return specWebpack;
}

function webpackJsBundle(spec, name) {
    var taskName = "js:" + name;
    var config = getWebpackConfig(spec.webpack, name);
    var packer = webpack(config);

    var complete = function(err, stats) {
        if (err) {
            throw new gutil.PluginError(taskName, err);
        }
        gutil.log(taskName, stats.toString({colors: true}));
    };

    gulp.task(taskName, function(callback) {
        if (settings.WATCH) {
            if (config.context) {
                packer.watch({aggregateTimeout: 300}, function(err, stats) {
                    complete(err, stats);
                });
                gutil.log("Webpack watcher initialized: " + taskName);
            } else {
                gutil.log("The Webpack configuration for " + taskName + " is not adequate for --watch!");
            }
        } else {
            packer.run(function(err, stats) {
                complete(err, stats);
                callback();
            });
        }
    });
    return taskName;
}

module.exports = function(spec, name) {
    if (spec.webpack) {
        return webpackJsBundle(spec, name);
    } else {
        return normalJsBundle(spec, name);
    }
};
