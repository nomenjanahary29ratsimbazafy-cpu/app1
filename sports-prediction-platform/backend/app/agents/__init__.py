"""
Multi-Agent System for Sports Prediction Platform.

This package contains all specialized agents:
- DataCollector: Collects sports data from APIs
- StatisticalEngine: Poisson, xG, Monte Carlo simulations
- MachineLearningAgent: ML predictions and pattern detection
- MarketAnalyzer: Odds movement and sharp money detection
- PsychologicalContext: Motivation, fatigue, pressure analysis
- RiskManagement: Bankroll and bet sizing
- MasterOrchestrator: Fuses all analyses
"""

from app.agents.base_agent import BaseAgent, AsyncAgent, AgentResult, AgentStatus
from app.agents.data_collector import DataCollectorAgent, get_data_collector
from app.agents.statistical_engine import StatisticalEngineAgent, get_statistical_engine
from app.agents.master_orchestrator import MasterOrchestratorAgent, get_master_orchestrator

__all__ = [
    "BaseAgent",
    "AsyncAgent",
    "AgentResult",
    "AgentStatus",
    "DataCollectorAgent",
    "get_data_collector",
    "StatisticalEngineAgent",
    "get_statistical_engine",
    "MasterOrchestratorAgent",
    "get_master_orchestrator",
]
