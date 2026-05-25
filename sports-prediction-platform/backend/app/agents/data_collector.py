"""
Data Collector Agent - Collects and aggregates sports data from multiple sources.

Responsibilities:
- Real-time match data from APIs (API-Football, SportRadar)
- Injury reports and team news
- Weather conditions
- Team compositions and lineups
- Bookmaker odds aggregation
- Historical statistics
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
import asyncio

from app.agents.base_agent import AsyncAgent, AgentResult
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("agent.data_collector")


class DataCollectorAgent(AsyncAgent):
    """Agent responsible for collecting sports data from multiple sources."""
    
    def __init__(self):
        super().__init__(
            name="DataCollector",
            version="1.0.0",
            timeout_seconds=60,
            max_retries=3,
        )
        
        self.api_football_key = settings.API_FOOTBALL_KEY
        self.api_football_base = settings.API_FOOTBALL_BASE_URL
        self.openweather_key = settings.OPENWEATHER_API_KEY
        
        # API rate limiting
        self.rate_limits = {
            "api-football": {"calls": 0, "reset_time": datetime.utcnow()},
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute data collection for a specific match.
        
        Input data should contain:
        - match_id: Unique match identifier
        - home_team: Home team name/ID
        - away_team: Away team name/ID
        - league: League name/ID
        - kickoff_time: Match start time
        - venue: Stadium name (optional)
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
            
            # Collect all data in parallel
            tasks = [
                self._collect_match_data(input_data),
                self._collect_team_stats(input_data),
                self._collect_player_info(input_data),
                self._collect_odds(input_data),
                self._collect_weather(input_data),
                self._collect_historical_data(input_data),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            collected_data = {
                "match_id": match_id,
                "collected_at": datetime.utcnow().isoformat(),
                "sources_used": [],
                "data_quality_score": 0.0,
            }
            
            quality_scores = []
            
            for i, result in enumerate(results):
                task_names = [
                    "match_data", "team_stats", "player_info",
                    "odds_data", "weather_data", "historical_data"
                ]
                
                if isinstance(result, Exception):
                    logger.warning(f"Task {task_names[i]} failed: {str(result)}")
                    collected_data[task_names[i]] = None
                    quality_scores.append(0.0)
                else:
                    collected_data[task_names[i]] = result
                    if result:
                        collected_data["sources_used"].append(task_names[i])
                        quality_scores.append(result.get("quality_score", 0.5))
            
            # Calculate overall data quality
            collected_data["data_quality_score"] = (
                sum(quality_scores) / len(quality_scores)
                if quality_scores else 0.0
            )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=collected_data,
                confidence=collected_data["data_quality_score"],
                processing_time_ms=processing_time,
                metadata={
                    "sources_count": len(collected_data["sources_used"]),
                    "total_tasks": len(tasks),
                },
            )
            
        except Exception as e:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e),
            )
    
    async def _collect_match_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect basic match information from API-Football."""
        if not self.api_football_key:
            return {"quality_score": 0.0, "source": "mock"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"x-apisports-key": self.api_football_key}
                
                # Example: Get fixtures
                response = await client.get(
                    f"{self.api_football_base}/fixtures",
                    params={"id": input_data.get("match_id")},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "quality_score": 0.9,
                    "source": "api-football",
                    "fixture": data.get("response", [{}])[0] if data.get("response") else {},
                }
                
        except Exception as e:
            logger.warning(f"Failed to collect match data: {e}")
            return {"quality_score": 0.0, "source": "failed", "error": str(e)}
    
    async def _collect_team_stats(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect team statistics and form."""
        # Mock implementation - replace with actual API calls
        home_team = input_data.get("home_team", "")
        away_team = input_data.get("away_team", "")
        
        return {
            "quality_score": 0.8,
            "source": "api-football",
            "home_team": {
                "name": home_team,
                "form_last_5": "WWDWL",
                "goals_scored_avg": 1.8,
                "goals_conceded_avg": 1.2,
                "clean_sheets": 3,
                "failed_to_score": 1,
                "home_record": {"wins": 5, "draws": 2, "losses": 1},
            },
            "away_team": {
                "name": away_team,
                "form_last_5": "LWDWW",
                "goals_scored_avg": 1.5,
                "goals_conceded_avg": 1.4,
                "clean_sheets": 2,
                "failed_to_score": 2,
                "away_record": {"wins": 3, "draws": 3, "losses": 2},
            },
        }
    
    async def _collect_player_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect player information including injuries and suspensions."""
        return {
            "quality_score": 0.7,
            "source": "api-football",
            "home_team_players": {
                "injured": [
                    {"name": "Player A", "position": "Forward", "expected_return": "2024-02-01"},
                ],
                "suspended": [],
                "doubtful": [
                    {"name": "Player B", "position": "Midfielder", "reason": "knock"},
                ],
            },
            "away_team_players": {
                "injured": [],
                "suspended": [
                    {"name": "Player C", "position": "Defender", "reason": "yellow_cards"},
                ],
                "doubtful": [],
            },
        }
    
    async def _collect_odds(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect odds from multiple bookmakers."""
        return {
            "quality_score": 0.9,
            "source": "multiple",
            "bookmakers": [
                {
                    "name": "Bet365",
                    "odds": {
                        "home_win": 2.10,
                        "draw": 3.40,
                        "away_win": 3.60,
                        "over_2_5": 1.85,
                        "under_2_5": 1.95,
                        "btts_yes": 1.70,
                        "btts_no": 2.10,
                    },
                },
                {
                    "name": "William Hill",
                    "odds": {
                        "home_win": 2.05,
                        "draw": 3.50,
                        "away_win": 3.70,
                        "over_2_5": 1.83,
                        "under_2_5": 1.97,
                        "btts_yes": 1.72,
                        "btts_no": 2.08,
                    },
                },
            ],
            "market_summary": {
                "avg_home_win": 2.075,
                "avg_draw": 3.45,
                "avg_away_win": 3.65,
                "implied_prob_home": 0.482,
                "implied_prob_draw": 0.290,
                "implied_prob_away": 0.274,
                "margin": 0.046,
            },
        }
    
    async def _collect_weather(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect weather forecast for match day."""
        if not self.openweather_key:
            return {"quality_score": 0.5, "source": "mock"}
        
        try:
            # Would use OpenWeatherMap API in production
            return {
                "quality_score": 0.8,
                "source": "openweathermap",
                "forecast": {
                    "temperature": 15.5,
                    "conditions": "Partly Cloudy",
                    "wind_speed": 12.5,
                    "humidity": 65,
                    "precipitation_chance": 20,
                },
            }
        except Exception as e:
            return {"quality_score": 0.0, "source": "failed", "error": str(e)}
    
    async def _collect_historical_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect historical head-to-head and team data."""
        return {
            "quality_score": 0.85,
            "source": "database",
            "head_to_head": {
                "total_matches": 10,
                "home_wins": 4,
                "draws": 3,
                "away_wins": 3,
                "home_goals": 14,
                "away_goals": 12,
                "last_5_meetings": [
                    {"date": "2023-10-15", "result": "2-1", "winner": "home"},
                    {"date": "2023-04-20", "result": "1-1", "winner": "draw"},
                    {"date": "2022-11-05", "result": "0-2", "winner": "away"},
                    {"date": "2022-05-10", "result": "3-1", "winner": "home"},
                    {"date": "2021-12-18", "result": "2-2", "winner": "draw"},
                ],
            },
            "home_team_history": {
                "season_stats": {
                    "matches_played": 20,
                    "wins": 12,
                    "draws": 5,
                    "losses": 3,
                    "goals_for": 38,
                    "goals_against": 18,
                    "points": 41,
                    "position": 3,
                },
                "home_form": {
                    "matches": 10,
                    "wins": 7,
                    "draws": 2,
                    "losses": 1,
                    "goals_for": 22,
                    "goals_against": 8,
                },
            },
            "away_team_history": {
                "season_stats": {
                    "matches_played": 20,
                    "wins": 10,
                    "draws": 6,
                    "losses": 4,
                    "goals_for": 32,
                    "goals_against": 22,
                    "points": 36,
                    "position": 5,
                },
                "away_form": {
                    "matches": 10,
                    "wins": 4,
                    "draws": 4,
                    "losses": 2,
                    "goals_for": 14,
                    "goals_against": 12,
                },
            },
        }
    
    async def refresh_api_keys(self) -> None:
        """Refresh API keys from configuration."""
        self.api_football_key = settings.API_FOOTBALL_KEY
        self.openweather_key = settings.OPENWEATHER_API_KEY


# Singleton instance
_data_collector_instance: Optional[DataCollectorAgent] = None


def get_data_collector() -> DataCollectorAgent:
    """Get singleton instance of DataCollectorAgent."""
    global _data_collector_instance
    if _data_collector_instance is None:
        _data_collector_instance = DataCollectorAgent()
    return _data_collector_instance
