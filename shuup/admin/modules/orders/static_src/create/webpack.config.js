/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

module.exports = {
    context: __dirname,
    entry: "./index.js",
    output: {
        library: "OrderCreator"
    },
    externals: {
        "lodash": "window._",
        "mithril": "window.m",
        "moment": "window.moment",
        "BrowseAPI": "window.BrowseAPI"
    },
    module: {
        loaders: [
            {
                exclude: /(node_modules|bower_components)/,
                test: /\.js(x?)$/,
                loader: "babel",
                query: { presets: ["env"] }
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
