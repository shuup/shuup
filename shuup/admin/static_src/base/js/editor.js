
/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

const getMediaButton = ($editor) => context => {
    if (!window.ShuupAdminConfig.browserUrls["media"]) {
        return null;
    }

    return (
        $.summernote.ui.button({
            contents: "<i class=\"fa fa-file-image-o\"/>",
            tooltip: gettext("Browse media"),
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
};

function activateEditor($editor, attrs = {}, options = {}) {
    function cancelEvent(event) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }

    let fontMenu = ["font", ["fontname", "fontsize"]];
    if (options.allowFontFamilySelection === false) {
        fontMenu = ["font", ["fontsize"]];
    }

    const toolbar = [
      ["style", ["style", "clear"]],
      fontMenu,
      ["style2", ["bold", "italic", "underline", "strikethrough", "superscript", "subscript"]],
      ["color", ["forecolor", "backcolor"]],
      ["para", ["ul", "ol", "paragraph", "height"]],
      ["table", ["table"]],
      ["insert", ["link", "media", "picture", "video", "codeview"]],
      [$.summernote.options.toolbar.filter((option => option[0] !== "insert")).concat([
        ["insert", ["link", "media", "picture", "video"]]
      ])],
    ];

    const $summernote = $editor.summernote($.extend(true, {
        fontSizes: ["8", "9", "10", "11", "12", "14", "16", "18", "24", "36"],
        height: 200,
        popatmouse: false,
        disableDragAndDrop: true,
        callbacks: {
            onBlur: function () {
                $editor.parent().find("textarea.hidden").val($(this).summernote("code"));
            },
            onPaste(event) {
                const clipboardData = (event.originalEvent || event).clipboardData || window.clipboardData;

                if (clipboardData) {
                    const bufferText = clipboardData.getData("Text");

                    if (!bufferText && clipboardData.items.length) {
                        // prevent pasting files
                        for (let x = 0; x < clipboardData.items.length; x += 1) {
                            if (clipboardData.items[x].kind === "file") {
                                cancelEvent(event);
                                return;
                            }
                        }
                    }

                    if (options.plainTextOnPaste && bufferText) {
                        cancelEvent(event);
                        setTimeout(function () {
                            document.execCommand("insertText", false, bufferText);
                        }, 10);
                    }
                }
            },
            onImageUpload: function(image) {
                const maxUploadFileSize = attrs.maxUploadFileSize || 256;
                const imageSizeKb = image[0]['size'] / 1000;
                if (imageSizeKb > maxUploadFileSize){
                    alert(interpolate(
                        gettext("Error! For images greater than %s kb, use the media browser instead."),
                        [maxUploadFileSize]
                    ));
                } else {
                    const file = image[0];
                    const reader = new FileReader();
                    reader.onloadend = function() {
                        const image = $('<img>').attr('src',  reader.result);
                        $editor.summernote("insertNode", image[0]);
                    }
                    reader.readAsDataURL(file);
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

window.ShuupAdminEditors = {
    _instances: [],

    activateEditors: function(target, options = {}) {
        const that = this;

        $(target).each(function (idx, object) {
            const $editor = $(object);
            if ($editor.parent().find(".note-editor").length === 0) {
                const textarea = $editor.parent().find("textarea");
                const params = textarea.data() || {};
                const attrs = {};
                const paramKeys = Object.keys(params);

                if (paramKeys.includes("height")) {
                    attrs.height = params.height;
                }

                that._instances.push(activateEditor($editor, attrs, options));

                if (paramKeys.includes("noresize")) {
                    $editor.parent().find(".note-statusbar").hide();
                }
            }
        });
    },

    destroyEditors: function() {
        while (this._instances.length) {
            const $instance = this._instances.pop();
            $($instance).summernote("destroy");
        }
    }
};
