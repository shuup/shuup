/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    function update() {
        $(".timesince").each(function() {
            var $el = $(this);
            var ts = $el.data("ts");
            if(!ts) return;
            var time = moment(ts);
            if(!time.isValid()) return;
            $el.text(time.fromNow());
        });
    }
    update();
    setInterval(update, 60000);
});
