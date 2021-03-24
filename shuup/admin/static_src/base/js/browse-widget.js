/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/**
 * Support for media browsing widgets.
 * Currently opens a real, actual, true-to-1998
 * popup window (just like the Django admin, mind)
 * but could just as well use an <iframe> modal.
 */

window.BrowseAPI = (function() {
    const browseData = {};

    window.addEventListener("message", function (event) {
        const data = event.data;
        if (!data.pick) {
            return;
        }
        const info = browseData[data.pick.id];
        if (!info) {
            return;
        }
        info.popup.close();
        const obj = data.pick.object;
        if (!obj) {
            return;
        }
        if (_.isFunction(info.onSelect)) {
            info.onSelect.call(this, obj);
        }
        delete browseData[data.pick.id];
    }, false);

    /**
     * Open a browsing window with the given options.
     *
     * Currently supported options are:
     * * `kind`: kind string (e.g. "product")
     * * `filter`: filter string (kind-dependent)
     * * `onSelect`: a function invoked when an object is selected
     * @return {Object}
     */
    function openBrowseWindow(options) {
        var filter = options.filter;
        const disabledMenus = options.disabledMenus;
        const kind = options.kind;
        const browserUrl = window.ShuupAdminConfig.browserUrls[kind];
        if (!browserUrl) {
            throw new Error(gettext("No browser URL for kind:") + " " + kind);
        }
        if(typeof filter !== "string") {
            filter = JSON.stringify(filter);
        }
        const id = "m-" + (+new Date);
        const qs = _.compact([
            "popup=1",
            "kind=" + kind,
            "pick=" + id,
            (filter ? "filter=" + filter : null),
            (disabledMenus ? "disabledMenus=" + disabledMenus.join(",") : null),
            (options.shop ? "shop=" + options.shop : null)
        ]).join("&");
        const popup = window.open(
            browserUrl + (browserUrl.indexOf("?") > -1 ? "&" : "?") + qs,
            "browser_popup_" + id,
            "resizable,menubar=no,location=no,scrollbars=yes"
        );
        return browseData[id] = _.extend(
            {popup, $container: null, onSelect: null},
            options
        );
    }

    return {
        openBrowseWindow
    };
}());

function init() {
  $(document).ready(function() {
    const $product = $(".browse-text");
    if (!$product.length) {
      return;
    }

    $product.each(function() {
      if ($(this).is(":hidden")) {
        $(this).siblings(".clear-btn").hide();
      }

      if ($(this).is(":visible")) {
        $(this).siblings(".browse-btn").hide();
        $(this).siblings(".clear-btn").show();
      }
    });
  });
}

$(function() {
    $(document).on("click", ".browse-widget .browse-btn", function() {
        const $container = $(this).closest(".browse-widget");
        if (!$container.length) {
            return;
        }
        const kind = $container.data("browse-kind");
        const filter = $container.data("filter");
        try {
            return window.BrowseAPI.openBrowseWindow({kind, filter, onSelect: (obj) => {
                $container.find("input").val(obj.id);
                $(this).hide();
                const $text = $container.find(".browse-text");
                $text.siblings('.clear-btn').show();
                $text.text(obj.text);
                $text.prop("href", obj.url || "#");
                $text.show();
            }});
        } catch(e) {
            console.error(e);
            return false;
        }
    });

    $(document).on("click", ".browse-widget .clear-btn", function() {
        const $container = $(this).closest(".browse-widget");
        const $browseBtn = $(this).siblings(".browse-btn");

        if (!$container.length) {
            return;
        }

        if ($browseBtn.is(':hidden')) {
          $browseBtn.show();
        }

        const emptyText = $container.data("empty-text") || "";
        $container.find("input").val("");
        const $text = $container.find(".browse-text");
        $text.text(emptyText);
        $text.prop("href", "#");
        $text.hide();
        $(this).hide();
    });

    $(document).on("click", ".browse-widget .browse-text", function(event) {
        const href = $(this).prop("href");
        if (/#$/.test(href)) {  // Looks empty, so prevent clicks
            event.preventDefault();
            return false;
        }
    });

    init();
});
