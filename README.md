# Chinatown

## Dockerized setup

The project now includes Docker support for:
- **frontend** (React app on port `3000`)
- **backend** (FastAPI + Socket.IO on port `8000`)
- **mongodb** (MongoDB on port `27017`)

### Prerequisites
- Docker
- Docker Compose

### Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

Then open:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api`

### Stop containers

```bash
docker compose down
```

To also remove persisted MongoDB data:

```bash
docker compose down -v
```
