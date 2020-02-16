/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

window.setNextActionAndSubmit = function(formId, nextAction) {
    const $form = $("#" + formId);
    if (!$form.length) {
        return;
    }
    var $nextAction = $form.find("input[name=__next]");
    if (!$nextAction.length) {
        $nextAction = $("<input>", {
            type: "hidden",
            name: "__next"
        });
        $form.append($nextAction);
    }
    $nextAction.val(nextAction);
    $form.submit();
};

window.serializeForm = function($form) {
    const arrayData = $form.serializeArray();
    let objectData = {};
    for(let i = 0; i < arrayData.length; i++) {
        let obj = arrayData[i];
        var value;
        if(obj.value !== null) {
            value = obj.value;
        } else {
            value = "";
        }

        if(typeof objectData[obj.name] !== "undefined") {
            if(!$.isArray(objectData[obj.name])) {
                objectData[obj.name] = [objectData[obj.name]];
            }
            objectData[obj.name].push(value);
        } else {
            objectData[obj.name] = value;
        }
    }
    return objectData;
};

window.renderFormErrors = function($form, errors) {
    Object.keys(errors).forEach((formName) => {
        const formErrors = errors[formName];
        Object.keys(formErrors).forEach((fieldName) => {
            const fieldErrors = formErrors[fieldName].join(" ");
            if(fieldName === "__all__") {
                $form.parent().find(".errors").append('<div class="alert alert-danger">' + fieldErrors + '</div>');
            } else {
                const field = $("[name=" + formName + "-" + fieldName + "]");
                field.closest(".form-group").addClass("has-error");
                $("<br><span class='help-block error-block'>" + fieldErrors + "</span>").insertBefore(field.closest(".form-input-group"));
            }
        });
    });
};

window.clearErrors = function ($form) {
    $form.find(".has-error").removeClass("has-error");
    $form.find(".error-block").remove();
    $form.find("br").remove();
    $form.parent().find(".errors").empty();
};

function inViewport (el) {

    var r, html;
    if ( !el || 1 !== el.nodeType ) { return false; }
    html = document.documentElement;
    r = el.getBoundingClientRect();

    return ( !!r
      && r.bottom >= 0
      && r.right >= 0
      && r.top <= html.clientHeight
      && r.left <= html.clientWidth
    );

}


$(function() {
    $(".language-dependent-content").each(function() {
        const $ctr = $(this);
        var firstTabWithErrorsOpened = false;
        $ctr.find(".nav-tabs li").each(function() {
            const $tab = $(this);
            const lang = $tab.data("lang");
            if (!lang) {
                return;
            }
            const $tabPane = $ctr.find(".tab-pane[data-lang=" + lang + "]");
            if (!$tabPane) {
                return;
            }
            const tabHasErrors = ($tabPane.find(".has-error").length > 0);
            if (tabHasErrors) {
                const $tabLink = $tab.find("a");
                $tabLink.append($(" <div class=error-indicator><i class=\"fa fa-exclamation-circle\"></i></div>"));
                if (!firstTabWithErrorsOpened) {
                    $tabLink.tab("show");
                    firstTabWithErrorsOpened = true;
                }
            }
        });
    });

    window.onscroll = function() {
        const saveBtn = document.getElementsByClassName("btn btn-success btn-save")[0];
        const groupBtn = document.getElementsByClassName("btn-group")[0];
        const dropBtn = document.getElementsByClassName("btn dropdown-toggle btn-success btn-dropdown-toggle")[0];
        elemArr = []
        if(dropBtn) {
            elemArr.push(groupBtn);
            elemArr.push(dropBtn);
        }
        else if (saveBtn) {
            elemArr.push(saveBtn);
        }

        if (document.body.scrollTop === 0 && document.documentElement.scrollTop === 0){
            for(let el of elemArr) {
                el.classList.remove("opaque");
            }
        }
        else if (!(inViewport(saveBtn))) {
            for(let el of elemArr) {
                el.classList.add("opaque");
            }
        }
    };
}());
