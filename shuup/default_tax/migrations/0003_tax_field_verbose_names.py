# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0002_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='country_codes_pattern',
            field=models.CharField(blank=True, verbose_name='Country codes pattern', max_length=300),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='customer_tax_groups',
            field=models.ManyToManyField(blank=True, verbose_name='Customer tax groups', to='shuup.CustomerTaxGroup'),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='postal_codes_pattern',
            field=models.CharField(blank=True, verbose_name='Postal codes pattern', max_length=500),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='priority',
            field=models.IntegerField(verbose_name='priority', help_text='Rules with same priority are value-added (e.g. US taxes) and rules with different priority are compound taxes (e.g. Canada Quebec PST case)', default=0),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='region_codes_pattern',
            field=models.CharField(blank=True, verbose_name='Region codes pattern', help_text='Note: This is same as State codes for the US.', max_length=500),
        ),
        migrations.AlterField(
            model_name='taxrule',
            name='tax_classes',
            field=models.ManyToManyField(verbose_name='Tax classes', help_text='Tax classes of the items to be taxed', to='shuup.TaxClass'),
        ),
    ]
