/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var gulp = require("gulp");
var glob = require("glob");
var bower = require("bower");
var gutil = require("gulp-util");
var _ = require("lodash");
var path = require("path");
var fs = require("fs");

gulp.task("bower", gulp.parallel([], function(complete) {
    glob("{modules,static_src}/**/bower.json", {
        ignore: ["**/node_modules/**", "**/bower_components/**"]
    }, function(er, files) {
        var deferredComplete = _.after(files.length, complete);
        _.each(files, function(bowerJsonPath) {
            var dir = path.dirname(bowerJsonPath);
            var bowerComponentsDir = path.join(dir, "bower_components");
            gutil.log("Bower start:", bowerJsonPath);
            if (!fs.existsSync(bowerComponentsDir)) {
                fs.mkdirSync(bowerComponentsDir);
                gutil.log("  mkdir:", bowerComponentsDir);
            }
            var install = bower.commands.install(
                [],
                {},
                {cwd: dir, directory: "bower_components"},
                {"interactive": false}
            );
            install.on("log", function(log) {
                gutil.log("Bower/" + bowerJsonPath + ":" + log.message);
            });
            install.on("end", function() {
                gutil.log("Bower complete:", bowerJsonPath);
                deferredComplete();
            });
        });
    });
}));
