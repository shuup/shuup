/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var FileUpload = require("./FileUpload");

var button = function(prop, value, label, title) {
    var active = (prop() == value);
    return m("button.btn.btn-default" + (active ? ".active" : ""), {
        type: "button",
        onclick: _.bind(prop, null, value),
        title: title
    }, label);
};

var fileLink = function(file) {
    var attrs = {};
    var pickMatch = /pick=([^&]+)/.exec(window.location.search);
    if (pickMatch) {
        attrs = {
            href: "#",
            onclick: function(event) {
                window.opener.postMessage({"pick": {"id": pickMatch[1], "file": file}}, "*");
                event.preventDefault();
            }
        };
    } else {
        attrs = {
            href: file.url,
            target: "_blank"
        };
    }
    return m("a", attrs, file.name);
};

var folderLink = function(ctrl, folder) {
    return m("a", {
        href: "#", onclick: function() {
            ctrl.setFolder(folder.id);
        }
    }, folder.name);
};

var findPathToFolder = function(rootFolder, folderId) {
    var pathToFolder = null;

    function walk(folder, folderPath) {
        if (folder.id == folderId) {
            pathToFolder = folderPath.concat([folder]);
            return;
        }
        folderPath = [].concat(folderPath).concat([folder]);
        _.each(folder.children, function(folder) {
            if (!pathToFolder) walk(folder, folderPath);
        });
    }

    walk(rootFolder, []);
    return pathToFolder || [];
};

var folderTree = function view(ctrl) {
    var currentFolderId = ctrl.currentFolderId();
    var folderPath = ctrl.currentFolderPath();
    var idsToCurrent = _.pluck(folderPath, "id");

    function clickFolder(event, folderId) {
        ctrl.setFolder(folderId);
        event.preventDefault();
        return false;
    }

    function walk(folder) {
        if (folder.id === undefined) return;
        var inPath = (idsToCurrent.indexOf(folder.id) > -1);
        var isCurrent = (currentFolderId == folder.id);
        var nameLink = m("a", {href: "#", onclick: _.partialRight(clickFolder, folder.id)}, [
            (inPath ? m("i.caret-icon.fa.fa-caret-down") : m("i.caret-icon.fa.fa-caret-right")),
            (isCurrent ? m("i.folder-icon.fa.fa-folder-open") : m("i.folder-icon.fa.fa-folder")),
            m("span.name", folder.name)
        ]);
        var childLis = (inPath ? _.map(folder.children, walk) : []);
        if (isCurrent) {
            childLis.push(m("li.new-folder-item", {key: "new-folder"}, m("a", {
                href: "#",
                onclick: _.bind(ctrl.promptCreateFolder, ctrl, folder.id),
            }, m("i.fa.fa-plus"), " New folder")));
        }
        var className = _({
            "current": isCurrent,
            "in-path": inPath,
            "has-children": (folder.children.length > 0),
        }).pick(_.identity).keys().join(" ");
        return m("li",
            {"key": folder.id, "className": className},
            [nameLink, (childLis && childLis.length ? m("ul", childLis) : null)]
        );
    }

    var rootLi = walk(ctrl.rootFolder());
    return m("ul", rootLi);
};

var gridFileView = function(ctrl, folders, files) {
    var folderItems = _.map(folders, function(folder) {
        return m("div.col-xs-6.col-md-4.col-lg-3.grid-folder", {key: "folder-" + folder.id}, [
            m("a.file-preview", {
                onclick: function() { ctrl.setFolder(folder.id); return false },
                href: "#",
            }, m("i.fa.fa-folder-open.folder-icon")),
            m("div.file-name", folderLink(ctrl, folder))
        ]);
    });
    var fileItems = _.map(files, function(file) {
        return m("div.col-xs-6.col-md-4.col-lg-3.grid-file", {key: file.id}, [
            m("a.file-preview", {
                href: file.url,
                target: "_blank",
            }, (file.thumbnail ? m("img.img-responsive", {src: file.thumbnail}) : null)),
            m("div.file-name", fileLink(file))
        ]);
    });
    return m("div.row", folderItems.concat(fileItems));
};

var listFileView = function(ctrl, folders, files) {
    var folderItems = _.map(folders, function(folder) {
        return m("tr", {key: "folder-" + folder.id}, [
            m("td", {colspan: 3}, [m("i.fa.fa-folder.folder-icon"), " ", folderLink(ctrl, folder)]),
        ]);
    });
    var fileItems = _.map(files, function(file) {
        return m("tr", {key: file.id}, [
            m("td", fileLink(file)),
            m("td.text-right", file.size),
            m("td.text-right", moment(file.date).format())
        ]);
    });
    return m("div.table-responsive", [
        m("table.table.table-condensed.table-striped.table-bordered", [
            m("thead", m("tr", _.map(["Name", "Size", "Date"], function(title) {
                return m("th", title);
            }))),
            m("tbody", folderItems.concat(fileItems))
        ])
    ]);
};

var emptyFolderView = function(ctrl, folder) {
    return m("div.empty-folder", [
        m("div.empty-image",
            m("img", {src: require("!url!./file-icons.svg")})
        ),
        m("div.empty-text", [
            m("div.visible-sm.visible-xs",
                m.trust("Click the <strong>Upload</strong> button to upload files.")
            ),
            m("div.visible-md.visible-lg" ,
                m.trust("<span>Drag and drop</span> files here<br> or click the <span>Upload</span> button.")
            )
        ])
    ]);
};

