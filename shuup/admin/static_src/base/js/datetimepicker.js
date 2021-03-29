/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".form-control.datetime").datetimepicker({
        format: window.ShuupAdminConfig.settings.datetimeInputFormat,
        step: window.ShuupAdminConfig.settings.datetimeInputStep,
        scrollMonth : false, // Scrolling is disabled due to it being broken (always going down)
        scrollInput : false
    });

    $(".form-control.date").datetimepicker({
        format: window.ShuupAdminConfig.settings.dateInputFormat,
        timepicker: false,
        scrollMonth : false,
        scrollInput : false
    });

    $(".form-control.time").datetimepicker({
        format: window.ShuupAdminConfig.settings.timeInputFormat,
        step: window.ShuupAdminConfig.settings.datetimeInputStep,
        datepicker: false,
        scrollInput : false
    });

    jQuery.datetimepicker.setLocale(window.ShuupAdminConfig.settings.dateInputLocale);
});
