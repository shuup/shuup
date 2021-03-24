/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const path = require("path");
const os = require("os");
const {exec, execSync, spawn, spawnSync} = require("child_process");

const DEFAULT_CACHE_DIR = path.join(os.homedir(), ".cache", "shuup");

module.exports = {
    getParcelBuildCommand(options = {}) {
        const watch = process.argv.includes("--watch");
        const sourceMaps = options.sourceMaps || (watch ? false : true);
        const outputDir = options.outputDir || "static/";
        const outputFileName = options.outputFileName;
        const entryFile = options.entryFile;
        const publicURL = options.publicURL || "./";
        let cacheDir = DEFAULT_CACHE_DIR;

        if (options.cacheDir) {
            if (path.isAbsolute(options.cacheDir)) {
                cacheDir = options.cacheDir;
            } else {
                cacheDir = path.join(cacheDir, options.cacheDir);
            }
        }

        const args = [watch ? "watch" : "build"];

        if (watch) {
            args.push("--no-hmr");
            args.push("--no-autoinstall");
        }
        if (!sourceMaps) {
            args.push("--no-source-maps");
        }
        args.push("-d", outputDir);
        if (outputFileName) {
            args.push("-o", outputFileName);
        }
        args.push(entryFile);
        args.push("--cache-dir", cacheDir);
        if (process.argv.includes("--no-cache")) {
            args.push("--no-cache");
        }
        args.push("--public-url", publicURL);
        return {
            cmd: "./node_modules/.bin/parcel",
            args: args
        };
    },
    runBuildCommands(commands) {
        commands.forEach((command) => {
            if (process.argv.includes("--sync")) {
                process.stdout.write(`Building in sync mode: ${command.cmd} ${command.args.join(" ")}`);
                let nodeCmd;
                if (process.platform === 'win32') {
                    const commandString = `${command.cmd} ${command.args.join(" ")}`.replace(/\//g, '\\')
                    nodeCmd = execSync(commandString)
                } else {
                    nodeCmd = spawnSync(command.cmd, command.args);
                }
                process.stdout.write(nodeCmd.output.join("\n"));
                if (nodeCmd.status !== 0) {
                    console.error(`Error! Command exited with code ${nodeCmd.status}`);
                }
            } else {
                let nodeCmd;
                if (process.platform === 'win32') {
                    const commandString = `${command.cmd} ${command.args.join(" ")}`.replace(/\//g, '\\')
                    nodeCmd = exec(commandString)
                } else {
                    nodeCmd = spawn(command.cmd, command.args);
                }
                nodeCmd.stdout.on("data", (data) => {
                    process.stdout.write(data);
                });
                nodeCmd.stderr.on("data", (data) => {
                    process.stderr.write(data);
                });
                nodeCmd.on("close", (code) => {
                    if (code !== 0) {
                        console.error(`Error! Command ${command.cmd} ${command.args} exited with code ${code}`);
                    }
                });
            }
        });
    }
};
