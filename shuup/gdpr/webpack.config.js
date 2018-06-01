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
const ExtractTextPlugin = require("extract-text-webpack-plugin");
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');

module.exports = function getConfig(env) {
    const production = (env.dist === true);
    const extractLess = new ExtractTextPlugin({
        filename: "[name].css",
        disable: false
    });

    let plugins = [
        extractLess
    ];

    if (production) {
        plugins = plugins.concat([
            new webpack.DefinePlugin({ "process.env.NODE_ENV": JSON.stringify("production") }),
            new UglifyJSPlugin({ sourceMap: false }),
        ]);
    }

    return (
        {
            entry: {
                shuup_gdpr: path.resolve(__dirname, "./static_src/js/index.js"),
                shuup_gdpr_styles: path.resolve(__dirname, "./static_src/less/index.less")
            },
            output: {
                path: path.resolve(__dirname, "./static/shuup_gdpr/"),
                filename: "[name].js",
                publicPath: "/static/shuup_gdpr/",
                sourceMapFilename: "[name].map"
            },
            module: {
                loaders: [],
                rules: [
                    { test: /\.js$/, use: "babel-loader" },
                    {
                        test: /\.less$/,
                        use: extractLess.extract({
                            use: [
                                {
                                    loader: "css-loader",
                                    options: {
                                        minimize: production
                                    }
                                },
                                "postcss-loader",
                                {
                                    loader: "less-loader",
                                    options: {
                                        compress: production
                                    }
                                }
                            ]
                        })
                    }
                ]
            },
            plugins: plugins
        }
    );
};
