# Agent IA Autonome – Deployed App

Agent IA autonome exposé via une API REST, dockerisé et prêt pour un déploiement VPS avec monitoring intégré.

## Architecture

```
POST /run  →  FastAPI  →  Agent (Claude)  →  Tools (search, scrape)
                 │
                 ├── SQLite  →  GET /costs
                 └── Prometheus  →  GET /metrics  →  Grafana
```

**Stack :**
- FastAPI + Gunicorn (UvicornWorker) — serveur de production multi-workers
- Claude claude-sonnet-4-6 (Anthropic) — modèle de l'agent
- SQLite — persistance des coûts API par requête
- Prometheus + Grafana — métriques et dashboards

## Structure du projet

```
deployed_app_ai/
├── app/
│   ├── main.py                  # FastAPI app + MetricsMiddleware
│   ├── api/routes.py            # Endpoints REST
│   ├── agent/core.py            # Boucle agent + tracking tokens
│   ├── tools/                   # scraper, searcher, definitions, executor
│   ├── models/schemas.py        # Modèles Pydantic
│   ├── monitoring/
│   │   ├── cost_tracker.py      # SQLite – coût par run
│   │   └── metrics.py           # Compteurs Prometheus
│   └── config/settings.py       # Variables d'environnement
├── docker/
│   ├── prometheus.yml           # Config scrape Prometheus
│   └── nginx.conf               # Reverse proxy VPS
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py
└── requirements.txt
```

## Démarrage rapide

### Prérequis

- Docker et Docker Compose installés
- Une clé API Anthropic

### Installation

```bash
git clone <repo>
cd deployed_app_ai

cp .env.example .env
# Editer .env et renseigner ANTHROPIC_API_KEY

docker compose up --build
```

L'API est disponible sur `http://localhost:8000`.

### Développement local (sans Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Editer .env

uvicorn app.main:app --reload
```

## API

### `POST /run`

Soumet une tâche à l'agent.

**Request**
```json
{
  "task": "Analyse les principaux concurrents de Notion"
}
```

**Response**
```json
{
  "task": "Analyse les principaux concurrents de Notion",
  "status": "completed",
  "iterations": 3,
  "summary": "...",
  "tool_calls": [
    {
      "tool": "search_web",
      "inputs": { "query": "Notion competitors 2024" },
      "output_preview": "..."
    }
  ],
  "input_tokens": 4200,
  "output_tokens": 980,
  "estimated_cost_usd": 0.000126
}
```

### `GET /health`

Vérifie l'état de l'application et de ses dépendances.

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "api_key": "ok"
  }
}
```

`status` vaut `ok` ou `degraded`.

### `GET /costs`

Statistiques de consommation API depuis le démarrage.

```json
{
  "total_runs": 12,
  "total_input_tokens": 48000,
  "total_output_tokens": 11200,
  "total_cost_usd": 0.001512,
  "recent_runs": [...]
}
```

### `GET /metrics`

Métriques au format Prometheus (scrape par Prometheus toutes les 15s).

Métriques exposées :

| Métrique | Type | Description |
|---|---|---|
| `http_requests_total` | Counter | Requêtes HTTP par method/endpoint/status |
| `http_request_duration_seconds` | Histogram | Durée des requêtes par endpoint |
| `agent_runs_total` | Counter | Runs par statut (completed/failed) |
| `agent_tokens_total` | Counter | Tokens par type (input/output) |
| `agent_cost_usd_total` | Counter | Coût total cumulé en USD |

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Obligatoire.** Clé API Anthropic |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Modèle Claude utilisé |
| `MAX_AGENT_ITERATIONS` | `10` | Nombre max de tours de l'agent |
| `SCRAPER_TIMEOUT` | `15` | Timeout HTTP du scraper (secondes) |
| `DB_PATH` | `data/costs.db` | Chemin du fichier SQLite |
| `PORT` | `8000` | Port d'écoute |
| `WORKERS` | `2` | Nombre de workers Gunicorn |
| `WORKER_TIMEOUT` | `120` | Timeout worker (secondes) |
| `LOG_LEVEL` | `info` | Niveau de log (`debug`, `info`, `warning`) |
| `GRAFANA_PASSWORD` | `admin` | Mot de passe admin Grafana |

## Monitoring

### Prometheus

Accessible sur `http://localhost:9090`.

Prometheus scrape automatiquement `GET /metrics` toutes les 15 secondes. La rétention des données est configurée à 15 jours.

### Grafana

Accessible sur `http://localhost:3000` (login : `admin` / valeur de `GRAFANA_PASSWORD`).

**Configuration de la datasource Prometheus dans Grafana :**
1. Settings → Data Sources → Add data source → Prometheus
2. URL : `http://prometheus:9090`
3. Save & Test

**Exemples de requêtes PromQL utiles :**

```promql
# Taux de requêtes par minute
rate(agent_runs_total[1m]) * 60

# Coût cumulé en USD
agent_cost_usd_total

# Latence médiane sur /run
histogram_quantile(0.5, rate(http_request_duration_seconds_bucket{endpoint="/run"}[5m]))

# Tokens consommés par minute
rate(agent_tokens_total[1m]) * 60
```

## Déploiement VPS

### Avec nginx (recommandé en production)

Ajouter le service nginx dans `docker-compose.yml` :

```yaml
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    restart: unless-stopped
```

Le fichier `docker/nginx.conf` configure :
- Le reverse proxy vers l'app sur le port 8000
- `proxy_read_timeout 130s` (aligné avec `WORKER_TIMEOUT`)
- Le blocage de `/metrics` depuis l'extérieur (`deny all`)

### Nombre de workers en production

La règle standard est `2 * nb_CPU + 1`. Sur un VPS 2 vCPU :

```bash
WORKERS=5
```

### Variables à changer obligatoirement en production

```bash
ANTHROPIC_API_KEY=<ta_vraie_clé>
GRAFANA_PASSWORD=<mot_de_passe_fort>
LOG_LEVEL=warning
```

## Pricing estimatif

Basé sur `claude-sonnet-4-6` :

| Usage | Coût estimé |
|---|---|
| 1 run simple (recherche + résumé) | ~$0.0001 |
| 100 runs/jour | ~$0.01/jour |
| 3000 runs/mois | ~$0.30/mois |

Les coûts réels sont consultables via `GET /costs`.
