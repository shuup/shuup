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
                    label,
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

    function valueTr(ctrl, value) {
        var showIdentifierFields = ctrl.showIdentifierFields();
        return m("tr",
            getIdfrAndLanguagesCells("td", value, "texts", "", showIdentifierFields),
            m("td", m("a", {href: "#", onclick: () => {
                value.DELETE = true;
                refreshField();
            }}, m("i.fa.fa-minus"), " Delete value"))
        );
    }

    function renderVariable(ctrl, variable) {
        var showIdentifierFields = ctrl.showIdentifierFields();
        var deleteVariableButton = m("a", {href: "#", onclick: () => {
            if(variable.values.length === 0 || confirm("Are you sure?")) {
                variable.DELETE = true;
                refreshField();
            }
        }}, m("i.fa.fa-minus"), " Delete variable");
        var addValueButton = m("a", {href: "#", onclick: (event) => {
            variable.values.push({pk: newPk(), identifier: "", texts: {}});
            event.preventDefault();
        }}, m("i.fa.fa-plus"), " Add new value");

        var infoDiv = m("div", [
            getIdfrAndLanguagesCells("div", variable, "names", "Variable Name ($)", showIdentifierFields),
            m("br"),
            deleteVariableButton
        ]);
        var valuesTable = m(
            "table.table.table-condensed.table-bordered",
            m("thead", m("tr", _.map(languages, ({name}) => m("th", "Value Text (" + name + ")")), m("td"))),
            m("tbody", _.map(_.reject(variable.values, "DELETE"), _.partial(valueTr, ctrl)))
        );
        var valuesDiv = m("div", [
            valuesTable,
            addValueButton
        ]);
        return m("div.variable", {key: variable.pk}, [
            m("div.row", [
                m("div.col-sm-4", infoDiv),
                m("div.col-sm-8", valuesDiv)
            ])
        ]);
    }

    function view(ctrl) {
        var variablesDiv = m(
            "div",
            _.map(_.reject(variables, "DELETE"), _.partial(renderVariable, ctrl))
        );
        var identifierFieldsCheckbox = m("label", [
            m("input", {
                type: "checkbox",
                checked: !!ctrl.showIdentifierFields(),
                onclick: m.withAttr("checked", ctrl.showIdentifierFields)
            }),
            " Show identifier fields (for advanced users)"
        ]);
        if(!variables.length) {
            variablesDiv = m("div.alert.alert-info", "There are no variables defined.");
            identifierFieldsCheckbox = null;
        }
        return m("div", [
            identifierFieldsCheckbox,
            variablesDiv,
            m("a", {href: "#", onclick: (event) => {
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

