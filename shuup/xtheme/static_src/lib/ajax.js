/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/**
 * BASED ON:
 * xhr-ajax.js Copyright (C) 2013 Craig Roberts (http://craig0990.co.uk)
 *
 * Licensed under the MIT License (http://mit-license.org)
 */

export default function ajax(options) {
    const noop = function() {};
    const client = new XMLHttpRequest();
    options.success = options.success || noop;
    options.error = options.error || noop;
    options.async = true;
    client.open(options.method || "GET", options.url);
    client.send(options.data);
    client.onreadystatechange = function() {
        if (this.readyState !== 4) {
            return;
        }
        if (this.status === 200) {
            options.success(this.responseText, this);
        } else {
            options.error(this.status, this.statusText, this);
        }
        client.onreadystatechange = noop;
    };
    return client;
}
