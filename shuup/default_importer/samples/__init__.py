# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os


def get_sample_file_content(file_name):
    path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(path):
        from six import BytesIO

        return BytesIO(open(path, "rb").read())
