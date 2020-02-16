/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const callbacks = [];
const events = ["DOMContentLoaded", "load"];
var loaded = (document.readyState === "complete");

function listener() {
    events.forEach((ev) => { document.removeEventListener(ev, listener); });
    if (!loaded) {
        loaded = true;
        var fn;
        while ((fn = callbacks.shift())) {
            fn();
        }
    }
}

if (!loaded) {
    events.forEach((ev) => { document.addEventListener(ev, listener); });
}

export default function(fn) {
    if (loaded) {
        setTimeout(fn, 0);
    } else {
        callbacks.push(fn);
    }
}
