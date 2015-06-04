/**
* This file is part of Shoop.
*
* Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
*
* This source code is licensed under the AGPLv3 license found in the
* LICENSE file in the root directory of this source tree.
 */
/**
 * Materialize a Mithril.js virtual tree into a DOM node.
 * @param mithrilElement The virtual tree's root (a retval of `m()`)
 * @returns {Node} The materialized root of the virtual tree
 */
function materialize(mithrilElement) {
    // Cache a document fragment for materialization
    var root = (window._materialize_root || (window._materialize_root = document.createDocumentFragment()));
    // Render something into that root
    m.render(root, mithrilElement, true);
    // Then return the first child
    return root.firstChild;
}
