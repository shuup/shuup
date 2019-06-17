/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function activateDropzone($dropzone, attrs={}) {
    if(!$dropzone.length) {
        console.error("[dropzone.js] Unable to find requested element ", $dropzone);
        return;
    }

    const selector = "#" + $dropzone.attr("id");
    const $data = $(selector).data();
    const uploadPath = attrs.uploadPath || $data.upload_path;
    const addRemoveLinks = $data.add_remove_links;
    const uploadUrl = $data.upload_url || window.ShuupAdminConfig.browserUrls.media;
    const browsable = ($data.browsable !== "False");
    const maxFiles = $data.maxFiles ? parseInt($data.maxFiles, 10) : 1;
    const params = $.extend(true, {
        url: uploadUrl + "?action=upload&path=" + uploadPath,
        uploadUrl,
        params: {
            csrfmiddlewaretoken: window.ShuupAdminConfig.csrf
        },
        addRemoveLinks: (addRemoveLinks === "True"),
        dictRemoveFile: gettext("Clear"),
        autoProcessQueue: true,
        uploadMultiple: false,
        parallelUploads: 1,
        maxFiles,
        dictDefaultMessage: gettext("Drop files here or click to browse."),
        clickable: false,
        accept: function(file, done) {
            if ($data.kind === "images" && file.type.indexOf("image") < 0) {
                done(gettext("only images can be uploaded!"));
            } else {
                done();
            }
        }
    }, attrs);
    const dropzone = new Dropzone(selector, params);

    dropzone.on("addedfile", attrs.onAddedFile || function(file) {
        if(params.maxFiles === 1 && dropzone.files.length > 1) {
            dropzone.removeFile(dropzone.files[0]);
        }
    });

    dropzone.on("removedfile", attrs.onSuccess || function(data){
        const $input = $(selector).find("input");
        if (maxFiles > 1) {
            const currentVal = String($input.val());
            const ids = currentVal.split(";");
            const removeId = String(data.id);
            const index = ids.indexOf(removeId);
            if (index >= 0) {
                ids.splice(index, 1);
            }
            $input.val(ids.filter(id => id).join(";"));
        } else {
            $input.val("");
        }
    });

    dropzone.on("success", attrs.onSuccess || function(data){
        // file selected through dnd
        if(data.xhr) {
            data = JSON.parse(data.xhr.responseText).file;
        }
        const $input = $(selector).find("input");
        if (maxFiles > 1) {
            const currentVal = String($input.val());
            const ids = currentVal.split(";");
            if (!ids.includes(String(data.id))) {
                ids.push(data.id);
            }
            $input.val(ids.filter(id => id).join(";"));
        } else {
            $input.val(data.id);
        }
    });

    dropzone.on("queuecomplete", attrs.onQueueComplete || $.noop);

    $(selector).on("click", function() {
        if (browsable) {
            window.BrowseAPI.openBrowseWindow({
                kind: "media",
                disabledMenus: ["delete", "rename"],
                filter: $(selector).data().kind,
                onSelect: (obj) => {
                    obj.name = obj.text;
                    $(selector).find("input").val(obj.id);
                    $(selector).find(".dz-preview").remove();
                    dropzone.emit("addedfile", obj);
                    if(obj.thumbnail) {
                        dropzone.emit("thumbnail", obj, obj.thumbnail);
                    }
                    dropzone.emit("success", obj);
                    dropzone.emit("complete", obj);
                }
            });
        } else {
            const fileInput = document.createElement("input");
            document.body.appendChild(fileInput);
            $(fileInput).prop("type", "file").css("display", "none").on("change", (evt) => {
                const file = evt.target.files[0];
                dropzone.addFile(file);
                fileInput.remove();
            }).trigger("click");
        }
    });

    const initialFilesCount = $data.initialFiles ? parseInt($data.initialFiles, 0) : 0;
    for (let index = 0; index <= initialFilesCount; index += 1) {
        const data = {
            url: $data["file" + index + "_url"],
            id: $data["file" + index + "_id"],
            name: $data["file" + index + "_name"],
            size: $data["file" + index + "_size"],
            thumbnail: $data["file" + index + "_thumbnail"],
            date: $data["file" + index + "_date"],
        };
        if(data.url) {
            dropzone.files.push(data);
            dropzone.emit("addedfile", data);
            if(data.thumbnail){
                dropzone.emit("thumbnail", data, data.thumbnail);
            }
            dropzone.emit("complete", data);
        }
    }
}

window.activateDropzones = function() {
    $("div[data-dropzone='true']").each(function(idx, object) {
        const dropzone = $(object);
        if(!dropzone.attr("id").includes("__prefix__") && dropzone.find(".dz-message").length === 0) {
            activateDropzone(dropzone);
        }
    });
};

$(function(){
    window.activateDropzones();
});

module.exports = { activateDropzone };
