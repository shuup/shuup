/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    function update() {
        $(".timesince").each(function() {
            const $el = $(this);
            const ts = $el.data("ts");
            if (!ts) {
                return;
            }
            const time = moment(ts);
            if (!time.isValid()) {
                return;
            }
            $el.text(time.fromNow());
        });
    }
    update();
    setInterval(update, 60000);
});
