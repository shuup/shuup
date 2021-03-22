# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def media_folder_from_folder(folder):
    """
    Gets media folder from folder

    :param Folder: the folder you want to get the media folder from

    :rtype: shuup.MediaFolder
    """

    return folder.media_folder.first()
