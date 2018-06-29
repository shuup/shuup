/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

'use strict';
const webpack = require("webpack");
const path = require("path");
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');

module.exports = function getConfig(env) {
    const production = (env.dist === true);
    let plugins = [];
    if (production) {
        plugins = plugins.concat([
            new webpack.DefinePlugin({ "process.env.NODE_ENV": JSON.stringify("production") }),
            new UglifyJSPlugin({ sourceMap: false }),
        ]);
    }
    return (
        {
            entry: {
                shuup_regions: path.resolve(__dirname, "./static_src/index.js")
            },
            output: {
                path: path.resolve(__dirname, "./static/shuup_regions/"),
                filename: "[name].js",
                publicPath: "/static/shuup_regions/",
                sourceMapFilename: "[name].map"
            },
            module: {
                loaders: [],
                rules: [
                    { test: /\.js$/, use: "babel-loader" }
                ]
            },
            plugins: plugins
        }
    );
};
