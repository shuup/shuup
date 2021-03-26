/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

//-- jQuery
var jquery = require("jquery");
window.$ = window.jQuery = jquery;
const select2 = require("select2");
select2($);

const _ = require('lodash');
window._ = _;

const Sortable = require('sortablejs');
window.Sortable = Sortable.default || Sortable;

require('bootstrap');
require("summernote/dist/summernote.js");
require("../../../admin/static_src/base/js/browse-widget.js");
