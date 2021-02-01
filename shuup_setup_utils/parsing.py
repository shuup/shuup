# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os


def get_test_requirements_from_tox_ini(path):
    result = []
    between_begin_and_end = False
    with open(os.path.join(path, 'tox.ini'), 'rt') as fp:
        for line in fp:
            if line.strip() == '# BEGIN testing deps':
                between_begin_and_end = True
            elif line.strip() == '# END testing deps' or not line[0].isspace():
                between_begin_and_end = False
            elif between_begin_and_end:
                result.append(line.strip())
    return result


def get_long_description(path):
    """
    Get long description from file.
    """
    if path:
        with open(path, 'rt') as fp:
            return fp.read()
    return None
