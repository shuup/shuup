/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".form-control.datetime").datetimepicker({
        format: window.ShuupAdminConfig.settings.datetimeInputFormat,
        step: window.ShuupAdminConfig.settings.datetimeInputStep
    });

    $(".form-control.date").datetimepicker({
        format: window.ShuupAdminConfig.settings.dateInputFormat,
        timepicker: false
    });

    $(".form-control.time").datetimepicker({
        format: window.ShuupAdminConfig.settings.timeInputFormat,
        datepicker: false,
        step: window.ShuupAdminConfig.settings.datetimeInputStep
    });

    jQuery.datetimepicker.setLocale(window.ShuupAdminConfig.settings.dateInputLocale);
});
