/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

require("@babel/polyfill");

import select2 from 'select2';

//-- jQuery
var jquery = require("jquery");
window.$ = window.jQuery = jquery;

import CodeMirror from "codemirror";

import "codemirror/mode/javascript/javascript";
import "codemirror/mode/css/css";
import "codemirror/mode/htmlmixed/htmlmixed";
import "codemirror/addon/edit/closebrackets";
import "codemirror/addon/edit/closetag";
import "codemirror/addon/edit/matchbrackets";
import "codemirror/addon/edit/matchtags";

const _ = require('lodash');
window._ = _;

window.Dropzone = require('dropzone');
Dropzone.autoDiscover = false;

window.OrderCreator = require('../../modules/orders/static_src/create/index.js');

const m = require('mithril');
window.m = m;

select2($);

const Sortable = require('sortablejs');  // TODO: Deprecate and merge to html5sortable
window.Sortable = Sortable.default || Sortable;
window.html5sortable = require('html5sortable/dist/html5sortable.cjs');
window.ShuupCodeMirror = CodeMirror;

require('bootstrap');
require('../../node_modules/chart.js/dist/Chart.js');
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
