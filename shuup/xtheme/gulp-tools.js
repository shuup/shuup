/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable prefer-const */
var gulp = require("gulp");
var gutil = require("gulp-util");
var merge = require("merge");
var path = require("path");
var webpack = require("webpack");

// --production works in place of the environment variable
var PRODUCTION = (gutil.env.production) || (process.env.NODE_ENV === "production");

function buildWebpackConfig(entry, outputFilename) {
    return {
        context: path.join(__dirname, "static_src"),
        entry: entry,
        output: {
            path: path.join(__dirname, "static", "xtheme"),
            filename: outputFilename
        },
        module: {
            loaders: [
                {
                    exclude: /(node_modules|bower_components)/,
                    test: /\.js$/,
                    loader: "babel",
                    query: { presets: ["env"] }
                },
                {
                    test: /\.png$/,
                    loader: "url"
                }
            ]
        }
    };
}

function webpackRunner(config, watch) {
    config = merge.recursive({}, config);
    config.plugins = config.plugins || [];
    if (PRODUCTION) {
        var UglifyJsPlugin = require("webpack/lib/optimize/UglifyJsPlugin");
        var OccurenceOrderPlugin = require("webpack/lib/optimize/OccurenceOrderPlugin");
        config.plugins.push(new UglifyJsPlugin());
        config.plugins.push(new OccurenceOrderPlugin());
    } else {
        config = merge.recursive(config, {
            debug: true,
            devtool: "sourcemap",
            output: {pathinfo: true}
        });
    }
    var compiler = webpack(config);

    return function(callback) {
        var cb = function(err, stats) {
            if (err) {
                throw new gutil.PluginError("webpack", err);
            }
            gutil.log("[webpack]", stats.toString({colors: true}));
            if (callback) {
                callback();
            }
            if (watch) {
                callback = null;  // can't call the callback more than once
            }
        };
        if (watch) {
            compiler.watch({}, cb);
        } else {
            compiler.run(cb);
        }
    };
}

function webpackTasks(name, config) {
    gulp.task(name, webpackRunner(config));
    gulp.task("watch:" + name, webpackRunner(config, true));
}

function registerWatchTask(directDeps, fn) {
    var deps = [].concat(directDeps || []);
    if (gulp.registry().tasks()) {
        Object.keys(gulp.registry().tasks()).filter(function(n) {
            return n.indexOf("watch:") === 0;
        }).forEach(function(n) {
            deps.push(n);
        });
    }
    gulp.task("watch", gulp.parallel(deps), fn || gutil.noop);
}

module.exports.buildWebpackConfig = buildWebpackConfig;
module.exports.PRODUCTION = PRODUCTION;
module.exports.registerWatchTask = registerWatchTask;
module.exports.webpackRunner = webpackRunner;
module.exports.webpackTasks = webpackTasks;
