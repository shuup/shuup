# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import subprocess
from fnmatch import fnmatch
from setup import EXCLUDE_PATTERNS
from nodejs_verify import verify_nodejs


verify_nodejs()

package_jsons = []

for root, dirnames, filenames in os.walk("."):
    dirnames[:] = [dn for dn in dirnames if not any(fnmatch(dn, exc) for exc in EXCLUDE_PATTERNS)]
    if "package.json" in filenames:
        if root != ".":  # Ignore the root package json
            package_jsons.append(os.path.join(root, "package.json").replace(os.sep, "/"))

for i, package_json in enumerate(package_jsons, 1):
    print("*** (%-2d/%2d) Running `npm run build`: %s" % (i, len(package_jsons), package_json))
    subprocess.check_call(
        "npm run build",
        cwd=os.path.dirname(package_json),
        shell=True
    )
