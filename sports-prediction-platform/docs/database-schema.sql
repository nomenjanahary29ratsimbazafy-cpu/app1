-- Sports Prediction Platform Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE sport_type AS ENUM ('football', 'basketball', 'tennis', 'hockey', 'baseball', 'handball', 'volleyball');
CREATE_TYPE match_status AS ENUM ('scheduled', 'live', 'finished', 'postponed', 'cancelled');
CREATE TYPE bet_type AS ENUM ('1x2', 'over_under', 'asian_handicap', 'both_teams_score', 'correct_score', 'double_chance');
CREATE_TYPE prediction_status AS ENUM ('pending', 'active', 'won', 'lost', 'void', 'cashout');
CREATE TYPE agent_type AS ENUM ('data_collector', 'statistical_engine', 'machine_learning', 'market_analyzer', 'psychological_context', 'risk_management', 'master_orchestrator');
CREATE TYPE odds_movement AS ENUM ('up', 'down', 'stable');

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Sports & Leagues
CREATE TABLE sports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name sport_type NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leagues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport_id UUID REFERENCES sports(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    tier INTEGER DEFAULT 1,
    logo_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, country)
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id UUID REFERENCES leagues(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    logo_url VARCHAR(500),
    founded_year INTEGER,
    stadium_name VARCHAR(255),
    stadium_capacity INTEGER,
    city VARCHAR(100),
    country VARCHAR(100),
    form_last_5 VARCHAR(5), -- e.g., 'WWDLL'
    rating DECIMAL(5,2), -- ELO or similar rating
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Players
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50),
    jersey_number INTEGER,
    date_of_birth DATE,
    nationality VARCHAR(100),
    height_cm INTEGER,
    weight_kg INTEGER,
    market_value_eur DECIMAL(12,2),
    is_injured BOOLEAN DEFAULT FALSE,
    injury_details TEXT,
    expected_return DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id UUID REFERENCES leagues(id) ON DELETE SET NULL,
    season VARCHAR(20), -- e.g., '2024-2025'
    round VARCHAR(50),
    home_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    kickoff_time TIMESTAMP WITH TIME ZONE NOT NULL,
    venue VARCHAR(255),
    status match_status DEFAULT 'scheduled',
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    home_score_ht INTEGER DEFAULT 0,
    away_score_ht INTEGER DEFAULT 0,
    
    -- Match statistics
    home_possession DECIMAL(5,2),
    away_possession DECIMAL(5,2),
    home_shots INTEGER,
    away_shots INTEGER,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_xg DECIMAL(5,3),
    away_xg DECIMAL(5,3),
    home_corners INTEGER,
    away_corners INTEGER,
    home_yellow_cards INTEGER,
    away_yellow_cards INTEGER,
    home_red_cards INTEGER,
    away_red_cards INTEGER,
    
    -- Weather conditions
    weather_temperature DECIMAL(5,2),
    weather_conditions VARCHAR(100),
    weather_wind_speed DECIMAL(5,2),
    weather_humidity DECIMAL(5,2),
    
    referee VARCHAR(255),
    attendance INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_scores CHECK (home_score >= 0 AND away_score >= 0)
);

-- ============================================================================
-- ODDS & BOOKMAKERS
-- ============================================================================

CREATE TABLE bookmakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100),
    license_number VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    reliability_score DECIMAL(3,2) DEFAULT 1.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE odds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker_id UUID REFERENCES bookmakers(id) ON DELETE CASCADE,
    bet_type bet_type NOT NULL,
    
    -- Odds values
    home_win DECIMAL(10,4),
    draw DECIMAL(10,4),
    away_win DECIMAL(10,4),
    over_2_5 DECIMAL(10,4),
    under_2_5 DECIMAL(10,4),
    btts_yes DECIMAL(10,4),
    btts_no DECIMAL(10,4),
    asian_handicap_home DECIMAL(10,4),
    asian_handicap_away DECIMAL(10,4),
    handicap_value DECIMAL(5,2),
    
    -- Market info
    implied_prob_home DECIMAL(7,6),
    implied_prob_draw DECIMAL(7,6),
    implied_prob_away DECIMAL(7,6),
    margin DECIMAL(7,6),
    volume DECIMAL(15,2), -- Betting volume
    
    -- Movement tracking
    opening_home DECIMAL(10,4),
    opening_draw DECIMAL(10,4),
    opening_away DECIMAL(10,4),
    movement_direction odds_movement,
    movement_percentage DECIMAL(7,4),
    
    is_active BOOLEAN DEFAULT TRUE,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_odds UNIQUE(match_id, bookmaker_id, bet_type, captured_at)
);

