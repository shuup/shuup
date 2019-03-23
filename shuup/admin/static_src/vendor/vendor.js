/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

require("@babel/polyfill");

import select2 from 'select2';

//-- jQuery
var jquery = require("jquery");
window.$ = window.jQuery = jquery;

const _ = require('lodash');
window._ = _;

window.Dropzone = require('dropzone');
Dropzone.autoDiscover = false;

window.OrderCreator = require('../../modules/orders/static_src/create/index.js');

const m = require('mithril');
window.m = m;

select2($);

window.Sortable = require('sortablejs');  // TODO: Deprecate and merge to html5sortable
window.html5sortable = require('html5sortable/dist/html5sortable.cjs');

require('bootstrap');
require('chart.js');
require('imagelightbox');
require('get-size');
require('desandro-matches-selector');
require('ev-emitter');
require('fizzy-ui-utils');
require('jquery.easing');
require('jquery.scrollbar');
require('moment');
require('outlayer');
require('summernote/dist/summernote-bs4.js');
require('jquery-datetimepicker');
require('bootstrap-colorpicker');
