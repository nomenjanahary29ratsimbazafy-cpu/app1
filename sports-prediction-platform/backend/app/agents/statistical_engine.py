"""
Statistical Engine Agent - Core statistical models for match prediction.

Implements:
- Poisson distribution for score prediction
- Expected Goals (xG) calculations
- Monte Carlo simulations
- Implied probability extraction
- Value betting identification
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy.stats import poisson
import random

from app.agents.base_agent import AsyncAgent, AgentResult
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("agent.statistical_engine")


class StatisticalEngineAgent(AsyncAgent):
    """
    Statistical analysis agent implementing core prediction models.
    
    Uses Poisson distribution, expected goals, and Monte Carlo simulations
    to generate probabilistic match outcome predictions.
    """
    
    def __init__(self):
        super().__init__(
            name="StatisticalEngine",
            version="1.0.0",
            timeout_seconds=120,  # Monte Carlo can be slow
            max_retries=2,
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute statistical analysis on match data.
        
        Input data should contain:
        - home_team stats (goals scored/conceded, form, etc.)
        - away_team stats
        - head_to_head history
        - odds data for value detection
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract team statistics
            home_stats = input_data.get("team_stats", {}).get("home_team", {})
            away_stats = input_data.get("team_stats", {}).get("away_team", {})
            h2h = input_data.get("historical_data", {}).get("head_to_head", {})
            odds_data = input_data.get("odds_data", {})
            
            if not home_stats or not away_stats:
                return AgentResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    processing_time_ms=0,
                    error="Missing team statistics",
                )
            
            # Calculate expected goals using multiple methods
            xg_poisson = self._calculate_xg_poisson(home_stats, away_stats)
            xg_form = self._calculate_xg_from_form(home_stats, away_stats)
            xg_h2h = self._calculate_xg_from_h2h(h2h)
            
            # Weighted average of xG calculations
            expected_home_goals = (
                xg_poisson["home"] * 0.5 +
                xg_form["home"] * 0.3 +
                xg_h2h["home"] * 0.2
            )
            expected_away_goals = (
                xg_poisson["away"] * 0.5 +
                xg_form["away"] * 0.3 +
                xg_h2h["away"] * 0.2
            )
            
            # Run Monte Carlo simulation
            monte_carlo_results = await self._run_monte_carlo(
                expected_home_goals,
                expected_away_goals,
                iterations=settings.MONTE_CARLO_ITERATIONS,
            )
            
            # Calculate probabilities from simulation
            probabilities = self._calculate_probabilities(monte_carlo_results)
            
            # Detect value bets
            value_bets = self._detect_value_bets(
                probabilities,
                odds_data.get("market_summary", {}),
            )
            
            # Calculate most likely scores
            score_probs = self._calculate_score_probabilities(
                expected_home_goals,
                expected_away_goals,
            )
            most_likely_score = max(score_probs.items(), key=lambda x: x[1])
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result_data = {
                "expected_goals": {
                    "home": round(expected_home_goals, 3),
                    "away": round(expected_away_goals, 3),
                    "total": round(expected_home_goals + expected_away_goals, 3),
                },
                "xg_breakdown": {
                    "poisson": xg_poisson,
                    "form_based": xg_form,
                    "h2h_based": xg_h2h,
                },
                "probabilities": probabilities,
                "most_likely_score": f"{most_likely_score[0][0]}-{most_likely_score[0][1]}",
                "score_probabilities": {
                    f"{k[0]}-{k[1]}": round(v, 4)
                    for k, v in sorted(score_probs.items(), key=lambda x: -x[1])[:10]
                },
                "monte_carlo": {
                    "iterations": settings.MONTE_CARLO_ITERATIONS,
                    "home_win_pct": round(monte_carlo_results["home_win_pct"], 2),
                    "draw_pct": round(monte_carlo_results["draw_pct"], 2),
                    "away_win_pct": round(monte_carlo_results["away_win_pct"], 2),
                },
                "value_bets": value_bets,
                "model_confidence": self._calculate_model_confidence(
                    home_stats, away_stats, h2h
                ),
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                confidence=result_data["model_confidence"],
                processing_time_ms=processing_time,
                metadata={
                    "methods_used": ["poisson", "form_analysis", "h2h_analysis", "monte_carlo"],
                    "simulation_iterations": settings.MONTE_CARLO_ITERATIONS,
                },
            )
            
        except Exception as e:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Statistical engine failed: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e),
            )
    
    def _calculate_xg_poisson(
        self,
        home_stats: Dict[str, Any],
        away_stats: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate expected goals using Poisson model."""
        # League averages (would be dynamic in production)
        league_avg_goals_home = 1.55
        league_avg_goals_away = 1.25
        
        # Home team attack strength
        home_attack = (
            home_stats.get("goals_scored_avg", league_avg_goals_home) /
            league_avg_goals_home
        )
        
        # Away team defense weakness
        away_defense = (
            away_stats.get("goals_conceded_avg", league_avg_goals_away) /
            league_avg_goals_away
        )
        
        # Away team attack strength
        away_attack = (
            away_stats.get("goals_scored_avg", league_avg_goals_away) /
            league_avg_goals_away
        )
        
        # Home team defense weakness
        home_defense = (
            home_stats.get("goals_conceded_avg", league_avg_goals_home) /
            league_avg_goals_home
        )
        
        # Calculate expected goals
        expected_home = home_attack * away_defense * league_avg_goals_home
        expected_away = away_attack * home_defense * league_avg_goals_away
        
        # Apply home advantage (typically 10-15%)
        expected_home *= 1.12
        
        return {
            "home": max(0.1, min(4.0, expected_home)),
            "away": max(0.1, min(4.0, expected_away)),
        }
    
    def _calculate_xg_from_form(
        self,
        home_stats: Dict[str, Any],
        away_stats: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate expected goals based on recent form."""
        home_form = home_stats.get("form_last_5", "")
        away_form = away_stats.get("form_last_5", "")
        
        # Form scoring: W=3, D=1, L=0
        def form_score(form: str) -> float:
            points = {"W": 3, "D": 1, "L": 0}
            total = sum(points.get(c, 0) for c in form[-5:])
            return total / 15  # Normalize to 0-1
        
        home_form_factor = 0.8 + (form_score(home_form) * 0.4)
        away_form_factor = 0.8 + (form_score(away_form) * 0.4)
        
        base_home = home_stats.get("goals_scored_avg", 1.5)
        base_away = away_stats.get("goals_scored_avg", 1.3)
        
        return {
            "home": base_home * home_form_factor,
            "away": base_away * away_form_factor,
        }
    
    def _calculate_xg_from_h2h(
        self,
        h2h: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate expected goals from head-to-head history."""
        last_5 = h2h.get("last_5_meetings", [])
        
        if not last_5:
            return {"home": 1.5, "away": 1.3}
        
        home_goals = []
        away_goals = []
        
        for match in last_5[:5]:
            result = match.get("result", "0-0")
            parts = result.split("-")
            if len(parts) == 2:
                try:
                    home_goals.append(int(parts[0]))
                    away_goals.append(int(parts[1]))
                except ValueError:
                    pass
        
        if not home_goals:
            return {"home": 1.5, "away": 1.3}
        
        return {
            "home": sum(home_goals) / len(home_goals),
            "away": sum(away_goals) / len(away_goals),
        }
    
    async def _run_monte_carlo(
        self,
        expected_home: float,
        expected_away: float,
        iterations: int = 10000,
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation for match outcomes."""
        home_wins = 0
        draws = 0
        away_wins = 0
        score_distribution: Dict[Tuple[int, int], int] = {}
        
        # Set seed for reproducibility (optional)
        if settings.MONTE_CARLO_SEED:
            random.seed(settings.MONTE_CARLO_SEED)
            np.random.seed(settings.MONTE_CARLO_SEED)
        
        for _ in range(iterations):
            # Sample goals from Poisson distribution
            home_goals = np.random.poisson(expected_home)
            away_goals = np.random.poisson(expected_away)
            
            # Record result
            if home_goals > away_goals:
                home_wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                away_wins += 1
            
            # Track score distribution
            score = (int(home_goals), int(away_goals))
            score_distribution[score] = score_distribution.get(score, 0) + 1
        
        return {
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins,
            "home_win_pct": (home_wins / iterations) * 100,
            "draw_pct": (draws / iterations) * 100,
            "away_win_pct": (away_wins / iterations) * 100,
            "score_distribution": score_distribution,
            "mean_home_goals": expected_home,
            "mean_away_goals": expected_away,
        }
    
    def _calculate_probabilities(
        self,
        monte_carlo_results: Dict[str, Any],
    ) -> Dict[str, float]:
        """Convert Monte Carlo results to probability distributions."""
        return {
            "home_win": monte_carlo_results["home_win_pct"] / 100,
            "draw": monte_carlo_results["draw_pct"] / 100,
            "away_win": monte_carlo_results["away_win_pct"] / 100,
            "over_2_5": self._calc_over_under_prob(
                monte_carlo_results, threshold=2.5, over=True
            ),
            "under_2_5": self._calc_over_under_prob(
                monte_carlo_results, threshold=2.5, over=False
            ),
            "btts_yes": self._calc_btts_prob(monte_carlo_results, yes=True),
            "btts_no": self._calc_btts_prob(monte_carlo_results, yes=False),
        }
    
    def _calc_over_under_prob(
        self,
        results: Dict[str, Any],
        threshold: float = 2.5,
        over: bool = True,
    ) -> float:
        """Calculate over/under probability from score distribution."""
        score_dist = results.get("score_distribution", {})
        if not score_dist:
            return 0.5
        
        total = sum(score_dist.values())
        matching = sum(
            count for (home, away), count in score_dist.items()
            if (home + away > threshold) == over
        )
        
        return matching / total
    
    def _calc_btts_prob(
        self,
        results: Dict[str, Any],
        yes: bool = True,
    ) -> float:
        """Calculate both teams to score probability."""
        score_dist = results.get("score_distribution", {})
        if not score_dist:
            return 0.5
        
        total = sum(score_dist.values())
        matching = sum(
            count for (home, away), count in score_dist.items()
            if (home > 0 and away > 0) == yes
        )
        
        return matching / total
    
    def _calculate_score_probabilities(
        self,
        expected_home: float,
        expected_away: float,
        max_goals: int = 5,
    ) -> Dict[Tuple[int, int], float]:
        """Calculate exact score probabilities using Poisson."""
        probs = {}
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                home_prob = poisson.pmf(home_goals, expected_home)
                away_prob = poisson.pmf(away_goals, expected_away)
                probs[(home_goals, away_goals)] = home_prob * away_prob
        
        return probs
    
    def _detect_value_bets(
        self,
        probabilities: Dict[str, float],
        market_summary: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Detect value betting opportunities."""
        value_bets = []
        threshold = settings.VALUE_BET_THRESHOLD
        
        # 1X2 Market
        for outcome in ["home_win", "draw", "away_win"]:
            model_prob = probabilities.get(outcome, 0)
            implied_prob = market_summary.get(f"implied_prob_{outcome.split('_')[0]}", 0)
            
            if model_prob > implied_prob + threshold:
                value_pct = ((model_prob * (1/implied_prob)) - 1) * 100 if implied_prob > 0 else 0
                value_bets.append({
                    "market": "1x2",
                    "selection": outcome,
                    "model_probability": round(model_prob, 4),
                    "implied_probability": round(implied_prob, 4),
                    "value_percentage": round(value_pct, 2),
                    "recommendation": "BACK",
                })
        
        # Over/Under Market
        for market in ["over_2_5", "under_2_5"]:
            model_prob = probabilities.get(market, 0)
            # Simplified - would need actual odds in production
            implied_prob = 0.5  # Placeholder
            
            if model_prob > implied_prob + threshold:
                value_bets.append({
                    "market": "over_under",
                    "selection": market,
                    "model_probability": round(model_prob, 4),
                    "value_percentage": round(((model_prob / implied_prob) - 1) * 100, 2),
                    "recommendation": "BACK",
                })
        
        return value_bets
    
    def _calculate_model_confidence(
        self,
        home_stats: Dict[str, Any],
        away_stats: Dict[str, Any],
        h2h: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for the model prediction."""
        confidence = 0.5  # Base confidence
        
        # More data = more confidence
        if home_stats.get("form_last_5"):
            confidence += 0.1
        if away_stats.get("form_last_5"):
            confidence += 0.1
        if h2h.get("last_5_meetings"):
            confidence += 0.1
        if len(h2h.get("last_5_meetings", [])) >= 5:
            confidence += 0.1
        
        # Consistent stats = more confidence
        home_goals_avg = home_stats.get("goals_scored_avg", 0)
        if 0.5 <= home_goals_avg <= 3.0:
            confidence += 0.05
        
        return min(0.95, confidence)


# Singleton instance
_statistical_engine_instance: Optional[StatisticalEngineAgent] = None


def get_statistical_engine() -> StatisticalEngineAgent:
    """Get singleton instance of StatisticalEngineAgent."""
    global _statistical_engine_instance
    if _statistical_engine_instance is None:
        _statistical_engine_instance = StatisticalEngineAgent()
    return _statistical_engine_instance
