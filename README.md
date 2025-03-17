# MoneyExchange API

**MoneyExchange API** is a Django-based application that provides currency exchange rates, user balance management, and transaction history. The API integrates with an external ExchangeRate API, uses JWT authentication, and is fully containerized using Docker and managed via Poetry.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation & Configuration](#installation--configuration)
- [Running the Project with Docker Compose](#running-the-project-with-docker-compose)
- [Database Migrations](#database-migrations)
- [API Endpoints](#api-endpoints)
- [Admin Panel](#admin-panel)
- [API Documentation](#api-documentation)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)

---

## Features

- **User Registration:** Create a new user account with an initial balance of 1000 coins.
- **User Balance:** Retrieve the current coin balance of the authenticated user.
- **Currency Exchange:** Retrieve the exchange rate for a given currency code (e.g., USD), decrement the user's balance by 1 coin, and store the exchange record.
- **Exchange History:** Get a list of previous currency exchange requests with optional filtering by currency code and date.
- **JWT Authentication:** Secure API endpoints using JWT tokens.
- **Interactive API Documentation:** Swagger and Redoc provide full API documentation.
- **Admin Panel:** Jazzmin-enhanced Django Admin for user and transaction management.
- **Fully Dockerized:** The entire application (including PostgreSQL) runs via Docker Compose.

---

## Requirements

- Python 3.12
- PostgreSQL
- Docker & Docker Compose
- Poetry

---

## Installation & Configuration

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/moneyexchange-api.git
   cd moneyexchange-api
   ```

2. **Configure Environment Variables:**

   Copy the provided `.env.sample` file to a new file called `.env`:

   ```bash
   cp .env.sample .env
   ```

   Edit the `.env` file and update the variables with your own values:

   ```ini
   DEBUG=True
   SECRET_KEY=your-secret-key

   # PostgreSQL settings
   POSTGRES_DB=DB
   POSTGRES_USER=USER
   POSTGRES_PASSWORD=PASSWORD
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   # API key for ExchangeRate API
   EXCHANGE_RATE_API_KEY=your-exchange-rate-api-key

   # External Exchange Rate API URL
   EXCHANGE_RATE_API_URL=https://v6.exchangerate-api.com/v6
   ```

   **Note:** In a Dockerized environment, these variables are injected into the container via Docker Compose.

---

## Running the Project with Docker Compose

To build and run the entire application (both the web service and the PostgreSQL database), use:

```bash
docker-compose up --build
```

This command will:

- Build the Docker image for the web service using the provided Dockerfile.
- Start the PostgreSQL service.
- Launch the Django development server on port `8000`.

Access the application at: [http://localhost:8000](http://localhost:8000)

---

## Database Migrations

After the containers are up, apply database migrations:

```bash
docker-compose exec web poetry run python manage.py migrate
```

If you need to create a superuser for the admin panel:

```bash
docker-compose exec web poetry run python manage.py createsuperuser
```

Follow the prompts to enter the username, email, and password.

---

## API Endpoints

### POST `/api/register/`
**Summary:** Register a new user.

**Request Body:**

```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Responses:**
- `201 Created`: User registered successfully.
- `400 Bad Request`: Validation errors.

### GET `/api/balance/`
**Summary:** Retrieve user balance.

**Responses:**
- `200 OK`: Returns the balance.
- `404 Not Found`: If the balance record is not found.

### POST `/api/currency/`
**Summary:** Get currency exchange rate.

**Request Body:**

```json
{
  "currency_code": "string"  // e.g., "USD"
}
```

**Responses:**
- `200 OK`: Success (returns the exchange record).
- `400 Bad Request`: Missing/invalid currency code or failure in retrieving the rate.
- `403 Forbidden`: Insufficient balance.
- `500 Server Error`: Error contacting the exchange rate API.

### GET `/api/history/`
**Summary:** Get exchange history.

**Query Parameters:**
- `currency_code` (string): Filter by currency code, e.g., "USD".
- `date` (string in YYYY-MM-DD format): Filter by the date of the exchange request.

**Responses:**
- `200 OK`: Returns a list of exchange records.

---

## Admin Panel

The project includes an enhanced **Django Admin Panel** powered by **Jazzmin**.

### **Access the admin panel**:

- URL: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- Login using the superuser credentials created earlier.
- Manage users, transactions, and balance records.

---

## API Documentation

Interactive API documentation is available at:

- **Swagger UI:** [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- **Redoc UI:** [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

These interfaces provide full details about each endpoint including summaries, descriptions, request/response formats, and error codes.

---

## Running Tests

The project uses `pytest` and `pytest-django` for testing.

### Run tests:

```bash
docker-compose exec web poetry run pytest
```

### Generate a coverage report:

```bash
docker-compose exec web poetry run coverage run --source=. -m pytest
docker-compose exec web poetry run coverage report
```

### Generate an HTML coverage report:

```bash
docker-compose exec web poetry run coverage html
```

Then open the `htmlcov/index.html` file in your browser.

---

## Project Structure

```markdown
moneyexchange-api/
├── api/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── test_api.py
├── moneyexchange_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .env.sample
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```