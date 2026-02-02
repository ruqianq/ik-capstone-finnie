# FinnIE Deployment Guide

## Prerequisites

Before deploying FinnIE, ensure you have:

1. **Docker** and **Docker Compose** installed
   - Docker: https://docs.docker.com/get-docker/
   - Docker Compose: https://docs.docker.com/compose/install/

2. **Google API Key** for GenAI
   - Get your API key from: https://aistudio.google.com/app/apikey

## Local Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/ruqianq/ik-capstone-finnie.git
cd ik-capstone-finnie
```

### Step 2: Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

### Step 3: Start the Services

Build and start all services using Docker Compose:

```bash
docker compose up --build
```

Or run in detached mode:

```bash
docker compose up --build -d
```

### Step 4: Verify Deployment

Once the services are running, verify they are accessible:

1. **API Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Phoenix Dashboard:**
   Open http://localhost:6006 in your browser

3. **API Documentation:**
   Open http://localhost:8000/docs in your browser

## Service Endpoints

- **FinnIE API**: http://localhost:8000
- **Phoenix Dashboard**: http://localhost:6006
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## Testing the API

### 1. Using cURL

```bash
# Check available agents
curl http://localhost:8000/agents

# Submit a financial query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How should I budget my $5000 monthly income?",
    "user_id": "user123"
  }'
```

### 2. Using Python

```python
import requests

# Query the FinnIE API
response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "What investment options are best for beginners?",
        "user_id": "user123"
    }
)

result = response.json()
print(f"Query routed to: {result['routed_to']}")
print(f"Response: {result['response']}")
```

### 3. Using the Swagger UI

Open http://localhost:8000/docs and use the interactive API documentation.

## Monitoring and Observability

### Phoenix Dashboard

The Phoenix dashboard provides:

- **Real-time Tracing**: View the flow of requests through agents
- **Performance Metrics**: Monitor response times and throughput
- **Error Tracking**: Identify and debug issues
- **Agent Analytics**: See which agents handle what queries

Access it at: http://localhost:6006

## Stopping the Services

To stop all services:

```bash
docker compose down
```

To stop and remove volumes:

```bash
docker compose down -v
```

## Troubleshooting

### Issue: Services won't start

**Solution:**
1. Check if ports 8000 and 6006 are available:
   ```bash
   netstat -an | grep -E "8000|6006"
   ```
2. If ports are in use, update the port mappings in `docker-compose.yml`

### Issue: API returns 503 errors

**Solution:**
1. Verify the Google API key is correctly set in `.env`
2. Check service logs:
   ```bash
   docker compose logs finnie
   ```

### Issue: Phoenix dashboard is not accessible

**Solution:**
1. Wait for the Phoenix service to become healthy:
   ```bash
   docker compose ps
   ```
2. Check Phoenix logs:
   ```bash
   docker compose logs phoenix
   ```

### Issue: Permission denied errors

**Solution:**
Run with sudo or add your user to the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Logs and Debugging

View logs for all services:
```bash
docker compose logs -f
```

View logs for a specific service:
```bash
docker compose logs -f finnie
docker compose logs -f phoenix
```

## Updating the Deployment

To update with the latest code:

```bash
git pull
docker compose down
docker compose up --build
```

## Production Considerations

For production deployment, consider:

1. **Security:**
   - Use secrets management (e.g., Docker Secrets, Vault)
   - Enable HTTPS/TLS
   - Implement authentication/authorization
   - Set up rate limiting

2. **Scalability:**
   - Use container orchestration (Kubernetes, ECS)
   - Implement load balancing
   - Add caching layer (Redis)
   - Database for user data persistence

3. **Monitoring:**
   - Set up additional monitoring (Prometheus, Grafana)
   - Configure alerting
   - Log aggregation (ELK stack)

4. **Backup and Recovery:**
   - Regular backups
   - Disaster recovery plan
   - High availability setup

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google API key for GenAI | Required |
| `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix collector endpoint | http://phoenix:6006 |
| `APP_HOST` | Application host | 0.0.0.0 |
| `APP_PORT` | Application port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |

## Support

For issues and questions:
- Open an issue on GitHub
- Check the main README.md for additional documentation
- Review Phoenix documentation: https://docs.arize.com/phoenix
