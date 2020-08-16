/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shuup Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-shadow,eqeqeq */
import _ from "lodash";

export default function(folderPath, folderId) {

    var folder = folderPath.find(obj => {
        return obj.id === folderId
      })

    return folder;
}
