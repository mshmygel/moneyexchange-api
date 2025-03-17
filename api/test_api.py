import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from api.models import UserBalance, CurrencyExchange


@pytest.fixture
def api_client():
    """
    Returns an instance of APIClient.
    """
    return APIClient()


@pytest.fixture
def create_user(db):
    """
    Create and return a test user with an initial balance of 10 coins.
    """
    user = User.objects.create_user(
        username="jwtuser",
        email="jwt@example.com",
        password="testpass123"
    )
    UserBalance.objects.create(user=user, balance=10)
    return user


@pytest.fixture
def jwt_auth_client(api_client, create_user):
    """
    Obtain JWT tokens for the test user and set the Authorization header
    in the APIClient.
    """
    token_url = reverse("token_obtain_pair")
    response = api_client.post(token_url, {"username": "jwtuser", "password": "testpass123"}, format="json")
    assert response.status_code == status.HTTP_200_OK, f"Token request failed: {response.json()}"
    access_token = response.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def fake_exchange_response(monkeypatch):
    """
    Monkeypatch the requests.get call in the api.views module to return
    a fake response with conversion_rates.
    """

    def fake_get(url):
        class FakeResponse:
            status_code = 200

            def json(self):
                # Return a fake conversion rate for UAH (e.g., 40.0)
                return {"conversion_rates": {"UAH": 40.0}}

        return FakeResponse()

    monkeypatch.setattr("api.views.requests.get", fake_get)


def test_registration(api_client, db):
    """
    Test the registration endpoint to ensure a user and balance record are created.
    """
    url = reverse("register")
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpass123"
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Verify that the user is created
    user = User.objects.get(username="newuser")
    assert user is not None

    # Verify that a UserBalance record is created with default balance 1000
    balance = UserBalance.objects.get(user=user)
    assert balance.balance == 1000


def test_balance(jwt_auth_client, create_user):
    """
    Test the balance retrieval endpoint for the authenticated user via JWT.
    """
    url = reverse("balance")
    response = jwt_auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert "balance" in json_data
    # The test user is created with an initial balance of 10 coins.
    assert json_data["balance"] == 10


def test_currency_exchange(jwt_auth_client, fake_exchange_response, create_user):
    """
    Test the currency exchange endpoint with a mocked external API.
    Verifies that the user's balance is decremented by 1 and an exchange record is created.
    """
    url = reverse("currency_exchange")
    data = {"currency_code": "USD"}
    response = jwt_auth_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    # Verify that the user's balance decreased by 1 coin (from 10 to 9)
    user = User.objects.get(username="jwtuser")
    balance = UserBalance.objects.get(user=user)
    assert balance.balance == 9

    # Verify that an exchange record is created and returns the correct data
    json_data = response.json()
    assert "id" in json_data
    assert json_data["currency_code"] == "USD"
    # Check that the returned rate matches the fake response (could be string or float)
    assert json_data["rate"] in ["40.0", "40.0000", 40.0]


def test_history(jwt_auth_client, create_user):
    """
    Test the history endpoint to retrieve exchange records for the authenticated user.
    Also tests filtering by currency code.
    """
    # Create an exchange record for testing history
    user = User.objects.get(username="jwtuser")
    CurrencyExchange.objects.create(user=user, currency_code="USD", rate=40.0)
    url = reverse("history")

    # Retrieve all history records for the user
    response = jwt_auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert len(json_data) >= 1

    # Test filtering by currency_code query parameter
    url_with_params = f"{url}?currency_code=USD"
    response_param = jwt_auth_client.get(url_with_params)
    assert response_param.status_code == status.HTTP_200_OK
    filtered_data = response_param.json()
    assert len(filtered_data) >= 1
