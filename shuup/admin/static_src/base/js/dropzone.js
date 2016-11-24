/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function activateDropzone($dropzone) {
    const selector = "#" + $dropzone.attr("id");
    const uploadPath = $(selector).data().upload_path;
    const dropzone = new Dropzone(selector, {
        url: "/sa/media/?action=upload&path=" + uploadPath,
        params: {
            csrfmiddlewaretoken: window.ShuupAdminConfig.csrf
        },
        autoProcessQueue: true,
        uploadMultiple: false,
        parallelUploads: 1,
        maxFiles: 1,
        dictDefaultMessage: gettext("Drop files here or click to browse."),
        clickable: false
    });

    dropzone.on("addedfile", function(file) {
        if(dropzone.files.length > 1) {
            dropzone.removeFile(dropzone.files[0]);
        }
    });

    dropzone.on("success", function(data){
        let response = JSON.parse(data.xhr.responseText);
        $(selector).find("input").val(response.file.id);
        $(selector).addClass("has-file");
    });

    $(selector).on("click", function(e) {
        window.BrowseAPI.openBrowseWindow({kind: "media", filter: $(selector).data().kind, onSelect: (obj) => {
            obj.name = obj.text;
            let ext = obj.name.split(".")
            $(selector).find("input").val(obj.id);
            $(selector).find(".dz-preview").remove();
            dropzone.emit("addedfile", obj);
            if(obj.thumbnail) {
                dropzone.emit("thumbnail", obj, obj.thumbnail);
            }
            dropzone.emit("complete", obj);
            $(selector).addClass("has-file");
        }});
    });

    const data = $(selector).data();
    if(data.url) {
        dropzone.emit("addedfile", data);
        if(data.thumbnail){
            dropzone.emit("thumbnail", data, data.thumbnail);
        }
        dropzone.emit("complete", data);
    }
}

function activateDropzones() {
    $("div.dropzone").each(function(idx, object) {
        const dropzone = $(object);
        if(dropzone.find(".dz-message").length === 0) {
            activateDropzone(dropzone);
        }
    });
}

$(function(){
    Dropzone.autoDiscover = false;
    activateDropzones();
});
