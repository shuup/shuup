# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0005_taxrule_override_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='override_group',
            field=models.IntegerField(help_text='If several rules match, only the rules with the highest override group number will be effective.  This can be used, for example, to implement tax exemption by adding a rule with very high override group that sets a zero tax.', default=0, verbose_name='override group number'),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='priority',
            field=models.IntegerField(help_text='Rules with same priority define added taxes (e.g. US taxes) and rules with different priority define compound taxes (e.g. Canada Quebec PST case)', default=0, verbose_name='priority'),
        ),
    ]
