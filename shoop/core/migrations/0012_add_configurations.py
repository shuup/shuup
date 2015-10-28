# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0011_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=100, verbose_name='key')),
                ('value', jsonfield.fields.JSONField(verbose_name='value')),
                ('shop', models.ForeignKey(blank=True, null=True, related_name='+', to='shoop.Shop')),
            ],
            options={
                'verbose_name': 'configuration item',
                'verbose_name_plural': 'configuration items',
            },
        ),
        migrations.AlterUniqueTogether(
            name='configurationitem',
            unique_together=set([('shop', 'key')]),
        ),
    ]
