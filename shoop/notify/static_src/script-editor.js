/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var style = require("style!css!autoprefixer!less!./script-editor.less");

var cx = require("classnames");

var settings = {};
var names = {};
var infos = {};
var controller = null;
var optionLists = {};

function showSuccessAndError(data) {
    if (data.error) Messages.enqueue({
        text: _.isString(data.error) ? data.error : "An error occurred.",
        tags: "error"
    });
    if (data.success) Messages.enqueue({
        text: _.isString(data.success) ? data.success : "Success.",
        tags: "success"
    });
}

function apiRequest(command, data, options) {
    var request = _.extend({}, {"command": command}, data || {});
    var req = m.request(_.extend({
        method: "POST",
        url: settings.apiUrl,
        data: request,
        config: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
        }
    }, options));
    req.then(function(data) {
        showSuccessAndError(data);
    }, function() {
        Messages.enqueue({text: "An unspecified error occurred.", tags: "error"});
    });
    return req;
}

function Controller() {
    var ctrl = this;
    ctrl.steps = m.prop([]);
    ctrl.currentItem = m.prop(null);
    ctrl.newStepItemModalInfo = m.prop(null);

    apiRequest("getData").then(function(data) {
        ctrl.steps(data.steps);
    });

    ctrl.removeStepItem = function(step, itemType, item) {
        var listName = itemType + "s";
        step[listName] = _.reject(step[listName], function(i) {
            return i === item;
        });
        if(ctrl.currentItem() === item) {
            ctrl.activateStepItem(null, null, null);
        }
    };

    ctrl.addStepItem = function(step, itemType, identifier, activateForEdit) {
        var item = {"identifier": identifier};
        var listName = itemType + "s";
        step[listName].push(item);
        if (activateForEdit) ctrl.activateStepItem(step, itemType, item);
    };
    ctrl.setStepItemEditorState = function(state) {
        if(!!state) {
            document.getElementById("step-item-wrapper").style.display = "block";
        } else {
            document.getElementById("step-item-wrapper").style.display = "none";
            document.getElementById("step-item-frame").src = "about:blank";
        }
    };
    ctrl.activateStepItem = function(step, itemType, item) {
        if (step && item) {
            ctrl.currentItem(item);
            var frm = _.extend(document.createElement("form"), {
                target: "step-item-frame",
                method: "POST",
                action: settings.itemEditorUrl
            });
            frm.appendChild(_.extend(document.createElement("input"), {
                name: "init_data",
                type: "hidden",
                value: JSON.stringify({
                    eventIdentifier: settings.eventIdentifier,
                    itemType: itemType,
                    data: item
                })
            }));
            document.body.appendChild(frm);
            frm.submit();
            ctrl.setStepItemEditorState(true);
        } else {
            ctrl.currentItem(null);
            ctrl.setStepItemEditorState(false);
        }
    };
    ctrl.receiveItemEditData = function(data) {
        var currentItem = ctrl.currentItem();
        if(!currentItem) {
            alert("Unexpected edit data received.");
            return;
        }
        m.startComputation();
        ctrl.currentItem(_.extend(currentItem, data));
        m.endComputation();
    };
    ctrl.saveState = function() {
        apiRequest("saveData", {
            steps: ctrl.steps()
        }).then(function(data) {

        });
    };
    ctrl.deleteStep = function(step) {
        ctrl.steps(_.reject(ctrl.steps(), function(s) {
            return s === step;
        }));
    };
    ctrl.addNewStep = function() {
        var step = {
            actions: [],
            conditions: [],
            enabled: true,
            next: "continue",
            condOp: "and"
        };
        var steps = ctrl.steps();
        steps.push(step);
        ctrl.steps(steps);
    };
    ctrl.moveStep = function(step, delta) {
        var steps = ctrl.steps();
        var oldIndex = _.indexOf(steps, step);
        if (oldIndex === -1) return false;
        var newIndex = oldIndex + delta;
        steps.splice(newIndex, 0, steps.splice(oldIndex, 1)[0]);
        ctrl.steps(steps);
    };
    ctrl.promptForNewStepItem = function(step, itemType) {
        ctrl.newStepItemModalInfo({
            step: step,
            itemType: itemType,
            title: "Add new " + itemType
        });
    };
    ctrl.closeNewStepItemModal = function() {
        ctrl.newStepItemModalInfo(null);
    };
    ctrl.createNewStepItemFromModal = function(identifier) {
        var info = ctrl.newStepItemModalInfo();
        ctrl.closeNewStepItemModal();
        if (info === null) return;
        ctrl.addStepItem(info.step, info.itemType, identifier, true);
    };
}

function workflowItemList(ctrl, step, itemType) {
    var listName = itemType + "s";
    var nameMap = names[itemType];
    var items = step[listName];
    var list = m("ul.action-list", items.map(function(item) {
        var name = nameMap[item.identifier] || item.identifier;
        var tag = "li";
        var current = (ctrl.currentItem() === item);
        if(current) tag += ".current";
        return m(tag,
            [
                m("a", {
                    href: "#",
                    onclick: (!current ? _.partial(ctrl.activateStepItem, step, itemType, item) : null)
                }, name),
                " ",
                m("a.delete", {
                    href: "#", onclick: function() {
                        if (!confirm("Delete this item?\nThis can not be undone.")) return;
                        ctrl.removeStepItem(step, itemType, item);
                    }
                }, m("i.fa.fa-trash"))
            ]
        );
    }));
    return m("div", [
        list,
        m("div.action-new", [m("a.btn.btn-xs.btn-primary", {
            href: "#",
            onclick: _.partial(ctrl.promptForNewStepItem, step, itemType)
        }, m("i.fa.fa-plus"), " New " + itemType)])
    ]);
}

