# app1# 🏆 Sport AI Platform — Système de prédiction sportive multi-agents

> Plateforme IA haute performance pour l'analyse d'événements sportifs, l'estimation de probabilités et la détection d'opportunités de value betting.

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Agents IA](#agents-ia)
- [Structure des dossiers](#structure-des-dossiers)
- [Base de données](#base-de-données)
- [API Reference](#api-reference)
- [WebSocket temps réel](#websocket-temps-réel)
- [Pipeline ML](#pipeline-ml)
- [Infrastructure](#infrastructure)
- [CI/CD](#cicd)
- [Sécurité](#sécurité)
- [Installation](#installation)
- [Configuration](#configuration)
- [Monitoring](#monitoring)

---

## Vue d'ensemble

Sport AI Platform est un système multi-agents modulaire et scalable qui orchestre 7 agents spécialisés pour produire des recommandations de paris à valeur positive (value bets) en temps réel.

**Fonctionnalités principales :**

- Collecte de données sportives en temps réel (APIs, bookmakers, météo, blessures)
- Modélisation statistique (Poisson, xG, Monte Carlo 10 000 itérations)
- Machine Learning continu (XGBoost, LightGBM, Random Forest, Neural Net)
- Analyse des marchés de paris (sharp money, arbitrage, anomalies de cotes)
- Analyse du contexte psychologique (motivation, fatigue, rivalités)
- Risk management automatique (Kelly Criterion, stop-loss, bankroll)
- Dashboard React/Next.js avec alertes WebSocket temps réel

**Stack technique :**

| Composant | Technologie |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 14 / React |
| Base de données | PostgreSQL 16 + TimescaleDB |
| Cache | Redis Cluster |
| Message bus | Apache Kafka |
| ML tracking | MLflow |
| Orchestration | Kubernetes + Helm |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana + Jaeger |
| Secrets | HashiCorp Vault |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sources de données externes                   │
│  APIs sportives · Bookmakers · Météo · Blessures · Stats hist.  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              Agent Data Collector — Ingestion                    │
│         FastAPI · Kafka Streams · Redis Cache · Normalisation    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────────┐
         │                │                    │
┌────────▼───────┐ ┌──────▼──────┐ ┌──────────▼────────┐
│ Statistical    │ │  ML Engine  │ │  Market Analyzer  │
│ Engine         │ │             │ │                   │
│ Poisson · xG   │ │ XGBoost     │ │ Sharp money       │
│ Monte Carlo    │ │ Auto-train  │ │ Arbitrage         │
└────────┬───────┘ └──────┬──────┘ └──────────┬────────┘
         │                │                    │
┌────────▼───────┐ ┌──────▼──────────────────▼────────┐
│ Psych. Context │ │        Master Orchestrator         │
│ Motivation     │ │  Fusion · Pondération dynamique    │
│ Fatigue        │ │  Score final · Justification NLP   │
└────────┬───────┘ └──────┬──────────────────┬────────┘
         │                │                  │
         └────────────────▼                  │
                   Risk Manager              │
                   Kelly · Stop-loss         │
                          │                  │
┌─────────────────────────▼──────────────────▼──────────────────┐
│              PostgreSQL · TimescaleDB · Redis · S3             │
└─────────────────────────┬──────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│           Dashboard Next.js · WebSocket temps réel              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agents IA

### 1. Agent Data Collector

Responsable de la collecte, normalisation et mise en cache de toutes les données externes.

**Sources :**
- APIs sportives : Sportmonks, API-Football, Opta
- Cotes bookmakers : Pinnacle, Bet365, Betfair Exchange
- Météo : OpenWeatherMap API
- Blessures et compositions : équipes médicales / presse officielle
- Statistiques historiques : base interne TimescaleDB

**Comportement :**
- Polling toutes les 30 secondes en pré-match
- Streaming temps réel en live (WebSocket vers Kafka)
- Cache Redis avec TTL adaptatif (30s pré-match, 5s live)
- Normalisation vers un schéma unifié `MatchContext`

---

### 2. Agent Statistical Engine

Produit des probabilités calibrées à partir de modèles mathématiques éprouvés.

**Modèles implémentés :**

```python
# Modèle de Poisson bivarié
λ_home = attack_home * defense_away * home_advantage
λ_away = attack_away * defense_home

# Simulation Monte Carlo
for i in range(10_000):
    goals_home = poisson.rvs(λ_home)
    goals_away = poisson.rvs(λ_away)
    results[i] = classify(goals_home, goals_away)

# Expected Goals (xG)
xg_home = sum(shot_xg for shot in home_shots)
xg_away = sum(shot_xg for shot in away_shots)

# Value betting
fair_prob = simulated_win_rate
implied_prob = 1 / bookmaker_odds
expected_value = (fair_prob * bookmaker_odds) - 1
is_value = expected_value > VALUE_THRESHOLD  # 5% par défaut
```

---

### 3. Agent Machine Learning

Entraîne et déploie des modèles prédictifs avec apprentissage continu.

**Modèles :**
- XGBoost (modèle principal, production)
- LightGBM (challenger)
- Random Forest (interprétabilité)
- PyTorch Neural Net (patterns complexes)
- Ensemble stacking (méta-modèle final)

**Features (150+) :**
- Forme récente (5, 10, 20 derniers matchs)
- Statistiques domicile/extérieur
- Head-to-head historique
- xG offensif et défensif
- Fatigue (densité calendrier)
- Valeur marchande des effectifs
- Mouvements de cotes (features marché)
- Contexte météo

**Scoring de confiance :**

```python
confidence_score = (
    model_accuracy_weight * model_calibration_score +
    data_quality_weight   * data_completeness_score +
    market_agreement_weight * market_alignment_score
)
```

---

### 4. Agent Market Analyzer

Surveille les marchés de paris pour détecter des signaux d'information.

**Signaux détectés :**
- **Sharp money** : mouvements de cotes sans news publique (activité des parieurs professionnels)
- **Steam moves** : chute rapide et synchronisée chez plusieurs bookmakers
- **Reverse line movement** : cotes qui bougent à l'opposé du flux de mises public
- **Arbitrage** : situations sans risque entre bookmakers
- **Anomalies** : outliers statistiques détectés par isolation forest

```python
# Détection de sharp money
odds_delta = current_odds - opening_odds
volume_ratio = sharp_volume / total_volume
sharp_signal = odds_delta < -0.05 and volume_ratio > 0.7
```

---

### 5. Agent Psychological Context

Quantifie les facteurs humains qui influencent la performance sportive.

**Facteurs analysés :**

| Facteur | Source | Poids |
|---|---|---|
| Motivation (enjeu du match) | Classement / Coupe | 0.25 |
| Fatigue (densité calendrier) | Schedule API | 0.20 |
| Pression (streak, attentes) | Presse / historique | 0.15 |
| Rivalités historiques | BDD interne | 0.15 |
| Cohésion d'équipe | Transferts récents | 0.15 |
| Contexte émotionnel | NLP presse | 0.10 |

---

### 6. Agent Risk Management

Protège le capital en appliquant une gestion rigoureuse du risque.

**Kelly Criterion :**

```python
def kelly_fraction(probability: float, odds: float, fraction: float = 0.25) -> float:
    """
    Fraction de Kelly réduite (quarter Kelly) pour limiter la variance.
    probability : probabilité estimée de victoire
    odds        : cotes décimales du bookmaker
    fraction    : réduction du Kelly complet (0.25 recommandé)
    """
    edge = (probability * odds) - 1
    kelly = edge / (odds - 1)
    return max(0, kelly * fraction)

# Contraintes de risque
MAX_STAKE_PER_BET    = 0.03  # 3% du bankroll
MAX_EXPOSURE_PER_DAY = 0.10  # 10% du bankroll
STOP_LOSS_DAILY      = 0.05  # Arrêt si -5% sur la journée
MIN_CONFIDENCE       = 0.70  # Score de confiance minimum
MIN_EXPECTED_VALUE   = 0.05  # EV minimum +5%
```

---

### 7. Master Orchestrator

Fusionne les analyses de tous les agents et produit la décision finale.

**Pondération dynamique :**

```python
AGENT_WEIGHTS = {
    "statistical":   0.30,  # Modèle de base fiable
    "ml":            0.25,  # Patterns complexes
    "market":        0.20,  # Signal informationnel
    "psychological": 0.15,  # Contexte humain
    "data_quality":  0.10,  # Méta-poids sur la qualité des données
}

# Bayesian update : ajustement des poids selon performances historiques
def update_weights(agent_id: str, was_correct: bool):
    performance_history[agent_id].append(was_correct)
    recent_accuracy = mean(performance_history[agent_id][-100:])
    AGENT_WEIGHTS[agent_id] = softmax(recent_accuracy)
```

---

## Structure des dossiers

```
sport-ai-platform/
├── services/
│   ├── data-collector/
│   │   ├── main.py                   # FastAPI app
│   │   ├── agents/
│   │   │   ├── sports_api.py         # Collecte APIs sportives
│   │   │   ├── odds_scraper.py       # Scraping cotes
│   │   │   ├── weather.py            # API météo
│   │   │   └── injuries.py           # Blessures / compositions
│   │   ├── models/                   # Schemas Pydantic
│   │   ├── cache/                    # Redis helpers
│   │   ├── kafka/                    # Producers Kafka
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── statistical-engine/
│   │   ├── main.py
│   │   ├── poisson_model.py
│   │   ├── monte_carlo.py
│   │   ├── expected_goals.py
│   │   ├── value_betting.py
│   │   └── Dockerfile
│   │
│   ├── ml-engine/
│   │   ├── main.py
│   │   ├── training/
│   │   │   ├── pipeline.py           # Pipeline sklearn / MLflow
│   │   │   ├── feature_engineering.py
│   │   │   └── hyperparameter_tuning.py  # Optuna
│   │   ├── inference/
│   │   │   └── predictor.py
│   │   ├── models/                   # Fichiers modèles (.pkl / .pt)
│   │   ├── mlflow_tracker.py
│   │   └── Dockerfile
│   │
│   ├── market-analyzer/
│   │   ├── main.py
│   │   ├── sharp_money_detector.py
│   │   ├── arbitrage_finder.py
│   │   └── Dockerfile
│   │
│   ├── psych-context/
│   │   ├── main.py
│   │   ├── motivation_scorer.py
│   │   ├── nlp_press_analyzer.py
│   │   └── Dockerfile
│   │
│   ├── risk-manager/
│   │   ├── main.py
│   │   ├── kelly_criterion.py
│   │   ├── bankroll_tracker.py
│   │   └── Dockerfile
│   │
│   └── orchestrator/
│       ├── main.py
│       ├── fusion_engine.py          # Pondération dynamique
│       ├── bayesian_updater.py       # Mise à jour des poids
│       ├── justification_generator.py
│       ├── websocket_emitter.py
│       └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/page.tsx        # Vue principale
│   │   ├── bets/page.tsx             # Historique paris
│   │   ├── monitor/page.tsx          # Monitoring IA
│   │   └── api/                      # Next.js API routes
│   ├── components/
│   │   ├── LiveBetAlert.tsx
│   │   ├── AgentScoreCard.tsx
│   │   ├── BankrollChart.tsx
│   │   └── MatchAnalysisPanel.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts
│   └── package.json
│
├── shared/
│   ├── schemas/
│   │   ├── match_context.py          # Schéma unifié
│   │   ├── prediction.py
│   │   └── value_bet.py
│   └── utils/
│       ├── logging.py
│       └── metrics.py
│
├── infra/
│   ├── k8s/
│   │   ├── base/
│   │   │   ├── namespace.yaml
│   │   │   ├── deployments/
│   │   │   ├── services/
│   │   │   └── configmaps/
│   │   └── overlays/
│   │       ├── dev/
│   │       └── prod/
│   ├── helm/
│   │   └── sport-ai/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       └── templates/
│   └── terraform/
│       ├── main.tf
│       ├── eks.tf
│       └── rds.tf
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── docker-compose.yml                # Développement local
├── docker-compose.prod.yml
└── Makefile
```

---

## Base de données

### Schéma principal (PostgreSQL)

```sql
-- Équipes
CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    country     VARCHAR(50),
    league      VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Matchs
CREATE TABLE matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_team_id    UUID REFERENCES teams(id),
    away_team_id    UUID REFERENCES teams(id),
    competition_id  UUID,
    match_date      TIMESTAMPTZ NOT NULL,
    status          VARCHAR(20) DEFAULT 'scheduled',
    home_score      INT,
    away_score      INT,
    metadata        JSONB DEFAULT '{}'
);

-- Prédictions générées par l'orchestrateur
CREATE TABLE predictions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id         UUID REFERENCES matches(id),
    home_win_prob    FLOAT NOT NULL,
    draw_prob        FLOAT NOT NULL,
    away_win_prob    FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    expected_value   FLOAT,
    agent_scores     JSONB NOT NULL,
    justification    TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Value bets détectés
CREATE TABLE value_bets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id       UUID REFERENCES predictions(id),
    bookmaker_id        UUID REFERENCES bookmakers(id),
    market_type         VARCHAR(50),
    selection           VARCHAR(50),
    odds                FLOAT NOT NULL,
    fair_odds           FLOAT NOT NULL,
    expected_value      FLOAT NOT NULL,
    kelly_fraction      FLOAT NOT NULL,
    recommended_stake   FLOAT NOT NULL,
    status              VARCHAR(20) DEFAULT 'pending',
    result              VARCHAR(20),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Historique des cotes (TimescaleDB hypertable)
CREATE TABLE odds_history (
    id            UUID DEFAULT gen_random_uuid(),
    match_id      UUID REFERENCES matches(id),
    bookmaker_id  UUID REFERENCES bookmakers(id),
    market        VARCHAR(50),
    odds_home     FLOAT,
    odds_draw     FLOAT,
    odds_away     FLOAT,
    recorded_at   TIMESTAMPTZ DEFAULT NOW()
);
SELECT create_hypertable('odds_history', 'recorded_at');

-- Logs des agents (pour audit et réentraînement)
CREATE TABLE agent_logs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id       UUID REFERENCES matches(id),
    agent_name     VARCHAR(50) NOT NULL,
    input_data     JSONB NOT NULL,
    output_data    JSONB NOT NULL,
    processing_ms  INT,
    executed_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Suivi du bankroll
CREATE TABLE bankroll_events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type    VARCHAR(30) NOT NULL,  -- 'bet', 'win', 'loss', 'deposit'
    amount        FLOAT NOT NULL,
    value_bet_id  UUID REFERENCES value_bets(id),
    balance_after FLOAT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Reference

### Analyser un match

```http
POST /api/v1/analyze
Content-Type: application/json
Authorization: Bearer <token>
```

**Corps de la requête :**

```json
{
  "match_id": "uuid-match-123",
  "home_team": "PSG",
  "away_team": "Olympique de Marseille",
  "competition": "Ligue 1",
  "match_date": "2026-05-30T20:45:00Z",
  "agents": ["statistical", "ml", "market", "psychological"],
  "options": {
    "min_confidence": 0.70,
    "min_expected_value": 0.05
  }
}
```

**Réponse :**

```json
{
  "prediction_id": "pred-abc-456",
  "match": {
    "home_team": "PSG",
    "away_team": "Olympique de Marseille"
  },
  "probabilities": {
    "home_win": 0.54,
    "draw": 0.24,
    "away_win": 0.22
  },
  "confidence_score": 0.81,
  "value_bets": [
    {
      "market": "1X2",
      "selection": "home_win",
      "bookmaker": "Pinnacle",
      "odds": 2.05,
      "fair_odds": 1.85,
      "expected_value": 0.108,
      "kelly_fraction": 0.032,
      "recommended_stake_eur": 64,
      "expires_at": "2026-05-30T20:44:00Z"
    }
  ],
  "agent_scores": {
    "statistical":   { "score": 0.56, "confidence": 0.84, "processing_ms": 312 },
    "ml":            { "score": 0.52, "confidence": 0.78, "processing_ms": 89  },
    "market":        { "score": 0.55, "confidence": 0.89, "processing_ms": 45  },
    "psychological": { "score": 0.59, "confidence": 0.71, "processing_ms": 210 }
  },
  "justification": "PSG domine à domicile (72% win rate sur les 20 derniers matchs). OM en baisse de forme (1 victoire sur 5). Signal marché : cotes PSG en baisse de 2.20 → 2.05 (sharp money détecté). Contexte : match à fort enjeu pour le titre.",
  "created_at": "2026-05-25T14:32:00Z"
}
```

---

### Autres endpoints

```http
# Récupérer l'historique des value bets
GET /api/v1/bets?status=pending&min_ev=0.05&limit=20

# Statut du bankroll
GET /api/v1/bankroll/status

# Performances des agents
GET /api/v1/agents/performance?period=30d

# Lancer un retraining ML manuel
POST /api/v1/ml/retrain
{ "model": "xgboost", "competition": "ligue1" }

# Santé des services
GET /api/v1/health
```

---

## WebSocket temps réel

```javascript
// Connexion au flux de value bets
const ws = new WebSocket('wss://api.sport-ai.com/ws/live-bets');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Alerte value bet
  if (data.event === 'value_bet_alert') {
    console.log({
      match:           data.match,        // "PSG vs OM"
      selection:       data.selection,    // "home_win @ 2.05"
      expected_value:  data.ev,           // "+10.8%"
      confidence:      data.confidence,   // "HIGH"
      expires_in:      data.expires_in_seconds,  // 47
      recommended_stake: data.stake_eur  // 64
    });
  }

  // Mise à jour de cotes en live
  if (data.event === 'odds_update') { /* ... */ }

  // Résultat d'un match (déclenche l'apprentissage)
  if (data.event === 'match_result') { /* ... */ }
};
```

---

## Pipeline ML

```
Feature Engineering (150+ features)
        │
        ▼
Nettoyage & imputation (sklearn Pipeline)
        │
        ▼
Cross-validation 5-fold stratifiée (TimeSeriesSplit)
        │
        ┌───────────────────────────────────────────┐
        ▼           ▼            ▼           ▼      ▼
    XGBoost    LightGBM   RandomForest  PyTorch  CatBoost
        │           │            │           │      │
        └───────────┴────────────┴───────────┴──────┘
                                │
                    Hyperparameter tuning (Optuna)
                                │
                     Calibration (Platt / Isotonic)
                                │
                      Ensemble stacking (méta-modèle)
                                │
                         MLflow Registry
                                │
                  Shadow test (A/B 7 jours en prod)
                                │
                       Déploiement production
                                │
              Monitoring drift (PSI, KS-test quotidien)
                                │
                  Retraining nightly si drift détecté
```

**Commandes utiles :**

```bash
# Lancer un entraînement
make train COMPETITION=ligue1 SEASON=2025-2026

# Évaluer un modèle
make evaluate MODEL_ID=xgb-v3.2.1

# Déployer en production
make deploy-model MODEL_ID=xgb-v3.2.1 SHADOW=true
```

---

## Infrastructure

### Namespaces Kubernetes

```yaml
# sport-ai-apps : services applicatifs
- data-collector   (3 replicas, HPA 2-8)
- stat-engine      (2 replicas, CPU: 2 cores)
- ml-engine        (1 replica, GPU node)
- market-analyzer  (2 replicas)
- psych-context    (2 replicas)
- risk-manager     (2 replicas)
- orchestrator     (2 replicas, RAM: 4 Gi)
- websocket-srv    (2 replicas, Socket.io)
- frontend         (3 replicas, Next.js)
- ml-scheduler     (CronJob, retraining nightly)

# sport-ai-data : stockage
- postgresql       (StatefulSet, PVC 100 Gi)
- redis-cluster    (3 shards + Sentinel)
- kafka            (3 brokers + Zookeeper)
- elasticsearch    (3 nodes + Kibana)

# monitoring
- prometheus
- grafana
- jaeger           (distributed tracing)
- alertmanager     (PagerDuty + Slack)
- mlflow           (experiments + registry)
```

### Docker Compose (développement local)

```yaml
# docker-compose.yml
version: '3.9'
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: sport_ai
      POSTGRES_USER: sport_ai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    ports:
      - "9092:9092"

  orchestrator:
    build: ./services/orchestrator
    environment:
      DATABASE_URL: postgresql://sport_ai:${POSTGRES_PASSWORD}@postgres:5432/sport_ai
      REDIS_URL: redis://redis:6379
      KAFKA_BOOTSTRAP: kafka:9092
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - kafka
```

---

## CI/CD

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v --cov=. --cov-report=xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker images
        run: docker compose build
      - name: Security scan (Trivy)
        uses: aquasecurity/trivy-action@master
      - name: Push to registry
        run: docker push ghcr.io/org/sport-ai:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          helm upgrade --install sport-ai ./infra/helm/sport-ai \
            --set image.tag=${{ github.sha }} \
            --namespace sport-ai-apps \
            --atomic --wait
```

---

## Sécurité

| Couche | Mécanisme |
|---|---|
| Authentification | JWT RS256 · OAuth2 · API keys |
| Secrets | HashiCorp Vault (rotation automatique) |
| Communication inter-services | mTLS (Istio service mesh) |
| Autorisation | RBAC Kubernetes + OPA Gatekeeper |
| Réseau | NetworkPolicies K8s (deny-all par défaut) |
| Scan images | Trivy dans CI (bloque si CRITICAL) |
| Code | SAST (Bandit) + DAST (OWASP ZAP) |
| Données | Chiffrement at-rest (AES-256) + in-transit (TLS 1.3) |
| Audit | Logs d'accès centralisés Elasticsearch |

---

## Installation

### Prérequis

- Docker 24+ et Docker Compose
- kubectl + Helm 3
- Python 3.11+
- Node.js 20+

### Démarrage rapide (local)

```bash
# Cloner le dépôt
git clone https://github.com/org/sport-ai-platform.git
cd sport-ai-platform

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Lancer tous les services
make dev

# Initialiser la base de données
make db-migrate

# Accéder au dashboard
open http://localhost:3000
```

### Déploiement Kubernetes

```bash
# Créer les namespaces
kubectl apply -f infra/k8s/base/namespace.yaml

# Configurer les secrets dans Vault
make vault-setup

# Déployer avec Helm
helm install sport-ai ./infra/helm/sport-ai \
  -f infra/helm/sport-ai/values.prod.yaml \
  --namespace sport-ai-apps

# Vérifier les pods
kubectl get pods -n sport-ai-apps
```

---

## Configuration

```bash
# .env.example

# Base de données
DATABASE_URL=postgresql://sport_ai:password@localhost:5432/sport_ai
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP=localhost:9092

# APIs sportives
SPORTMONKS_API_KEY=your_key
API_FOOTBALL_KEY=your_key
OPENWEATHER_API_KEY=your_key

# Bookmakers
PINNACLE_API_KEY=your_key
BETFAIR_APP_KEY=your_key
BETFAIR_SESSION_TOKEN=your_token

# ML
MLFLOW_TRACKING_URI=http://localhost:5000
AWS_S3_BUCKET=sport-ai-models

# Risk management
DEFAULT_BANKROLL=10000
MAX_STAKE_PERCENT=0.03
MIN_EXPECTED_VALUE=0.05
MIN_CONFIDENCE=0.70
KELLY_FRACTION=0.25

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

---

## Monitoring

**Métriques clés suivies :**

- `agent_processing_duration_ms` — latence par agent
- `predictions_total` — nombre de prédictions / heure
- `value_bets_detected_total` — value bets détectés
- `model_accuracy_30d` — précision glissante 30 jours
- `bankroll_balance` — solde du bankroll en temps réel
- `odds_staleness_seconds` — fraîcheur des cotes
- `kafka_consumer_lag` — retard consommation Kafka

**Alertes configurées :**

| Alerte | Condition | Canal |
|---|---|---|
| Agent down | Pod restart > 3 en 5 min | PagerDuty |
| Model drift | PSI > 0.2 | Slack |
| Database latency | P99 > 500ms | Slack |
| Value bet expirée | Bet non placé avant expiry | Dashboard |
| Bankroll stop-loss | Drawdown > 5% / jour | PagerDuty |

---

## Commandes Makefile

```bash
make dev          # Démarrer l'environnement local
make test         # Lancer les tests
make train        # Entraîner les modèles ML
make db-migrate   # Appliquer les migrations
make logs         # Afficher les logs de tous les services
make clean        # Nettoyer les conteneurs et volumes
```

---

## Licence

MIT License — Voir [LICENSE](LICENSE)

---

*Sport AI Platform — Conçu pour être modulaire, scalable et production-ready.*
