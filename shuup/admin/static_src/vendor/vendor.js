/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

//-- jQuery
var jquery = require("jquery");
window.$ = window.jQuery = jquery;

const _ = require('lodash');
window._ = _;

window.Dropzone = require('dropzone');
Dropzone.autoDiscover = false;

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
require('select2');
require('popper.js');

require('summernote');
require('tether');
require('@chenfengyuan/datepicker');

window.Shepherd = require('tether-shepherd');

const m = require('mithril');
window.m = m;


