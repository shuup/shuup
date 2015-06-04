#!/usr/bin/env python
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import os
import subprocess
import sys


APIDOC_EXCLUDES = [
]


def main():
    os.chdir(os.path.dirname(__file__))
    apidoc_dir = os.path.join('doc', 'api')

    # Remove all the previous versions
    for filename in os.listdir(apidoc_dir):
        if filename.endswith('.rst') and filename != 'modules.rst':
            os.remove(os.path.join(apidoc_dir, filename))

    # Generate new
    retcode = subprocess.call(
        ['sphinx-apidoc', '-o', 'doc/api', 'shoop'] +
        APIDOC_EXCLUDES + sys.argv)
    raise SystemExit(retcode)


if __name__ == '__main__':
    main()
