# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ('default_tax', '0001_initial'),
        ('default_tax', '0002_postal_code_pattern_to_text'),
        ('default_tax', '0003_alter_names'),
    ]

    dependencies = [
        ('shuup', '0001_squashed_0039_alter_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxRule',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    verbose_name='ID',
                    serialize=False)),
                ('enabled', models.BooleanField(
                    default=True,
                    db_index=True,
                    help_text='Check this if this tax rule is active.',
                    verbose_name='enabled')),
                ('country_codes_pattern', models.CharField(
                    verbose_name='country codes pattern',
                    blank=True,
                    max_length=300)),
                ('region_codes_pattern', models.CharField(
                    verbose_name='region codes pattern',
                    blank=True,
                    max_length=500)),
                ('postal_codes_pattern', models.TextField(
                    verbose_name='postal codes pattern', blank=True)),
                ('_postal_codes_min', models.CharField(
                    null=True, blank=True, max_length=100)),
                ('_postal_codes_max', models.CharField(
                    null=True, blank=True, max_length=100)),
                ('priority', models.IntegerField(
                    default=0,
                    help_text=(
                        'Rules with same priority define added taxes '
                        '(e.g. US taxes) and rules with different priority '
                        'define compound taxes (e.g. Canada Quebec PST case)'),
                    verbose_name='priority')),
                ('override_group', models.IntegerField(
                    default=0,
                    help_text=(
                        'If several rules match, only the rules with the '
                        'highest override group number will be effective.  '
                        'This can be used, for example, to implement tax '
                        'exemption by adding a rule with very high override '
                        'group that sets a zero tax.'),
                    verbose_name='override group number')),
                ('customer_tax_groups', models.ManyToManyField(
                    to='shuup.CustomerTaxGroup',
                    help_text=(
                        'The customer tax groups for which this tax rule '
                        'is limited.'),
                    verbose_name='customer tax groups',
                    blank=True)),
                ('tax', models.ForeignKey(
                    verbose_name='tax',
                    on_delete=django.db.models.deletion.PROTECT,
                    help_text='The tax to apply when this rule is applied.',
                    to='shuup.Tax')),
                ('tax_classes', models.ManyToManyField(
                    to='shuup.TaxClass',
                    help_text='Tax classes of the items to be taxed',
                    verbose_name='tax classes')),
            ], ),
    ]
