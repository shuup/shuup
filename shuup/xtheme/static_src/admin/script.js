$(document).ready(function() {
    $(".theme-select").click(function(e) {
        e.preventDefault();
        $(".theme-screenshot").each(function(idx, elem) {$(elem).removeClass("active")});
        $(this).closest(".theme-screenshot").addClass("active");
        var target = $(this).data("target");
        var selector = "#id_stylesheet";
        $(selector).select2("destroy");
        $(selector).val(target);
        $(selector).select2();
    });
});