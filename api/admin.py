from django.contrib import admin
from .models import CurrencyExchange, UserBalance

admin.site.register(CurrencyExchange)
admin.site.register(UserBalance)

