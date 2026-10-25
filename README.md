# WindWise UK

WindWise evaluates UK wind generation forecasts against actual BMRS data.

## Run locally with Docker Compose

From the project root:

```bash
docker compose up --build
```

The application is then available at:

- Frontend: <http://localhost:8080>
- Backend health through Nginx: <http://localhost:8080/api/health>
- Backend directly: <http://localhost:8000/api/health>

The frontend is built with `VITE_API_URL=/api`. Nginx serves the React SPA
and proxies `/api/` requests to the `backend` Compose service.

### Stop the application

```bash
docker compose down
```

To also remove the Compose-built images:

```bash
docker compose down --rmi local
```

### Rebuild after code or dependency changes

```bash
docker compose build --no-cache
docker compose up
```

### Verify service health

```bash
docker compose ps
curl http://localhost:8080/api/health
```

Both services should report `healthy`, and the health endpoint should return:

```json
{"status":"ok","service":"windwise-api"}
```

No credentials or local virtual environments are copied into either image.
