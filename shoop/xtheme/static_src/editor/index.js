/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const domready = require("../lib/domready");
const qs = require("../lib/qs");
const el = require("../lib/el");
const $ = require("../lib/miniq");

function post(args) {
    if (window.CSRF_TOKEN) {
        args.csrfmiddlewaretoken = window.CSRF_TOKEN;
    }
    const inputs = Object.keys(args).
        map((key) => {
            const val = args[key];
            return val ? el("input", {type: "hidden", name: key, value: val}) : null;
        }
    );
    const form = el("form", {method: "POST", action: location.href}, inputs);
    document.body.appendChild(form);
    form.submit();
}

domready(() => {
    $(".layout-cell").on("click", function() {
        const {x, y} = this.dataset;
        const newQs = qs.mutate({x, y});
        location.href = "?" + newQs;
    });
    $(".layout-add-cell-btn").on("click", function() {
        const {y} = this.dataset;
        post({y, command: "add_cell"});
    });
    $(".layout-add-row-btn").on("click", function() {
        const {y} = this.dataset;
        post({y, command: "add_row"});
    });
    $(".layout-del-row-btn").on("click", function() {
        if(!confirm("Are you sure you wish to delete this row?")) {
            return;
        }
        const {y} = this.dataset;
        post({y, command: "del_row"});
    });
    $(".del-cell-btn").on("click", function() {
        if(!confirm("Are you sure you wish to delete this cell?")) {
            return;
        }
        const {x, y} = this.dataset;
        post({x, y, command: "del_cell"});
    });
    $(".publish-btn").on("click", function() {
        if(!confirm("Are you sure you wish to publish changes made to this view?")) {
            return;
        }
        post({command: "publish"});
    });
    $(".revert-btn").on("click", function() {
        if(!confirm("Are you sure you wish to revert all changes made since the last published version?")) {
            return;
        }
        post({command: "revert"});
    });
    var changesMade = false;
    $("input, select, textarea").on("change,input", function() {
        if(this.id === "id_general-plugin") {
            return;
        }
        changesMade = true;
    });
    $("#id_general-plugin").on("change", function() {
        if(changesMade) {
            if(!confirm("Changing plugins will cause other changes made on this form to be lost.")) {
                return;
            }
        }
        post({command: "change_plugin", plugin: this.value});
    });
});
