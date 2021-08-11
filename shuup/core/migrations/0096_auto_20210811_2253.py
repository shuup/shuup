# Generated by Django 2.2.24 on 2021-08-11 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0095_reindex_catalog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttranslation',
            name='keywords',
            field=models.TextField(blank=True, help_text='You can enter keywords that describe your product. This will help your shoppers learn about your products. It will also help shoppers find them in the store and on the web. Enter the keywords as a comma separated list. EXAMPLE: cotton, wool, clothing', verbose_name='keywords'),
        ),
    ]
