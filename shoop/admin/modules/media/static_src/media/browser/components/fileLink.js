/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");

export default function(file) {
    var attrs = {};
    const pickMatch = /pick=([^&]+)/.exec(window.location.search);
    if (pickMatch) {
        attrs = {
            href: "#",
            onclick: function(event) {
                window.opener.postMessage({
                    "pick": {
                        "id": pickMatch[1],
                        "object": {
                            "id": file.id,
                            "text": file.name,
                            "url": file.url,
                        }
                    }
                }, "*");
                event.preventDefault();
            }
        };
    } else {
        attrs = {
            href: file.url,
            target: "_blank"
        };
    }
    return m("a", attrs, file.name);
};
