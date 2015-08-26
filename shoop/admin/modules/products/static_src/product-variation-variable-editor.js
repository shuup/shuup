/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.VariationVariableEditor = (function(m, _) {
    "use strict";
    var languages = null;
    var variables = null;
    var ctrlSingleton = null;

    function controller() {
        this.showIdentifierFields = m.prop(false);
    }

    function refreshField() {
        document.getElementById("id_variables-data").value = JSON.stringify(variables);
    }

    function newPk() {
        return "$" + Math.random();
    }

    function getIdfrAndLanguagesCells(cellSelector, object, langKey, langLabelFormat="$", showIdentifierFields=true) {
        var changeIdentifier = m.withAttr("value", (value) => { object.identifier = value; refreshField(); });
        var changeXlate = (code, value) => { object[langKey][code] = value; refreshField(); };
        return [
            _.map(languages, ({name, code}) => {
                var changeXlateP = m.withAttr("value", _.partial(changeXlate, code));
                var label = langLabelFormat.replace("$", name);
                return m(cellSelector, [
                    (label && label.length ? m("label", label) : null),
                    m("input.form-control", {
                        value: object[langKey][code] || "",
                        placeholder: label,
                        oninput: changeXlateP,
                        onchange: changeXlateP
                    })
                ]);
            }),
            (showIdentifierFields ? m(cellSelector, [
                "Identifier",
                m("input.form-control", {
                    value: object.identifier,
                    placeholder: "Identifier",
                    oninput: changeIdentifier,
                    onchange: changeIdentifier
                })
            ]) : null),
        ];
    }

    function valueTr(ctrl, value, index) {
        var showIdentifierFields = ctrl.showIdentifierFields();
        return m("tr",
            m("th", "Value " + (index + 1) + " Name"),
            getIdfrAndLanguagesCells("td", value, "texts", "", showIdentifierFields),
            m("td", m("a.btn.text-danger.btn-xs", {href: "#", onclick: () => {
                value.DELETE = true;
                refreshField();
            }}, m("i.fa.fa-times-circle"), " Delete value"))
        );
    }

    function renderVariable(ctrl, variable) {
        var showIdentifierFields = ctrl.showIdentifierFields();
        var deleteVariableButton = m("a.btn.btn-xs.text-danger", {href: "#", onclick: () => {
            if(variable.values.length === 0 || confirm("Are you sure?")) {
                variable.DELETE = true;
                refreshField();
            }
        }}, m("i.fa.fa-times-circle"), " Delete Variable");
        var addValueButton = m("a.btn.btn-xs.btn-text", {href: "#", onclick: (event) => {
            variable.values.push({pk: newPk(), identifier: "", texts: {}});
            event.preventDefault();
        }}, m("i.fa.fa-plus"), " Add new value");
        var bodyRows = [];
        bodyRows.push(
            m("tr", [m("th", "Variable Name")].concat(
                getIdfrAndLanguagesCells("td", variable, "names", "", showIdentifierFields)
            ).concat([m("td")]))
        );
        bodyRows = bodyRows.concat(
            _.map(_.reject(variable.values, "DELETE"), _.partial(valueTr, ctrl))
        );
        return m("div.product-variable", {key: variable.pk}, [
            m("div.variable-heading.clearfix", [
                m("h3.pull-left", "Variable"),
                m("div.pull-right", deleteVariableButton)
            ]),
            m("div.variable-body", [
                m("div.table-responsive", [
                    m("table.table.table-bordered", [
                        m("thead", [
                            m("tr", [m("th")].concat(
                                _.map(languages, ({name}) => m("th", name))
                            ).concat([m("th")])),
                        ]),
                        m("tbody", bodyRows)
                    ])
                ]),
                m("div.new-row", addValueButton)
            ])
        ]);
    }

    function view(ctrl) {
        var variablesDiv = m(
            "div.product-variable-wrap",
            _.map(_.reject(variables, "DELETE"), _.partial(renderVariable, ctrl))
        );
        var identifierFieldsCheckbox = m("p", [
            m("label.small", [
                m("input", {
                    type: "checkbox",
                    checked: !!ctrl.showIdentifierFields(),
                    onclick: m.withAttr("checked", ctrl.showIdentifierFields)
                }),
                " Show identifier fields (for advanced users)"
            ])
        ]);
        if(!variables.length) {
            variablesDiv = m("p.text-info", [
                m("i.fa.fa-exclamation-circle"), " There are no variables defined.",
                m("hr")
            ]);
            identifierFieldsCheckbox = null;
        }
        return m("div", [
            identifierFieldsCheckbox,
            m("hr"),
            variablesDiv,
            m("a.btn.btn-lg.btn-text", {href: "#", onclick: (event) => {
                variables.push({pk: newPk(), identifier: "", names: {}, values: []});
                event.preventDefault();
            }}, m("i.fa.fa-plus"), " Add new variable")
        ])
    }

    function init(options) {
        if(ctrlSingleton) {
            return;
        }
        languages = options.languages;
        variables = options.variables;
        var domNode = document.getElementById("variation-variable-editor");
        window.VariationVariableEditor.ctrl = ctrlSingleton = m.mount(domNode, {controller: controller, view: view});
    }
    return {init: init};
}(window.m, window._));

