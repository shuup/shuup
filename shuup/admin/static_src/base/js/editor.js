
/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

const getMediaButton = ($editor) => context => (
  $.summernote.ui.button({
    contents: $.summernote.ui.icon($.summernote.options.icons.picture),
    // tooltip: $.summernote.lang[$.summernote.options.lang].image.image, //Temporarily disabled
    click() {
            window.BrowseAPI.openBrowseWindow({
                kind: "media",
                clearable: true,
                onSelect: (obj) => {
                    $editor.summernote("insertImage", obj.url);
                }
            });
        }
    }).render()
);

function activateEditor($editor, attrs = {}) {
    function cancelEvent(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }

    const toolbar = [
      ["style", ["style", "bold", "italic", "underline", "clear"]],
      ["color", ["color"]],
      ["para", ["ul", "ol", "paragraph"]],
      ["table", ["table"]],
      ["insert", ["link", "media", "video", "codeview"]],
      [$.summernote.options.toolbar.filter((option => option[0] !== "insert")).concat([
        ["insert", ["link", "media", "video"]]
      ])],
    ];

    const $summernote = $editor.summernote($.extend(true, {
        height: 200,
        popatmouse: false,
        disableDragAndDrop: true,
        callbacks: {
            onBlur: function () {
                $editor.parent().find("textarea.hidden").val($(this).summernote("code"));
            },
            onPaste(event) {
                // prevent pasting files
                const clipboardData = event.originalEvent.clipboardData;
                if (clipboardData) {
                    for (let x = 0; x < clipboardData.items.length; x += 1) {
                        if (clipboardData.items[x].kind === "file") {
                            cancelEvent(event);
                            return;
                        }
                    }
                }
            }
        },
        toolbar: toolbar,
        buttons: {
            media: getMediaButton($editor)
        }
    }, attrs));

    // prevent drop events
    $editor.parent().find(".note-editable").off("drop");
    $editor.parent().find(".note-editable").on("drop", (event) => {
        cancelEvent(event);
    });

    $editor.parent().find(".note-codable").on("blur", function () {
        var textarea = $editor.parent().find("textarea");
        textarea.val($editor.summernote("code"));
    });
    return $summernote;
}

function activateEditors() {
    $(".summernote-editor").each(function (idx, object) {
        const $editor = $(object);
        if ($editor.parent().find(".note-editor").length === 0) {
            const textarea = $editor.parent().find("textarea");
            const params = textarea.data() || {};
            const attrs = {};
            const paramKeys = Object.keys(params);

            if (paramKeys.includes("height")) {
                attrs.height = params.height;
            }
            activateEditor($editor, attrs);
            if (paramKeys.includes("noresize")) {
                $editor.parent().find(".note-statusbar").hide();
            }
        }
    });
}

activateEditors();
