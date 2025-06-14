# Splitwise Microservices Project

This project implements a simplified Splitwise application using a microservices architecture, orchestrated with Docker Compose.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Services](#services)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the Services](#running-the-services)
  - [Accessing Services](#accessing-services)
- [Development](#development)
  - [Stopping Services](#stopping-services)
  - [Rebuilding Services](#rebuilding-services)
  - [Checking Logs](#checking-logs)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

This application aims to mimic core functionalities of a expense-sharing platform like Splitwise, broken down into independent, small services. Key features include:

* User Authentication & Authorization
* User Management (profiles, friends)
* Group Management
* Expense Tracking & Splitting
* AI-powered Splitting Suggestions (e.g., based on natural language)
* Payment Recording
* Reporting & Analytics

## Architecture

The project follows a microservices pattern, where each core functionality is encapsulated within its own service. These services communicate primarily via REST APIs (for synchronous operations) and a Message Queue (for asynchronous events). Docker Compose is used to define and run the multi-container application.

### Key Components:

* **API Gateway (Implicit):** Docker's port mapping acts as a simple gateway.
* **MongoDB:** Primary data store for all services.
* **RabbitMQ:** Message broker for inter-service communication (e.g., expense events for reporting/AI splitting).
* **Auth Service:** Handles user registration, login, and JWT token generation/validation.
* **User Service:** Manages user profiles, friend lists, and user-related queries.
* **Group Service:** Manages groups, members, and group-specific settings.
* **Expense Service:** Core service for creating, managing, and splitting expenses. Publishes events to RabbitMQ.
* **AI Splitter Service:** A background worker that consumes expense events and provides intelligent splitting suggestions.
* **Payment Service:** Handles recording of payments and settlements.
* **Reporting Service:** A background worker that consumes expense events to generate reports or aggregate data.

## Services

Here's a brief overview of each service and its exposed port (if applicable):

| Service Name          | Type           | Description                                  | Exposed Port (Host:Container) |
| :-------------------- | :------------- | :------------------------------------------- | :---------------------------- |
| `mongodb`             | Database       | MongoDB instance                             | `27017:27017`                 |
| `rabbitmq`            | Message Broker | RabbitMQ with Management UI                  | `5672:5672`, `15672:15672`    |
| `auth_service`        | API Service    | User authentication & authorization          | `8001:8000`                   |
| `user_service`        | API Service    | User profiles, friends                       | `8002:8000`                   |
| `group_service`       | API Service    | Group creation & management                  | `8003:8000`                   |
| `expense_service`     | API Service    | Expense tracking, splitting                  | `8004:8000`                   |
| `payment_service`     | API Service    | Payment recording                            | `8005:8000`                   |
| `ai_splitter_service` | Background Worker | AI-powered splitting suggestions            | (None)                        |
| `reporting_service`   | Background Worker | Data aggregation for reports               | (None)                        |

## Getting Started

Follow these steps to get the project up and running on your local machine.

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Engine and Docker Compose) installed.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/ai_splitwise.git](https://github.com/your-username/ai_splitwise.git)
    cd ai_splitwise
    ```
    (Replace `your-username/ai_splitwise.git` with your actual repository URL)

2.  **Create `.env` files:**
    Each service in the `backend/` directory requires an `.env` file for its configuration. Create these files and populate them based on the examples below. **Do NOT commit these files to Git.**

    * **`backend/auth_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/auth_db"
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars"
        JWT_ALGORITHM="HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        ```
        *Replace `your-super-secret-jwt-key...` with a strong, random key.*

    * **`backend/user_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/user_db"
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM="HS256"
        ```

    * **`backend/group_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/group_db"
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM="HS256"
        ```

    * **`backend/expense_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/expense_db"
        RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM="HS256"
        ```

    * **`backend/ai_splitter_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/expense_db" # Connects to the same DB as expense service
        RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE" # Replace with your actual Google Gemini API Key
        SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # A general secret key for internal use if needed
        ```
        *You'll need to obtain a Gemini API key from Google AI Studio.*

    * **`backend/payment_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/payment_db"
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM="HS256"
        STRIPE_SECRET_KEY="sk_test_..." # Replace with your Stripe secret key (test or live)
        STRIPE_PUBLISHABLE_KEY="pk_test_..." # Replace with your Stripe publishable key
        ```
        *You'll need Stripe API keys for this service.*

    * **`backend/reporting_service/.env`**:
        ```env
        MONGO_DB_URL="mongodb://mongodb:27017/reporting_db" # Could aggregate from other dbs
        RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
        ```

### Running the Services

From the root directory of the project (where `docker-compose.yml` is located), run:

```bash
docker compose up -d --build