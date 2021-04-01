/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
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
    m("div.d-block.d-lg-none", m.trust(NO_DND_UPLOAD_HINT)),
    m("div.d-none.d-lg-block", m.trust(DND_UPLOAD_HINT))
];

export default responsiveUploadHint;
