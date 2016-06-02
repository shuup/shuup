from django.db.models.signals import pre_save
from django.dispatch import receiver

from shoop.default_tax.models import TaxRule


@receiver(pre_save, sender=TaxRule)
def tax_rule_pre_save(sender, instance, **kwargs):
    """
    Set minimum and maximum postal code value

    When `TaxRule` object is being saved the object should have updated min and max values
    """
    def get_min_max(ranges):
        if "!" in ranges:
            return (None, None)
        values = [r for r in ranges.split(",")]
        all = []
        for v in values:
            pieces = v.split("-")
            all = all + pieces
        return (min(all), max(all))

    if instance.postal_codes_pattern:
        instance.postal_codes_min, instance.postal_codes_max = get_min_max(instance.postal_codes_pattern)
