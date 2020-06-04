# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shuup Inc. All rights reserved.
#
# This source code is licensed under the SHUUP® ENTERPRISE EDITION -
# END USER LICENSE AGREEMENT executed by Anders Innovations Inc. DBA as Shuup
# and the Licensee.
from django.core.management import BaseCommand
from shuup.core.models import Shop
from shuup.xtheme.models import Snippet, SnippetType


snippet_text = """\
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">\
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        shops = Shop.objects.all()
        for shop in shops:
            snippet = Snippet.objects.create(
                shop=shop,
                snippet_type=SnippetType.InlineHTMLMarkup,
                location="head_start",
                force_to_all_pages=True,
                snippet=snippet_text
            )
            snippet.save()
