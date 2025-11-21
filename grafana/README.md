# Grafana Monitoring Setup

This directory contains the Grafana dashboard configuration and initialization scripts for the Yoga RAG System.

![Grafana Dashboard](../assets/grafana_dashboard.png)

## Files

- `dashboard.json` - Grafana dashboard configuration with 7 panels
- `init.py` - Initialization script to set up datasource and import dashboard
- `test_dashboard.py` - Test script to generate sample data and verify queries

## Dashboard Panels

The monitoring dashboard includes:

1. **Recent Conversations Table** - Last 10 conversations with timestamps, questions, answers, and feedback
2. **User Feedback Distribution** - Pie chart showing positive vs negative feedback
3. **Relevance Score** - Gauge showing percentage of RELEVANT responses
4. **Model Usage Distribution** - Bar chart showing which LLM models are being used
5. **LLM Cost Over Time** - Time series tracking spending
6. **Token Usage Over Time** - Time series monitoring token consumption
7. **Response Time Over Time** - Time series tracking latency

## Setup Instructions

### 1. Start Services

Start PostgreSQL and Grafana using docker-compose:

```bash
docker-compose up -d postgres grafana
```

Wait for services to be healthy (about 30 seconds).

### 2. Initialize Database

Make sure the database schema is created:

```bash
python yoga_assistant/db_prep.py
```

### 3. Generate Test Data (Optional)

Generate sample conversations to test the dashboard:

```bash
python grafana/test_dashboard.py
```

This will:

- Create 20 sample conversations
- Add realistic feedback and metrics
- Verify all dashboard queries work

### 4. Initialize Grafana

Run the initialization script to set up the datasource and import the dashboard:

```bash
python grafana/init.py
```

This will:

- Wait for Grafana to be ready
- Create a PostgreSQL datasource
- Import the monitoring dashboard
- Verify the setup

### 5. Access Dashboard

Open your browser and navigate to:

```
http://localhost:3000/d/yoga-rag-dashboard
```

Default credentials:

- Username: `admin`
- Password: `admin`

## Environment Variables

The initialization script uses these environment variables:

### Grafana Configuration

- `GRAFANA_URL` - Grafana URL (default: http://localhost:3000)
- `GRAFANA_USER` - Admin username (default: admin)
- `GRAFANA_PASSWORD` - Admin password (default: admin)

### PostgreSQL Configuration

- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_DB` - Database name (default: yoga_rag)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password (required)

## Troubleshooting

### Grafana not starting

Check if the service is running:

```bash
docker-compose ps grafana
```

View logs:

```bash
docker-compose logs grafana
```

### Dashboard not showing data

1. Verify database has data:

```bash
python grafana/test_dashboard.py
```

2. Check datasource connection in Grafana:

   - Go to Configuration → Data Sources
   - Click on "Yoga RAG PostgreSQL"
   - Click "Test" button

3. Verify queries in dashboard:
   - Open dashboard
   - Click on panel title → Edit
   - Check query syntax

### Connection refused errors

Make sure services are running and healthy:

```bash
docker-compose ps
```

**Important**: When Grafana runs in Docker, it needs to connect to PostgreSQL using the Docker service name `postgres` instead of `localhost`. The init script automatically handles this by converting `localhost` to `postgres` for the datasource URL.

If you manually created the datasource with `localhost:5432`, update it to use `postgres:5432` instead.

## Manual Dashboard Import

If the init script fails, you can manually import the dashboard:

1. Open Grafana at http://localhost:3000
2. Login with admin/admin
3. Go to Dashboards → Import
4. Click "Upload JSON file"
5. Select `grafana/dashboard.json`
6. Select the PostgreSQL datasource
7. Click "Import"

## Customization

To modify the dashboard:

1. Edit panels in Grafana UI
2. Export the dashboard:
   - Dashboard settings → JSON Model
   - Copy JSON
3. Save to `dashboard.json`
4. Commit changes to version control

## Production Deployment

For production deployments:

1. Change default Grafana password
2. Use environment variables for credentials
3. Enable HTTPS for Grafana
4. Set up proper authentication (LDAP, OAuth, etc.)
5. Configure alerting for critical metrics
6. Set up regular backups of Grafana data

## Metrics Tracked

The dashboard tracks these key metrics:

- **Conversations**: Total queries processed
- **Feedback**: User satisfaction (thumbs up/down)
- **Relevance**: Quality of generated answers
- **Cost**: LLM API spending
- **Tokens**: Token consumption per query
- **Response Time**: Latency metrics
- **Model Usage**: Which models are being used

These metrics help monitor system performance and identify areas for improvement.
