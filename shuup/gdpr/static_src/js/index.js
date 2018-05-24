(() => {
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
        $("#consent-form").submit();
    }

    $("#btn-save-preferences").click(() => {
        saveConsent();
    });

    $("#agree-btn").click(() => {
        saveConsent();
    });
})();
