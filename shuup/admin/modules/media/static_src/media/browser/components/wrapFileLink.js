/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const getPickId = require("../util/getPickId");

export default function(file, tag = "a", content = file.name) {
    const attrs = {href: file.url, target: "_blank"};
    const pickId = getPickId();
    if (pickId) {
        attrs.onclick = function(event) {
            window.opener.postMessage({
                "pick": {
                    "id": pickId,
                    "object": {
                        "id": file.id,
                        "text": file.name,
                        "url": file.url
                    }
                }
            }, "*");
            event.preventDefault();
            return false;
        };
    }
    return m(tag, attrs, content);
}
