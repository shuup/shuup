/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var path = require("path");

module.exports = {
    context: path.join(__dirname, "static_src", "media", "browser"),
    entry: "./Browser.js",
    output: {
        library: "MediaBrowser"
    },
    externals: {
        "lodash": "window._",
        "mithril": "window.m",
        "moment": "window.moment"
    },
    module: {
        loaders: [
            {
                test: /\.js(x?)$/,
                exclude: /(node_modules|bower_components)/,
                loader: "babel-loader?loose=all"
            },
            {
                test: /\.less/,
                loader: "style-loader!css-loader" +
                    "!autoprefixer-loader?browsers=last 2 version" +
                    "!less-loader"
            },
            {
                test: /\.(png|jpg|woff)$/,
                loader: "url-loader"
            }
        ]
    }
};
