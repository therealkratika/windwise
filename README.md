# WindWise UK

WindWise evaluates UK wind generation forecasts against actual BMRS data.
The frontend is a React/Vite application and the API is a FastAPI service
that retrieves data from Elexon BMRS.

## Project structure

```text
windwise-uk/
├── backend/
│   ├── app/
│   │   ├── analytics.py
│   │   ├── elexon.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.js
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── render.yaml
└── pytest.ini
```

## Deployment status

The frontend has been deployed to Vercel and the backend has been deployed to
Render. Both deployment URLs were verified on October 25, 2026:

- Frontend: <https://frontend-orcin-two-er1unc8o0r.vercel.app/>
- Backend: <https://windwise-mnks.onrender.com/>

Health check: <https://windwise-mnks.onrender.com/api/health>

## Environment variables

### Backend

Copy [backend/.env.example](./backend/.env.example) to `backend/.env` for
local development:

| Variable | Required | Description |
| --- | --- | --- |
| `FRONTEND_ORIGIN` | Production | Comma-separated Vercel origin(s) allowed by CORS. |
| `PORT` | Render supplies it | Port for Uvicorn; defaults to `8000` locally. |

`FRONTEND_ORIGIN` must contain origins only, for example
`https://windwise.vercel.app`, not an API path.

### Frontend

Copy [frontend/.env.example](./frontend/.env.example) to `frontend/.env`:

| Variable | Required | Description |
| --- | --- | --- |
| `VITE_API_URL` | Yes | Public FastAPI base URL, without a trailing slash. |

For local development use `http://localhost:8000`. For Vercel use the public
Render URL, such as `https://windwise-api.onrender.com`.

Environment files are intentionally ignored by Git. Only the `.env.example`
placeholders should be committed.

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

## Local development without Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

The local API is available at <http://localhost:8000>. The frontend is
available at <http://localhost:5173>.

## Testing and production build

Run backend tests from the repository root:

```bash
backend/.venv/bin/pytest -v
```

Build and lint the frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

## Deploy the backend to Render

This repository includes [render.yaml](./render.yaml). In Render:

1. Create a new Blueprint from the GitHub repository, or create a Python web
   service using the `backend` directory as its root directory.
2. Use `pip install -r requirements.txt` as the build command.
3. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command.
4. Set `FRONTEND_ORIGIN` to the deployed Vercel origin.
5. Configure the health check path as `/api/health`.

Render provides `PORT`; the application listens on `0.0.0.0` and uses it.
Verify the deployed service before configuring the frontend:

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/api/health
```

## Deploy the frontend to Vercel

Import the repository into Vercel with these settings:

| Setting | Value |
| --- | --- |
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Set this Vercel environment variable for Production (and Preview if needed):

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

After deployment, update Render’s `FRONTEND_ORIGIN` to the exact Vercel
origin and redeploy/restart the backend if necessary.

## API endpoints

- `GET /api/health` — deployment health check.
- `GET /api/analysis?start=YYYY-MM-DD&end=YYYY-MM-DD&cutoff_hour=10` —
  forecast evaluation for an exclusive end date.

The analysis endpoint limits requests to 32 days or fewer and uses the
Elexon BMRS `FUELHH` and `WINDFOR` datasets. Forecast vintages are selected
using the latest publication available before the configured previous-day
Europe/London cutoff.

## Known limitations

- Elexon availability and upstream response quality are outside WindWise’s
  control; upstream failures are returned as HTTP 502 errors.
- The decision cutoff is configurable but its business meaning must be
  confirmed before operational use.
- Forecast and actual data may have different resolutions; only correctly
  aligned observations are included in metrics.
- Render free-tier services may sleep between requests, increasing the first
  response latency.

## AI tools disclosure

AI-assisted development tools were used to help inspect the codebase, implement
frontend and backend changes, create tests, prepare Docker and deployment
configuration, and review documentation. All generated changes were reviewed
and validated with the project’s lint, build, test, Docker, and health-check
commands where applicable. External data behavior was checked against the
official Elexon BMRS API documentation and live endpoint responses.
