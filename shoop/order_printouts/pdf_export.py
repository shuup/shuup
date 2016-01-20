# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from shoop.utils.excs import Problem

try:
    import weasyprint
except ImportError:
    weasyprint = None


def render_html_to_pdf(html):
    if not weasyprint:
        raise Problem(_("Could not create PDF since Weasyprint is not available. Please contact support."))
    pdf = weasyprint.HTML(string=html).write_pdf()
    return wrap_pdf_in_response(pdf)


def wrap_pdf_in_response(pdf_data):
    response = HttpResponse(content_type='application/pdf')
    response.write(pdf_data)
    return response
