from django.conf import settings
from django.db import migrations

from shuup import configuration
from shuup.core.setting_keys import (
    SHUUP_ADDRESS_HOME_COUNTRY,
    SHUUP_ALLOW_ANONYMOUS_ORDERS,
    SHUUP_ALLOW_ARBITRARY_REFUNDS,
    SHUUP_ALLOW_EDITING_ORDER,
    SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE,
    SHUUP_DEFAULT_ORDER_LABEL,
    SHUUP_DISCOUNT_MODULES,
    SHUUP_ENABLE_ATTRIBUTES,
    SHUUP_ENABLE_MULTIPLE_SHOPS,
    SHUUP_ENABLE_MULTIPLE_SUPPLIERS,
    SHUUP_HOME_CURRENCY,
    SHUUP_MANAGE_CONTACTS_PER_SHOP,
    SHUUP_ORDER_SOURCE_MODIFIER_MODULES,
    SHUUP_PRICING_MODULE,
    SHUUP_REFERENCE_NUMBER_LENGTH,
    SHUUP_REFERENCE_NUMBER_METHOD,
    SHUUP_REFERENCE_NUMBER_PREFIX,
    SHUUP_TAX_MODULE,
    SHUUP_TELEMETRY_ENABLED,
)


def move_settings_to_db(apps, schema_editor):
    configuration.set(None, SHUUP_HOME_CURRENCY, settings.SHUUP_HOME_CURRENCY)
    configuration.set(None, SHUUP_ADDRESS_HOME_COUNTRY, settings.SHUUP_ADDRESS_HOME_COUNTRY)
    configuration.set(None, SHUUP_ALLOW_ANONYMOUS_ORDERS, settings.SHUUP_ALLOW_ANONYMOUS_ORDERS)
    configuration.set(None, SHUUP_REFERENCE_NUMBER_METHOD, settings.SHUUP_REFERENCE_NUMBER_METHOD)
    configuration.set(None, SHUUP_REFERENCE_NUMBER_LENGTH, settings.SHUUP_REFERENCE_NUMBER_LENGTH)
    configuration.set(None, SHUUP_REFERENCE_NUMBER_PREFIX, settings.SHUUP_REFERENCE_NUMBER_PREFIX)
    configuration.set(None, SHUUP_DISCOUNT_MODULES, settings.SHUUP_DISCOUNT_MODULES)
    configuration.set(None, SHUUP_PRICING_MODULE, settings.SHUUP_PRICING_MODULE)
    configuration.set(None, SHUUP_ORDER_SOURCE_MODIFIER_MODULES, settings.SHUUP_ORDER_SOURCE_MODIFIER_MODULES)
    configuration.set(None, SHUUP_TAX_MODULE, settings.SHUUP_TAX_MODULE)
    configuration.set(None, SHUUP_ENABLE_ATTRIBUTES, settings.SHUUP_ENABLE_ATTRIBUTES)
    configuration.set(None, SHUUP_ENABLE_MULTIPLE_SHOPS, settings.SHUUP_ENABLE_MULTIPLE_SHOPS)
    configuration.set(None, SHUUP_ENABLE_MULTIPLE_SUPPLIERS, settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS)
    configuration.set(None, SHUUP_MANAGE_CONTACTS_PER_SHOP, settings.SHUUP_MANAGE_CONTACTS_PER_SHOP)
    configuration.set(None, SHUUP_ALLOW_EDITING_ORDER, settings.SHUUP_ALLOW_EDITING_ORDER)
    configuration.set(None, SHUUP_DEFAULT_ORDER_LABEL, settings.SHUUP_DEFAULT_ORDER_LABEL)
    configuration.set(None, SHUUP_TELEMETRY_ENABLED, settings.SHUUP_TELEMETRY_ENABLED)
    configuration.set(
        None, SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE, settings.SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE
    )
    configuration.set(None, SHUUP_ALLOW_ARBITRARY_REFUNDS, settings.SHUUP_ALLOW_ARBITRARY_REFUNDS)


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0098_change_productmedia_verbose_text"),
    ]

    operations = [migrations.RunPython(move_settings_to_db, migrations.RunPython.noop)]
