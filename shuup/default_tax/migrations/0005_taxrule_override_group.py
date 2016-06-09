# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0004_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxrule',
            name='override_group',
            field=models.IntegerField(help_text='If several rules match, only the rules with the highest override group number will be effective.  This can be used, for example, to implement tax exemption by adding a rule with very high priority that sets a zero tax.', verbose_name='override group number', default=0),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='region_codes_pattern',
            field=models.CharField(max_length=500, blank=True, verbose_name='Region codes pattern'),
        ),
    ]
