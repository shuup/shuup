/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

const m = require('mithril');
window.m = m;

window.VariationVariableEditor = (function(m, _) {
    "use strict";
    var languages = null;
    var variables = null;
    var ctrlSingleton = null;

    /**
     * Adapted from https://www.npmjs.com/package/array.prototype.move
     */
    if(!Array.prototype.reindex) {
        Array.prototype.reindex = function (oldIndex, newIndex) {
            this.splice(newIndex, 0, this.splice(oldIndex, 1)[0]);
        };
    }

    function controller() {
        this.showIdentifierFields = m.prop(false);

    }

    function config(el) {
        variableSortableSetup();
        valueSortableSetup();
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
                m("input.form-control", {
                    value: object.identifier,
                    placeholder: gettext("Identifier"),
                    oninput: changeIdentifier,
                    onchange: changeIdentifier
                })
            ]) : null),
        ];
    }

    /**
     * Sets up Sortable on the variation variables
     */
    function variableSortableSetup() {
        const variableWrap = document.getElementById("product-variable-wrap");
        if (document.getElementsByClassName("variable-sort-handle").length > 0) {
            window.Sortable.create(variableWrap, {
              group: "variable-sort",
              handle: ".variable-sort-handle",
              onEnd: function (event) {
                  variables.reindex(event.oldIndex, event.newIndex);
                  refreshField();
              }
            });
        }
    }

    /**
     * Sets up Sortable on the variation values
     */
    function valueSortableSetup(index) {
        const valuesTables = document.getElementsByClassName('product-variable-values');
        var index = 0;
        [].forEach.call(valuesTables, function (el) {
            window.Sortable.create(el, {
                group: "value-sort-" + index,
                handle: ".value-sort-handle",
                onEnd: function (event) {
                    // The event.oldIndex is unreliable, it seems to be an
                    // issue with nested sortables. The oldIndex is the one
                    // from the parent sortable.
                    const itemId = event.item.getAttribute('data-id');
                    const newIndex = event.newIndex;
                    var currentVariable = null;
                    var currentValue = null;
                    for(var varIndex=0; varIndex < variables.length; varIndex++) {
                        currentVariable = variables[varIndex];
                        for(var valIndex=0; valIndex < currentVariable.values.length; valIndex++) {
                            currentValue = currentVariable.values[valIndex];
                            if(currentValue.pk == itemId) {
                                variables[varIndex].values.reindex(valIndex, newIndex);
                            }
                        }
                    }
                    refreshField();
                }
            });
            index = index + 1;
        });
    }

    /**
     *  Return the sorting handle component
     */
    function sortingHandle(className) {
        return m("i.fa.fa-bars." + className + ".pull-left", "");
    }

    function valueTr(ctrl, value, index) {
        const showIdentifierFields = ctrl.showIdentifierFields();
        const rowLabel = interpolate(gettext("Value %s Name"), [(index + 1)]);
        return m("tr", {'data-id': value.pk},
            m("th", [sortingHandle("value-sort-handle"), rowLabel]),
            getIdfrAndLanguagesCells("td", value, "texts", "", showIdentifierFields),
            m("td", m("a.btn.text-danger.btn-xs", {href: "#", onclick: () => {
                value.DELETE = true;
                refreshField();
                return false;
            }}, m("i.fa.fa-times-circle"), " " + gettext("Delete value")))
        );
    }

    function renderVariable(ctrl, variable) {
        const showIdentifierFields = ctrl.showIdentifierFields();
        const deleteVariableButton = m("a.btn.btn-xs.text-danger", {href: "#", onclick: () => {
            if (variable.values.length === 0 || confirm(gettext("Are you sure?"))) {
                variable.DELETE = true;
                refreshField();
                return false;
            }
        }}, m("i.fa.fa-times-circle"), " " + gettext("Delete Variable"));
        const addValueButton = m("a.btn.btn-xs.btn-text", {href: "#", onclick: (event) => {
            variable.values.push({pk: newPk(), identifier: "", texts: {}});
            event.preventDefault();
        }}, m("i.fa.fa-plus"), " " + gettext("Add new value"));
        const nameRow = m("tr", [m("th", gettext("Variable Name"))].concat(
                getIdfrAndLanguagesCells("td", variable, "names", "", showIdentifierFields)
            ).concat([m("td")])
        );
        const bodyRows = _.map(_.reject(variable.values, "DELETE"), _.partial(valueTr, ctrl));
        return m("div.product-variable", {key: variable.pk}, [
            m("div.variable-heading.clearfix", [
                sortingHandle("variable-sort-handle"),
                m("h3.pull-left", gettext("Variable")),
                m("div.pull-right", deleteVariableButton)
            ]),
            m("div.variable-body", [
                m("div.table-responsive", [
                    m("table.table.table-bordered", [
                        m("thead", [
                            m("tr", [m("th")].concat(
                                _.map(languages, ({name}) => m("th", name))
                            ).concat([
                                showIdentifierFields ? m("th", [
                                    gettext("Identifer")
                                ]) : null,
                                m("th")
                            ])),
                        ]),
                        m("tbody.product-variable-name", nameRow),
                        m("tbody.product-variable-values", bodyRows)
                    ])
                ]),
                m("div.new-row", addValueButton)
            ])
        ]);
    }

    function view(ctrl) {
        var variablesDiv = m(
            "div.product-variable-wrap", {id: "product-variable-wrap"},
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
        return m("div", {config: config}, [
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

