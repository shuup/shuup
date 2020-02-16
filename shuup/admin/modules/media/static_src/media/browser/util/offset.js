/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

// adapted from
// https://github.com/jquery/jquery/blob/250a1990baa571de60325ab2c52eabb399c4cf9e/src/offset.js#L76-L116
export default function(elem) {
    if (!elem.getClientRects().length) {
        return null;
    }

    const rect = elem.getBoundingClientRect();

    if (!(rect.width || rect.height)) {
        return null;
    }
    const doc = elem.ownerDocument;
    const win = doc.defaultView || window;
    const docElem = doc.documentElement;

    return {
        top: rect.top + win.pageYOffset - docElem.clientTop,
        left: rect.left + win.pageXOffset - docElem.clientLeft,
        width: rect.width,
        height: rect.height
    };
}