-- Odds history for tracking movements
CREATE TABLE odds_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    odds_id UUID REFERENCES odds(id) ON DELETE CASCADE,
    home_win DECIMAL(10,4),
    draw DECIMAL(10,4),
    away_win DECIMAL(10,4),
    volume DECIMAL(15,2),
    movement_type odds_movement,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PREDICTIONS & ANALYTICS
-- ============================================================================

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    
    -- Probability distributions
    home_win_prob DECIMAL(7,6),
    draw_prob DECIMAL(7,6),
    away_win_prob DECIMAL(7,6),
    over_2_5_prob DECIMAL(7,6),
    under_2_5_prob DECIMAL(7,6),
    btts_yes_prob DECIMAL(7,6),
    btts_no_prob DECIMAL(7,6),
    
    -- Expected goals
    expected_home_goals DECIMAL(5,3),
    expected_away_goals DECIMAL(5,3),
    
    -- Most likely scores
    most_likely_score VARCHAR(10), -- e.g., '2-1'
    score_probabilities JSONB, -- {"1-0": 0.12, "2-0": 0.10, ...}
    
    -- Confidence metrics
    confidence_score DECIMAL(5,4), -- 0-1
    model_version VARCHAR(50),
    
    -- Value betting
    value_bet_detected BOOLEAN DEFAULT FALSE,
    value_bet_type bet_type,
    value_bet_selection VARCHAR(50),
    value_percentage DECIMAL(7,4),
    kelly_stake DECIMAL(7,4), -- Kelly criterion recommendation
    
    -- Status
    status prediction_status DEFAULT 'pending',
    actual_result VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_probs CHECK (
        home_win_prob + draw_prob + away_win_prob BETWEEN 0.99 AND 1.01
    )
);

-- Agent contributions to predictions
CREATE TABLE agent_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    agent_type agent_type NOT NULL,
    
    -- Analysis results
    input_data JSONB NOT NULL, -- Raw data used by agent
    analysis_output JSONB NOT NULL, -- Processed analysis
    confidence_score DECIMAL(5,4),
    weight_assigned DECIMAL(5,4), -- Weight in final prediction
    
    -- Processing info
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Monte Carlo simulation results
CREATE TABLE monte_carlo_simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    iterations INTEGER NOT NULL,
    
    -- Results distribution
    home_wins INTEGER,
    draws INTEGER,
    away_wins INTEGER,
    
    -- Score distribution
    score_distribution JSONB, -- {"1-0": 1234, "2-1": 987, ...}
    
    -- Statistics
    mean_home_goals DECIMAL(5,3),
    mean_away_goals DECIMAL(5,3),
    std_home_goals DECIMAL(5,3),
    std_away_goals DECIMAL(5,3),
    
    percentiles JSONB, -- {"p10": "...", "p50": "...", "p90": "..."}
    
    simulation_seed INTEGER,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MARKET ANALYSIS
-- ============================================================================

CREATE TABLE market_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    
    -- Signal types
    sharp_money_detected BOOLEAN DEFAULT FALSE,
    sharp_money_direction VARCHAR(20), -- 'home', 'draw', 'away'
    sharp_money_confidence DECIMAL(5,4),
    
    reverse_line_movement BOOLEAN DEFAULT FALSE,
    public_betting_percentage JSONB, -- {"home": 65, "draw": 20, "away": 15}
    
    arbitrage_opportunity BOOLEAN DEFAULT FALSE,
    arbitrage_profit_percentage DECIMAL(7,4),
    arbitrage_bookmakers UUID[], -- Array of bookmaker IDs
    
    anomaly_detected BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(100),
    anomaly_severity VARCHAR(20), -- 'low', 'medium', 'high'
    
    liquidity_score DECIMAL(5,4),
    market_efficiency_score DECIMAL(5,4),
    
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PSYCHOLOGICAL CONTEXT
-- ============================================================================

