from django.urls import path
from .views import RegistrationAPIView, BalanceAPIView, CurrencyExchangeAPIView, HistoryView

urlpatterns = [
    path("register/", RegistrationAPIView.as_view(), name="register"),
    path("balance/", BalanceAPIView.as_view(), name="balance"),
    path("currency/", CurrencyExchangeAPIView.as_view(), name="currency_exchange"),
    path("history/", HistoryView.as_view(), name="history"),
]
