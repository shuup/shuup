# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-09 21:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0045_disable_default_marketing_permission'),
        ('product_filter', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriesFilterModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, verbose_name='Enabled')),
                ('category', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='shuup.Category')),
                ('shop', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='shuup.Shop')),
            ],
            options={
                'verbose_name_plural': 'Filter categories settings',
                'verbose_name': 'Filter categories settings',
            },
        ),
        migrations.AlterModelOptions(
            name='basicfiltersettingsmodel',
            options={'verbose_name': 'Filter basic settings', 'verbose_name_plural': 'Filter basic settings'},
        ),
    ]
