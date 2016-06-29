/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
export default function() {
    const pickMatch = /pick=([^&]+)/.exec(window.location.search);
    return (pickMatch ? pickMatch[1] : null);
}