function stepTableRows(ctrl) {
    return _.map(ctrl.steps(), function(step, index) {
        var condOpSelect = m("select", {
            value: step.cond_op,
            onchange: m.withAttr("value", function(value) {
                step.cond_op = value;
            })
        }, optionLists.condOps);
        var stepNextSelect = m("select", {
            value: step.next,
            onchange: m.withAttr("value", function(value) {
                step.next = value;
            })
        }, optionLists.stepNexts);

        return m("div", {
            className: cx("step", {disabled: !step.enabled}),
            key: step.id
        }, [
            m("div.step-buttons", [
                (index > 0 ? m("a", {
                    href: "#",
                    title: "Move Up",
                    onclick: _.partial(ctrl.moveStep, step, -1)
                }, m("i.fa.fa-caret-up")) : null),
                (index < ctrl.steps().length - 1 ? m("a", {
                    href: "#",
                    title: "Move Down",
                    onclick: _.partial(ctrl.moveStep, step, +1)
                }, m("i.fa.fa-caret-down")) : null),
                (step.enabled ?
                    m("a", {
                        href: "#", title: "Disable", onclick: function() {
                            step.enabled = false;
                        }
                    }, m("i.fa.fa-ban")) :
                    m("a", {
                        href: "#", title: "Enable", onclick: function() {
                            step.enabled = true;
                        }
                    }, m("i.fa.fa-check-circle"))
                ),
                m("a", {
                    href: "#", title: "Delete", onclick: function() {
                        if (!confirm("Are you sure you wish to delete this step?")) return;
                        ctrl.deleteStep(step);
                    }
                }, m("i.fa.fa-trash"))
            ]),
            m("div.step-conds", [
                m("span.hint", "If ", condOpSelect, " of these conditions hold..."),
                workflowItemList(ctrl, step, "condition")
            ]),
            m("div.step-actions", [
                m("span.hint", "then execute these actions..."),
                workflowItemList(ctrl, step, "action")
            ]),
            m("div.step-next", [
                m("span.hint", "and then..."),
                stepNextSelect
            ])
        ]);
    });
}

function renderNewStepItemModal(ctrl, modalInfo) {
    return m("div.new-step-item-modal-overlay", {onclick: ctrl.closeNewStepItemModal}, [
        m("div.new-step-item-modal", [
            m("div.title", modalInfo.title),
            m("div.item-options", _.map(_.sortBy(_.values(infos[modalInfo.itemType]), "name"), function(item) {
                return m("div.item-option", {onclick: _.partial(ctrl.createNewStepItemFromModal, item.identifier)}, [
                    m("div.item-name", item.name),
                    (item.description ? m("div.item-description", item.description) : null)
                ])
            }))
        ])
    ]);
}

function view(ctrl) {
    var modal = null, modalInfo = null;
    if ((modalInfo = ctrl.newStepItemModalInfo()) !== null) {
        modal = renderNewStepItemModal(ctrl, modalInfo);
    }
    return m("div.step-list-wrapper", [
        m("div.steps", [
            stepTableRows(ctrl),
            m("hr.script-separator"),
            m("a.new-step-link.btn.btn-info.btn-sm", {href: "#", onclick: ctrl.addNewStep}, m("i.fa.fa-plus"), " New step")
        ]),
        modal
    ]);
}

function generateItemOptions(nameMap) {
    return _.sortBy(_.map(nameMap, function(name, value) {
        return m("option", {value: value}, name);
    }), function(o) {
        return o.children[0].toLowerCase();
    });
}

function itemInfosToNameMap(infos) {
    return _(infos).map(function(info, identifier) {
        return [identifier, info.name]
    }).zipObject().value();
}


function init(iSettings) {
    settings = _.extend({}, iSettings);
    infos.condition = settings.conditionInfos;
    infos.action = settings.actionInfos;
    names.condition = itemInfosToNameMap(infos.condition);
    names.action = itemInfosToNameMap(infos.action);
    optionLists.condOps = generateItemOptions(settings.condOps);
    optionLists.stepNexts = generateItemOptions(settings.stepNexts);

    controller = m.mount(document.getElementById("step-table-container"), {
        controller: Controller,
        view: view
    });
    window.addEventListener("message", function(event) {
        if(event.data.new_data) controller.receiveItemEditData(event.data.new_data);
    }, false);
}

function save() {
    controller.saveState();
}

module.exports.init = init;
module.exports.save = save;
module.exports.hideEditModal = function() {
    if(controller) {
        m.startComputation();
        controller.setStepItemEditorState(false);
        controller.activateStepItem(null);  // Deactivate the modal once data is received
        m.endComputation();
    }
};
