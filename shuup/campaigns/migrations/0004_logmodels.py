# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shuup.utils.analog
from django.conf import settings
import django.db.models.deletion
import enumfields.fields
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('campaigns', '0003_category_products'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasketCampaignLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(verbose_name='message', max_length=256)),
                ('identifier', models.CharField(verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(verbose_name='log entry kind', default=0, enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(on_delete=models.CASCADE, related_name='log_entries', to='campaigns.BasketCampaign', verbose_name='target')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CatalogCampaignLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(verbose_name='message', max_length=256)),
                ('identifier', models.CharField(verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(verbose_name='log entry kind', default=0, enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(on_delete=models.CASCADE, related_name='log_entries', to='campaigns.CatalogCampaign', verbose_name='target')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CouponLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(verbose_name='message', max_length=256)),
                ('identifier', models.CharField(verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(verbose_name='log entry kind', default=0, enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(on_delete=models.CASCADE, related_name='log_entries', to='campaigns.Coupon', verbose_name='target')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CouponUsageLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(verbose_name='message', max_length=256)),
                ('identifier', models.CharField(verbose_name='identifier', blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(verbose_name='log entry kind', default=0, enum=shuup.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(verbose_name='extra data', null=True, blank=True)),
                ('target', models.ForeignKey(on_delete=models.CASCADE, related_name='log_entries', to='campaigns.CouponUsage', verbose_name='target')),
                ('user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, verbose_name='user', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
