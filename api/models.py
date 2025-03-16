from django.db import models
from django.conf import settings

class CurrencyExchange(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exchanges",
    )
    currency_code = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.currency_code} - {self.rate}"

class UserBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="balance",
    )
    balance = models.IntegerField(default=1000)

    def __str__(self):
        return f"{self.user.username} balance: {self.balance}"