CREATE TABLE psychological_factors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    
    -- Home team factors
    home_motivation_score DECIMAL(5,4), -- 0-1
    home_fatigue_score DECIMAL(5,4), -- 0-1 (1 = very fatigued)
    home_pressure_score DECIMAL(5,4), -- 0-1
    home_momentum_score DECIMAL(5,4), -- -1 to 1
    home_rivalry_intensity DECIMAL(5,4), -- 0-1
    
    -- Away team factors
    away_motivation_score DECIMAL(5,4),
    away_fatigue_score DECIMAL(5,4),
    away_pressure_score DECIMAL(5,4),
    away_momentum_score DECIMAL(5,4),
    away_rivalry_intensity DECIMAL(5,4),
    
    -- Context factors
    derby_match BOOLEAN DEFAULT FALSE,
    relegation_battle BOOLEAN DEFAULT FALSE,
    title_race BOOLEAN DEFAULT FALSE,
    european_qualification BOOLEAN DEFAULT FALSE,
    cup_final BOOLEAN DEFAULT FALSE,
    
    -- Recent events
    recent_manager_change_home BOOLEAN DEFAULT FALSE,
    recent_manager_change_away BOOLEAN DEFAULT FALSE,
    controversy_level VARCHAR(20), -- 'low', 'medium', 'high'
    
    -- Overall assessment
    home_emotional_state VARCHAR(50),
    away_emotional_state VARCHAR(50),
    overall_intensity_score DECIMAL(5,4),
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RISK MANAGEMENT
-- ============================================================================

