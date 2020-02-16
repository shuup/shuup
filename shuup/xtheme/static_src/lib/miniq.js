/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const functions = {};

/**
 * @return Array
 */
function maybeSplit(strOrArray) {
    if (Array.isArray(strOrArray)) {
        return strOrArray;
    }
    return ("" + strOrArray).split(/,\s*/);
}

functions.on = function on(events, fn) {
    events = maybeSplit(events);
    this.each((el) => {
        events.forEach((event) => el.addEventListener(event, fn));
    });
    return this;
};

functions.off = function off(events, fn) {
    events = maybeSplit(events);
    this.each((el) => {
        events.forEach((event) => el.removeEventListener(event, fn));
    });
    return this;
};

functions.each = function(fn) {
    this.elements.forEach(fn);
    return this;
};

export default function init(selector, context=document) {
    const rv = {
        context: context,

        // querySelectorAll returns a non-live collection anyway, so it's not a bad idea
        // to array-fy it right here.
        elements: [].slice.call(context.querySelectorAll(selector))
    };
    for (var key in functions) {
        if (functions.hasOwnProperty(key)) {
            rv[key] = functions[key].bind(rv);
        }
    }
    return rv;
}
