# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import subprocess


def get_version(version, root, version_file):
    """
    Get version from given version or from git or from version_file.

    If version does not contain string 'dev', it is used as is.
    Otherwise if we're inside a Git checkout, we'll try to get version
    with "git describe" and if we're not in a git checkout (e.g. we're
    in sdist package), then we'll return version from the version_file,
    which should have been written there when the package was created.
    """
    if 'dev' not in version:
        return version
    elif not os.path.exists(os.path.join(root, '.git')):
        verstr = ''
        if os.path.exists(version_file):
            with open(version_file, 'rt') as fp:
                verstr = fp.read(100).strip()
        if verstr.startswith("__version__ = '" + version):
            return verstr.split("'", 2)[1]
        return version
    tag_name = 'v' + version.split('.post')[0].split('.dev')[0]
    describe_cmd = ['git', 'describe', '--dirty', '--match', tag_name]
    try:
        described = subprocess.check_output(describe_cmd, cwd=root)
    except Exception:
        return version
    suffix = described.decode('utf-8')[len(tag_name):].strip()
    cleaned_suffix = suffix[1:].replace('-g', '+g').replace('-dirty', '.dirty')
    return version + cleaned_suffix


def write_version_to_file(version, version_file):
    with open(version_file, 'wt') as fp:
        fp.write("__version__ = {!r}\n".format(str(version)))
