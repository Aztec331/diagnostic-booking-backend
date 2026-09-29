# Diagnostic Booking Backend

FastAPI/PostgreSQL backend for diagnostic-test bookings. It provides JWT authentication, centre-specific test pricing, user-owned bookings, simulated payments, and idempotent payment webhooks.

## Tech Stack

- Backend: FastAPI
- Language: Python 3.12
- Database: PostgreSQL 16
- ORM: SQLAlchemy
- Migrations: Alembic
- Authentication: JWT
- Password Hashing: Passlib + bcrypt
- Validation: Pydantic
- Testing: Pytest + FastAPI TestClient
- Containerization: Docker + Docker Compose
- API Documentation: Swagger UI / OpenAPI

## Contents

- [System design diagram](#system-design-diagram)
- [Project structure](#project-structure)
- [Database diagram](#database-diagram)
- [API reference](#api-reference)
- [Software / request flow diagrams](#software--request-flow-diagrams)
- [Getting started](#getting-started)
- [Testing and engineering notes](#testing-and-engineering-notes)

## System Design Diagram

This is a single FastAPI application. Route handlers perform HTTP, authentication, and ownership checks; CRUD helpers use SQLAlchemy to persist to PostgreSQL. The `services/` package is present but its modules currently contain no service logic.

```mermaid
flowchart TD
  C[Client / Postman] --> A[FastAPI application]
  A --> J[JWT authentication]
  A --> R[API routes]
  J --> Q[CRUD helpers]
  R --> Q
  Q --> O[SQLAlchemy ORM]
  O --> D[(PostgreSQL)]
  P[Payment simulator] -->|POST webhook| W[/api/payments/webhook/]
  W --> E[payment_events]
  W --> PY[payments]
  W --> B[bookings]
  E --> D
  PY --> D
  B --> D
```

The application title is **Diagnostic Booking API**. Swagger UI is available at `/docs` and the OpenAPI document at `/openapi.json`.

## Project Structure

```text
diagnostic-booking-backend/
├── alembic/                 # Migration environment and revisions
├── core/                    # Settings, security, and dependencies
├── crud/                    # Database query and persistence helpers
├── models/                  # SQLAlchemy models
├── routes/                  # FastAPI route handlers
├── schemas/                 # Pydantic request schemas
├── services/                # Present; currently empty service modules
├── tests/                   # Pytest API tests
├── alembic.ini
├── constants.py
├── database.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Database Diagram

Models use foreign keys (there are no SQLAlchemy `relationship()` declarations). All columns below except generated primary keys are non-null.

```mermaid
erDiagram
  users ||--o{ bookings : creates
  diagnostic_centres ||--o{ bookings : hosts
  diagnostic_tests ||--o{ bookings : contains
  diagnostic_centres ||--o{ centre_tests : offers
  diagnostic_tests ||--o{ centre_tests : listed_in
  bookings ||--|| payments : has
  payments ||--o{ payment_events : receives
  users { int id PK string name string email UK string hashed_password }
  diagnostic_centres { int id PK string name string location }
  diagnostic_tests { int id PK string name }
  centre_tests { int id PK int centre_id FK int test_id FK decimal price }
  bookings { int id PK int user_id FK int centre_id FK int test_id FK datetime appointment_at decimal amount string status }
  payments { int id PK int booking_id FK decimal amount string status }
  payment_events { int id PK int payment_id FK string event_id UK string event_type datetime created_at }
```

| Constraint / relationship | Implementation |
|---|---|
| Users → bookings | One user has many bookings; `bookings.user_id` is a foreign key. |
| Centre/test catalogue | `centre_tests` is a many-to-many junction table and carries the centre-specific `Numeric(10,2)` price. `uq_centre_test` makes `(centre_id, test_id)` unique. |
| Booking | References user, centre, and test. `uq_duplicate_booking` covers `(user_id, centre_id, test_id, appointment_at)`. |
| Payment | `payments.booking_id` is a foreign key and uniquely constrained (`uq_payment_booking`): at most one payment per booking. |
| Payment event | `payment_events.payment_id` references payment. `event_id` is unique and indexed. |
| User e-mail | `users.email` is unique and indexed. |

## API reference

Protected routes require `Authorization: Bearer <access_token>`. FastAPI/Pydantic return `422 Unprocessable Entity` for missing required fields or invalid types/formats (including invalid e-mail and datetime input).

### Authentication

| Method | Endpoint | Auth | Body | Success | Key errors |
|---|---|---:|---|---|---|
| `POST` | `/api/auth/signup` | No | `name`, `email`, `password` | `201`, user `id/name/email` | `409` duplicate e-mail; `422` invalid input |
| `POST` | `/api/auth/login` | No | `email`, `password` | `200`, bearer `access_token` | `401` unknown e-mail/bad password; `422` invalid input |
| `GET` | `/api/auth/me` | Yes | — | `200`, current `id/name/email` | `401` missing, invalid, expired, malformed, or deleted-user token |

### Centres and tests

| Method | Endpoint | Auth | Body | Success | Key errors |
|---|---|---:|---|---|---|
| `POST` | `/api/centres/` | Yes | `name`, `location` | `201`, centre | `401`, `422` |
| `GET` | `/api/centres/` | No | — | `200`, all centres | — |
| `POST` | `/api/centres/{centre_id}/tests/` | Yes | `test_id`, `price` | `201`, mapping | `404` centre/test absent; `409` duplicate mapping |
| `GET` | `/api/centres/{centre_id}/tests/` | No | — | `200`, `{test_id, price}` mappings | Nonexistent centre returns `[]`, not `404` |
| `POST` | `/api/tests/` | Yes | `name` | `201`, test | `401`, `422` |
| `GET` | `/api/tests/` | No | — | `200`, all tests | — |

### Bookings and payments

| Method | Endpoint | Auth | Body | Success | Key errors |
|---|---|---:|---|---|---|
| `POST` | `/api/bookings/` | Yes | `centre_id`, `test_id`, `appointment_at` | `201`, `PENDING` booking | `404` unavailable centre/test pair; `409` duplicate booking |
| `GET` | `/api/bookings/` | Yes | — | `200`, caller's bookings | `401` |
| `GET` | `/api/bookings/{booking_id}` | Yes | — | `200`, caller's booking | `404` absent **or another user's** booking |
| `PATCH` | `/api/bookings/{booking_id}/cancel` | Yes | — | `200`, `{id, status: "CANCELLED"}` | `404` absent/not owned; `409` already cancelled or failed |
| `POST` | `/api/payments/` | Yes | `booking_id` | `201`, `PENDING` payment | `404` absent/not owned; `409` existing payment or booking is not `PENDING` (`Only pending bookings can be paid`) |
| `POST` | `/api/payments/webhook/` | No | `event_id`, `payment_id`, `event_type` | `200`, status update | `404` missing payment; `400` event type other than `SUCCESS`/`FAILED`; `422` invalid body |
| `GET` | `/` | No | — | `200`, running message | — |

`amount` is intentionally absent from the booking schema: the server reads it from `centre_tests` and stores it on the booking. Payments copy their amount from the booking.

A payment may be created only while its booking status is `PENDING`. `CONFIRMED`, `FAILED`, and `CANCELLED` bookings cannot be paid again; the endpoint returns `409 Conflict` with `"Only pending bookings can be paid"`.

## Software / Request Flow Diagrams

```mermaid
flowchart TD
  S[POST signup] --> SV[Validate input] --> SE{E-mail exists?}
  SE -->|Yes| S409[409 Conflict]
  SE -->|No| SH[Hash password] --> SU[Create user] --> S201[201 response]
  L[POST login] --> LF[Find user and verify password]
  LF -->|Invalid| L401[401]
  LF -->|Valid| LJ[Create expiring JWT] --> L200[200 bearer token]
  PR[Protected request] --> PT[Extract Bearer token] --> PD[Decode JWT and load user] --> PC[Continue request]
```

```mermaid
flowchart TD
  U[Authenticated user] --> R[POST /api/bookings/]
  R --> V[Validate IDs and appointment_at]
  V --> M{Centre/test mapping exists?}
  M -->|No| N[404]
  M -->|Yes| P[Read centre_tests.price]
  P --> B[Create PENDING booking; amount is server-derived]
  B --> D{Duplicate unique key?}
  D -->|Yes| C[409]
  D -->|No| OK[201 booking]
```

```mermaid
flowchart TD
  U[Authenticated user] --> R[POST /api/payments/]
  R --> B{Booking exists and belongs to caller?}
  B -->|No| N[404]
  B -->|Yes| PS{Booking status is PENDING?}
  PS -->|No| S409[409 Only pending bookings can be paid]
  PS -->|Yes| X{Payment exists?}
  X -->|Yes| C[409]
  X -->|No| P[Create PENDING payment from booking amount]
  W[Webhook] --> V[Validate payload]
  V --> E{event_id already stored?}
  E -->|Yes| AP[200 already processed]
  E -->|No| F[Find payment and booking]
  F --> T{event_type}
  T -->|SUCCESS| S[Payment SUCCESS; booking CONFIRMED]
  T -->|FAILED| Q[Payment FAILED; booking FAILED]
  T -->|Other| I[400]
  S --> PE[Store event and commit]
  Q --> PE
```

Cancellation loads the booking, returns `404` if absent or not owned, then returns `409` only for `CANCELLED` or `FAILED`. Any other current status, including `PENDING` and `CONFIRMED`, is set to `CANCELLED`.

### Appointment date/time

`appointment_at` is a Pydantic `datetime`. Send an ISO 8601 value:

```json
{
  "centre_id": 1,
  "test_id": 1,
  "appointment_at": "2030-01-10T10:30:00"
}
```

`2030-01-10` is the date, `T` separates date/time, and `10:30:00` is `HH:MM:SS`. The model/database do not explicitly define timezone semantics; agree a client convention rather than relying on implicit conversion. Do not send `amount`.

### Webhook idempotency

`event_id` must be non-empty. The handler first looks up `payment_events.event_id`; an existing event returns `200` with `Event already processed`. A new valid event changes payment/booking status, stores a `PaymentEvent`, and commits, so ordinary repeat delivery does not apply the state transition twice.

The unique `event_id` index is the persistence backstop. The handler is check-then-insert and has no locking or integrity-error recovery, so simultaneous duplicate deliveries can still race. There is also no webhook signature verification or retry mechanism.

## Getting started

### Configuration

`.env` is required and ignored by Git; no `.env.example` is included. The application reads `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM` (default `HS256`), and `ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`). Do not commit actual secrets.

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/diagnostic_booking_db
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

For the Docker API container, use `db` as the database hostname: `postgresql://postgres:postgres@db:5432/diagnostic_booking_db`.

### Docker

```bash
docker compose up --build
docker compose exec web alembic upgrade head
```

Compose starts a PostgreSQL 16 `db` service on port 5432 and the API on port 8000; migrations are not run automatically by the Dockerfile/Compose configuration. Open <http://localhost:8000>, <http://localhost:8000/docs>, or <http://localhost:8000/openapi.json>.

### Local Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

Start PostgreSQL and set a reachable local `DATABASE_URL` before migrating or running Uvicorn.

### Migrations

Alembic reads `DATABASE_URL` in `alembic/env.py` and imports all models. Apply all revisions with `alembic upgrade head`.

- `fedfa99030e7_initial_schema` creates the initial schema, foreign keys, indexes, and booking/catalogue constraints.
- `4ecea7999617_add_unique_constraint_to_payments` adds `uq_payment_booking`.

## Examples

```bash
# Sign up and log in
curl -X POST http://localhost:8000/api/auth/signup -H "Content-Type: application/json" -d '{"name":"Asha Sharma","email":"asha@example.com","password":"password123"}'
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"asha@example.com","password":"password123"}'
export TOKEN='copy-access_token-here'

# Authenticated request, centre, test, and priced catalogue entry
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/api/centres/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"City Diagnostics","location":"Bengaluru"}'
curl -X POST http://localhost:8000/api/tests/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Complete Blood Count"}'
curl -X POST http://localhost:8000/api/centres/1/tests/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"test_id":1,"price":599.00}'

# Booking and payment
curl -X POST http://localhost:8000/api/bookings/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"centre_id":1,"test_id":1,"appointment_at":"2030-01-10T10:30:00"}'
curl http://localhost:8000/api/bookings/ -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/api/payments/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"booking_id":1}'

# SUCCESS and FAILED webhook examples (use a unique event_id each time)
curl -X POST http://localhost:8000/api/payments/webhook/ -H "Content-Type: application/json" -d '{"event_id":"payment-1-success-001","payment_id":1,"event_type":"SUCCESS"}'
curl -X POST http://localhost:8000/api/payments/webhook/ -H "Content-Type: application/json" -d '{"event_id":"payment-2-failed-001","payment_id":2,"event_type":"FAILED"}'

# Cancellation is invalid after FAILED or CANCELLED
curl -X PATCH http://localhost:8000/api/bookings/1/cancel -H "Authorization: Bearer $TOKEN"
```

## Testing and engineering notes

Run tests after configuring a database and applying migrations:

```bash
pytest
```

The current automated suite contains **25 tests**. The latest verified result was **25 passed, 3 warnings**.

The test suite covers authentication, missing authentication, booking creation and duplicates, ownership boundaries, cancellation after failed payment, payment creation/duplicates, the non-`PENDING` booking payment rule, webhook success/failure, invalid payment/event input, and duplicate webhook events. It uses the configured database, so use a disposable test database to avoid development-data pollution.

### Security and scope

- Passwords use Passlib's bcrypt context; the user model stores only `hashed_password`.
- JWT signing settings are environment-derived; protected routes validate bearer tokens and resolve the current user.
- Ownership checks protect booking retrieval/cancellation and payment creation. Other-user bookings deliberately return `404` to avoid existence disclosure.
- Input validation, foreign keys, and uniqueness constraints enforce the documented invariants.
- No admin role, slot/capacity management, pagination, caching, background jobs, structured logging, rate limiting, production payment gateway, webhook retries, or enterprise security controls are implemented.

### Future improvements

Potential additions—not current features—include provider webhook signatures and retry handling, concurrency-safe idempotency, role-based catalogue administration, appointment capacity rules, pagination, rate limiting, structured logging/metrics/tracing, background processing, and real payment-provider integration.
