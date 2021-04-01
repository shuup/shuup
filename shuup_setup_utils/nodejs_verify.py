# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import subprocess
import sys

PRELUDE = """
Oops! You don't seem to have Node.js installed, or at the very least
it's not called `node`, as we expect it to be.
""".strip()

DEBIAN_ARGH = """
However, you do have a binary called `nodejs` (version %(version)s),
which strongly implies you may be running Debian or a derivative
thereof, where it's necessary to install the `nodejs-legacy` package to
provide a symlink for `/usr/bin/node`.

So, in short, to continue:
    Run (or ask your administrator to run) `apt-get install nodejs-legacy`.
""".strip()

NO_NODE_WHATSOEVER = """
You need to install Node.js (version 0.12 or newer) to continue.
Please see
  https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager
for instructions relevant to your system.
""".strip()

NO_NPM = """
We could find Node.js, but NPM, the Node.js Package Manager, is not installed.
This is a strange situation indeed, and we're not quite sure how to resolve it.

However we do need `npm` to continue.
""".strip()

DIVIDER = "\n\n%s\n\n" % ("@" * 80)


def snarf(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        return ""
    return stdout.strip().decode("UTF-8", "ignore")


def verify_nodejs():
    node_version = snarf("node --version")
    if not node_version:
        sys.stderr.write(DIVIDER)
        sys.stderr.write(PRELUDE)
        sys.stderr.write("\n\n")
        nodejs_version = snarf("nodejs --version")
        if nodejs_version:
            sys.stderr.write(DEBIAN_ARGH % {"version": nodejs_version})
        else:
            sys.stderr.write(NO_NODE_WHATSOEVER)
        sys.stderr.write(DIVIDER)
        sys.exit(5)
    npm_version = snarf("npm --version")
    if not npm_version:
        sys.stderr.write(DIVIDER)
        sys.stderr.write(NO_NPM)
        sys.stderr.write(DIVIDER)
        sys.exit(6)