CREATE TABLE bankroll (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    
    initial_amount DECIMAL(15,2) NOT NULL,
    current_amount DECIMAL(15,2) NOT NULL,
    peak_amount DECIMAL(15,2) DEFAULT 0,
    lowest_amount DECIMAL(15,2) DEFAULT 0,
    
    currency VARCHAR(3) DEFAULT 'EUR',
    
    total_bets INTEGER DEFAULT 0,
    winning_bets INTEGER DEFAULT 0,
    losing_bets INTEGER DEFAULT 0,
    
    roi DECIMAL(7,4) DEFAULT 0, -- Return on investment
    yield DECIMAL(7,4) DEFAULT 0, -- Yield percentage
    
    risk_level VARCHAR(20) DEFAULT 'medium', -- 'conservative', 'medium', 'aggressive'
    kelly_fraction DECIMAL(5,4) DEFAULT 0.25, -- Fractional Kelly
    
    max_stake_percentage DECIMAL(5,4) DEFAULT 0.05, -- 5% max stake
    stop_loss_percentage DECIMAL(5,4) DEFAULT 0.20, -- 20% drawdown stop
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bankroll_id UUID REFERENCES bankroll(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    
    bet_type bet_type NOT NULL,
    selection VARCHAR(100) NOT NULL, -- e.g., 'Home Win', 'Over 2.5'
    
    stake DECIMAL(15,2) NOT NULL,
    odds DECIMAL(10,4) NOT NULL,
    potential_return DECIMAL(15,2) NOT NULL,
    actual_return DECIMAL(15,2) DEFAULT 0,
    
    kelly_recommended DECIMAL(15,2),
    kelly_actual DECIMAL(15,2),
    
    bookmaker_id UUID REFERENCES bookmakers(id),
    status prediction_status DEFAULT 'pending',
    
    result_notes TEXT,
    
    placed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    settled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risk_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bankroll_id UUID REFERENCES bankroll(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'stop_loss_triggered', 'max_exposure_reached', etc.
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
    description TEXT NOT NULL,
    metadata JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- MODEL MANAGEMENT
-- ============================================================================

CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL, -- 'xgboost', 'neural_network', 'ensemble', etc.
    
    -- Performance metrics
    accuracy DECIMAL(7,6),
    precision DECIMAL(7,6),
    recall DECIMAL(7,6),
    f1_score DECIMAL(7,6),
    auc_roc DECIMAL(7,6),
    log_loss DECIMAL(7,6),
    
    -- Training info
    training_samples INTEGER,
    features_count INTEGER,
    training_start TIMESTAMP WITH TIME ZONE,
    training_end TIMESTAMP WITH TIME ZONE,
    
    -- Model artifacts
    model_path VARCHAR(500),
    feature_importance JSONB,
    hyperparameters JSONB,
    
    is_active BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE model_predictions_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES ml_models(id),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    
    input_features JSONB NOT NULL,
    raw_output JSONB NOT NULL,
    processed_output JSONB,
    confidence DECIMAL(5,4),
    
    prediction_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SYSTEM & MONITORING
-- ============================================================================

CREATE TABLE agent_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type agent_type NOT NULL UNIQUE,
    
    status VARCHAR(20) DEFAULT 'idle', -- 'idle', 'running', 'error', 'maintenance'
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    
    total_predictions INTEGER DEFAULT 0,
    successful_predictions INTEGER DEFAULT 0,
    failed_predictions INTEGER DEFAULT 0,
    
    avg_processing_time_ms INTEGER,
    last_error TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,
    
    version VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    context JSONB,
    trace_id VARCHAR(100),
    span_id VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    
    response_time_ms INTEGER,
    status_code INTEGER,
    
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    
    client_ip INET,
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Core tables
CREATE INDEX idx_leagues_sport ON leagues(sport_id);
CREATE INDEX idx_teams_league ON teams(league_id);
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_matches_league ON matches(league_id);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX idx_matches_kickoff ON matches(kickoff_time);
CREATE INDEX idx_matches_status ON matches(status);

-- Odds tables
CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker_id);
CREATE INDEX idx_odds_captured ON odds(captured_at);
CREATE INDEX idx_odds_history_odds ON odds_history(odds_id);
CREATE INDEX idx_odds_history_captured ON odds_history(captured_at);

-- Predictions
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_status ON predictions(status);
CREATE INDEX idx_predictions_created ON predictions(created_at);
CREATE INDEX idx_agent_analyses_prediction ON agent_analyses(prediction_id);
CREATE INDEX idx_agent_analyses_type ON agent_analyses(agent_type);
CREATE INDEX idx_monte_carlo_prediction ON monte_carlo_simulations(prediction_id);

-- Market analysis
CREATE INDEX idx_market_signals_match ON market_signals(match_id);
CREATE INDEX idx_market_signals_detected ON market_signals(detected_at);

-- Psychological
CREATE INDEX idx_psychological_match ON psychological_factors(match_id);

-- Risk management
CREATE INDEX idx_bankroll_user ON bankroll(user_id);
CREATE INDEX idx_bets_bankroll ON bets(bankroll_id);
CREATE INDEX idx_bets_match ON bets(match_id);
CREATE INDEX idx_bets_status ON bets(status);
CREATE INDEX idx_risk_events_bankroll ON risk_events(bankroll_id);

-- ML models
CREATE INDEX idx_ml_models_active ON ml_models(is_active);
CREATE INDEX idx_ml_models_production ON ml_models(is_production);
CREATE INDEX idx_model_pred_model ON model_predictions_log(model_id);
CREATE INDEX idx_model_pred_created ON model_predictions_log(created_at);

-- System
CREATE INDEX idx_agent_status_type ON agent_status(agent_type);
CREATE INDEX idx_system_logs_service ON system_logs(service_name);
CREATE INDEX idx_system_logs_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_created ON system_logs(created_at);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_created ON api_usage(created_at);

-- ============================================================================
-- TRIGGERS & FUNCTIONS
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sports_updated_at BEFORE UPDATE ON sports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leagues_updated_at BEFORE UPDATE ON leagues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bankroll_updated_at BEFORE UPDATE ON bankroll FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_status_updated_at BEFORE UPDATE ON agent_status FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Bankroll tracking trigger
CREATE OR REPLACE FUNCTION update_bankroll_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update peak and lowest amounts
    IF NEW.current_amount > NEW.peak_amount THEN
        NEW.peak_amount = NEW.current_amount;
    END IF;
    
    IF NEW.lowest_amount = 0 OR NEW.current_amount < NEW.lowest_amount THEN
        NEW.lowest_amount = NEW.current_amount;
    END IF;
    
    -- Calculate ROI and yield
    IF NEW.initial_amount > 0 THEN
        NEW.roi = ((NEW.current_amount - NEW.initial_amount) / NEW.initial_amount) * 100;
    END IF;
    
    IF NEW.total_bets > 0 THEN
        NEW.yield = ((NEW.current_amount - NEW.initial_amount) / 
            (SELECT COALESCE(SUM(stake), 1) FROM bets WHERE bankroll_id = NEW.id)) * 100;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_bankroll_metrics_trigger 
BEFORE UPDATE ON bankroll 
FOR EACH ROW 
EXECUTE FUNCTION update_bankroll_metrics();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default sports
INSERT INTO sports (name) VALUES 
    ('football'),
    ('basketball'),
    ('tennis'),
    ('hockey'),
    ('baseball'),
    ('handball'),
    ('volleyball');

-- Initialize agent statuses
INSERT INTO agent_status (agent_type, status) VALUES 
    ('data_collector', 'idle'),
    ('statistical_engine', 'idle'),
    ('machine_learning', 'idle'),
    ('market_analyzer', 'idle'),
    ('psychological_context', 'idle'),
    ('risk_management', 'idle'),
    ('master_orchestrator', 'idle');

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active predictions view
CREATE VIEW active_predictions AS
SELECT 
    p.id,
    m.kickoff_time,
    t1.name as home_team,
    t2.name as away_team,
    l.name as league,
    p.home_win_prob,
    p.draw_prob,
    p.away_win_prob,
    p.confidence_score,
    p.value_bet_detected,
    p.status,
    p.created_at
FROM predictions p
JOIN matches m ON p.match_id = m.id
JOIN teams t1 ON m.home_team_id = t1.id
JOIN teams t2 ON m.away_team_id = t2.id
LEFT JOIN leagues l ON m.league_id = l.id
WHERE p.status IN ('pending', 'active')
ORDER BY p.created_at DESC;

-- Value bets view
CREATE VIEW value_bets AS
SELECT 
    p.id as prediction_id,
    m.kickoff_time,
    t1.name as home_team,
    t2.name as away_team,
    p.value_bet_type,
    p.value_bet_selection,
    p.value_percentage,
    p.kelly_stake,
    p.confidence_score,
    o.bookmaker_id,
    b.name as bookmaker_name,
    CASE p.value_bet_type
        WHEN '1x2' THEN 
            CASE p.value_bet_selection
                WHEN 'home' THEN o.home_win
                WHEN 'draw' THEN o.draw
                WHEN 'away' THEN o.away_win
            END
        WHEN 'over_under' THEN 
            CASE p.value_bet_selection
                WHEN 'over_2.5' THEN o.over_2_5
                WHEN 'under_2.5' THEN o.under_2_5
            END
        WHEN 'both_teams_score' THEN 
            CASE p.value_bet_selection
                WHEN 'yes' THEN o.btts_yes
                WHEN 'no' THEN o.btts_no
            END
    END as odds_value
FROM predictions p
JOIN matches m ON p.match_id = m.id
JOIN teams t1 ON m.home_team_id = t1.id
JOIN teams t2 ON m.away_team_id = t2.id
JOIN odds o ON o.match_id = m.id AND o.is_active = true
JOIN bookmakers b ON o.bookmaker_id = b.id
WHERE p.value_bet_detected = true AND p.status = 'pending'
ORDER BY p.value_percentage DESC, p.confidence_score DESC;

-- Performance dashboard view
CREATE VIEW performance_dashboard AS
SELECT 
    b.id as bankroll_id,
    b.initial_amount,
    b.current_amount,
    b.peak_amount,
    b.lowest_amount,
    b.roi,
    b.yield,
    b.total_bets,
    b.winning_bets,
    b.losing_bets,
    ROUND((b.winning_bets::DECIMAL / NULLIF(b.total_bets, 0)) * 100, 2) as win_rate,
    (SELECT COUNT(*) FROM predictions WHERE status = 'won') as total_won_predictions,
    (SELECT COUNT(*) FROM predictions WHERE status = 'lost') as total_lost_predictions,
    (SELECT AVG(confidence_score) FROM predictions WHERE status IN ('won', 'lost')) as avg_confidence,
    (SELECT AVG(value_percentage) FROM predictions WHERE value_bet_detected = true AND status IN ('won', 'lost')) as avg_value
FROM bankroll b
WHERE b.is_active = true;
