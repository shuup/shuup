from django.utils.encoding import force_text
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


def force_ascii(string):
    return str(force_text(string).encode('ascii', 'backslashreplace'))
