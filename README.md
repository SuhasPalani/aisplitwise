# AI-Powered Expense Splitter: A Microservices Ecosystem


[![Built with FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://react.dev/)
[![Kubernetes Deployment](https://img.shields.io/badge/Orchestration-Kubernetes-326CE5.svg)](https://kubernetes.io/)

This project implements a sophisticated AI-powered expense-sharing platform, akin to Splitwise, built upon a robust microservices architecture. It demonstrates modern full-stack development practices, distributed system design, and cloud-native deployment using Docker and Kubernetes.

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [System Design](#system-design)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development with Docker Compose](#local-development-with-docker-compose)
  - [Deployment to Kubernetes](#deployment-to-kubernetes)
- [API Documentation (Postman)](#api-documentation-postman)
- [Frontend Usage](#frontend-usage)
- [Development Workflow](#development-workflow)
  - [Stopping Services](#stopping-services)
  - [Rebuilding Services](#rebuilding-services)
  - [Checking Logs](#checking-logs)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

This application meticulously mimics core functionalities of an expense-sharing platform like Splitwise, but with an enhanced, AI-driven dimension for intelligent expense distribution. The system is designed as a collection of independent, collaborating microservices, ensuring high scalability, maintainability, and fault tolerance. From user authentication to complex expense splitting and detailed reporting, every aspect is handled by dedicated services.

## Key Features

* **Comprehensive User Management:** Secure registration, authentication (JWT), profile management, and friend relationships.
* **Dynamic Group Management:** Create, join, and manage groups for shared expenses.
* **Intuitive Expense Tracking:** Record, categorize, and manage expenses within groups or with friends.
* **AI-Powered Splitting:** Leverage the `ai-splitter-service` for intelligent suggestions on how to divide costs based on natural language input.
* **Streamlined Payment Recording:** Log payments and manage settlements efficiently.
* **Financial Reporting & Analytics:** Generate insights and summaries of spending patterns.
* **Distributed Architecture:** Robust inter-service communication via REST APIs and a message broker (RabbitMQ).
* **Containerized Deployment:** All services are containerized using Docker for consistency across environments.
* **Cloud-Native Orchestration:** Full deployment and management using Kubernetes for production-grade environments.

## Architecture

The project adheres to a microservices architectural pattern, where each core business capability is encapsulated within its own loosely coupled service. Communication between services primarily occurs through RESTful APIs for synchronous operations and a robust Message Queue (RabbitMQ) for asynchronous event-driven interactions (e.g., notifying reporting or AI services about new expenses). Data is persisted in MongoDB, with each service maintaining its own dedicated database for autonomy.

### Key Components and Interactions:

* **Frontend (React/TypeScript):** The user interface, interacting with the backend services via a central API Gateway (Kubernetes Ingress).
* **API Services (FastAPI):**
    * **Auth Service:** Manages user authentication, registration, and JWT token issuance.
    * **User Service:** Handles user profiles, friend lists, and friend requests.
    * **Group Service:** Manages group creation, membership, and settings.
    * **Expense Service:** Core service for creating, updating, and querying expenses. Publishes `expense_created` events to RabbitMQ.
    * **Payment Service:** Facilitates recording of payments and settlements. Publishes `payment_processed` events to RabbitMQ.
* **Background Workers (FastAPI):**
    * **AI Splitter Service:** Subscribes to `expense_created` events, processes expense details using the Gemini AI API, and might update the expense with intelligent splitting suggestions or notify users.
    * **Reporting Service:** Subscribes to `expense_created` and `payment_processed` events to aggregate data and generate financial reports.
* **Data Stores:**
    * **MongoDB:** The primary NoSQL database, with each service typically having its own database or collection for strong data separation.
* **Message Broker:**
    * **RabbitMQ:** Enables asynchronous communication between services, facilitating event-driven workflows and ensuring decoupling.
* **Containerization & Orchestration:**
    * **Docker:** Used to containerize each service for consistent runtime environments.
    * **Docker Compose:** For easy local development and testing of the entire microservices stack.
    * **Kubernetes:** The production-grade container orchestration platform, handling deployment, scaling, load balancing, and self-healing of the microservices.
    * **Kubernetes Ingress:** Acts as the API Gateway, routing external HTTP/HTTPS traffic to the appropriate backend services based on defined rules.

## Services

Here's a detailed overview of each service, its location, and exposed ports:

| Service Name          | Location                      | Type              | Description                                                          | Exposed Port (Host:Container) (Docker Compose) | Kubernetes Service Port | Ingress Path (Kubernetes) |
| :-------------------- | :---------------------------- | :---------------- | :------------------------------------------------------------------- | :--------------------------------------------- | :---------------------- | :------------------------ |
| `mongodb`             | `docker-compose.yml`, `kubernetes/mongodb` | Database          | MongoDB instance for data persistence                                | `27017:27017`                                  | `27017`                 | N/A                       |
| `rabbitmq`            | `docker-compose.yml`, `kubernetes/rabbitmq` | Message Broker    | RabbitMQ with Management UI for async communication                  | `5672:5672`, `15672:15672`                     | `5672`, `15672`         | N/A                       |
| `auth_service`        | `backend/auth_service`        | API Service       | Handles user authentication, registration, and JWT validation.       | `8001:8000`                                    | `8001`                  | `/auth`                   |
| `user_service`        | `backend/user_service`        | API Service       | Manages user profiles, friend lists, and friend requests.            | `8002:8000`                                    | `8002`                  | `/users`                  |
| `group_service`       | `backend/group_service`       | API Service       | Manages group creation, membership, and group-specific settings.     | `8003:8000`                                    | `8003`                  | `/groups`                 |
| `expense_service`     | `backend/expense_service`     | API Service       | Core service for creating, managing, and splitting expenses.         | `8004:8000`                                    | `8004`                  | `/expenses`               |
| `payment_service`     | `backend/payment_service`     | API Service       | Handles recording of payments, settlements, and integrates with Stripe. | `8005:8000`                                    | `8005`                  | `/payments`               |
| `ai_splitter_service` | `backend/ai_splitter_service` | Background Worker | Consumes expense events, provides intelligent splitting suggestions using Gemini AI. | (None)                                         | `8006`                  | `/ai`                     |
| `reporting_service`   | `backend/reporting_service`   | Background Worker | Consumes expense and payment events to generate reports/analytics.   | (None)                                         | `8007`                  | `/reports`                |
| `frontend`            | `frontend/`                   | Frontend          | React/TypeScript application for user interaction.                   | `5173:5173` (Vite Dev)                         | `80` (Nginx/Proxy)      | `/`                       |

## Technology Stack

* **Backend:**
    * **Framework:** FastAPI (Python)
    * **Database:** MongoDB (NoSQL)
    * **Message Broker:** RabbitMQ
    * **AI:** Google Gemini API
    * **Payments:** Stripe API (via `payment_service`)
    * **Authentication:** JWT (JSON Web Tokens)
* **Frontend:**
    * **Framework:** React (TypeScript)
    * **Build Tool:** Vite
    * **Styling:** Tailwind CSS
    * **Routing:** React Router DOM
    * **HTTP Client:** Axios
* **Containerization & Orchestration:**
    * **Docker**
    * **Docker Compose** (for local development)
    * **Kubernetes** (for deployment)
 
## System Design
![image](https://github.com/user-attachments/assets/f07ae583-1c19-4c95-aa8b-34c4588ab26a)

## Getting Started

Follow these steps to get the project up and running.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Git:** For cloning the repository.
* **Docker Desktop:** (Includes Docker Engine and Docker Compose) - [Download](https://www.docker.com/products/docker-desktop/)
* **Python 3.10+:** For backend development (if running services outside Docker).
* **Node.js 18+ & npm/yarn:** For frontend development - [Download](https://nodejs.org/en/download)
* **kubectl:** Kubernetes command-line tool - [Installation Guide](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
* **A Kubernetes Cluster:**
    * **Local:** [Minikube](https://minikube.sigs.k8s.io/docs/start/) (recommended for local development)
    * **Cloud:** GKE, EKS, AKS, etc.
* **Kubernetes Ingress Controller:** (e.g., NGINX Ingress Controller, essential for external access to services) - [Installation Guide](https://kubernetes.github.io/ingress-nginx/deploy/)

### Local Development with Docker Compose

This method allows you to run all backend services and infrastructure (MongoDB, RabbitMQ) locally using Docker Compose, while you can run the frontend development server separately.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/ai-splitwise-clone.git](https://github.com/your-username/ai-splitwise-clone.git)
    cd ai-splitwise-clone
    ```
    (Replace `your-username/ai-splitwise-clone.git` with your actual repository URL)

2.  **Create `.env` files for Backend Services:**
    Each service in the `backend/` directory requires an `.env` file for its configuration. Create these files within each service directory (e.g., `backend/auth_service/.env`). **These files should be in your `.gitignore` and not committed to source control.**

    **Important Note:** The `JWT_SECRET_KEY` **must be identical** across `auth_service`, `user_service`, `group_service`, `expense_service`, and `payment_service` for token validation to work. Choose a strong, random key.

    * **`backend/auth_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/auth_db
        SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars"
        ALGORITHM=HS256
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        ```
    * **`backend/user_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/user_db
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM=HS256
        ```
    * **`backend/group_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/group_db
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM=HS256
        ```
    * **`backend/expense_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/expense_db
        RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM=HS256
        ```
    * **`backend/ai_splitter_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/expense_db # Connects to the same DB as expense service for expense details
        RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
        GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY_HERE" # Get from Google AI Studio
        SECRET_KEY="your-general-internal-service-secret-key" # Can be different from JWT_SECRET_KEY
        ```
    * **`backend/payment_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/payment_db
        RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
        JWT_SECRET_KEY="your-super-secret-jwt-key-that-is-long-and-random-at-least-32-chars" # MUST MATCH AUTH_SERVICE
        JWT_ALGORITHM=HS256
        STRIPE_SECRET_KEY="sk_test_..." # Your Stripe secret key (e.g., sk_test_xxxxxxxxxxxxxxxxxxxxxxxx)
        STRIPE_PUBLISHABLE_KEY="pk_test_..." # Your Stripe publishable key (e.g., pk_test_xxxxxxxxxxxxxxxxxxxxxxxx)
        ```
    * **`backend/reporting_service/.env`**:
        ```env
        MONGO_DB_URL=mongodb://mongodb:27017/reporting_db # Or point to expense/payment dbs directly
        RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
        ```
    * **`frontend/.env.local`**: (for local frontend environment variables, e.g., if you have a different API base URL for dev)
        ```env
        VITE_API_BASE_URL=http://localhost:8000 # Example, adjust if you're hitting Docker ports directly
        ```

3.  **Run Backend Services with Docker Compose:**
    From the root directory of the project, execute:
    ```bash
    docker compose up -d --build
    ```
    This command will:
    * Build Docker images for all your backend services (FastAPI applications).
    * Download images for MongoDB and RabbitMQ.
    * Start all containers in detached mode (`-d`).
    * You can verify services are running using `docker compose ps`.

4.  **Install Frontend Dependencies:**
    Navigate into the `frontend/` directory and install Node.js dependencies:
    ```bash
    cd frontend/
    npm install # or yarn install
    ```

5.  **Start Frontend Development Server:**
    From the `frontend/` directory:
    ```bash
    npm run dev # or yarn dev
    ```
    This will start the React development server, typically at `http://localhost:5173`. The frontend will communicate with your backend services via the Docker Compose network (or Kubernetes Ingress if configured for local K8s development).

### Deployment to Kubernetes

This section outlines how to deploy your microservices to a Kubernetes cluster.

1.  **Build and Push Docker Images:**
    For each service in the `backend/` directory, you need to build its Docker image and push it to a container registry (e.g., Docker Hub, Google Container Registry, GitLab Container Registry). Replace `your_docker_username` with your actual Docker Hub username or registry path.

    ```bash
    # Example for auth_service
    docker build -t your_docker_username/auth-service:latest backend/auth_service
    docker push your_docker_username/auth-service:latest

    # Repeat for user_service, group_service, expense_service, ai_splitter_service, payment_service, reporting_service
    # And for your frontend if you are serving it from Kubernetes (e.g., with Nginx)
    # docker build -t your_docker_username/frontend:latest frontend/
    # docker push your_docker_username/frontend:latest
    ```
    **Remember to update the `image:` fields in all Kubernetes deployment YAMLs (`kubernetes/*/deployment.yaml`) to point to your pushed images.**

2.  **Configure Kubernetes Secrets and ConfigMaps:**
    Kubernetes handles sensitive data (API keys, passwords) via `Secrets` and non-sensitive configurations via `ConfigMaps`.

    * **`kubernetes/namespace.yaml`**: Creates a dedicated namespace.
        ```bash
        kubectl apply -f kubernetes/namespace.yaml
        ```
    * **`kubernetes/configmap.yaml`**: Populates common configurations.
        ```bash
        kubectl apply -f kubernetes/configmap.yaml
        ```
    * **`kubernetes/secrets.yaml`**: **This file contains sensitive data. Base64 encode your actual values.**
        **Example Encoding:** `echo -n "your_secret_value" | base64`
        ```yaml
        # Example for JWT_SECRET_KEY (replace with your actual base64 encoded value)
        JWT_SECRET_KEY: VmY5MWpaQHI1dSVGcUshM3hObXpUI0w2eVc4ZVpiOVFTQzFwTzdSZw==
        # Example for MONGO_ROOT_PASSWORD
        MONGO_ROOT_PASSWORD: <base64-encoded-mongo-root-password>
        # Example for GEMINI_API_KEY
        GEMINI_API_KEY: <base64-encoded-gemini-api-key>
        # ... and so on for all secrets
        ```
        ```bash
        kubectl apply -f kubernetes/secrets.yaml
        ```

3.  **Deploy Core Infrastructure (MongoDB & RabbitMQ):**
    Deploy the database and message broker first, and wait for them to be ready.
    ```bash
    kubectl apply -f kubernetes/mongodb/service.yaml
    kubectl apply -f kubernetes/mongodb/persistentvolumeclaim.yaml
    kubectl apply -f kubernetes/mongodb/deployment.yaml # This is a StatefulSet

    kubectl apply -f kubernetes/rabbitmq/service.yaml
    kubectl apply -f kubernetes/rabbitmq/deployment.yaml # This is a StatefulSet (includes PVC)

    # Monitor until pods are running and ready (e.g., 1/1 READY)
    echo "Waiting for MongoDB and RabbitMQ to be ready..."
    kubectl wait --for=condition=Ready pod -l app=mongodb -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=rabbitmq -n splitwise-dev --timeout=300s
    ```

4.  **Deploy Microservices:**
    Deploy each of your FastAPI microservices.
    ```bash
    kubectl apply -f kubernetes/auth-service/service.yaml
    kubectl apply -f kubernetes/auth-service/deployment.yaml
    kubectl apply -f kubernetes/user-service/service.yaml
    kubectl apply -f kubernetes/user-service/deployment.yaml
    kubectl apply -f kubernetes/group-service/service.yaml
    kubectl apply -f kubernetes/group-service/deployment.yaml
    kubectl apply -f kubernetes/expense-service/service.yaml
    kubectl apply -f kubernetes/expense-service/deployment.yaml
    kubectl apply -f kubernetes/ai-splitter-service/service.yaml
    kubectl apply -f kubernetes/ai-splitter-service/deployment.yaml
    kubectl apply -f kubernetes/payment-service/service.yaml
    kubectl apply -f kubernetes/payment-service/deployment.yaml
    kubectl apply -f kubernetes/reporting-service/service.yaml
    kubectl apply -f kubernetes/reporting-service/deployment.yaml

    # Monitor until pods are running and ready
    echo "Waiting for microservices to be ready..."
    kubectl wait --for=condition=Ready pod -l app=auth-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=user-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=group-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=expense-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=ai-splitter-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=payment-service -n splitwise-dev --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=reporting-service -n splitwise-dev --timeout=300s
    ```
    (Add `kubectl apply -f kubernetes/frontend/` if you containerized and deployed your frontend as well).

5.  **Deploy Ingress:**
    Ensure you have an Ingress Controller installed in your cluster (e.g., NGINX Ingress Controller).
    ```bash
    kubectl apply -f kubernetes/ingress.yaml
    ```
    To access the application locally using the Ingress, you may need to map the Ingress IP to `splitwise.local` in your hosts file (`/etc/hosts` on Linux/macOS, `C:\Windows\System32\drivers\etc\hosts` on Windows):
    * Get Ingress IP:
        * **Minikube:** `minikube ip` (then use this IP in hosts file)
        * **Cloud:** `kubectl get ingress splitwise-ingress -n splitwise-dev` (look for the `ADDRESS` column).
    * Add to hosts file (example):
        ```
        <YOUR_INGRESS_IP> splitwise.local
        ```

### Accessing Services

* **Frontend (Local Dev):** Typically at `http://localhost:5173` (from `npm run dev`).
* **Backend API (Local Dev with Docker Compose):**
    * Auth Service: `http://localhost:8001`
    * User Service: `http://localhost:8002`
    * ...and so on for other API services.
* **RabbitMQ Management UI (Local Dev):** `http://localhost:15672` (default guest/guest)
* **Application (Kubernetes Deployment):** Access via your configured Ingress host, e.g., `http://splitwise.local` for the frontend, and API calls will use `http://splitwise.local/auth`, `http://splitwise.local/users`, etc.

## API Documentation (Postman)

A Postman collection with example requests for all services will be provided (or is located in `docs/postman_collection.json`).
* Ensure your Postman environment's base URLs are configured correctly (e.g., `http://localhost:8001` for local, or `http://splitwise.local/auth` for Kubernetes).

## Frontend Usage

Once the frontend development server is running or deployed to Kubernetes and accessible, you can interact with the application:

1.  **Signup:** Navigate to `/signup` to create a new user account.
2.  **Login:** Use your credentials to log in.
3.  **Explore:** After successful login, you'll be redirected to the home page. Navigate through the various sections (Profile, Groups, Expenses, Payments, Reports) to explore the functionalities.

## Development Workflow

### Stopping Services (Docker Compose)

To stop all running Docker containers:
```bash
docker compose down
