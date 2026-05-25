# Multi-Agent Workflow Documentation

## Overview

The Sports Prediction Platform uses a multi-agent architecture where specialized agents work together to produce accurate match predictions and identify value betting opportunities.

## Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MATCH INPUT                                        │
│  (match_id, home_team, away_team, kickoff_time)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    1. DATA COLLECTOR AGENT                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Match Data  │ │ Team Stats  │ │ Player Info │ │   Odds      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                                            │
│  │  Weather    │ │ Historical  │                                            │
│  └─────────────┘ └─────────────┘                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              2. STATISTICAL ENGINE AGENT                                     │
│  • Calculate Expected Goals (Poisson model)                                 │
│  • Form-based xG adjustment                                                  │
│  • H2H-based xG calculation                                                  │
│  • Monte Carlo Simulation (10,000 iterations)                               │
│  • Probability distribution                                                  │
│  • Value bet detection                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              3. MACHINE LEARNING AGENT                                       │
│  • Load trained ensemble models                                              │
│  • Feature extraction                                                        │
│  • Pattern recognition                                                       │
│  • Confidence scoring                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              4. MARKET ANALYZER AGENT                                        │
│  • Odds movement tracking                                                    │
│  • Sharp money detection                                                     │
│  • Arbitrage opportunity identification                                      │
│  • Market anomaly detection                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              5. PSYCHOLOGICAL CONTEXT AGENT                                  │
│  • Motivation analysis                                                       │
│  • Fatigue assessment                                                        │
│  • Pressure situations                                                       │
│  • Rivalry intensity                                                         │
│  • Emotional state evaluation                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              6. RISK MANAGEMENT AGENT                                        │
│  • Kelly Criterion calculation                                               │
│  • Stake optimization                                                        │
│  • Exposure limits                                                           │
│  • Bankroll protection                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              7. MASTER ORCHESTRATOR                                          │
│  • Fuse all agent analyses                                                   │
│  • Dynamic weighting based on confidence                                     │
│  • Generate final probabilities                                              │
│  • Create human-readable justification                                       │
│  • Output final prediction with stake recommendation                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FINAL OUTPUT                                       │
│  • Probabilities (Home/Draw/Away, O/U, BTTS)                                │
│  • Expected Goals                                                            │
│  • Most Likely Score                                                         │
│  • Confidence Score                                                          │
│  • Value Bets                                                                │
│  • Kelly Stake Recommendation                                                │
│  • Detailed Justification                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Weighting System

Each agent's output is weighted based on:
1. **Base weight**: Configured importance of the agent type
2. **Confidence score**: Agent's self-assessed confidence
3. **Historical performance**: Past accuracy (future enhancement)

### Default Weights
| Agent | Base Weight |
|-------|-------------|
| Data Collector | 1.0 |
| Statistical Engine | 1.2 |
| Machine Learning | 1.3 |
| Market Analyzer | 1.1 |
| Psychological Context | 0.8 |
| Risk Management | 1.0 |

## Probability Fusion

Final probabilities are calculated using weighted averaging:

```
final_prob = Σ(agent_prob × base_weight × confidence) / Σ(base_weight × confidence)
```

1X2 probabilities are then normalized to sum to 1.0.

## Value Bet Detection

A value bet is detected when:
```
model_probability > implied_probability + threshold
```

Where threshold defaults to 5%.

Value percentage is calculated as:
```
value_pct = ((model_prob / implied_prob) - 1) × 100
```

## Kelly Criterion

Stake recommendation uses fractional Kelly:
```
f* = (bp - q) / b

where:
  b = odds - 1
  p = model_probability
  q = 1 - p

recommended_stake = f* × kelly_fraction (default 25%)
```

Maximum stake is capped at configured limit (default 5%).

## Error Handling

- Each agent has timeout protection (default 30s)
- Retry logic with exponential backoff (max 3 retries)
- Graceful degradation if agents fail
- Fallback to default uniform distribution if all agents fail

## Monitoring

All agent executions are logged with:
- Processing time
- Success/failure status
- Confidence scores
- Error details (if applicable)

Performance metrics are exposed via Prometheus for Grafana dashboards.
