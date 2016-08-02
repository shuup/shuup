/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
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
        const changeIdentifier = m.withAttr("value", (value) => {
            object.identifier = value; refreshField();
        });
        const changeXlate = (code, value) => {
            object[langKey][code] = value; refreshField();
        };
        return [
            _.map(languages, ({name, code}) => {
                const changeXlateP = m.withAttr("value", _.partial(changeXlate, code));
                const label = langLabelFormat.replace("$", name);
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
                gettext("Identifier"),
                m("input.form-control", {
                    value: object.identifier,
                    placeholder: gettext("Identifier"),
                    oninput: changeIdentifier,
                    onchange: changeIdentifier
                })
            ]) : null),
        ];
    }

    function valueTr(ctrl, value, index) {
        const showIdentifierFields = ctrl.showIdentifierFields();
        return m("tr",
            m("th", interpolate(gettext("Value %s Name"), [(index + 1)])),
            getIdfrAndLanguagesCells("td", value, "texts", "", showIdentifierFields),
            m("td", m("a.btn.text-danger.btn-xs", {href: "#", onclick: () => {
                value.DELETE = true;
                refreshField();
            }}, m("i.fa.fa-times-circle"), " " + gettext("Delete value")))
        );
    }

    function renderVariable(ctrl, variable) {
        const showIdentifierFields = ctrl.showIdentifierFields();
        const deleteVariableButton = m("a.btn.btn-xs.text-danger", {href: "#", onclick: () => {
            if (variable.values.length === 0 || confirm(gettext("Are you sure?"))) {
                variable.DELETE = true;
                refreshField();
            }
        }}, m("i.fa.fa-times-circle"), " " + gettext("Delete Variable"));
        const addValueButton = m("a.btn.btn-xs.btn-text", {href: "#", onclick: (event) => {
            variable.values.push({pk: newPk(), identifier: "", texts: {}});
            event.preventDefault();
        }}, m("i.fa.fa-plus"), " " + gettext("Add new value"));
        var bodyRows = [];
        bodyRows.push(
            m("tr", [m("th", gettext("Variable Name"))].concat(
                getIdfrAndLanguagesCells("td", variable, "names", "", showIdentifierFields)
            ).concat([m("td")]))
        );
        bodyRows = bodyRows.concat(
            _.map(_.reject(variable.values, "DELETE"), _.partial(valueTr, ctrl))
        );
        return m("div.product-variable", {key: variable.pk}, [
            m("div.variable-heading.clearfix", [
                m("h3.pull-left", gettext("Variable")),
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
                " " + gettext("Show identifier fields (for advanced users)")
            ])
        ]);
        if (!variables.length) {
            variablesDiv = m("p.text-info", [
                m("i.fa.fa-exclamation-circle"), " " + gettext("There are no variables defined."),
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
            }}, m("i.fa.fa-plus"), " " + gettext("Add new variable"))
        ]);
    }

    function init(options) {
        if (ctrlSingleton) {
            return;
        }
        languages = options.languages;
        variables = options.variables;
        window.VariationVariableEditor.ctrl = ctrlSingleton = m.mount(
            document.getElementById("variation-variable-editor"),
            {controller: controller, view: view}
        );
    }
    return {init: init};
}(window.m, window._));

