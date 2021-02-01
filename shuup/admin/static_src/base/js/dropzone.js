/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function activateDropzone($dropzone, attrs={}) {
    if(!$dropzone.length) {
        console.error("Error! [dropzone.js] Unable to find requested element ", $dropzone);
        return;
    }

    const selector = "#" + $dropzone.attr("id");
    const $data = $(selector).data();
    const uploadPath = $data.upload_path || attrs.uploadPath;
    const addRemoveLinks = $data.add_remove_links;
    const uploadUrl = (
        $data.upload_url ||
        window.ShuupAdminConfig.browserUrls.media ||
        window.ShuupAdminConfig.browserUrls.upload
    );
    const browsable = (window.ShuupAdminConfig.browserUrls["media"] && $data.browsable && $data.browsable !== "False");

    // Load attributes encoded in attributes with `data-dz-` prefixes
    // e.g.: data-dz-maxFilesize="10000"
    const extraAttrs = {};
    Object.keys($data).filter(attr => attr.startsWith("dz_")).forEach((attr) => {
        const attrKey = attr.replace("dz_", "");
        extraAttrs[attrKey] = $data[attr];
    });

    const params = Object.assign({
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
        maxFiles: 1,
        dictDefaultMessage: gettext("Drop files here or click to browse."),
        clickable: false,
        accept: function(file, done) {
            if ($data.kind === "images" && file.type.indexOf("image") < 0) {
                done(gettext("only images can be uploaded!"));
            } else {
                done();
            }
        }
    }, extraAttrs, attrs);
    const dropzone = new Dropzone(selector, params);

    dropzone.on("addedfile", attrs.onAddedFile || function(file) {
        if(params.maxFiles === 1 && dropzone.files.length > 1) {
            dropzone.removeFile(dropzone.files[0]);
        }
    });

    dropzone.on("removedfile", attrs.onRemovedFile || function(data){
        $(selector).find("input").val("");
    });

    dropzone.on("success", attrs.onSuccess || function(data){
        // file selected through dnd
        if(data.xhr) {
            data = JSON.parse(data.xhr.responseText).file;
        }
        $(selector).find("input").val(data.id);
    });

    dropzone.on("error", attrs.onError|| function(data){
        let errorMessage = gettext("Error happened while uploading file.")
        if(data.xhr) {
            response = JSON.parse(data.xhr.responseText)
            if (response.error && response.error.file) {
                errorMessage = JSON.parse(data.xhr.responseText).error.file
            }
        }

        window.Messages.enqueue({ tags: "error", text: errorMessage});
        dropzone.removeFile(data);
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

    const data = $(selector).data();
    if(data.url) {
        dropzone.files.push(data);
        dropzone.emit("addedfile", data);
        if(data.thumbnail){
            dropzone.emit("thumbnail", data, data.thumbnail);
        }
        dropzone.emit("complete", data);
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
window.activateDropzone = activateDropzone;

$(function(){
    window.activateDropzones();
});

module.exports = { activateDropzone }
