# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_first_and_last_names(apps, schema_editor):
    person_contact_cls = apps.get_model("shoop", "PersonContact")

    for person in person_contact_cls.objects.all():
        if person.first_name or person.last_name:
            continue  # Safety check
        names = person.name.rsplit(" ", 1)
        if len(names) < 2:
            person.first_name = person.name
            person.last_name = ""
        else:
            person.first_name = names[0]
            person.last_name = names[1]
        person.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0017_contact_group_price_display_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='personcontact',
            name='first_name',
            field=models.CharField(max_length=30, verbose_name='first name', blank=True),
        ),
        migrations.AddField(
            model_name='personcontact',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='last name', blank=True),
        ),
        migrations.RunPython(populate_first_and_last_names),
    ]
