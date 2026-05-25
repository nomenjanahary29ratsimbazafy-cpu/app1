"""
Master Orchestrator Agent - Coordinates all specialized agents and fuses analyses.

Responsibilities:
- Fuses analyses from all agents
- Dynamic weighting based on confidence
- Final probability calculation
- Detailed justification generation
- Decision logging
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from app.agents.base_agent import AsyncAgent, AgentResult
from app.agents.data_collector import get_data_collector
from app.agents.statistical_engine import get_statistical_engine
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("agent.master_orchestrator")


class MasterOrchestratorAgent(AsyncAgent):
    """
    Master agent that coordinates all specialized agents and produces final predictions.
    
    Implements a weighted ensemble approach where each agent's output is weighted
    by its confidence score and historical performance.
    """
    
    def __init__(self):
        super().__init__(
            name="MasterOrchestrator",
            version="1.0.0",
            timeout_seconds=180,
            max_retries=1,
        )
        
        # Initialize sub-agents
        self.data_collector = get_data_collector()
        self.statistical_engine = get_statistical_engine()
        
        # Agent weights (can be dynamically adjusted)
        self.agent_weights = {
            "data_collector": settings.AGENT_WEIGHT_DATA_COLLECTOR,
            "statistical_engine": settings.AGENT_WEIGHT_STATISTICAL,
            "machine_learning": settings.AGENT_WEIGHT_ML,
            "market_analyzer": settings.AGENT_WEIGHT_MARKET,
            "psychological_context": settings.AGENT_WEIGHT_PSYCHOLOGICAL,
            "risk_management": settings.AGENT_WEIGHT_RISK,
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute full prediction pipeline for a match.
        
        Input data should contain:
        - match_id: Unique identifier
        - home_team: Home team info
        - away_team: Away team info
        - kickoff_time: Match start time
        """
        start_time = datetime.utcnow()
        
        try:
            match_id = input_data.get("match_id")
            if not match_id:
                return AgentResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    processing_time_ms=0,
                    error="match_id is required",
                )
            
            logger.info(f"Starting prediction pipeline for match {match_id}")
            
            # Step 1: Collect data
            data_result = await self.data_collector.run_with_retry(input_data)
            
            if not data_result.success:
                logger.warning(f"Data collection failed: {data_result.error}")
                # Continue with partial data
            
            collected_data = data_result.data
            
            # Step 2: Run statistical analysis
            stat_input = collected_data if collected_data else input_data
            stat_result = await self.statistical_engine.run_with_retry(stat_input)
            
            # Step 3: Run other agents (ML, Market, Psychological, Risk)
            # These would be implemented similarly to the statistical engine
            agent_results = {
                "data_collector": data_result,
                "statistical_engine": stat_result,
            }
            
            # Placeholder for other agents
            # In production, these would be actual agent calls
            ml_result = await self._run_ml_agent(input_data, collected_data)
            market_result = await self._run_market_agent(collected_data)
            psychological_result = await self._run_psychological_agent(input_data)
            risk_result = await self._run_risk_agent(stat_result)
            
            agent_results.update({
                "machine_learning": ml_result,
                "market_analyzer": market_result,
                "psychological_context": psychological_result,
                "risk_management": risk_result,
            })
            
            # Step 4: Fuse all analyses
            fused_result = self._fuse_analyses(agent_results)
            
            # Step 5: Generate justification
            justification = self._generate_justification(fused_result, agent_results)
            
            # Step 6: Calculate Kelly stake
            kelly_stake = self._calculate_kelly_stake(
                fused_result["probabilities"],
                fused_result.get("value_bets", []),
            )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            final_result = {
                "match_id": match_id,
                "generated_at": datetime.utcnow().isoformat(),
                "probabilities": fused_result["probabilities"],
                "expected_goals": fused_result.get("expected_goals", {}),
                "most_likely_score": fused_result.get("most_likely_score"),
                "confidence_score": fused_result["confidence"],
                "value_bets": fused_result.get("value_bets", []),
                "kelly_stake_recommendation": kelly_stake,
                "justification": justification,
                "agent_contributions": {
                    name: {
                        "success": result.success,
                        "confidence": result.confidence,
                        "processing_time_ms": result.processing_time_ms,
                        "weight": self.agent_weights.get(name, 1.0),
                    }
                    for name, result in agent_results.items()
                },
                "model_version": self.version,
                "processing_time_ms": processing_time,
            }
            
            return AgentResult(
                success=True,
                data=final_result,
                confidence=fused_result["confidence"],
                processing_time_ms=processing_time,
                metadata={
                    "agents_used": list(agent_results.keys()),
                    "all_agents_successful": all(r.success for r in agent_results.values()),
                },
            )
            
        except Exception as e:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Master orchestrator failed: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e),
            )
    
    def _fuse_analyses(self, agent_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Fuse analyses from all agents using weighted averaging."""
        
        # Extract probabilities from each agent
        all_probabilities = []
        weights = []
        
        for agent_name, result in agent_results.items():
            if not result.success:
                continue
            
            base_weight = self.agent_weights.get(agent_name, 1.0)
            adjusted_weight = base_weight * result.confidence
            weights.append(adjusted_weight)
            
            # Extract probabilities based on agent type
            probs = self._extract_probabilities(result.data, agent_name)
            if probs:
                all_probabilities.append((probs, adjusted_weight))
        
        if not all_probabilities:
            # Default uniform distribution
            return {
                "probabilities": {
                    "home_win": 0.33,
                    "draw": 0.34,
                    "away_win": 0.33,
                },
                "confidence": 0.3,
                "expected_goals": {"home": 1.5, "away": 1.3},
            }
        
        # Weighted average of probabilities
        total_weight = sum(weights)
        fused_probs: Dict[str, float] = {}
        
        prob_keys = ["home_win", "draw", "away_win", "over_2_5", "under_2_5", "btts_yes", "btts_no"]
        
        for key in prob_keys:
            weighted_sum = sum(
                probs.get(key, 0) * weight
                for probs, weight in all_probabilities
            )
            fused_probs[key] = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Normalize 1X2 probabilities to sum to 1
        x12_total = fused_probs.get("home_win", 0) + fused_probs.get("draw", 0) + fused_probs.get("away_win", 0)
        if x12_total > 0:
            fused_probs["home_win"] /= x12_total
            fused_probs["draw"] /= x12_total
            fused_probs["away_win"] /= x12_total
        
        # Calculate overall confidence
        avg_confidence = sum(
            result.confidence * self.agent_weights.get(name, 1.0)
            for name, result in agent_results.items()
            if result.success
        ) / total_weight if total_weight > 0 else 0
        
        # Get expected goals from statistical engine
        expected_goals = agent_results.get("statistical_engine", {}).data.get("expected_goals", {})
        
        # Get most likely score
        most_likely_score = agent_results.get("statistical_engine", {}).data.get("most_likely_score")
        
        # Aggregate value bets
        all_value_bets = []
        for result in agent_results.values():
            if result.success and result.data.get("value_bets"):
                all_value_bets.extend(result.data["value_bets"])
        
        return {
            "probabilities": fused_probs,
            "confidence": min(0.95, avg_confidence),
            "expected_goals": expected_goals,
            "most_likely_score": most_likely_score,
            "value_bets": all_value_bets,
        }
    
    def _extract_probabilities(
        self,
        data: Dict[str, Any],
        agent_name: str,
    ) -> Dict[str, float]:
        """Extract probability estimates from agent output."""
        if not data:
            return {}
        
        if agent_name == "statistical_engine":
            return data.get("probabilities", {})
        
        if agent_name == "machine_learning":
            return data.get("predicted_probabilities", {})
        
        if agent_name == "market_analyzer":
            # Convert odds to implied probabilities
            odds = data.get("best_odds", {})
            if odds:
                return {
                    "home_win": 1 / odds.get("home_win", 2),
                    "draw": 1 / odds.get("draw", 3.5),
                    "away_win": 1 / odds.get("away_win", 2),
                }
        
        return {}
    
    def _generate_justification(
        self,
        fused_result: Dict[str, Any],
        agent_results: Dict[str, AgentResult],
    ) -> str:
        """Generate human-readable justification for the prediction."""
        justifications = []
        
        probs = fused_result.get("probabilities", {})
        
        # Determine most likely outcome
        outcomes = [
            ("Home Win", probs.get("home_win", 0)),
            ("Draw", probs.get("draw", 0)),
            ("Away Win", probs.get("away_win", 0)),
        ]
        most_likely = max(outcomes, key=lambda x: x[1])
        
        justifications.append(
            f"Our model predicts {most_likely[0]} as the most likely outcome "
            f"with {most_likely[1]*100:.1f}% probability."
        )
        
        # Add statistical reasoning
        stat_result = agent_results.get("statistical_engine")
        if stat_result and stat_result.success:
            xg = stat_result.data.get("expected_goals", {})
            justifications.append(
                f"Expected goals analysis suggests {xg.get('home', 0):.2f} - {xg.get('away', 0):.2f}."
            )
        
        # Add value bet information
        value_bets = fused_result.get("value_bets", [])
        if value_bets:
            best_bet = max(value_bets, key=lambda x: x.get("value_percentage", 0))
            justifications.append(
                f"Value opportunity detected: {best_bet.get('selection')} "
                f"with {best_bet.get('value_percentage', 0):.1f}% value."
            )
        
        # Add confidence explanation
        confidence = fused_result.get("confidence", 0)
        if confidence > 0.75:
            justifications.append("High confidence based on strong data quality and model agreement.")
        elif confidence > 0.5:
            justifications.append("Moderate confidence with reasonable data support.")
        else:
            justifications.append("Lower confidence due to limited data or model disagreement.")
        
        return " ".join(justifications)
    
    def _calculate_kelly_stake(
        self,
        probabilities: Dict[str, float],
        value_bets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate optimal stake using Kelly Criterion."""
        if not value_bets:
            return {"recommended_stake_pct": 0, "reason": "No value bets detected"}
        
        best_bet = max(value_bets, key=lambda x: x.get("value_percentage", 0))
        
        # Kelly formula: f* = (bp - q) / b
        # where b = odds - 1, p = probability, q = 1 - p
        model_prob = best_bet.get("model_probability", 0)
        
        # Estimate odds from implied probability
        implied_prob = model_prob / (1 + best_bet.get("value_percentage", 0) / 100)
        odds = 1 / implied_prob if implied_prob > 0 else 0
        
        if odds <= 1:
            return {"recommended_stake_pct": 0, "reason": "Invalid odds"}
        
        b = odds - 1
        p = model_prob
        q = 1 - p
        
        kelly_full = (b * p - q) / b if b > 0 else 0
        
        # Apply fractional Kelly (default 25%)
        kelly_fractional = kelly_full * settings.KELLY_FRACTION
        
        # Apply maximum stake limit
        recommended = min(kelly_fractional, settings.MAX_STAKE_PERCENTAGE)
        recommended = max(0, recommended)  # No negative stakes
        
        return {
            "kelly_full_pct": round(kelly_full * 100, 2),
            "kelly_fractional_pct": round(kelly_fractional * 100, 2),
            "recommended_stake_pct": round(recommended * 100, 2),
            "odds_used": round(odds, 2),
            "bet_selection": best_bet.get("selection"),
        }
    
    async def _run_ml_agent(
        self,
        input_data: Dict[str, Any],
        collected_data: Dict[str, Any],
    ) -> AgentResult:
        """Placeholder for ML agent - would load trained models."""
        # In production, this would load and run trained ML models
        return AgentResult(
            success=True,
            data={
                "predicted_probabilities": {
                    "home_win": 0.45,
                    "draw": 0.28,
                    "away_win": 0.27,
                },
                "model_type": "ensemble",
            },
            confidence=0.7,
            processing_time_ms=100,
        )
    
    async def _run_market_agent(
        self,
        collected_data: Dict[str, Any],
    ) -> AgentResult:
        """Placeholder for Market Analyzer agent."""
        return AgentResult(
            success=True,
            data={
                "best_odds": {
                    "home_win": 2.10,
                    "draw": 3.50,
                    "away_win": 3.60,
                },
                "sharp_money_detected": False,
            },
            confidence=0.8,
            processing_time_ms=50,
        )
    
    async def _run_psychological_agent(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """Placeholder for Psychological Context agent."""
        return AgentResult(
            success=True,
            data={
                "home_motivation": 0.75,
                "away_motivation": 0.65,
                "pressure_factor": 0.4,
            },
            confidence=0.6,
            processing_time_ms=30,
        )
    
    async def _run_risk_agent(
        self,
        stat_result: AgentResult,
    ) -> AgentResult:
        """Placeholder for Risk Management agent."""
        return AgentResult(
            success=True,
            data={
                "max_exposure": 0.05,
                "risk_level": "medium",
            },
            confidence=0.9,
            processing_time_ms=20,
        )


# Singleton instance
_master_orchestrator_instance: Optional[MasterOrchestratorAgent] = None


def get_master_orchestrator() -> MasterOrchestratorAgent:
    """Get singleton instance of MasterOrchestratorAgent."""
    global _master_orchestrator_instance
    if _master_orchestrator_instance is None:
        _master_orchestrator_instance = MasterOrchestratorAgent()
    return _master_orchestrator_instance