var folderView = function folderView(ctrl) {
    var folderData = ctrl.folderData();
    var viewModeGroup = m("div.btn-group.btn-group-sm.icons", [
        button(ctrl.viewMode, "grid", m("i.fa.fa-th"), "Grid"),
        button(ctrl.viewMode, "list", m("i.fa.fa-th-list"), "List")
    ]);
    var sortGroup = m("div.btn-group.btn-group-sm", [
        button(ctrl.sortMode, "+name", "A-Z"),
        button(ctrl.sortMode, "-name", "Z-A"),
        button(ctrl.sortMode, "+date", "Oldest first"),
        button(ctrl.sortMode, "-date", "Newest first"),
        button(ctrl.sortMode, "+size", "Smallest first"),
        button(ctrl.sortMode, "-size", "Largest first")
    ]);
    var toolbar = m("div.btn-toolbar", [viewModeGroup, sortGroup]);

    var sortSpec = /^([+-])(.+)$/.exec(ctrl.sortMode());
    var files = _.sortBy(folderData.files || [], sortSpec[2]);
    if (sortSpec[1] == "-") files = files.reverse();
    var folders = folderData.folders || [];
    var contents = null, uploadHint = null;
    if(folders.length == 0 && files.length == 0) {
        contents = emptyFolderView(ctrl, folderData);
        toolbar = null;
    } else {
        switch (ctrl.viewMode()) {
            case "grid":
                contents = gridFileView(ctrl, folders, files);
                break;
            case "list":
                contents = listFileView(ctrl, folders, files);
                break;
        }
        uploadHint = m("div.upload-hint",
            m("div.visible-sm.visible-xs",
                m.trust("Click the <strong>Upload</strong> button to upload files.")
            ),
            m("div.visible-md.visible-lg" ,
                m.trust("<strong>Drag and drop</strong> files here or click the <strong>Upload</strong> button.")
            )
        );
    }
    var container = m("div.folder-contents", {config: FileUpload.dropzoneConfig(ctrl)}, [
        contents,
        uploadHint,
        m("div.upload-indicator", [
            m("div.image",
                m("img", {src: require("!url!./file-icons.svg")})
            ),
            m("div.text", [
                m.trust("Drop your files here")
            ])
        ])
    ]);

    return m("div.folder-view", [toolbar, container]);
};

var folderBreadcrumbs = function(ctrl) {
    var items = [], folderPath = ctrl.currentFolderPath();
    _.each(folderPath, function(folder, index) {
        items.push(
            m("a.breadcrumb-link" + (index == folderPath.length - 1 ? ".current" : ""), {
                href: "#",
                key: folder.id,
                onclick: _.partial(ctrl.setFolder, folder.id)
            }, folder.name)
        );
        items.push(m("i.fa.fa-angle-right"));
    });
    items.pop(); // pop last chevron
    items.unshift(m("i.fa.fa-folder-open.folder-icon"));
    return items;
};

var view = function view(ctrl) {
    return m("div.container-fluid", [
        m("div.row", [
            m("div.col-md-3.page-inner-navigation.folder-tree", folderTree(ctrl)),
            m("div.col-md-9.page-content", m("div.content-block", [
                m("div.title", folderBreadcrumbs(ctrl)),
                m("div.content", folderView(ctrl))
            ]))
        ])
    ]);
};


var controller = function controller() {
    var ctrl = this;
    ctrl.currentFolderId = m.prop(0);
    ctrl.currentFolderPath = m.prop([]);
    ctrl.rootFolder = m.prop({});
    ctrl.folderData = m.prop({});
    ctrl.viewMode = m.prop("grid");
    ctrl.sortMode = m.prop("+name");

    ctrl.setFolder = function(newFolderId) {
        ctrl.currentFolderId(0 | newFolderId);
        ctrl.currentFolderPath(findPathToFolder(ctrl.rootFolder(), newFolderId));
        ctrl.reloadFolderContents();
        location.hash = "#!id=" + newFolderId;
    };
    ctrl.promptCreateFolder = function(parentFolderId) {
        var name;
        if ((name = prompt("New folder name?"))) {
            m.request({
                method: "POST",
                url: location.pathname,
                data: {
                    "action": "new_folder",
                    "parent": parentFolderId,
                    "name": name
                },
                config: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
                }
            }).then(function(response) {
                ctrl.reloadFolderTree();
            });
        }
    };
    ctrl.promptCreateFolderHere = function() {
        return ctrl.promptCreateFolder(ctrl.currentFolderId());
    };
    ctrl.reloadFolderTree = function() {
        m.request({
            method: "GET",
            url: location.pathname,
            data: {"action": "folders"}
        }).then(function(response) {
            ctrl.rootFolder(response.rootFolder);
            ctrl.setFolder(ctrl.currentFolderId()); // Force reloading current folder too
        });
    };
    ctrl.reloadFolderContents = function() {
        var id = 0 | ctrl.currentFolderId();
        m.request({
            method: "GET",
            url: location.pathname,
            data: {"action": "folder", "id": id}
        }).then(function(response) {
            ctrl.folderData(response.folder || {});
        });
    };

    ctrl.getUploadUrl = function() {
        var uploadUrl = window.location.pathname;
        var folderId = ctrl.currentFolderId();
        return uploadUrl + "?action=upload&folder_id=" + folderId;
    };
    ctrl.reloadFolderContentsSoon = _.debounce(ctrl.reloadFolderContents, 1000);
};


module.exports = {
    controller: controller,
    view: view
};
