/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";
import folderClick from "./folderClick";

export default function(ctrl) {
    const items = [];
    const folderPath = ctrl.currentFolderPath();
    _.each(folderPath, function(folder, index) {
        items.push(
            m("a.breadcrumb-link" + (index === folderPath.length - 1 ? ".current" : ""), {
                href: "#",
                key: folder.id,
                onclick: folderClick(ctrl, folder)
            }, folder.name)
        );
        items.push(m("i.fa.fa-angle-right"));
    });
    items.pop(); // pop last chevron
    items.unshift(m("i.fa.fa-folder-open.folder-icon"));
    return items;
}
