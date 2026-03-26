# Serving & Configuration Spec

## Deployment Topology

```
┌─────────────────────────────────┐
│           Docker Host (VPS)     │
│                                 │
│  ┌───────┐  ┌─────┐  ┌──────┐  │
│  │  app  │  │redis│  │worker│  │
│  │:8000  │  │:6379│  │      │  │
│  │Granian│  │     │  │Taskiq│  │
│  └───┬───┘  └──┬──┘  └───┬──┘  │
│      │         │         │     │
│      └─────────┴─────────┘     │
│         internal network        │
└─────────────────────────────────┘
```

## Services

### app (Webhook Server)

- **Runtime**: Granian ASGI, 0.0.0.0:8000
- **Entrypoint**: `python -m judge` → `judge/__main__.py`
- **Role**: Receive webhooks, verify signature, enqueue tasks
- **Scaling**: Single instance (PoC). Stateless — можно scale horizontally за reverse proxy.
- **Health**: `GET /health` → 200

### worker (Task Worker)

- **Runtime**: `taskiq worker judge.tasks.broker:broker`
- **Role**: Dequeue tasks, run grading agent, handle Q&A
- **Scaling**: Single instance (PoC). Multiple workers share Redis queue.
- **State**: In-memory cache (roster, rubrics). Lost on restart.

### redis

- **Image**: `redis:7-alpine`
- **Role**: Task queue broker (ListQueueBroker)
- **Persistence**: None (PoC). Tasks lost on restart.
- **Scaling**: Single instance, no HA.

## Container Image

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "python", "-m", "judge"]
```

- **Base**: slim Debian Bookworm + uv
- **Size**: ~200MB (estimated)
- **Build**: Two-stage `uv sync` for layer caching
- **No multi-stage**: PoC simplicity, acceptable image size

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_APP_ID` | yes | — | GitHub App ID |
| `GITHUB_PRIVATE_KEY_PATH` | yes* | — | Path to PEM file |
| `GITHUB_PRIVATE_KEY` | yes* | — | PEM content directly |
| `GITHUB_WEBHOOK_SECRET` | yes | — | HMAC secret for webhook verification |
| `ZAI_API_KEY` | yes | — | Z.AI API key |
| `ZAI_BASE_URL` | no | `https://api.z.ai/api/paas/v4` | Z.AI endpoint |
| `ZAI_MODEL` | no | `glm-4.7` | Model name |
| `REDIS_URL` | no | `redis://localhost:6379/0` | Redis connection |
| `LANGFUSE_PUBLIC_KEY` | no | `""` | Langfuse (optional) |
| `LANGFUSE_SECRET_KEY` | no | `""` | Langfuse (optional) |
| `LANGFUSE_HOST` | no | `https://cloud.langfuse.com` | Langfuse host |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | no | `""` | Path to service account JSON |
| `SPREADSHEET_ID` | no | `""` | Fallback spreadsheet ID |
| `SPREADSHEET_MAP` | no | `""` | JSON: repo → spreadsheet ID mapping |
| `E2B_API_KEY` | no | `""` | E2B sandbox (optional) |
| `ROSTER_CACHE_TTL` | no | `300` | Cache TTL in seconds |
| `SANDBOX_TIMEOUT` | no | `600` | E2B sandbox timeout in seconds |
| `SPEC_BASE_URL` | no | `""` | Base URL for lab spec pages |

*One of `GITHUB_PRIVATE_KEY` or `GITHUB_PRIVATE_KEY_PATH` required.

### Secrets Management

| Secret | Storage | Rotation |
|--------|---------|----------|
| GitHub private key | File on disk (PEM) | Manual |
| GitHub webhook secret | Env var | Manual |
| Z.AI API key | Env var | Manual |
| Google SA JSON | File on disk | Manual |
| E2B API key | Env var | Manual |
| Langfuse keys | Env var | Manual |
| Installation tokens | In-memory cache | Auto (55 min) |

### Compose Variants

| File | Use Case |
|------|----------|
| `compose.yml` | Production: bridge network |
| `compose.dev.yml` | Development: Redis port exposed |
| `compose.host.yml` | Host networking (ngrok/cloudflared) |

## Startup Sequence

1. `docker compose up` → Redis starts first (healthcheck)
2. `app` starts → Granian binds 0.0.0.0:8000
3. `worker` starts → connects to Redis broker, listens for tasks
4. GitHub sends test webhook → `/health` returns 200

## Graceful Shutdown

- Granian: handles SIGTERM, drains connections
- Taskiq worker: finishes current task, then exits
- Redis: immediate stop (no persistence)
- E2B sandbox: `finally: sandbox.kill()` guarantees cleanup even on crash
