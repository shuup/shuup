# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0006_taxrule_help_texts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='country_codes_pattern',
            field=models.CharField(verbose_name='country codes pattern', blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='customer_tax_groups',
            field=models.ManyToManyField(verbose_name='customer tax groups', blank=True, to='shoop.CustomerTaxGroup'),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='postal_codes_pattern',
            field=models.CharField(verbose_name='postal codes pattern', blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='region_codes_pattern',
            field=models.CharField(verbose_name='region codes pattern', blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='tax',
            field=models.ForeignKey(verbose_name='tax', to='shoop.Tax', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='tax_classes',
            field=models.ManyToManyField(verbose_name='tax classes', to='shoop.TaxClass', help_text='Tax classes of the items to be taxed'),
        ),
    ]
