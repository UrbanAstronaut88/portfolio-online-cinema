# 🎬 Online Cinema API

**Online Cinema API** is a backend application built with **FastAPI** that implements a full online cinema workflow —  
from browsing the movie catalog to ordering, payments, and webhook processing.

The project is designed as a **production-ready backend service** with authentication, role-based access, testing, documentation, and modern DevOps practices.

---

##  Key Features

- JWT-based authentication and authorization
- Role-based access control (**USER / MODERATOR / ADMIN**)
- Movie catalog management (movies, genres, certifications)
- Shopping cart
- Orders lifecycle
- Payments and refunds (Stripe integration)
- Stripe webhook processing (real + mock mode)
- Email notifications
- Full test coverage
- Poetry for dependency management
- Docker & Docker Compose support
- CI/CD with GitHub Actions
- Complete Swagger / OpenAPI documentation (v3.0)

---

##  Project Architecture

- **FastAPI** — REST API framework
- **SQLAlchemy (async)** — ORM
- **PostgreSQL** — production database
- **SQLite** — test database
- **Stripe** — payment processing
- **Docker & Docker Compose** — containerization
- **Poetry** — dependency and environment management
- **Pytest** — automated testing
- **GitHub Actions** — CI/CD pipelines

---

##  User Roles

| Role       | Capabilities |
|------------|-------------|
| USER       | Browse movies, manage cart, create orders |
| MODERATOR  | Manage movies, payments |
| ADMIN      | Full access, user & role management |

---

##  Swagger / OpenAPI Documentation

The API is fully documented using **OpenAPI 3.0** (Swagger).

Each endpoint includes:
- clear `summary` and `description`
- request and response schemas
- query and path parameters
- possible HTTP responses
- role-based access restrictions

###  Access Control for Documentation
Swagger UI access can be restricted to authorized users only  
(using FastAPI configuration or middleware).

---

##  Testing & Coverage

### 🛠 Tools Used
- `pytest`
- `pytest-asyncio`
- `httpx.AsyncClient`
- `coverage`

###  Covered Modules

| Module | Covered Functionality |
|------|----------------------|
| Auth | registration, login, password reset/change |
| Movies | CRUD operations, filters, role restrictions |
| Certifications | creation (ADMIN only) |
| Cart | add / remove / clear |
| Orders | create, cancel, list |
| Payments | create, refund, mock success |
| Webhooks | mock Stripe webhook |
| Users | admin-only users list |

✅ Successful scenarios and error cases  
✅ Role and permission checks  
✅ Tests do **not** affect production database  

---

## 🐳 Docker & Docker Compose

### Services (planned / supported)
- FastAPI
- PostgreSQL
- Redis
- Celery
- MinIO

### ▶️ Run the project with a single command
```bash
docker-compose up --build
