/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

(() => {
    function init() {
    $(document).ready(function() {
        if(navigator.userAgent.match(/Windows Phone/i)){
            $(".gdpr-consent-warn-content").addClass("windows-phone");
        }

    });

    $("#privacy-preferences-btn").click(() => {
        $(".gdpr-consent-preferences").addClass("visible");
        $("body").addClass("body-noscroll");
    });

    $(".gdpr-consent-preferences .btn-close").click(() => {
        $(".gdpr-consent-preferences").removeClass("visible");
        $("body").removeClass("body-noscroll");
    });

    $(".consent-option-item").click((e) => {
        $(".gdpr-consent-preference-panel").removeClass("active");
        $(".consent-option-item").removeClass("active");
        $(e.target).addClass("active");
        const data = $(e.target).data();
        $("#consent_" + data.target).addClass("active");
    });

    function saveConsent() {
        $(".gdpr-consent-warn-bar").hide();
        $(".gdpr-consent-preferences").hide();
        data = $("#consent-form").serialize();
        var request = $.ajax({
            url: $("#consent-form").attr("action"),
            type: 'POST',
            data: data,
            success: function() {
                // Remove GDPR divs and their content upon successful completion
                $(".gdpr-consent-warn-bar").remove();
                $(".gdpr-consent-preferences").remove();
                $("body").removeClass("body-noscroll");
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $(".gdpr-consent-warn-bar").show();
                $(".gdpr-consent-preferences").show();
                window.alert(gettext("Error! Saving the consent failed, please try again."));
            }
        });
    }

    $("#btn-save-preferences").click(() => {
        saveConsent();
    });

    $("#agree-btn").click(() => {
        saveConsent();
    });
    }
    if (typeof jQuery === "undefined") {
        document.getElementsByClassName("gdpr-consent-warn-bar")[0].hidden = true;
        document.getElementsByClassName("gdpr-consent-preferences")[0].hidden = true;
    } else {
        init();
    }

})();
