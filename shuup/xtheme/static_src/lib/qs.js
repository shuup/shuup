/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
export function stringify(obj) {
    const bits = [];
    for (var key in obj) {
        if (obj.hasOwnProperty(key) && obj[key]) {
            bits.push(encodeURIComponent(key) + "=" + encodeURIComponent(obj[key]));
        }
    }
    return bits.sort().join("&");
}

export function parse(queryString) {
    const kw = {};
    if (queryString === null || queryString === undefined) {
        queryString = location.search.replace(/^\?/, "");
    }
    queryString.split("&").forEach((bit) => {
        const [key, val] = bit.split("=", 2);
        kw[key] = (val !== undefined ? val : true);
    });
    return kw;
}

export function mutateObj(obj, mutations) {
    for (var key in mutations) {
        if (!mutations.hasOwnProperty(key)) {
            continue;
        }
        const val = mutations[key];
        if (val === null || val === undefined) {
            delete obj[key];
        } else {
            obj[key] = val;
        }
    }
    return obj;
}

export function mutate(mutations, queryString) {
    const kw = parse(queryString);
    mutateObj(kw, mutations);
    return stringify(kw);
}

export function mutateURL(url, mutations) {
    var [base, search] = url.split("?", 2);
    search = mutate(mutations, search || "");
    return base + (search.length ? "?" + search : "");
}
