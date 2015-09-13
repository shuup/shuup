/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    const isMobile = !!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent));
    $(".multiselect").selectpicker({
        mobile: isMobile,
        style: "btn btn-select",
        title: "",
        selectedTextFormat: "count > 3",
        countSelectedText: "{0}/{1} selected"
    });
}());
