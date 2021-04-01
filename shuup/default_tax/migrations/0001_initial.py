# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxRule',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(verbose_name='enabled', db_index=True, default=True)),
                ('country_codes_pattern', models.CharField(verbose_name='country codes pattern', max_length=300, blank=True)),
                ('region_codes_pattern', models.CharField(verbose_name='region codes pattern', max_length=500, blank=True)),
                ('postal_codes_pattern', models.CharField(verbose_name='postal codes pattern', max_length=500, blank=True)),
                ('_postal_codes_min', models.CharField(max_length=100, blank=True, null=True)),
                ('_postal_codes_max', models.CharField(max_length=100, blank=True, null=True)),
                ('priority', models.IntegerField(default=0, help_text='Rules with same priority define added taxes (e.g. US taxes) and rules with different priority define compound taxes (e.g. Canada Quebec PST case)', verbose_name='priority')),
                ('override_group', models.IntegerField(default=0, help_text='If several rules match, only the rules with the highest override group number will be effective.  This can be used, for example, to implement tax exemption by adding a rule with very high override group that sets a zero tax.', verbose_name='override group number')),
                ('customer_tax_groups', models.ManyToManyField(blank=True, verbose_name='customer tax groups', to='shuup.CustomerTaxGroup')),
                ('tax', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shuup.Tax', verbose_name='tax')),
                ('tax_classes', models.ManyToManyField(verbose_name='tax classes', help_text='Tax classes of the items to be taxed', to='shuup.TaxClass')),
            ],
        ),
    ]
