/* eslint-disable no-console */
var _ = require("lodash");
var chokidar = require("chokidar");
var gulp = require("gulp");
var gutil = require("gulp-util");

module.exports = function(paths, tasks) {
    var watcher = chokidar.watch(paths, {ignored: /[\/\\]\./, persistent: true});
    var callback = _.debounce(function() {
        gulp.start.apply(gulp, tasks);
    }, 150);
    watcher.on("raw", callback);
    console.log("Watch: " + gutil.colors.green(tasks) + " <= " + gutil.colors.yellow(paths));
    return watcher;
};
