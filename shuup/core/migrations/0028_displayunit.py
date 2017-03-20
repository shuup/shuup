# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import parler.models
from django.db import migrations, models

import shuup.core.fields
import shuup.core.models._units


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0027_modify_shop_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='salesunittranslation',
            old_name='short_name',
            new_name='symbol',
        ),
        migrations.CreateModel(
            name='DisplayUnit',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False)),
                ('internal_unit', models.ForeignKey(
                    to='shuup.SalesUnit', related_name='display_units')),
                ('ratio', shuup.core.fields.QuantityField(
                    default=1, max_digits=36, decimal_places=9, validators=[
                        shuup.core.models._units.validate_positive_not_zero])),
                ('decimals', models.PositiveSmallIntegerField(default=0)),
                ('comparison_value', shuup.core.fields.QuantityField(
                    default=1, max_digits=36, decimal_places=9, validators=[
                        shuup.core.models._units.validate_positive_not_zero])),
                ('allow_bare_number', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'display units',
                'verbose_name': 'display unit',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DisplayUnitTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False)),
                ('language_code', models.CharField(max_length=15, db_index=True)),
                ('name', models.CharField(max_length=150)),
                ('symbol', models.CharField(max_length=50)),
                ('master', models.ForeignKey(
                    to='shuup.DisplayUnit', editable=False,
                    related_name='translations', null=True)),
            ],
            options={
                'db_table': 'shuup_displayunit_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
                'verbose_name': 'display unit Translation',
            },
        ),
        migrations.AlterUniqueTogether(
            name='displayunittranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AddField(
            model_name='shopproduct',
            name='display_unit',
            field=models.ForeignKey(
                to='shuup.DisplayUnit', blank=True, null=True),
        ),
    ]
