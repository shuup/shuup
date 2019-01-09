/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import m from "mithril";
import { supportsDnD } from "../util/dragDrop";

const NO_DND_UPLOAD_HINT = gettext("Click the <strong>Upload</strong> button to upload files.");
const DND_UPLOAD_HINT = (
    supportsDnD ?
        gettext("<span>Drag and drop</span> files here<br> or click the <span>Upload</span> button.") :
        NO_DND_UPLOAD_HINT
);

const responsiveUploadHint = [
    m("div.visible-sm.visible-xs", m.trust(NO_DND_UPLOAD_HINT)),
    m("div.visible-md.visible-lg", m.trust(DND_UPLOAD_HINT))
];

export default responsiveUploadHint;
