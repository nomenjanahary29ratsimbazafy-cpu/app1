"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field, HttpUrl, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SportType(str, Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    HOCKEY = "hockey"
    BASEBALL = "baseball"
    HANDBALL = "handball"
    VOLLEYBALL = "volleyball"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class BetType(str, Enum):
    X12 = "1x2"
    OVER_UNDER = "over_under"
    ASIAN_HANDICAP = "asian_handicap"
    BOTH_TEAMS_SCORE = "both_teams_score"
    CORRECT_SCORE = "correct_score"
    DOUBLE_CHANCE = "double_chance"


class PredictionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    VOID = "void"
    CASHOUT = "cashout"


class AgentType(str, Enum):
    DATA_COLLECTOR = "data_collector"
    STATISTICAL_ENGINE = "statistical_engine"
    MACHINE_LEARNING = "machine_learning"
    MARKET_ANALYZER = "market_analyzer"
    PSYCHOLOGICAL_CONTEXT = "psychological_context"
    RISK_MANAGEMENT = "risk_management"
    MASTER_ORCHESTRATOR = "master_orchestrator"


class OddsMovement(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# ============================================================================
# TEAM & PLAYER MODELS
# ============================================================================

class TeamBase(BaseModel):
    name: str
    short_name: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    founded_year: Optional[int] = None
    stadium_name: Optional[str] = None
    stadium_capacity: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None


class TeamCreate(TeamBase):
    league_id: Optional[str] = None


class TeamResponse(TeamBase):
    id: str
    league_id: Optional[str] = None
    form_last_5: Optional[str] = None
    rating: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    name: str
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    market_value_eur: Optional[float] = None


class PlayerCreate(PlayerBase):
    team_id: Optional[str] = None


class PlayerResponse(PlayerBase):
    id: str
    team_id: Optional[str] = None
    is_injured: bool = False
    injury_details: Optional[str] = None
    expected_return: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# MATCH MODELS
# ============================================================================

class MatchBase(BaseModel):
    kickoff_time: datetime
    venue: Optional[str] = None
    season: Optional[str] = None
    round: Optional[str] = None


class MatchCreate(MatchBase):
    league_id: Optional[str] = None
    home_team_id: str
    away_team_id: str


class MatchStatistics(BaseModel):
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_yellow_cards: Optional[int] = None
    away_yellow_cards: Optional[int] = None
    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None


class WeatherConditions(BaseModel):
    temperature: Optional[float] = None
    conditions: Optional[str] = None
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None


class MatchResponse(MatchBase, MatchStatistics, WeatherConditions):
    id: str
    league_id: Optional[str] = None
    home_team_id: str
    away_team_id: str
    status: MatchStatus = MatchStatus.SCHEDULED
    home_score: int = 0
    away_score: int = 0
    home_score_ht: int = 0
    away_score_ht: int = 0
    referee: Optional[str] = None
    attendance: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MatchWithTeams(MatchResponse):
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None
    league: Optional[str] = None


# ============================================================================
# ODDS MODELS
# ============================================================================

class BookmakerBase(BaseModel):
    name: str
    country: Optional[str] = None
    license_number: Optional[str] = None


class BookmakerCreate(BookmakerBase):
    pass


class BookmakerResponse(BookmakerBase):
    id: str
    is_active: bool = True
    reliability_score: float = 1.0
    created_at: datetime
    
    class Config:
        from_attributes = True


class OddsBase(BaseModel):
    bet_type: BetType
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None
    asian_handicap_home: Optional[float] = None
    asian_handicap_away: Optional[float] = None
    handicap_value: Optional[float] = None


class OddsCreate(OddsBase):
    match_id: str
    bookmaker_id: str
    volume: Optional[float] = None


class OddsResponse(OddsBase):
    id: str
    match_id: str
    bookmaker_id: str
    implied_prob_home: Optional[float] = None
    implied_prob_draw: Optional[float] = None
    implied_prob_away: Optional[float] = None
    margin: Optional[float] = None
    opening_home: Optional[float] = None
    opening_draw: Optional[float] = None
    opening_away: Optional[float] = None
    movement_direction: Optional[OddsMovement] = None
    movement_percentage: Optional[float] = None
    is_active: bool = True
    captured_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PREDICTION MODELS
# ============================================================================

class PredictionBase(BaseModel):
    home_win_prob: float = Field(ge=0, le=1)
    draw_prob: float = Field(ge=0, le=1)
    away_win_prob: float = Field(ge=0, le=1)
    over_2_5_prob: Optional[float] = Field(None, ge=0, le=1)
    under_2_5_prob: Optional[float] = Field(None, ge=0, le=1)
    btts_yes_prob: Optional[float] = Field(None, ge=0, le=1)
    btts_no_prob: Optional[float] = Field(None, ge=0, le=1)
    expected_home_goals: Optional[float] = None
    expected_away_goals: Optional[float] = None
    most_likely_score: Optional[str] = None
    score_probabilities: Optional[Dict[str, float]] = None
    confidence_score: float = Field(ge=0, le=1)
    model_version: Optional[str] = None


class PredictionCreate(PredictionBase):
    match_id: str
    value_bet_detected: bool = False
    value_bet_type: Optional[BetType] = None
    value_bet_selection: Optional[str] = None
    value_percentage: Optional[float] = None
    kelly_stake: Optional[float] = None


class PredictionResponse(PredictionBase):
    id: str
    match_id: str
    value_bet_detected: bool
    value_bet_type: Optional[BetType] = None
    value_bet_selection: Optional[str] = None
    value_percentage: Optional[float] = None
    kelly_stake: Optional[float] = None
    status: PredictionStatus = PredictionStatus.PENDING
    actual_result: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PredictionWithMatch(PredictionResponse):
    match: Optional[MatchWithTeams] = None


class AgentAnalysisBase(BaseModel):
    agent_type: AgentType
    input_data: Dict[str, Any]
    analysis_output: Dict[str, Any]
    confidence_score: float
    weight_assigned: float
    processing_time_ms: Optional[int] = None
    model_version: Optional[str] = None


class AgentAnalysisResponse(AgentAnalysisBase):
    id: str
    prediction_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# MARKET ANALYSIS MODELS
# ============================================================================

class MarketSignalBase(BaseModel):
    sharp_money_detected: bool = False
    sharp_money_direction: Optional[str] = None
    sharp_money_confidence: Optional[float] = None
    reverse_line_movement: bool = False
    public_betting_percentage: Optional[Dict[str, int]] = None
    arbitrage_opportunity: bool = False
    arbitrage_profit_percentage: Optional[float] = None
    anomaly_detected: bool = False
    anomaly_type: Optional[str] = None
    anomaly_severity: Optional[str] = None
    liquidity_score: Optional[float] = None
    market_efficiency_score: Optional[float] = None


class MarketSignalResponse(MarketSignalBase):
    id: str
    match_id: str
    detected_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PSYCHOLOGICAL CONTEXT MODELS
# ============================================================================

class PsychologicalFactorsBase(BaseModel):
    home_motivation_score: float = Field(ge=0, le=1)
    home_fatigue_score: float = Field(ge=0, le=1)
    home_pressure_score: float = Field(ge=0, le=1)
    home_momentum_score: float = Field(ge=-1, le=1)
    home_rivalry_intensity: float = Field(ge=0, le=1)
    away_motivation_score: float = Field(ge=0, le=1)
    away_fatigue_score: float = Field(ge=0, le=1)
    away_pressure_score: float = Field(ge=0, le=1)
    away_momentum_score: float = Field(ge=-1, le=1)
    away_rivalry_intensity: float = Field(ge=0, le=1)
    derby_match: bool = False
    relegation_battle: bool = False
    title_race: bool = False
    european_qualification: bool = False
    cup_final: bool = False
    recent_manager_change_home: bool = False
    recent_manager_change_away: bool = False
    controversy_level: Optional[str] = None
    home_emotional_state: Optional[str] = None
    away_emotional_state: Optional[str] = None
    overall_intensity_score: float = Field(ge=0, le=1)


class PsychologicalFactorsResponse(PsychologicalFactorsBase):
    id: str
    match_id: str
    analyzed_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# RISK MANAGEMENT MODELS
# ============================================================================

class BankrollBase(BaseModel):
    user_id: str
    initial_amount: float = Field(gt=0)
    currency: str = "EUR"
    risk_level: str = "medium"
    kelly_fraction: float = Field(default=0.25, ge=0, le=1)
    max_stake_percentage: float = Field(default=0.05, ge=0, le=1)
    stop_loss_percentage: float = Field(default=0.20, ge=0, le=1)


class BankrollCreate(BankrollBase):
    pass


class BankrollResponse(BankrollBase):
    id: str
    current_amount: float
    peak_amount: float = 0
    lowest_amount: float = 0
    total_bets: int = 0
    winning_bets: int = 0
    losing_bets: int = 0
    roi: float = 0
    yield: float = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BetBase(BaseModel):
    bet_type: BetType
    selection: str
    stake: float = Field(gt=0)
    odds: float = Field(gt=1)
    bookmaker_id: Optional[str] = None


class BetCreate(BetBase):
    prediction_id: Optional[str] = None
    match_id: str


class BetResponse(BetBase):
    id: str
    bankroll_id: str
    prediction_id: Optional[str] = None
    match_id: str
    potential_return: float
    actual_return: float = 0
    kelly_recommended: Optional[float] = None
    kelly_actual: Optional[float] = None
    status: PredictionStatus = PredictionStatus.PENDING
    result_notes: Optional[str] = None
    placed_at: datetime
    settled_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ML MODEL MODELS
# ============================================================================

class MLModelBase(BaseModel):
    name: str
    version: str
    model_type: str


class MLModelCreate(MLModelBase):
    pass


class MLModelResponse(MLModelBase):
    id: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    log_loss: Optional[float] = None
    training_samples: Optional[int] = None
    features_count: Optional[int] = None
    training_start: Optional[datetime] = None
    training_end: Optional[datetime] = None
    model_path: Optional[str] = None
    feature_importance: Optional[Dict[str, float]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    is_active: bool = False
    is_production: bool = False
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SYSTEM MODELS
# ============================================================================

class AgentStatusBase(BaseModel):
    agent_type: AgentType
    status: str = "idle"
    version: Optional[str] = None


class AgentStatusResponse(AgentStatusBase):
    id: str
    last_heartbeat: Optional[datetime] = None
    total_predictions: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    avg_processing_time_ms: Optional[int] = None
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SystemLogBase(BaseModel):
    service_name: str
    log_level: str
    message: str
    context: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class SystemLogResponse(SystemLogBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# API RESPONSE WRAPPERS
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class PaginatedResponse(APIResponse):
    """Paginated API response."""
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0
    
    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
