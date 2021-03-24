/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/**
 * Materialize a Mithril.js virtual tree into a DOM node.
 * @param mithrilElement The virtual tree's root (a retval of `m()`)
 * @returns {Node} The materialized root of the virtual tree
 */
window.materialize = function materialize(mithrilElement) {
    // Cache a document fragment for materialization
    const root = (window._materializeRoot || (window._materializeRoot = document.createDocumentFragment()));

    // Render something into that root
    m.render(root, mithrilElement, true);

    // Then return the first child
    return root.firstChild;
};
