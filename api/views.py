from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .models import CurrencyExchange, UserBalance
from .serializers import (
    UserRegistrationSerializer,
    UserBalanceSerializer,
    CurrencyExchangeSerializer,
)
import requests
import os


class RegistrationAPIView(APIView):
    """
    API view for user registration.
    Creates a new user and automatically generates a UserBalance record.
    """
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Create a new user account with an initial balance of 1000 coins.",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response("User created", UserRegistrationSerializer),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """
        Handle POST requests for user registration.

        Expected JSON request body:
            {
                "username": "string",
                "email": "string",
                "password": "string"
            }
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class BalanceAPIView(APIView):
    """
    API view to retrieve the current balance of the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve user balance",
        operation_description="Return the current coin balance for the authenticated user.",
        responses={
            200: openapi.Response("Current balance", UserBalanceSerializer),
            404: "Balance not found"
        }
    )
    def get(self, request):
        """
        Handle GET requests to retrieve the user's balance.
        """
        try:
            balance_obj = request.user.balance
            serializer = UserBalanceSerializer(balance_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserBalance.DoesNotExist:
            return Response(
                {"error": "Balance not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class CurrencyExchangeAPIView(APIView):
    """
    API view to handle currency exchange requests.
    Retrieves the exchange rate for a given currency code, decrements the user's balance by 1 coin,
    and saves the exchange record.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get currency exchange rate",
        operation_description=(
            "Retrieve the exchange rate for a given currency code (e.g., 'USD'), "
            "decrement the user's balance by 1 coin, and store the result in the database."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "currency_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Code of the currency, e.g. 'USD'"
                ),
            },
            required=["currency_code"],
        ),
        responses={
            200: "Success",
            400: "Bad Request",
            403: "Forbidden (balance = 0)",
            500: "Server Error"
        },
    )
    def post(self, request):
        """
        Handle POST requests for currency exchange.

        Expected JSON request body:
            {
                "currency_code": "string"  # e.g., "USD"
            }
        """
        # Retrieve currency code from the request body
        currency_code = request.data.get("currency_code")
        if not currency_code:
            return Response({"error": "Currency code is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the exchange API URL and key from environment variables
        exchange_api_url = os.getenv("EXCHANGE_RATE_API_URL", "https://api.exchangerate-api.com/v4/latest")
        exchange_api_key = os.getenv("EXCHANGE_RATE_API_KEY", "")
        if not exchange_api_key:
            return Response({"error": "Exchange rate API key is not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Construct the API URL for ExchangeRate-API v6:
        # URL format: https://v6.exchangerate-api.com/v6/<API_KEY>/latest/<CURRENCY_CODE>
        api_url = f"{exchange_api_url}/{exchange_api_key}/latest/{currency_code}"
        try:
            response = requests.get(api_url)
            if response.status_code != 200:
                return Response({"error": "Failed to retrieve exchange rate."}, status=status.HTTP_400_BAD_REQUEST)
            data = response.json()
            # Retrieve the exchange rate for UAH from the conversion_rates field
            rate = data.get("conversion_rates", {}).get("UAH")
            if rate is None:
                return Response({"error": "Exchange rate for UAH not found."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error contacting exchange rate API."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check if the user has enough balance (decrement by 1 coin per request)
        balance_obj = request.user.balance
        if balance_obj.balance <= 0:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_403_FORBIDDEN)

        # Decrement the balance and save
        balance_obj.balance -= 1
        balance_obj.save()

        # Create a new CurrencyExchange record
        exchange_record = CurrencyExchange.objects.create(
            user=request.user,
            currency_code=currency_code,
            rate=rate
        )
        serializer = CurrencyExchangeSerializer(exchange_record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoryView(generics.ListAPIView):
    """
    API view to retrieve the history of currency exchange requests for the authenticated user.
    Supports optional filtering by currency code and date.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CurrencyExchangeSerializer

    @swagger_auto_schema(
        operation_summary="Get exchange history",
        operation_description=(
            "Return a list of previous currency exchange requests for the authenticated user. "
            "Optional query parameters: 'currency_code' (e.g. 'USD') and 'date' (YYYY-MM-DD)."
        ),
        manual_parameters=[
            openapi.Parameter(
                "currency_code",
                openapi.IN_QUERY,
                description="Filter by currency code, e.g. 'USD'",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "date",
                openapi.IN_QUERY,
                description="Filter by date in YYYY-MM-DD format",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve the exchange history.
        """
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return the queryset of CurrencyExchange records filtered by the authenticated user
        and optionally by currency_code and date provided as query parameters.
        """
        queryset = CurrencyExchange.objects.filter(user=self.request.user)
        currency_code = self.request.query_params.get("currency_code")
        date = self.request.query_params.get("date")
        if currency_code:
            queryset = queryset.filter(currency_code=currency_code)
        if date:
            queryset = queryset.filter(created_at__date=date)
        return queryset
