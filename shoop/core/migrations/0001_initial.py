# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.utils.analog
import shoop.core.models._orders
import shoop.core.models._product_variation
import django_countries.fields
import mptt.fields
import shoop.core.models._suppliers
import shoop.core.pricing
import enumfields.fields
import filer.fields.file
import shoop.core.models._attributes
from django.conf import settings
import shoop.core.models._order_lines
import shoop.core.models._product_media
import shoop.core.taxing._line_tax
import timezone_field.fields
import shoop.core.models._products
import shoop.core.models._shops
import django.db.models.deletion
import jsonfield.fields
import filer.fields.image
import shoop.core.utils.name_mixin
import shoop.core.models._categories
import shoop.core.models._addresses
import shoop.core.models._contacts
import shoop.core.fields
import shoop.core.models._counters
import shoop.core.models._shipments
import shoop.core.modules.interface
from enumfields import Enum


class MethodStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = 'disabled'
        ENABLED = 'enabled'


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('filer', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('prefix', models.CharField(verbose_name='name prefix', blank=True, max_length=64)),
                ('name', models.CharField(verbose_name='name', max_length=255)),
                ('suffix', models.CharField(verbose_name='name suffix', blank=True, max_length=64)),
                ('name_ext', models.CharField(verbose_name='name extension', blank=True, max_length=255)),
                ('company_name', models.CharField(verbose_name='company name', blank=True, max_length=255)),
                ('vat_code', models.CharField(verbose_name='VAT code', blank=True, max_length=64)),
                ('phone', models.CharField(verbose_name='phone', blank=True, max_length=64)),
                ('email', models.EmailField(verbose_name='email', blank=True, max_length=128)),
                ('street', models.CharField(verbose_name='street', max_length=255)),
                ('street2', models.CharField(verbose_name='street (2)', blank=True, max_length=255)),
                ('street3', models.CharField(verbose_name='street (3)', blank=True, max_length=255)),
                ('postal_code', models.CharField(verbose_name='ZIP / Postal code', blank=True, max_length=64)),
                ('city', models.CharField(verbose_name='city', max_length=255)),
                ('region_code', models.CharField(verbose_name='region code', blank=True, max_length=16)),
                ('region', models.CharField(verbose_name='region', blank=True, max_length=64)),
                ('country', django_countries.fields.CountryField(verbose_name='country', max_length=2)),
                ('is_immutable', models.BooleanField(default=False, verbose_name='immutable', editable=False, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'addresses',
                'verbose_name': 'address',
            },
            bases=(shoop.core.utils.name_mixin.NameMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('searchable', models.BooleanField(default=True)),
                ('type', enumfields.fields.EnumIntegerField(default=20, enum=shoop.core.models._attributes.AttributeType)),
                ('visibility_mode', enumfields.fields.EnumIntegerField(default=1, enum=shoop.core.models._attributes.AttributeVisibility)),
            ],
            options={
                'verbose_name_plural': 'attributes',
                'verbose_name': 'attribute',
            },
        ),
        migrations.CreateModel(
            name='AttributeTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(max_length=64)),
                ('master', models.ForeignKey(to='shoop.Attribute', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'attribute Translation',
                'db_table': 'shoop_attribute_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('status', enumfields.fields.EnumIntegerField(default=0, verbose_name='status', enum=shoop.core.models._categories.CategoryStatus, db_index=True)),
                ('ordering', models.IntegerField(default=0, verbose_name='ordering')),
                ('visibility', enumfields.fields.EnumIntegerField(default=1, verbose_name='visibility limitations', enum=shoop.core.models._categories.CategoryVisibility, db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('image', filer.fields.image.FilerImageField(to='filer.Image', verbose_name='image', blank=True, null=True)),
                ('parent', mptt.fields.TreeForeignKey(to='shoop.Category', verbose_name='parent category', blank=True, related_name='children', null=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'verbose_name': 'category',
            },
        ),
        migrations.CreateModel(
            name='CategoryLogEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(max_length=256)),
                ('identifier', models.CharField(blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(default=0, enum=shoop.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True)),
                ('target', models.ForeignKey(to='shoop.Category', related_name='log_entries')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CategoryTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=128)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('slug', models.SlugField(verbose_name='slug', blank=True, null=True)),
                ('master', models.ForeignKey(to='shoop.Category', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'category Translation',
                'db_table': 'shoop_category_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('language', shoop.core.fields.LanguageField(verbose_name='language', blank=True, max_length=10, choices=[('aa', 'aa'), ('ab', 'ab'), ('ace', 'ace'), ('ach', 'ach'), ('ada', 'ada'), ('ady', 'ady'), ('ae', 'ae'), ('af', 'af'), ('afa', 'afa'), ('afh', 'afh'), ('agq', 'agq'), ('ain', 'ain'), ('ak', 'ak'), ('akk', 'akk'), ('ale', 'ale'), ('alg', 'alg'), ('alt', 'alt'), ('am', 'am'), ('an', 'an'), ('ang', 'ang'), ('anp', 'anp'), ('apa', 'apa'), ('ar', 'ar'), ('ar_001', 'ar_001'), ('arc', 'arc'), ('arn', 'arn'), ('arp', 'arp'), ('art', 'art'), ('arw', 'arw'), ('as', 'as'), ('asa', 'asa'), ('ast', 'ast'), ('ath', 'ath'), ('aus', 'aus'), ('av', 'av'), ('awa', 'awa'), ('ay', 'ay'), ('az', 'az'), ('ba', 'ba'), ('bad', 'bad'), ('bai', 'bai'), ('bal', 'bal'), ('ban', 'ban'), ('bas', 'bas'), ('bat', 'bat'), ('bax', 'bax'), ('bbj', 'bbj'), ('be', 'be'), ('bej', 'bej'), ('bem', 'bem'), ('ber', 'ber'), ('bez', 'bez'), ('bfd', 'bfd'), ('bg', 'bg'), ('bh', 'bh'), ('bho', 'bho'), ('bi', 'bi'), ('bik', 'bik'), ('bin', 'bin'), ('bkm', 'bkm'), ('bla', 'bla'), ('bm', 'bm'), ('bn', 'bn'), ('bnt', 'bnt'), ('bo', 'bo'), ('br', 'br'), ('bra', 'bra'), ('brx', 'brx'), ('bs', 'bs'), ('bss', 'bss'), ('btk', 'btk'), ('bua', 'bua'), ('bug', 'bug'), ('bum', 'bum'), ('byn', 'byn'), ('byv', 'byv'), ('ca', 'ca'), ('cad', 'cad'), ('cai', 'cai'), ('car', 'car'), ('cau', 'cau'), ('cay', 'cay'), ('cch', 'cch'), ('ce', 'ce'), ('ceb', 'ceb'), ('cel', 'cel'), ('cgg', 'cgg'), ('ch', 'ch'), ('chb', 'chb'), ('chg', 'chg'), ('chk', 'chk'), ('chm', 'chm'), ('chn', 'chn'), ('cho', 'cho'), ('chp', 'chp'), ('chr', 'chr'), ('chy', 'chy'), ('ckb', 'ckb'), ('cmc', 'cmc'), ('co', 'co'), ('cop', 'cop'), ('cpe', 'cpe'), ('cpf', 'cpf'), ('cpp', 'cpp'), ('cr', 'cr'), ('crh', 'crh'), ('crp', 'crp'), ('cs', 'cs'), ('csb', 'csb'), ('cu', 'cu'), ('cus', 'cus'), ('cv', 'cv'), ('cy', 'cy'), ('da', 'da'), ('dak', 'dak'), ('dar', 'dar'), ('dav', 'dav'), ('day', 'day'), ('de', 'de'), ('de_AT', 'de_AT'), ('de_CH', 'de_CH'), ('del', 'del'), ('den', 'den'), ('dgr', 'dgr'), ('din', 'din'), ('dje', 'dje'), ('doi', 'doi'), ('dra', 'dra'), ('dsb', 'dsb'), ('dua', 'dua'), ('dum', 'dum'), ('dv', 'dv'), ('dyo', 'dyo'), ('dyu', 'dyu'), ('dz', 'dz'), ('dzg', 'dzg'), ('ebu', 'ebu'), ('ee', 'ee'), ('efi', 'efi'), ('egy', 'egy'), ('eka', 'eka'), ('el', 'el'), ('elx', 'elx'), ('en', 'en'), ('en_AU', 'en_AU'), ('en_CA', 'en_CA'), ('en_GB', 'en_GB'), ('en_US', 'en_US'), ('enm', 'enm'), ('eo', 'eo'), ('es', 'es'), ('es_419', 'es_419'), ('es_ES', 'es_ES'), ('et', 'et'), ('eu', 'eu'), ('ewo', 'ewo'), ('fa', 'fa'), ('fan', 'fan'), ('fat', 'fat'), ('ff', 'ff'), ('fi', 'fi'), ('fil', 'fil'), ('fiu', 'fiu'), ('fj', 'fj'), ('fo', 'fo'), ('fon', 'fon'), ('fr', 'fr'), ('fr_CA', 'fr_CA'), ('fr_CH', 'fr_CH'), ('frm', 'frm'), ('fro', 'fro'), ('frr', 'frr'), ('frs', 'frs'), ('fur', 'fur'), ('fy', 'fy'), ('ga', 'ga'), ('gaa', 'gaa'), ('gay', 'gay'), ('gba', 'gba'), ('gd', 'gd'), ('gem', 'gem'), ('gez', 'gez'), ('gil', 'gil'), ('gl', 'gl'), ('gmh', 'gmh'), ('gn', 'gn'), ('goh', 'goh'), ('gon', 'gon'), ('gor', 'gor'), ('got', 'got'), ('grb', 'grb'), ('grc', 'grc'), ('gsw', 'gsw'), ('gu', 'gu'), ('guz', 'guz'), ('gv', 'gv'), ('gwi', 'gwi'), ('ha', 'ha'), ('hai', 'hai'), ('haw', 'haw'), ('he', 'he'), ('hi', 'hi'), ('hil', 'hil'), ('him', 'him'), ('hit', 'hit'), ('hmn', 'hmn'), ('ho', 'ho'), ('hr', 'hr'), ('hsb', 'hsb'), ('ht', 'ht'), ('hu', 'hu'), ('hup', 'hup'), ('hy', 'hy'), ('hz', 'hz'), ('ia', 'ia'), ('iba', 'iba'), ('ibb', 'ibb'), ('id', 'id'), ('ie', 'ie'), ('ig', 'ig'), ('ii', 'ii'), ('ijo', 'ijo'), ('ik', 'ik'), ('ilo', 'ilo'), ('inc', 'inc'), ('ine', 'ine'), ('inh', 'inh'), ('io', 'io'), ('ira', 'ira'), ('iro', 'iro'), ('is', 'is'), ('it', 'it'), ('iu', 'iu'), ('ja', 'ja'), ('jbo', 'jbo'), ('jgo', 'jgo'), ('jmc', 'jmc'), ('jpr', 'jpr'), ('jrb', 'jrb'), ('jv', 'jv'), ('ka', 'ka'), ('kaa', 'kaa'), ('kab', 'kab'), ('kac', 'kac'), ('kaj', 'kaj'), ('kam', 'kam'), ('kar', 'kar'), ('kaw', 'kaw'), ('kbd', 'kbd'), ('kbl', 'kbl'), ('kcg', 'kcg'), ('kde', 'kde'), ('kea', 'kea'), ('kfo', 'kfo'), ('kg', 'kg'), ('kha', 'kha'), ('khi', 'khi'), ('kho', 'kho'), ('khq', 'khq'), ('ki', 'ki'), ('kj', 'kj'), ('kk', 'kk'), ('kkj', 'kkj'), ('kl', 'kl'), ('kln', 'kln'), ('km', 'km'), ('kmb', 'kmb'), ('kn', 'kn'), ('ko', 'ko'), ('kok', 'kok'), ('kos', 'kos'), ('kpe', 'kpe'), ('kr', 'kr'), ('krc', 'krc'), ('krl', 'krl'), ('kro', 'kro'), ('kru', 'kru'), ('ks', 'ks'), ('ksb', 'ksb'), ('ksf', 'ksf'), ('ksh', 'ksh'), ('ku', 'ku'), ('kum', 'kum'), ('kut', 'kut'), ('kv', 'kv'), ('kw', 'kw'), ('ky', 'ky'), ('la', 'la'), ('lad', 'lad'), ('lag', 'lag'), ('lah', 'lah'), ('lam', 'lam'), ('lb', 'lb'), ('lez', 'lez'), ('lg', 'lg'), ('li', 'li'), ('lkt', 'lkt'), ('ln', 'ln'), ('lo', 'lo'), ('lol', 'lol'), ('loz', 'loz'), ('lt', 'lt'), ('lu', 'lu'), ('lua', 'lua'), ('lui', 'lui'), ('lun', 'lun'), ('luo', 'luo'), ('lus', 'lus'), ('luy', 'luy'), ('lv', 'lv'), ('mad', 'mad'), ('maf', 'maf'), ('mag', 'mag'), ('mai', 'mai'), ('mak', 'mak'), ('man', 'man'), ('map', 'map'), ('mas', 'mas'), ('mde', 'mde'), ('mdf', 'mdf'), ('mdr', 'mdr'), ('men', 'men'), ('mer', 'mer'), ('mfe', 'mfe'), ('mg', 'mg'), ('mga', 'mga'), ('mgh', 'mgh'), ('mgo', 'mgo'), ('mh', 'mh'), ('mi', 'mi'), ('mic', 'mic'), ('min', 'min'), ('mis', 'mis'), ('mk', 'mk'), ('mkh', 'mkh'), ('ml', 'ml'), ('mn', 'mn'), ('mnc', 'mnc'), ('mni', 'mni'), ('mno', 'mno'), ('mo', 'mo'), ('moh', 'moh'), ('mos', 'mos'), ('mr', 'mr'), ('ms', 'ms'), ('mt', 'mt'), ('mua', 'mua'), ('mul', 'mul'), ('mun', 'mun'), ('mus', 'mus'), ('mwl', 'mwl'), ('mwr', 'mwr'), ('my', 'my'), ('mye', 'mye'), ('myn', 'myn'), ('myv', 'myv'), ('na', 'na'), ('nah', 'nah'), ('nai', 'nai'), ('nap', 'nap'), ('naq', 'naq'), ('nb', 'nb'), ('nd', 'nd'), ('nds', 'nds'), ('ne', 'ne'), ('new', 'new'), ('ng', 'ng'), ('nia', 'nia'), ('nic', 'nic'), ('niu', 'niu'), ('nl', 'nl'), ('nl_BE', 'nl_BE'), ('nmg', 'nmg'), ('nn', 'nn'), ('nnh', 'nnh'), ('no', 'no'), ('nog', 'nog'), ('non', 'non'), ('nqo', 'nqo'), ('nr', 'nr'), ('nso', 'nso'), ('nub', 'nub'), ('nus', 'nus'), ('nv', 'nv'), ('nwc', 'nwc'), ('ny', 'ny'), ('nym', 'nym'), ('nyn', 'nyn'), ('nyo', 'nyo'), ('nzi', 'nzi'), ('oc', 'oc'), ('oj', 'oj'), ('om', 'om'), ('or', 'or'), ('os', 'os'), ('osa', 'osa'), ('ota', 'ota'), ('oto', 'oto'), ('pa', 'pa'), ('paa', 'paa'), ('pag', 'pag'), ('pal', 'pal'), ('pam', 'pam'), ('pap', 'pap'), ('pau', 'pau'), ('peo', 'peo'), ('phi', 'phi'), ('phn', 'phn'), ('pi', 'pi'), ('pl', 'pl'), ('pon', 'pon'), ('pra', 'pra'), ('pro', 'pro'), ('ps', 'ps'), ('pt', 'pt'), ('pt_BR', 'pt_BR'), ('pt_PT', 'pt_PT'), ('qu', 'qu'), ('raj', 'raj'), ('rap', 'rap'), ('rar', 'rar'), ('rm', 'rm'), ('rn', 'rn'), ('ro', 'ro'), ('roa', 'roa'), ('rof', 'rof'), ('rom', 'rom'), ('root', 'root'), ('ru', 'ru'), ('rup', 'rup'), ('rw', 'rw'), ('rwk', 'rwk'), ('sa', 'sa'), ('sad', 'sad'), ('sah', 'sah'), ('sai', 'sai'), ('sal', 'sal'), ('sam', 'sam'), ('saq', 'saq'), ('sas', 'sas'), ('sat', 'sat'), ('sba', 'sba'), ('sbp', 'sbp'), ('sc', 'sc'), ('scn', 'scn'), ('sco', 'sco'), ('sd', 'sd'), ('se', 'se'), ('see', 'see'), ('seh', 'seh'), ('sel', 'sel'), ('sem', 'sem'), ('ses', 'ses'), ('sg', 'sg'), ('sga', 'sga'), ('sgn', 'sgn'), ('sh', 'sh'), ('shi', 'shi'), ('shn', 'shn'), ('shu', 'shu'), ('si', 'si'), ('sid', 'sid'), ('sio', 'sio'), ('sit', 'sit'), ('sk', 'sk'), ('sl', 'sl'), ('sla', 'sla'), ('sm', 'sm'), ('sma', 'sma'), ('smi', 'smi'), ('smj', 'smj'), ('smn', 'smn'), ('sms', 'sms'), ('sn', 'sn'), ('snk', 'snk'), ('so', 'so'), ('sog', 'sog'), ('son', 'son'), ('sq', 'sq'), ('sr', 'sr'), ('srn', 'srn'), ('srr', 'srr'), ('ss', 'ss'), ('ssa', 'ssa'), ('ssy', 'ssy'), ('st', 'st'), ('su', 'su'), ('suk', 'suk'), ('sus', 'sus'), ('sux', 'sux'), ('sv', 'sv'), ('sw', 'sw'), ('swb', 'swb'), ('swc', 'swc'), ('syc', 'syc'), ('syr', 'syr'), ('ta', 'ta'), ('tai', 'tai'), ('te', 'te'), ('tem', 'tem'), ('teo', 'teo'), ('ter', 'ter'), ('tet', 'tet'), ('tg', 'tg'), ('th', 'th'), ('ti', 'ti'), ('tig', 'tig'), ('tiv', 'tiv'), ('tk', 'tk'), ('tkl', 'tkl'), ('tl', 'tl'), ('tlh', 'tlh'), ('tli', 'tli'), ('tmh', 'tmh'), ('tn', 'tn'), ('to', 'to'), ('tog', 'tog'), ('tpi', 'tpi'), ('tr', 'tr'), ('trv', 'trv'), ('ts', 'ts'), ('tsi', 'tsi'), ('tt', 'tt'), ('tum', 'tum'), ('tup', 'tup'), ('tut', 'tut'), ('tvl', 'tvl'), ('tw', 'tw'), ('twq', 'twq'), ('ty', 'ty'), ('tyv', 'tyv'), ('tzm', 'tzm'), ('udm', 'udm'), ('ug', 'ug'), ('uga', 'uga'), ('uk', 'uk'), ('umb', 'umb'), ('und', 'und'), ('ur', 'ur'), ('uz', 'uz'), ('vai', 'vai'), ('ve', 've'), ('vi', 'vi'), ('vo', 'vo'), ('vot', 'vot'), ('vun', 'vun'), ('wa', 'wa'), ('wae', 'wae'), ('wak', 'wak'), ('wal', 'wal'), ('war', 'war'), ('was', 'was'), ('wen', 'wen'), ('wo', 'wo'), ('xal', 'xal'), ('xh', 'xh'), ('xog', 'xog'), ('yao', 'yao'), ('yap', 'yap'), ('yav', 'yav'), ('ybb', 'ybb'), ('yi', 'yi'), ('yo', 'yo'), ('ypk', 'ypk'), ('yue', 'yue'), ('za', 'za'), ('zap', 'zap'), ('zbl', 'zbl'), ('zen', 'zen'), ('zh', 'zh'), ('zh_Hans', 'zh_Hans'), ('zh_Hant', 'zh_Hant'), ('znd', 'znd'), ('zu', 'zu'), ('zun', 'zun'), ('zxx', 'zxx'), ('zza', 'zza')])),
                ('marketing_permission', models.BooleanField(default=True, verbose_name='marketing permission')),
                ('phone', models.CharField(verbose_name='phone', blank=True, max_length=64)),
                ('www', models.URLField(verbose_name='web address', blank=True, max_length=128)),
                ('timezone', timezone_field.fields.TimeZoneField(blank=True, null=True)),
                ('prefix', models.CharField(verbose_name='name prefix', blank=True, max_length=64)),
                ('name', models.CharField(verbose_name='name', max_length=256)),
                ('suffix', models.CharField(verbose_name='name suffix', blank=True, max_length=64)),
                ('name_ext', models.CharField(verbose_name='name extension', blank=True, max_length=256)),
                ('email', models.EmailField(verbose_name='email', blank=True, max_length=256)),
            ],
            options={
                'verbose_name_plural': 'contacts',
                'verbose_name': 'contact',
            },
        ),
        migrations.CreateModel(
            name='ContactGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('show_pricing', models.BooleanField(default=True, verbose_name='show as pricing option')),
            ],
            options={
                'verbose_name_plural': 'contact groups',
                'verbose_name': 'contact group',
            },
        ),
        migrations.CreateModel(
            name='ContactGroupTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('master', models.ForeignKey(to='shoop.ContactGroup', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'contact group Translation',
                'db_table': 'shoop_contactgroup_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', enumfields.fields.EnumIntegerField(primary_key=True, enum=shoop.core.models._counters.CounterType, serialize=False)),
                ('value', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'counters',
                'verbose_name': 'counter',
            },
        ),
        migrations.CreateModel(
            name='CustomerTaxGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
            ],
            options={
                'verbose_name_plural': 'customer tax groups',
                'verbose_name': 'customer tax group',
            },
        ),
        migrations.CreateModel(
            name='CustomerTaxGroupTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('master', models.ForeignKey(to='shoop.CustomerTaxGroup', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'customer tax group Translation',
                'db_table': 'shoop_customertaxgroup_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='added')),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('name', models.CharField(verbose_name='name', max_length=128)),
                ('url', models.CharField(verbose_name='URL', blank=True, max_length=128, null=True)),
            ],
            options={
                'verbose_name_plural': 'manufacturers',
                'verbose_name': 'manufacturer',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='order identifier', blank=True, null=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, db_index=True)),
                ('label', models.CharField(verbose_name='label', max_length=32, db_index=True)),
                ('key', models.CharField(verbose_name='key', max_length=32, unique=True)),
                ('reference_number', models.CharField(verbose_name='reference number', blank=True, null=True, unique=True, max_length=64, db_index=True)),
                ('vat_code', models.CharField(verbose_name='VAT code', blank=True, max_length=20)),
                ('phone', models.CharField(verbose_name='phone', blank=True, max_length=32)),
                ('email', models.EmailField(verbose_name='email address', blank=True, max_length=128)),
                ('deleted', models.BooleanField(default=False, db_index=True)),
                ('payment_status', enumfields.fields.EnumIntegerField(default=0, verbose_name='payment status', enum=shoop.core.models._orders.PaymentStatus, db_index=True)),
                ('shipping_status', enumfields.fields.EnumIntegerField(default=0, verbose_name='shipping status', enum=shoop.core.models._orders.ShippingStatus, db_index=True)),
                ('payment_method_name', models.CharField(default='', verbose_name='payment method name', blank=True, max_length=64)),
                ('payment_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('shipping_method_name', models.CharField(default='', verbose_name='shipping method name', blank=True, max_length=64)),
                ('shipping_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('extra_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('taxful_total_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='grand total', editable=False, decimal_places=9, max_digits=36)),
                ('taxless_total_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='taxless total', editable=False, decimal_places=9, max_digits=36)),
                ('display_currency', models.CharField(blank=True, max_length=4)),
                ('display_currency_rate', models.DecimalField(default=1, decimal_places=9, max_digits=36)),
                ('ip_address', models.GenericIPAddressField(verbose_name='IP address', blank=True, null=True)),
                ('order_date', models.DateTimeField(verbose_name='order date', editable=False)),
                ('payment_date', models.DateTimeField(verbose_name='payment date', editable=False, null=True)),
                ('language', shoop.core.fields.LanguageField(verbose_name='language', blank=True, max_length=10, choices=[('aa', 'aa'), ('ab', 'ab'), ('ace', 'ace'), ('ach', 'ach'), ('ada', 'ada'), ('ady', 'ady'), ('ae', 'ae'), ('af', 'af'), ('afa', 'afa'), ('afh', 'afh'), ('agq', 'agq'), ('ain', 'ain'), ('ak', 'ak'), ('akk', 'akk'), ('ale', 'ale'), ('alg', 'alg'), ('alt', 'alt'), ('am', 'am'), ('an', 'an'), ('ang', 'ang'), ('anp', 'anp'), ('apa', 'apa'), ('ar', 'ar'), ('ar_001', 'ar_001'), ('arc', 'arc'), ('arn', 'arn'), ('arp', 'arp'), ('art', 'art'), ('arw', 'arw'), ('as', 'as'), ('asa', 'asa'), ('ast', 'ast'), ('ath', 'ath'), ('aus', 'aus'), ('av', 'av'), ('awa', 'awa'), ('ay', 'ay'), ('az', 'az'), ('ba', 'ba'), ('bad', 'bad'), ('bai', 'bai'), ('bal', 'bal'), ('ban', 'ban'), ('bas', 'bas'), ('bat', 'bat'), ('bax', 'bax'), ('bbj', 'bbj'), ('be', 'be'), ('bej', 'bej'), ('bem', 'bem'), ('ber', 'ber'), ('bez', 'bez'), ('bfd', 'bfd'), ('bg', 'bg'), ('bh', 'bh'), ('bho', 'bho'), ('bi', 'bi'), ('bik', 'bik'), ('bin', 'bin'), ('bkm', 'bkm'), ('bla', 'bla'), ('bm', 'bm'), ('bn', 'bn'), ('bnt', 'bnt'), ('bo', 'bo'), ('br', 'br'), ('bra', 'bra'), ('brx', 'brx'), ('bs', 'bs'), ('bss', 'bss'), ('btk', 'btk'), ('bua', 'bua'), ('bug', 'bug'), ('bum', 'bum'), ('byn', 'byn'), ('byv', 'byv'), ('ca', 'ca'), ('cad', 'cad'), ('cai', 'cai'), ('car', 'car'), ('cau', 'cau'), ('cay', 'cay'), ('cch', 'cch'), ('ce', 'ce'), ('ceb', 'ceb'), ('cel', 'cel'), ('cgg', 'cgg'), ('ch', 'ch'), ('chb', 'chb'), ('chg', 'chg'), ('chk', 'chk'), ('chm', 'chm'), ('chn', 'chn'), ('cho', 'cho'), ('chp', 'chp'), ('chr', 'chr'), ('chy', 'chy'), ('ckb', 'ckb'), ('cmc', 'cmc'), ('co', 'co'), ('cop', 'cop'), ('cpe', 'cpe'), ('cpf', 'cpf'), ('cpp', 'cpp'), ('cr', 'cr'), ('crh', 'crh'), ('crp', 'crp'), ('cs', 'cs'), ('csb', 'csb'), ('cu', 'cu'), ('cus', 'cus'), ('cv', 'cv'), ('cy', 'cy'), ('da', 'da'), ('dak', 'dak'), ('dar', 'dar'), ('dav', 'dav'), ('day', 'day'), ('de', 'de'), ('de_AT', 'de_AT'), ('de_CH', 'de_CH'), ('del', 'del'), ('den', 'den'), ('dgr', 'dgr'), ('din', 'din'), ('dje', 'dje'), ('doi', 'doi'), ('dra', 'dra'), ('dsb', 'dsb'), ('dua', 'dua'), ('dum', 'dum'), ('dv', 'dv'), ('dyo', 'dyo'), ('dyu', 'dyu'), ('dz', 'dz'), ('dzg', 'dzg'), ('ebu', 'ebu'), ('ee', 'ee'), ('efi', 'efi'), ('egy', 'egy'), ('eka', 'eka'), ('el', 'el'), ('elx', 'elx'), ('en', 'en'), ('en_AU', 'en_AU'), ('en_CA', 'en_CA'), ('en_GB', 'en_GB'), ('en_US', 'en_US'), ('enm', 'enm'), ('eo', 'eo'), ('es', 'es'), ('es_419', 'es_419'), ('es_ES', 'es_ES'), ('et', 'et'), ('eu', 'eu'), ('ewo', 'ewo'), ('fa', 'fa'), ('fan', 'fan'), ('fat', 'fat'), ('ff', 'ff'), ('fi', 'fi'), ('fil', 'fil'), ('fiu', 'fiu'), ('fj', 'fj'), ('fo', 'fo'), ('fon', 'fon'), ('fr', 'fr'), ('fr_CA', 'fr_CA'), ('fr_CH', 'fr_CH'), ('frm', 'frm'), ('fro', 'fro'), ('frr', 'frr'), ('frs', 'frs'), ('fur', 'fur'), ('fy', 'fy'), ('ga', 'ga'), ('gaa', 'gaa'), ('gay', 'gay'), ('gba', 'gba'), ('gd', 'gd'), ('gem', 'gem'), ('gez', 'gez'), ('gil', 'gil'), ('gl', 'gl'), ('gmh', 'gmh'), ('gn', 'gn'), ('goh', 'goh'), ('gon', 'gon'), ('gor', 'gor'), ('got', 'got'), ('grb', 'grb'), ('grc', 'grc'), ('gsw', 'gsw'), ('gu', 'gu'), ('guz', 'guz'), ('gv', 'gv'), ('gwi', 'gwi'), ('ha', 'ha'), ('hai', 'hai'), ('haw', 'haw'), ('he', 'he'), ('hi', 'hi'), ('hil', 'hil'), ('him', 'him'), ('hit', 'hit'), ('hmn', 'hmn'), ('ho', 'ho'), ('hr', 'hr'), ('hsb', 'hsb'), ('ht', 'ht'), ('hu', 'hu'), ('hup', 'hup'), ('hy', 'hy'), ('hz', 'hz'), ('ia', 'ia'), ('iba', 'iba'), ('ibb', 'ibb'), ('id', 'id'), ('ie', 'ie'), ('ig', 'ig'), ('ii', 'ii'), ('ijo', 'ijo'), ('ik', 'ik'), ('ilo', 'ilo'), ('inc', 'inc'), ('ine', 'ine'), ('inh', 'inh'), ('io', 'io'), ('ira', 'ira'), ('iro', 'iro'), ('is', 'is'), ('it', 'it'), ('iu', 'iu'), ('ja', 'ja'), ('jbo', 'jbo'), ('jgo', 'jgo'), ('jmc', 'jmc'), ('jpr', 'jpr'), ('jrb', 'jrb'), ('jv', 'jv'), ('ka', 'ka'), ('kaa', 'kaa'), ('kab', 'kab'), ('kac', 'kac'), ('kaj', 'kaj'), ('kam', 'kam'), ('kar', 'kar'), ('kaw', 'kaw'), ('kbd', 'kbd'), ('kbl', 'kbl'), ('kcg', 'kcg'), ('kde', 'kde'), ('kea', 'kea'), ('kfo', 'kfo'), ('kg', 'kg'), ('kha', 'kha'), ('khi', 'khi'), ('kho', 'kho'), ('khq', 'khq'), ('ki', 'ki'), ('kj', 'kj'), ('kk', 'kk'), ('kkj', 'kkj'), ('kl', 'kl'), ('kln', 'kln'), ('km', 'km'), ('kmb', 'kmb'), ('kn', 'kn'), ('ko', 'ko'), ('kok', 'kok'), ('kos', 'kos'), ('kpe', 'kpe'), ('kr', 'kr'), ('krc', 'krc'), ('krl', 'krl'), ('kro', 'kro'), ('kru', 'kru'), ('ks', 'ks'), ('ksb', 'ksb'), ('ksf', 'ksf'), ('ksh', 'ksh'), ('ku', 'ku'), ('kum', 'kum'), ('kut', 'kut'), ('kv', 'kv'), ('kw', 'kw'), ('ky', 'ky'), ('la', 'la'), ('lad', 'lad'), ('lag', 'lag'), ('lah', 'lah'), ('lam', 'lam'), ('lb', 'lb'), ('lez', 'lez'), ('lg', 'lg'), ('li', 'li'), ('lkt', 'lkt'), ('ln', 'ln'), ('lo', 'lo'), ('lol', 'lol'), ('loz', 'loz'), ('lt', 'lt'), ('lu', 'lu'), ('lua', 'lua'), ('lui', 'lui'), ('lun', 'lun'), ('luo', 'luo'), ('lus', 'lus'), ('luy', 'luy'), ('lv', 'lv'), ('mad', 'mad'), ('maf', 'maf'), ('mag', 'mag'), ('mai', 'mai'), ('mak', 'mak'), ('man', 'man'), ('map', 'map'), ('mas', 'mas'), ('mde', 'mde'), ('mdf', 'mdf'), ('mdr', 'mdr'), ('men', 'men'), ('mer', 'mer'), ('mfe', 'mfe'), ('mg', 'mg'), ('mga', 'mga'), ('mgh', 'mgh'), ('mgo', 'mgo'), ('mh', 'mh'), ('mi', 'mi'), ('mic', 'mic'), ('min', 'min'), ('mis', 'mis'), ('mk', 'mk'), ('mkh', 'mkh'), ('ml', 'ml'), ('mn', 'mn'), ('mnc', 'mnc'), ('mni', 'mni'), ('mno', 'mno'), ('mo', 'mo'), ('moh', 'moh'), ('mos', 'mos'), ('mr', 'mr'), ('ms', 'ms'), ('mt', 'mt'), ('mua', 'mua'), ('mul', 'mul'), ('mun', 'mun'), ('mus', 'mus'), ('mwl', 'mwl'), ('mwr', 'mwr'), ('my', 'my'), ('mye', 'mye'), ('myn', 'myn'), ('myv', 'myv'), ('na', 'na'), ('nah', 'nah'), ('nai', 'nai'), ('nap', 'nap'), ('naq', 'naq'), ('nb', 'nb'), ('nd', 'nd'), ('nds', 'nds'), ('ne', 'ne'), ('new', 'new'), ('ng', 'ng'), ('nia', 'nia'), ('nic', 'nic'), ('niu', 'niu'), ('nl', 'nl'), ('nl_BE', 'nl_BE'), ('nmg', 'nmg'), ('nn', 'nn'), ('nnh', 'nnh'), ('no', 'no'), ('nog', 'nog'), ('non', 'non'), ('nqo', 'nqo'), ('nr', 'nr'), ('nso', 'nso'), ('nub', 'nub'), ('nus', 'nus'), ('nv', 'nv'), ('nwc', 'nwc'), ('ny', 'ny'), ('nym', 'nym'), ('nyn', 'nyn'), ('nyo', 'nyo'), ('nzi', 'nzi'), ('oc', 'oc'), ('oj', 'oj'), ('om', 'om'), ('or', 'or'), ('os', 'os'), ('osa', 'osa'), ('ota', 'ota'), ('oto', 'oto'), ('pa', 'pa'), ('paa', 'paa'), ('pag', 'pag'), ('pal', 'pal'), ('pam', 'pam'), ('pap', 'pap'), ('pau', 'pau'), ('peo', 'peo'), ('phi', 'phi'), ('phn', 'phn'), ('pi', 'pi'), ('pl', 'pl'), ('pon', 'pon'), ('pra', 'pra'), ('pro', 'pro'), ('ps', 'ps'), ('pt', 'pt'), ('pt_BR', 'pt_BR'), ('pt_PT', 'pt_PT'), ('qu', 'qu'), ('raj', 'raj'), ('rap', 'rap'), ('rar', 'rar'), ('rm', 'rm'), ('rn', 'rn'), ('ro', 'ro'), ('roa', 'roa'), ('rof', 'rof'), ('rom', 'rom'), ('root', 'root'), ('ru', 'ru'), ('rup', 'rup'), ('rw', 'rw'), ('rwk', 'rwk'), ('sa', 'sa'), ('sad', 'sad'), ('sah', 'sah'), ('sai', 'sai'), ('sal', 'sal'), ('sam', 'sam'), ('saq', 'saq'), ('sas', 'sas'), ('sat', 'sat'), ('sba', 'sba'), ('sbp', 'sbp'), ('sc', 'sc'), ('scn', 'scn'), ('sco', 'sco'), ('sd', 'sd'), ('se', 'se'), ('see', 'see'), ('seh', 'seh'), ('sel', 'sel'), ('sem', 'sem'), ('ses', 'ses'), ('sg', 'sg'), ('sga', 'sga'), ('sgn', 'sgn'), ('sh', 'sh'), ('shi', 'shi'), ('shn', 'shn'), ('shu', 'shu'), ('si', 'si'), ('sid', 'sid'), ('sio', 'sio'), ('sit', 'sit'), ('sk', 'sk'), ('sl', 'sl'), ('sla', 'sla'), ('sm', 'sm'), ('sma', 'sma'), ('smi', 'smi'), ('smj', 'smj'), ('smn', 'smn'), ('sms', 'sms'), ('sn', 'sn'), ('snk', 'snk'), ('so', 'so'), ('sog', 'sog'), ('son', 'son'), ('sq', 'sq'), ('sr', 'sr'), ('srn', 'srn'), ('srr', 'srr'), ('ss', 'ss'), ('ssa', 'ssa'), ('ssy', 'ssy'), ('st', 'st'), ('su', 'su'), ('suk', 'suk'), ('sus', 'sus'), ('sux', 'sux'), ('sv', 'sv'), ('sw', 'sw'), ('swb', 'swb'), ('swc', 'swc'), ('syc', 'syc'), ('syr', 'syr'), ('ta', 'ta'), ('tai', 'tai'), ('te', 'te'), ('tem', 'tem'), ('teo', 'teo'), ('ter', 'ter'), ('tet', 'tet'), ('tg', 'tg'), ('th', 'th'), ('ti', 'ti'), ('tig', 'tig'), ('tiv', 'tiv'), ('tk', 'tk'), ('tkl', 'tkl'), ('tl', 'tl'), ('tlh', 'tlh'), ('tli', 'tli'), ('tmh', 'tmh'), ('tn', 'tn'), ('to', 'to'), ('tog', 'tog'), ('tpi', 'tpi'), ('tr', 'tr'), ('trv', 'trv'), ('ts', 'ts'), ('tsi', 'tsi'), ('tt', 'tt'), ('tum', 'tum'), ('tup', 'tup'), ('tut', 'tut'), ('tvl', 'tvl'), ('tw', 'tw'), ('twq', 'twq'), ('ty', 'ty'), ('tyv', 'tyv'), ('tzm', 'tzm'), ('udm', 'udm'), ('ug', 'ug'), ('uga', 'uga'), ('uk', 'uk'), ('umb', 'umb'), ('und', 'und'), ('ur', 'ur'), ('uz', 'uz'), ('vai', 'vai'), ('ve', 've'), ('vi', 'vi'), ('vo', 'vo'), ('vot', 'vot'), ('vun', 'vun'), ('wa', 'wa'), ('wae', 'wae'), ('wak', 'wak'), ('wal', 'wal'), ('war', 'war'), ('was', 'was'), ('wen', 'wen'), ('wo', 'wo'), ('xal', 'xal'), ('xh', 'xh'), ('xog', 'xog'), ('yao', 'yao'), ('yap', 'yap'), ('yav', 'yav'), ('ybb', 'ybb'), ('yi', 'yi'), ('yo', 'yo'), ('ypk', 'ypk'), ('yue', 'yue'), ('za', 'za'), ('zap', 'zap'), ('zbl', 'zbl'), ('zen', 'zen'), ('zh', 'zh'), ('zh_Hans', 'zh_Hans'), ('zh_Hant', 'zh_Hant'), ('znd', 'znd'), ('zu', 'zu'), ('zun', 'zun'), ('zxx', 'zxx'), ('zza', 'zza')])),
                ('customer_comment', models.TextField(verbose_name='customer comment', blank=True)),
                ('admin_comment', models.TextField(verbose_name='admin comment/notes', blank=True)),
                ('require_verification', models.BooleanField(default=False, verbose_name='requires verification')),
                ('all_verified', models.BooleanField(default=False, verbose_name='all lines verified')),
                ('marketing_permission', models.BooleanField(default=True, verbose_name='marketing permission')),
                ('billing_address', shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='billing address', blank=True, related_name='billing_orders', to='shoop.Address', null=True)),
                ('creator', shoop.core.fields.UnsavedForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='creating user', blank=True, related_name='orders_created', null=True)),
            ],
            options={
                'verbose_name_plural': 'orders',
                'verbose_name': 'order',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('ordering', models.IntegerField(default=0, verbose_name='ordering')),
                ('type', enumfields.fields.EnumIntegerField(default=1, verbose_name='line type', enum=shoop.core.models._order_lines.OrderLineType)),
                ('sku', models.CharField(verbose_name='line SKU', blank=True, max_length=48)),
                ('text', models.CharField(verbose_name='line text', max_length=256)),
                ('accounting_identifier', models.CharField(verbose_name='accounting identifier', blank=True, max_length=32)),
                ('require_verification', models.BooleanField(default=False, verbose_name='require verification')),
                ('verified', models.BooleanField(default=False, verbose_name='verified')),
                ('extra_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('quantity', shoop.core.fields.QuantityField(default=1, verbose_name='quantity', decimal_places=9, max_digits=36)),
                ('_unit_price_amount', shoop.core.fields.MoneyValueField(default=0, verbose_name='unit price amount', decimal_places=9, max_digits=36)),
                ('_total_discount_amount', shoop.core.fields.MoneyValueField(default=0, verbose_name='total amount of discount', decimal_places=9, max_digits=36)),
                ('_prices_include_tax', models.BooleanField(default=True)),
                ('order', shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='order', to='shoop.Order', related_name='lines')),
                ('parent_line', shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='parent line', blank=True, related_name='child_lines', to='shoop.OrderLine', null=True)),
            ],
            options={
                'verbose_name_plural': 'order lines',
                'verbose_name': 'order line',
            },
            bases=(models.Model, shoop.core.pricing.Priceful),
        ),
        migrations.CreateModel(
            name='OrderLineTax',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='tax name', max_length=200)),
                ('amount', shoop.core.fields.MoneyValueField(default=0, verbose_name='tax amount', decimal_places=9, max_digits=36)),
                ('base_amount', shoop.core.fields.MoneyValueField(default=0, verbose_name='base amount', help_text='Amount that this tax is calculated from', decimal_places=9, max_digits=36)),
                ('ordering', models.IntegerField(default=0, verbose_name='ordering')),
                ('order_line', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='order line', to='shoop.OrderLine', related_name='taxes')),
            ],
            options={
                'ordering': ['ordering'],
            },
            bases=(models.Model, shoop.core.taxing._line_tax.LineTax),
        ),
        migrations.CreateModel(
            name='OrderLogEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(max_length=256)),
                ('identifier', models.CharField(blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(default=0, enum=shoop.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True)),
                ('target', models.ForeignKey(to='shoop.Order', related_name='log_entries')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderStatus',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, null=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, db_index=True)),
                ('ordering', models.IntegerField(default=0, db_index=True)),
                ('role', enumfields.fields.EnumIntegerField(default=0, enum=shoop.core.models._orders.OrderStatusRole, db_index=True)),
                ('default', models.BooleanField(default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderStatusTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='Name', max_length=64)),
                ('master', models.ForeignKey(to='shoop.OrderStatus', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'order status Translation',
                'db_table': 'shoop_orderstatus_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('gateway_id', models.CharField(max_length=32)),
                ('payment_identifier', models.CharField(max_length=96, unique=True)),
                ('amount', shoop.core.fields.MoneyValueField(default=0, decimal_places=9, max_digits=36)),
                ('description', models.CharField(blank=True, max_length=256)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shoop.Order', related_name='payments')),
            ],
            options={
                'verbose_name_plural': 'payments',
                'verbose_name': 'payment',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('status', enumfields.fields.EnumIntegerField(default=1, verbose_name='status', enum=MethodStatus, db_index=True)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('module_identifier', models.CharField(verbose_name='module', blank=True, max_length=64)),
                ('module_data', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'payment methods',
                'verbose_name': 'payment method',
            },
            bases=(shoop.core.modules.interface.ModuleInterface, models.Model),
        ),
        migrations.CreateModel(
            name='PaymentMethodTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('master', models.ForeignKey(to='shoop.PaymentMethod', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'payment method Translation',
                'db_table': 'shoop_paymentmethod_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='PersistentCacheEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('module', models.CharField(max_length=64)),
                ('key', models.CharField(max_length=64)),
                ('time', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField()),
            ],
            options={
                'verbose_name_plural': 'cache entries',
                'verbose_name': 'cache entry',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False, editable=False, db_index=True)),
                ('mode', enumfields.fields.EnumIntegerField(default=0, enum=shoop.core.models._products.ProductMode)),
                ('stock_behavior', enumfields.fields.EnumIntegerField(default=0, verbose_name='stock', enum=shoop.core.models._products.StockBehavior)),
                ('shipping_mode', enumfields.fields.EnumIntegerField(default=0, verbose_name='shipping mode', enum=shoop.core.models._products.ShippingMode)),
                ('sku', models.CharField(verbose_name='SKU', max_length=128, db_index=True, unique=True)),
                ('gtin', models.CharField(verbose_name='GTIN', blank=True, max_length=40, help_text='Global Trade Item Number')),
                ('barcode', models.CharField(verbose_name='barcode', blank=True, max_length=40)),
                ('accounting_identifier', models.CharField(verbose_name='bookkeeping account', blank=True, max_length=32)),
                ('profit_center', models.CharField(verbose_name='profit center', blank=True, max_length=32)),
                ('cost_center', models.CharField(verbose_name='cost center', blank=True, max_length=32)),
                ('width', shoop.core.fields.MeasurementField(default=0, verbose_name='width (mm)', unit='mm', decimal_places=9, max_digits=36)),
                ('height', shoop.core.fields.MeasurementField(default=0, verbose_name='height (mm)', unit='mm', decimal_places=9, max_digits=36)),
                ('depth', shoop.core.fields.MeasurementField(default=0, verbose_name='depth (mm)', unit='mm', decimal_places=9, max_digits=36)),
                ('net_weight', shoop.core.fields.MeasurementField(default=0, verbose_name='net weight (g)', unit='g', decimal_places=9, max_digits=36)),
                ('gross_weight', shoop.core.fields.MeasurementField(default=0, verbose_name='gross weight (g)', unit='g', decimal_places=9, max_digits=36)),
                ('purchase_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='purchase price', decimal_places=9, max_digits=36)),
                ('suggested_retail_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='suggested retail price', decimal_places=9, max_digits=36)),
                ('category', models.ForeignKey(to='shoop.Category', verbose_name='primary category', blank=True, related_name='primary_products', help_text='only used for administration and reporting', null=True)),
                ('manufacturer', models.ForeignKey(to='shoop.Manufacturer', verbose_name='manufacturer', blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'products',
                'verbose_name': 'product',
                'ordering': ('-id',),
            },
            bases=(shoop.core.models._attributes.AttributableMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numeric_value', models.DecimalField(blank=True, decimal_places=9, null=True, max_digits=36)),
                ('datetime_value', models.DateTimeField(blank=True, null=True)),
                ('untranslated_string_value', models.TextField(blank=True)),
                ('attribute', models.ForeignKey(to='shoop.Attribute')),
                ('product', models.ForeignKey(to='shoop.Product', related_name='attributes')),
            ],
            options={
                'verbose_name_plural': 'product attributes',
                'verbose_name': 'product attribute',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductAttributeTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('translated_string_value', models.TextField(blank=True)),
                ('master', models.ForeignKey(to='shoop.ProductAttribute', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'product attribute Translation',
                'db_table': 'shoop_productattribute_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProductCrossSell',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('weight', models.IntegerField(default=0)),
                ('type', enumfields.fields.EnumIntegerField(enum=shoop.core.models._products.ProductCrossSellType)),
                ('product1', models.ForeignKey(to='shoop.Product', related_name='cross_sell_1')),
                ('product2', models.ForeignKey(to='shoop.Product', related_name='cross_sell_2')),
            ],
            options={
                'verbose_name_plural': 'cross sell links',
                'verbose_name': 'cross sell link',
            },
        ),
        migrations.CreateModel(
            name='ProductLogEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(max_length=256)),
                ('identifier', models.CharField(blank=True, max_length=64)),
                ('kind', enumfields.fields.EnumIntegerField(default=0, enum=shoop.utils.analog.LogEntryKind)),
                ('extra', jsonfield.fields.JSONField(blank=True, null=True)),
                ('target', models.ForeignKey(to='shoop.Product', related_name='log_entries')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductMedia',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('kind', enumfields.fields.EnumIntegerField(default=1, verbose_name='kind', enum=shoop.core.models._product_media.ProductMediaKind, db_index=True)),
                ('external_url', models.URLField(verbose_name='URL', blank=True, null=True)),
                ('ordering', models.IntegerField(default=0)),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled', db_index=True)),
                ('public', models.BooleanField(default=True, verbose_name='public (shown on product page)')),
                ('purchased', models.BooleanField(default=False, verbose_name='purchased (shown for finished purchases)')),
                ('file', filer.fields.file.FilerFileField(to='filer.File', verbose_name='file', blank=True, null=True)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='media')),
            ],
            options={
                'verbose_name_plural': 'product attachments',
                'verbose_name': 'product attachment',
                'ordering': ['ordering'],
            },
        ),
        migrations.CreateModel(
            name='ProductMediaTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('title', models.CharField(verbose_name='title', blank=True, max_length=128)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('master', models.ForeignKey(to='shoop.ProductMedia', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'product attachment Translation',
                'db_table': 'shoop_productmedia_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProductPackageLink',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('quantity', shoop.core.fields.QuantityField(default=1, decimal_places=9, max_digits=36)),
                ('child', models.ForeignKey(to='shoop.Product', related_name='+')),
                ('parent', models.ForeignKey(to='shoop.Product', related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='ProductTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=256)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('slug', models.SlugField(verbose_name='slug', max_length=255, null=True)),
                ('keywords', models.TextField(verbose_name='keywords', blank=True)),
                ('status_text', models.CharField(verbose_name='status text', blank=True, max_length=128, help_text='This text will be shown alongside the product in the shop. (Ex.: "Available in a month")')),
                ('variation_name', models.CharField(verbose_name='variation name', blank=True, max_length=128)),
                ('master', models.ForeignKey(to='shoop.Product', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'product Translation',
                'db_table': 'shoop_product_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('attributes', models.ManyToManyField(to='shoop.Attribute', verbose_name='attributes', blank=True, related_name='product_types')),
            ],
            options={
                'verbose_name_plural': 'product types',
                'verbose_name': 'product type',
            },
        ),
        migrations.CreateModel(
            name='ProductTypeTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('master', models.ForeignKey(to='shoop.ProductType', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'product type Translation',
                'db_table': 'shoop_producttype_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProductVariationResult',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('combination_hash', models.CharField(max_length=40, db_index=True, unique=True)),
                ('status', enumfields.fields.EnumIntegerField(default=1, enum=shoop.core.models._product_variation.ProductVariationLinkStatus, db_index=True)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='variation_result_supers')),
                ('result', models.ForeignKey(to='shoop.Product', related_name='variation_result_subs')),
            ],
            options={
                'verbose_name_plural': 'variation results',
                'verbose_name': 'variation result',
            },
        ),
        migrations.CreateModel(
            name='ProductVariationVariable',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='variation_variables')),
            ],
            options={
                'verbose_name_plural': 'variation variables',
                'verbose_name': 'variation variable',
            },
        ),
        migrations.CreateModel(
            name='ProductVariationVariableTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=128)),
                ('master', models.ForeignKey(to='shoop.ProductVariationVariable', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'variation variable Translation',
                'db_table': 'shoop_productvariationvariable_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProductVariationVariableValue',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('variable', models.ForeignKey(to='shoop.ProductVariationVariable', related_name='values')),
            ],
            options={
                'verbose_name_plural': 'variation values',
                'verbose_name': 'variation value',
            },
        ),
        migrations.CreateModel(
            name='ProductVariationVariableValueTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('value', models.CharField(verbose_name='value', max_length=128)),
                ('master', models.ForeignKey(to='shoop.ProductVariationVariableValue', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'variation value Translation',
                'db_table': 'shoop_productvariationvariablevalue_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='SalesUnit',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('decimals', models.PositiveSmallIntegerField(default=0, verbose_name='allowed decimals')),
            ],
            options={
                'verbose_name_plural': 'sales units',
                'verbose_name': 'sales unit',
            },
        ),
        migrations.CreateModel(
            name='SalesUnitTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(max_length=128)),
                ('short_name', models.CharField(max_length=128)),
                ('master', models.ForeignKey(to='shoop.SalesUnit', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'sales unit Translation',
                'db_table': 'shoop_salesunit_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='SavedAddress',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('role', enumfields.fields.EnumIntegerField(default=1, verbose_name='role', enum=shoop.core.models._addresses.SavedAddressRole)),
                ('status', enumfields.fields.EnumIntegerField(default=1, verbose_name='status', enum=shoop.core.models._addresses.SavedAddressStatus)),
                ('title', models.CharField(verbose_name='title', blank=True, max_length=255)),
                ('address', models.ForeignKey(verbose_name='address', to='shoop.Address', related_name='saved_addresses')),
            ],
            options={
                'verbose_name_plural': 'saved addresses',
                'verbose_name': 'saved address',
                'ordering': ('owner_id', 'role', 'title'),
            },
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('status', enumfields.fields.EnumIntegerField(default=0, enum=shoop.core.models._shipments.ShipmentStatus)),
                ('tracking_code', models.CharField(verbose_name='tracking code', blank=True, max_length=64)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('volume', shoop.core.fields.MeasurementField(default=0, unit='m3', decimal_places=9, max_digits=36)),
                ('weight', shoop.core.fields.MeasurementField(default=0, unit='kg', decimal_places=9, max_digits=36)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shoop.Order', related_name='shipments')),
            ],
            options={
                'verbose_name_plural': 'shipments',
                'verbose_name': 'shipment',
            },
        ),
        migrations.CreateModel(
            name='ShipmentProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('quantity', shoop.core.fields.QuantityField(default=0, decimal_places=9, max_digits=36)),
                ('unit_volume', shoop.core.fields.MeasurementField(default=0, unit='m3', decimal_places=9, max_digits=36)),
                ('unit_weight', shoop.core.fields.MeasurementField(default=0, unit='g', decimal_places=9, max_digits=36)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='shipments')),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shoop.Shipment', related_name='products')),
            ],
            options={
                'verbose_name_plural': 'sent products',
                'verbose_name': 'sent product',
            },
        ),
        migrations.CreateModel(
            name='ShippingMethod',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('status', enumfields.fields.EnumIntegerField(default=1, verbose_name='status', enum=MethodStatus, db_index=True)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('module_identifier', models.CharField(verbose_name='module', blank=True, max_length=64)),
                ('module_data', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'shipping methods',
                'verbose_name': 'shipping method',
            },
            bases=(shoop.core.modules.interface.ModuleInterface, models.Model),
        ),
        migrations.CreateModel(
            name='ShippingMethodTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('master', models.ForeignKey(to='shoop.ShippingMethod', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'shipping method Translation',
                'db_table': 'shoop_shippingmethod_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('domain', models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ('status', enumfields.fields.EnumIntegerField(default=0, enum=shoop.core.models._shops.ShopStatus)),
                ('options', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('visible', models.BooleanField(default=True, db_index=True)),
                ('listed', models.BooleanField(default=True, db_index=True)),
                ('purchasable', models.BooleanField(default=True, db_index=True)),
                ('searchable', models.BooleanField(default=True, db_index=True)),
                ('visibility_limit', enumfields.fields.EnumIntegerField(default=1, verbose_name='visibility limitations', enum=shoop.core.models._products.ProductVisibility, db_index=True)),
                ('purchase_multiple', shoop.core.fields.QuantityField(default=0, verbose_name='purchase multiple', decimal_places=9, max_digits=36)),
                ('minimum_purchase_quantity', shoop.core.fields.QuantityField(default=1, verbose_name='minimum purchase', decimal_places=9, max_digits=36)),
                ('limit_shipping_methods', models.BooleanField(default=False)),
                ('limit_payment_methods', models.BooleanField(default=False)),
                ('categories', models.ManyToManyField(to='shoop.Category', verbose_name='categories', blank=True, related_name='shop_products')),
                ('payment_methods', models.ManyToManyField(to='shoop.PaymentMethod', verbose_name='payment methods', blank=True, related_name='payment_products')),
                ('primary_category', models.ForeignKey(to='shoop.Category', verbose_name='primary category', blank=True, related_name='primary_shop_products', null=True)),
                ('product', shoop.core.fields.UnsavedForeignKey(to='shoop.Product', related_name='shop_products')),
                ('shipping_methods', models.ManyToManyField(to='shoop.ShippingMethod', verbose_name='shipping methods', blank=True, related_name='shipping_products')),
                ('shop', models.ForeignKey(to='shoop.Shop', related_name='shop_products')),
                ('shop_primary_image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='primary_image_for_shop_products', to='shoop.ProductMedia', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShopTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(max_length=64)),
                ('master', models.ForeignKey(to='shoop.Shop', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'shop Translation',
                'db_table': 'shoop_shop_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='SuppliedProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sku', models.CharField(verbose_name='SKU', max_length=128, db_index=True)),
                ('alert_limit', models.IntegerField(default=0, verbose_name='alert limit')),
                ('purchase_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='purchase price', decimal_places=9, max_digits=36)),
                ('suggested_retail_price', shoop.core.fields.MoneyValueField(default=0, verbose_name='suggested retail price', decimal_places=9, max_digits=36)),
                ('physical_count', shoop.core.fields.QuantityField(default=0, verbose_name='physical stock count', editable=False, decimal_places=9, max_digits=36)),
                ('logical_count', shoop.core.fields.QuantityField(default=0, verbose_name='logical stock count', editable=False, decimal_places=9, max_digits=36)),
                ('product', models.ForeignKey(to='shoop.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('name', models.CharField(max_length=64)),
                ('type', enumfields.fields.EnumIntegerField(default=1, enum=shoop.core.models._suppliers.SupplierType)),
                ('stock_managed', models.BooleanField(default=False)),
                ('module_identifier', models.CharField(verbose_name='module', blank=True, max_length=64)),
                ('module_data', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            bases=(shoop.core.modules.interface.ModuleInterface, models.Model),
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('code', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('rate', models.DecimalField(verbose_name='tax rate', blank=True, decimal_places=5, help_text='The percentage rate of the tax. Mutually exclusive with flat amounts.', null=True, max_digits=6)),
                ('amount', shoop.core.fields.MoneyValueField(verbose_name='tax amount', blank=True, decimal_places=9, default=None, help_text='The flat amount of the tax. Mutually exclusive with percentage rates.', null=True, max_digits=36)),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
            ],
            options={
                'verbose_name_plural': 'taxes',
                'verbose_name': 'tax',
            },
        ),
        migrations.CreateModel(
            name='TaxClass',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', blank=True, unique=True, editable=False, help_text="Do not change this value if you are not sure what you're doing.", max_length=64, null=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
            ],
            options={
                'verbose_name_plural': 'tax classes',
                'verbose_name': 'tax class',
            },
        ),
        migrations.CreateModel(
            name='TaxClassTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('master', models.ForeignKey(to='shoop.TaxClass', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'tax class Translation',
                'db_table': 'shoop_taxclass_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TaxTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('name', models.CharField(max_length=64)),
                ('master', models.ForeignKey(to='shoop.Tax', related_name='translations', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'tax Translation',
                'db_table': 'shoop_tax_translation',
                'default_permissions': (),
                'db_tablespace': '',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='AnonymousContact',
            fields=[
                ('contact_ptr', models.OneToOneField(primary_key=True, to='shoop.Contact', serialize=False, parent_link=True, auto_created=True)),
            ],
            options={
                'managed': False,
            },
            bases=('shoop.contact',),
        ),
        migrations.CreateModel(
            name='CompanyContact',
            fields=[
                ('contact_ptr', models.OneToOneField(primary_key=True, to='shoop.Contact', serialize=False, parent_link=True, auto_created=True)),
                ('vat_code', models.CharField(verbose_name='VAT code', blank=True, max_length=32)),
            ],
            options={
                'verbose_name_plural': 'companies',
                'verbose_name': 'company',
            },
            bases=('shoop.contact',),
        ),
        migrations.CreateModel(
            name='PersonContact',
            fields=[
                ('contact_ptr', models.OneToOneField(primary_key=True, to='shoop.Contact', serialize=False, parent_link=True, auto_created=True)),
                ('gender', enumfields.fields.EnumField(default='u', enum=shoop.core.models._contacts.Gender, max_length=4)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, blank=True, related_name='contact', null=True)),
            ],
            options={
                'verbose_name_plural': 'persons',
                'verbose_name': 'person',
            },
            bases=('shoop.contact',),
        ),
        migrations.AddField(
            model_name='suppliedproduct',
            name='supplier',
            field=models.ForeignKey(to='shoop.Supplier'),
        ),
        migrations.AddField(
            model_name='shopproduct',
            name='suppliers',
            field=models.ManyToManyField(to='shoop.Supplier', blank=True, related_name='shop_products'),
        ),
        migrations.AddField(
            model_name='shopproduct',
            name='visibility_groups',
            field=models.ManyToManyField(to='shoop.ContactGroup', verbose_name='visible for groups', blank=True, related_name='visible_products'),
        ),
        migrations.AddField(
            model_name='shop',
            name='owner',
            field=models.ForeignKey(to='shoop.Contact', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shippingmethod',
            name='tax_class',
            field=models.ForeignKey(verbose_name='tax class', to='shoop.TaxClass'),
        ),
        migrations.AddField(
            model_name='shipment',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shoop.Supplier', related_name='shipments'),
        ),
        migrations.AddField(
            model_name='savedaddress',
            name='owner',
            field=models.ForeignKey(to='shoop.Contact'),
        ),
        migrations.AddField(
            model_name='productmedia',
            name='shops',
            field=models.ManyToManyField(to='shoop.Shop', related_name='product_media'),
        ),
        migrations.AddField(
            model_name='product',
            name='primary_image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='primary_image_for_products', to='shoop.ProductMedia', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sales_unit',
            field=models.ForeignKey(to='shoop.SalesUnit', verbose_name='unit', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='tax_class',
            field=models.ForeignKey(verbose_name='tax class', to='shoop.TaxClass'),
        ),
        migrations.AddField(
            model_name='product',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='product type', to='shoop.ProductType', related_name='products'),
        ),
        migrations.AddField(
            model_name='product',
            name='variation_parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='variation parent', blank=True, related_name='variation_children', to='shoop.Product', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='persistentcacheentry',
            unique_together=set([('module', 'key')]),
        ),
        migrations.AddField(
            model_name='paymentmethod',
            name='tax_class',
            field=models.ForeignKey(verbose_name='tax class', to='shoop.TaxClass'),
        ),
        migrations.AddField(
            model_name='orderlinetax',
            name='tax',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='tax', to='shoop.Tax', related_name='order_line_taxes'),
        ),
        migrations.AddField(
            model_name='orderline',
            name='product',
            field=shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='product', blank=True, related_name='order_lines', to='shoop.Product', null=True),
        ),
        migrations.AddField(
            model_name='orderline',
            name='supplier',
            field=shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='supplier', blank=True, related_name='order_lines', to='shoop.Supplier', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='customer',
            field=shoop.core.fields.UnsavedForeignKey(to='shoop.Contact', verbose_name='customer', blank=True, related_name='customer_orders', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='payment method', blank=True, related_name='payment_orders', default=None, to='shoop.PaymentMethod', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='shipping address', blank=True, related_name='shipping_orders', to='shoop.Address', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=shoop.core.fields.UnsavedForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='shipping method', blank=True, related_name='shipping_orders', default=None, to='shoop.ShippingMethod', null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='shop',
            field=shoop.core.fields.UnsavedForeignKey(to='shoop.Shop'),
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=shoop.core.fields.UnsavedForeignKey(verbose_name='status', to='shoop.OrderStatus'),
        ),
        migrations.AddField(
            model_name='contactgroup',
            name='members',
            field=models.ManyToManyField(to='shoop.Contact', verbose_name='members', blank=True, related_name='groups'),
        ),
        migrations.AddField(
            model_name='contact',
            name='default_billing_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='billing address', blank=True, related_name='+', to='shoop.Address', null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='default_payment_method',
            field=models.ForeignKey(to='shoop.PaymentMethod', verbose_name='default payment method', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='default_shipping_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='shipping address', blank=True, related_name='+', to='shoop.Address', null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='default_shipping_method',
            field=models.ForeignKey(to='shoop.ShippingMethod', verbose_name='default shipping method', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='polymorphic_shoop.contact_set+', editable=False, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='tax_group',
            field=models.ForeignKey(to='shoop.CustomerTaxGroup', null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='shops',
            field=models.ManyToManyField(to='shoop.Shop', blank=True, related_name='categories'),
        ),
        migrations.AddField(
            model_name='category',
            name='visibility_groups',
            field=models.ManyToManyField(to='shoop.ContactGroup', verbose_name='visible for groups', blank=True, related_name='visible_categories'),
        ),
        migrations.AlterUniqueTogether(
            name='taxtranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='taxclasstranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='suppliedproduct',
            unique_together=set([('supplier', 'product')]),
        ),
        migrations.AlterUniqueTogether(
            name='shoptranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='shopproduct',
            unique_together=set([('shop', 'product')]),
        ),
        migrations.AlterUniqueTogether(
            name='shippingmethodtranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='salesunittranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='productvariationvariablevaluetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='productvariationvariablevalue',
            unique_together=set([('variable', 'identifier')]),
        ),
        migrations.AlterUniqueTogether(
            name='productvariationvariabletranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='productvariationvariable',
            unique_together=set([('product', 'identifier')]),
        ),
        migrations.AlterUniqueTogether(
            name='producttypetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='producttranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='productpackagelink',
            unique_together=set([('parent', 'child')]),
        ),
        migrations.AlterUniqueTogether(
            name='productmediatranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='productattributetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='paymentmethodtranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='orderstatustranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AddField(
            model_name='order',
            name='orderer',
            field=shoop.core.fields.UnsavedForeignKey(to='shoop.PersonContact', verbose_name='orderer', blank=True, related_name='orderer_orders', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='customertaxgrouptranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='contactgrouptranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AddField(
            model_name='companycontact',
            name='members',
            field=models.ManyToManyField(to='shoop.Contact', blank=True, related_name='company_memberships'),
        ),
        migrations.AlterUniqueTogether(
            name='categorytranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='attributetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
