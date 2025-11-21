# Docker Deployment Guide

This guide explains how to run the Yoga Assistant using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Your Hyperbolic API key

## Quick Start

1. **Set up environment variables**

   Create a `.env` file in the project root:

   ```bash
   cp .env.template .env
   ```

   Edit `.env` and add your Hyperbolic API key:

   ```bash
   HYPERBOLIC_API_KEY=your_actual_api_key_here
   LLM_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
   TOP_K_RETRIEVAL=5
   SEARCH_MODE=hybrid
   ```

2. **Build and start all services**

   ```bash
   docker-compose up --build
   ```

   This will start three services:

   - **app**: Streamlit application (port 8501)
   - **postgres**: PostgreSQL database (port 5432)
   - **grafana**: Monitoring dashboard (port 3000)

3. **Access the application**

   - **Yoga Assistant UI**: http://localhost:8501
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin)

## Service Details

### Application (app)

- **Port**: 8501
- **Health Check**: Checks Streamlit health endpoint every 30s
- **Restart Policy**: Unless stopped manually
- **Dependencies**: Waits for PostgreSQL to be healthy before starting

### PostgreSQL (postgres)

- **Port**: 5432
- **Database**: yoga_rag
- **User**: postgres
- **Password**: yoga_password_123 (change in production!)
- **Volume**: postgres_data (persists data across restarts)

### Grafana (grafana)

- **Port**: 3000
- **Default Login**: admin/admin
- **Volume**: grafana_data (persists dashboards and settings)

## Common Commands

### Start services in background

```bash
docker-compose up -d
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f grafana
```

### Stop services

```bash
docker-compose down
```

### Stop and remove volumes (WARNING: deletes all data)

```bash
docker-compose down -v
```

### Rebuild application after code changes

```bash
docker-compose up --build app
```

### Reset database

```bash
# Stop services
docker-compose down

# Remove only postgres volume
docker volume rm yoga-assistant-knowledge-rag_postgres_data

# Start again
docker-compose up
```

## Troubleshooting

### Application fails to start

1. Check if PostgreSQL is ready:

   ```bash
   docker-compose logs postgres
   ```

2. Check application logs:

   ```bash
   docker-compose logs app
   ```

3. Verify environment variables:
   ```bash
   docker-compose config
   ```

### Database connection errors

- Ensure PostgreSQL service is healthy:

  ```bash
  docker-compose ps
  ```

- The app service waits for PostgreSQL health check to pass before starting

### Port conflicts

If ports 8501, 5432, or 3000 are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - '8502:8501' # Change host port (left side)
```

### API key not working

- Verify `.env` file exists and contains valid API key
- Check that `.env` is mounted in docker-compose.yml
- Restart services after changing `.env`:
  ```bash
  docker-compose restart app
  ```

## Development Workflow

### Local development with Docker database

Run only PostgreSQL and Grafana in Docker, run app locally:

```bash
# Start only database and grafana
docker-compose up postgres grafana

# In another terminal, run app locally
streamlit run yoga_assistant/app.py
```

### Testing changes

1. Make code changes
2. Rebuild and restart:
   ```bash
   docker-compose up --build app
   ```

## Production Considerations

1. **Change default passwords** in docker-compose.yml:

   - PostgreSQL password
   - Grafana admin password

2. **Use secrets management** instead of .env file:

   - Docker secrets
   - Environment variable injection from CI/CD

3. **Configure resource limits**:

   ```yaml
   app:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
   ```

4. **Use production-grade PostgreSQL**:

   - External managed database (AWS RDS, Google Cloud SQL)
   - Proper backup strategy
   - Connection pooling

5. **Enable HTTPS**:
   - Use reverse proxy (nginx, traefik)
   - SSL certificates (Let's Encrypt)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐ │
│  │              │    │              │    │          │ │
│  │  Streamlit   │───▶│  PostgreSQL  │◀───│ Grafana  │ │
│  │     App      │    │   Database   │    │Dashboard │ │
│  │              │    │              │    │          │ │
│  └──────┬───────┘    └──────────────┘    └────┬─────┘ │
│         │                                      │       │
└─────────┼──────────────────────────────────────┼───────┘
          │                                      │
          ▼                                      ▼
     Port 8501                              Port 3000
```

## Data Persistence

Two volumes are created for data persistence:

- `postgres_data`: Database files
- `grafana_data`: Grafana configuration and dashboards

These volumes persist even when containers are stopped or removed (unless you use `docker-compose down -v`).
