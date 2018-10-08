/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import domready from "../lib/domready";
import { mutate } from "../lib/qs";
import el from "../lib/el";

function post(args) {
    if (window.CSRF_TOKEN) {
        args.csrfmiddlewaretoken = window.CSRF_TOKEN;
    }
    const inputs = Object.keys(args).
        map((key) => {
            const val = args[key];
            return typeof val !== "undefined"? el("input", {type: "hidden", name: key, value: val}) : null;
        }
    );
    const form = el("form", {method: "POST", action: location.href}, inputs);
    document.body.appendChild(form);
    form.submit();
}

function updateModelChoiceWidgetURL(select) {
    const selectedObject = select.options[select.selectedIndex];
    const url = selectedObject.dataset.adminUrl;
    const widgetExtraDiv = document.getElementById("extra_for_" + select.id);
    const linkText = interpolate(gettext("Edit %s"), [selectedObject.text]);
    widgetExtraDiv.innerHTML = url ? el("a", {"target": "_blank", "href": url}, [linkText]).outerHTML : "";
}

domready(() => {
    let changesMade = false;
    $(".layout-cell").on("click", function() {
        const {x, y} = this.dataset;
        const newQs = mutate({x, y});
        location.href = "?" + newQs;
    });
    $(".layout-add-cell-btn").on("click", function() {
        const {y, cellCount, cellLimit} = this.dataset;
        if (cellCount >= cellLimit) {
            alert(interpolate(gettext("Error: Cannot add more than %s cells to one row."), [cellLimit]));
            return;
        }
        post({y: y, command: "add_cell"});
    });
    $(".layout-add-row-btn").on("click", function() {
        const {y} = this.dataset;
        post({y, command: "add_row"});
    });
    $(".layout-del-row-btn").on("click", function() {
        if (!confirm(gettext("Are you sure you wish to delete this row?"))) {
            return;
        }
        const {y} = this.dataset;
        post({y, command: "del_row"});
    });
    $(".del-cell-btn").on("click", function() {
        if (!confirm(gettext("Are you sure you wish to delete this cell?"))) {
            return;
        }
        const {x, y} = this.dataset;
        post({x, y, command: "del_cell"});
    });
    $(".publish-btn").on("click", function() {
        if (!confirm(gettext("Are you sure you wish to publish changes made to this view?"))) {
            return;
        }
        if (changesMade) {
            if (confirm(gettext("You have changed the form. Do you want to save them before publishing?"))) {
                document.getElementsByName("publish")[0].setAttribute("value", "1");
                document.getElementById("xt-editor-form").submit();
            } else {
                post({command: "publish"});
            }
        } else {
            post({command: "publish"});
        }
    });
    $(".revert-btn").on("click", function() {
        if (!confirm(gettext("Are you sure you wish to revert all changes made since the last published version?"))) {
            return;
        }
        post({command: "revert"});
    });
    $("input, select, textarea").on("change,input", function() {
        if (this.id === "id_general-plugin") {
            return;
        }
        changesMade = true;
    });
    $("#id_general-plugin").on("change", function() {
        if (changesMade) {
            if (!confirm(gettext("Changing plugins will cause other changes made on this form to be lost."))) {
                return;
            }
        }
        post({command: "change_plugin", plugin: this.value});
    });
    $(".xtheme-model-choice-widget").each(function(element) {
        updateModelChoiceWidgetURL(element);
        element.addEventListener("change", function() {
            updateModelChoiceWidgetURL(document.getElementById(this.id));
        });
    });

    // when summernote changes, set the flag on
    jQuery(".summernote-editor").on("summernote.change", (we, contents, $editable) => {
        changesMade = true;
    });

    new Sortable(document.querySelector(".layout-rows"), {
        handle: ".layout-move-row-btn",
		forceFallback: true,
        onUpdate: function(evt) {
            post({command: "move_row_to_index", from_y: evt.oldIndex, to_y: evt.newIndex});
        }
    });

    var els = document.getElementsByClassName("layout-row-cells");
    for(var i = 0; i < els.length; i++) {
        new Sortable(els[i], {
            group: 'cells',
            onUpdate: function(evt) {
                // cell re-arranged within the same row
                post({
                    command: "move_cell_to_position",
                    from_x: evt.item.dataset.x,
                    from_y: evt.item.dataset.y,
                    to_x: evt.newIndex,
                    to_y: evt.item.dataset.y
                });
            },
            onAdd: function(evt) {
                // cell moved to different row
                post({
                    command: "move_cell_to_position",
                    from_x: evt.item.dataset.x,
                    from_y: evt.item.dataset.y,
                    to_x: Array.prototype.indexOf.call(evt.item.parentNode.children, evt.item),
                    to_y: evt.item.parentNode.parentNode.dataset.y
                });
            }
        });
    }
});

window.refreshPlaceholderInParent = (placeholderName) => {
    window.parent.postMessage({"reloadPlaceholder": placeholderName}, "*");
};
