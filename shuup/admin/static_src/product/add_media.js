/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(document).on("click", "#product-section-dropzone", function(e) {
    return window.BrowseAPI.openBrowseWindow({
        kind: "media",
        clearable: true,
        onSelect: (obj) => {
            const productId = $("#product-section-dropzone").data().product_id;
            const kind = $("#product-section-dropzone").data().kind;
            if (!productId) {
                return;
            }
    
            var fileIds = getFileIds(kind);
            // Adds the files id
            fileIds.push(parseInt(obj.id))

            if (getFileCount(kind) === fileIds.length) {  // Skip add media if file count has not changed
                return;
            }
            $.ajax({
                url: window.ShuupAdminConfig.browserUrls.add_media.replace("/99999/", "/" + productId + "/"),
                method: "POST",
                data: {
                    csrfmiddlewaretoken: ShuupAdminConfig.csrf,
                    product_id: productId,
                    file_ids: fileIds,
                    kind
                },
                traditional: true,
                success: function(data) {
                    if (data.added) {
                        addMediaPanel($("#product-" + kind + "-section"), obj)
                        data.added.forEach((addedMedia) => {
                            const filePanel = $(".panel[data-file='" + addedMedia.file + "']");
                            const idx = parseInt(filePanel.data("idx"), 10) - 1;
                            $("#id_" + kind + "-" + idx + "-file").prop("value", addedMedia.file);
                            $("#id_" + kind + "-" + idx + "-id").prop("value", addedMedia.product_media);
                        });
                    }
                    window.Messages.enqueue({
                        tags: "success",
                        text: data.message
                    });
                },
                error: function(data) {
                    alert("Error!");
                }
            });

        }
    });
})
function getFileIds(kind) {
    const $fileInputs = $("#product-" + kind + "-section").find(".file-control input");
    var fileIds = [];
    for(var i = 0; i < $fileInputs.length; i++){
        let fileId = parseInt($($fileInputs[i]).val());
        if(!isNaN(fileId)) {
            fileIds.push(parseInt($($fileInputs[i]).val()));
        }
    }
    return fileIds
}

function getFileCount(kind) {
    return $("#product-" + kind + "-section").data("saved_file_count") || 0;
}

function addMediaPanel($section, file) {
    const section = $section.attr("id");
    const maxPanelId = $("#" + section + " .panel")
        .map((v, el) => $(el).data("idx")).toArray()
        .filter(value => value !== "__prefix_name__");
    const panelCount = maxPanelId.length ? Math.max(...maxPanelId) : 0;
    const $source = $("#" + section + "-placeholder-panel");

    let html = $source.html().replace(/__prefix__/g, panelCount).replace(/__prefix_name__/g, panelCount + 1);
    if (file) {
        html = html.replace(/__file_id__/g, file.id);
    }
    const $html = $(html);

    let targetId = "id_images";
    if (section.indexOf("media") > 0) {
        targetId = "id_media";
    }

    $("#" + targetId + "-TOTAL_FORMS").val($("#" + section + " .panel").length);
    $("#" + targetId + "-INITIAL_FORMS").val($("#" + section + " .panel").length);
    if (file) {
        let $contents = $("<a class='thumbnail-image' href='" + file.url + "' target='_blank'></a>");
        let $name = "<h4>" + file.name + "</h4>";
        if(targetId === "id_images") {
            $contents.append("<img src='" + file.thumbnail + "'>");
            $html.find(".thumbnail").append($contents);
        } else {
            $contents.append("<img src='" + file.url + "' />");
            $html.find(".extra-fields").prepend($name);
        }
        $html.find(".file-control").find("input").val(file.id);
    }
    $html.insertBefore($source);
}