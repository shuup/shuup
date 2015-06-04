/**
* This file is part of Shoop.
*
* Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
*
* This source code is licensed under the AGPLv3 license found in the
* LICENSE file in the root directory of this source tree.
 */
window.setNextActionAndSubmit = function(formId, nextAction) {
    var $form = $("#" + formId);
    if(!$form.length) return;
    var $nextAction = $form.find("input[name=__next]");
    if(!$nextAction.length) {
        $nextAction = $("<input>", {
            type: "hidden",
            name: "__next"
        });
        $form.append($nextAction);
    }
    $nextAction.val(nextAction);
    $form.submit();
};
