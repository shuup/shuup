/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import _ from "lodash";
import m from "mithril";
import * as BrowserView from "./BrowserView";
import * as dragDrop from "./util/dragDrop";
import * as FileUpload from "./FileUpload";
import * as menuManager from "./util/menuManager";
import * as remote from "./util/remote";

import folderContextMenu from "./menus/folderContextMenu";

window.m = m;

var controller = null;

class MediaBrowser {
  static init(config={}) {
      if (controller !== null) {
          return;
      }
      controller = m.mount(document.getElementById("BrowserView"), {
          view: BrowserView.view,
          controller: _.partial(BrowserView.controller, config)
      });
      controller.navigateByHash();
      controller.reloadFolderTree();

      dragDrop.disableIntraPageDragDrop();
  }

  static openFolderContextMenu(event) {
      const button = event.target;
      menuManager.open(button, folderContextMenu(controller));
  }

  static setupUploadButton(element) {
      const input = document.createElement("input");
      input.type = "file";
      input.multiple = true;
      input.style.display = "none";
      input.addEventListener("change", function(event) {
          FileUpload.enqueueMultiple(controller.getUploadUrl(), event.target.files);
          FileUpload.addQueueCompletionCallback(() => { controller.reloadFolderContentsSoon(); });
          FileUpload.processQueue();
      });
      document.body.appendChild(input);
      element.addEventListener("click", function(event) {
          input.click();
          event.preventDefault();
      }, false);
  }

  static setupCopyButton(element) {
    element.addEventListener("click", function(event) {
        remote.get({"action": "path", "id": controller.currentFolderId()}).then(function(response) {
            const path = response["folderPath"]
            var dummy = document.createElement("input");
            document.body.appendChild(dummy);
            dummy.setAttribute("id", "dummy_id");
            document.getElementById("dummy_id").value=path;
            dummy.select();
            document.execCommand("copy");
            document.body.removeChild(dummy);
            if (path === ""){
                alert("You are in the root folder")
            } else {
                alert(path + " was copied to your clipboard")
            }
        });
        event.preventDefault();
    }, false);
}

}

window.MediaBrowser = MediaBrowser;
