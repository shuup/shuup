/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

import { activateDropzone } from '../base/js/dropzone';

$(function() {
    $(".product-media-delete").on("click", function(e) {
        e.preventDefault();
        if (confirm(gettext("Are you sure you want to delete this media?")))
        {
            $(this).parents(".panel").fadeOut();
            $(this).next(".d-none").find("input").prop("checked", true);
        }
    });

    $(document).on("click", ".set-as-primary", function(e) {
        e.preventDefault();
        const $panel = $(this).parents(".panel");
        const prefix = $panel.data("prefix");

        const [, current] = prefix.split("-");

        const $imagePanels = $("#product-images-section .panel");

        $imagePanels.removeClass("panel-selected").addClass("panel-default");

        $(".is-primary-image").replaceWith(function() {
            return $("<a>", {"class": "set-as-primary btn btn-sm btn-inverse", "href": "#"}).text(gettext("Set as primary image"));
        });

        $imagePanels.each(function(i) {
            $("#id_images-" + i + "-is_primary").prop("checked", false);
        });

        $(this).replaceWith(function() {
            return $("<span>", {"class": "is-primary-image"}).text(gettext("Primary image"));
        });

        $panel.addClass("panel-selected");
        $("#id_images-" + current + "-is_primary").prop("checked", true);
    });

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
                $contents.append("<img src='" + file.url + "'>");
                $html.find(".thumbnail").append($contents);
            } else {
                $contents.append("<img src='" + file.url + "' />");
                $html.find(".extra-fields").prepend($name);
            }
            $html.find(".file-control").find("input").val(file.id);
        }
        $html.insertBefore($source);
    }

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

    function setFileCount(kind, count) {
        $("#product-" + kind + "-section").data("saved_file_count", count);
    }

    function onDropzoneQueueComplete(dropzone, kind) {
        if(location.pathname.indexOf("new") > 0) {
            // save product media the traditional way via the save button when creating a new product
            return;
        }
        const productId = $("#product-" + kind + "-section-dropzone").data().product_id;
        if (!productId) {
            return;
        }

        let fileIds = getFileIds(kind);
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

    function onDropzoneSuccess($section, file) {
        // file selected through dnd
        if(file.xhr) {
            file = JSON.parse(file.xhr.responseText).file;
        }
        addMediaPanel($section, file);
    }
    const dropzones = [
        {
            field: 'product-images-section',
            targetPath: "/products/images",
            maxFiles: 10,
            queueComplete: "images"
        },
        {
            field: 'product-media-section',
            targetPath: "/products/media",
            maxFiles: 10,
            queueComplete: "media"
        }
    ];
    dropzones.forEach(function(zoneData) {
        var fieldId = "#" + zoneData.field + "-dropzone";
        if ($(fieldId).length) {
            // Save file count so we can prevent saving product media
            // if file count has not changed
            setFileCount(zoneData.queueComplete, getFileIds(zoneData.queueComplete).length);
            activateDropzone($(fieldId), {
                uploadPath: zoneData.targetPath,
                maxFiles: zoneData.maxFiles,
                onSuccess: function(file) {
                    onDropzoneSuccess($("#" + zoneData.field), file);
                },
                onQueueComplete: function() {
                    onDropzoneQueueComplete(this, zoneData.queueComplete);
                }
            });
        }
    });
});
