from django.db import models


# Create your models here.
class PesapalPayment(models.Model):
    merchant_reference = models.CharField(max_length=255, null=False, blank=False)
    pesapal_reference = models.CharField(max_length=255, null=True, blank=True)
    merchant_used = models.BooleanField(null=False, blank=False, default=False)
    pesapal_status = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=10)
    payment_url = models.TextField()
