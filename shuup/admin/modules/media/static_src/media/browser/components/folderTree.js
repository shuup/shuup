/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import _ from "lodash";
import { dropzoneConfig } from "../util/dragDrop";
import * as folderActions from "../actions/folderActions";
import folderClick from "./folderClick";

export default function(ctrl) {
    const currentFolderId = ctrl.currentFolderId();
    const folderPath = ctrl.currentFolderPath();
    const idsToCurrent = _.map(folderPath, "id");

    function walk(folder) {
        if (folder.id === undefined) {
            return;
        }
        const inPath = (idsToCurrent.indexOf(folder.id) > -1);
        const isCurrent = (currentFolderId === folder.id);
        const nameLink = m("a", {href: "#", onclick: folderClick(ctrl, folder)}, [
            (inPath ? m("i.caret-icon.fa.fa-caret-down") : m("i.caret-icon.fa.fa-caret-right")),
            (isCurrent ? m("i.folder-icon.fa.fa-folder-open") : m("i.folder-icon.fa.fa-folder")),
            m("span.name", folder.name)
        ]);
        const childLis = (inPath ? _.map(folder.children, walk) : []);
        if (isCurrent) {
            childLis.push(m("li.new-folder-item", {key: "new-folder"}, m("a", {
                href: "#",
                onclick: _.bind(folderActions.promptCreateFolder, null, ctrl, folder.id),
            }, m("i.fa.fa-plus"), " " + gettext("New folder"))));
        }
        const className = _({
            "current": isCurrent,
            "in-path": inPath,
            "has-children": (folder.children.length > 0),
            "fd-zone": true
        }).pick(_.identity).keys().join(" ");
        return m("li",
            {
                "key": folder.id,
                "className": className,
                "data-folder-id": folder.id,
                "config": dropzoneConfig(ctrl)
            },
            [nameLink, (childLis && childLis.length ? m("ul", childLis) : null)]
        );
    }

    return m("ul", walk(ctrl.rootFolder()));
}
