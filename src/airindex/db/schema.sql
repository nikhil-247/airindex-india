-- Canonical relational schema for AirIndex India.
-- This file is intentionally SQL-first: the database is the durable source of truth.
-- Alembic migrations will own production schema evolution in the database phase.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('airline', 'ota', 'reference')),
    base_url TEXT,
    policy_version VARCHAR(40) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS airports (
    iata_code CHAR(3) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    city VARCHAR(120) NOT NULL,
    state VARCHAR(120),
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS airlines (
    iata_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin CHAR(3) NOT NULL REFERENCES airports(iata_code),
    destination CHAR(3) NOT NULL REFERENCES airports(iata_code),
    route_key VARCHAR(7) GENERATED ALWAYS AS (origin || '-' || destination) STORED UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (origin <> destination)
);

CREATE TABLE IF NOT EXISTS route_baskets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(40) NOT NULL UNIQUE,
    methodology_version VARCHAR(40) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS route_basket_members (
    basket_id UUID NOT NULL REFERENCES route_baskets(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES routes(id),
    weight NUMERIC(12, 8) NOT NULL CHECK (weight > 0),
    selection_score NUMERIC(12, 8),
    selection_basis JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (basket_id, route_id)
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'partial', 'failed')),
    collector_version VARCHAR(40) NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    observation_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS fare_observations (
    id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES sources(id),
    collection_run_id UUID REFERENCES collection_runs(id),
    collected_at TIMESTAMPTZ NOT NULL,
    origin CHAR(3) NOT NULL REFERENCES airports(iata_code),
    destination CHAR(3) NOT NULL REFERENCES airports(iata_code),
    travel_date DATE NOT NULL,
    carrier_code VARCHAR(3) NOT NULL REFERENCES airlines(iata_code),
    flight_number VARCHAR(20),
    fare_class VARCHAR(40),
    fare_family VARCHAR(80),
    departure_time TIME,
    arrival_time TIME,
    stops SMALLINT NOT NULL DEFAULT 0 CHECK (stops >= 0),
    base_fare NUMERIC(12, 2) NOT NULL CHECK (base_fare >= 0),
    taxes NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (taxes >= 0),
    user_development_fee NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (user_development_fee >= 0),
    convenience_fee NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (convenience_fee >= 0),
    other_fees NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (other_fees >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    availability VARCHAR(20) NOT NULL CHECK (availability IN ('available', 'sold_out', 'unknown')),
    scraper_version VARCHAR(40) NOT NULL,
    source_url TEXT,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    quality_score NUMERIC(5, 2),
    extra_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (travel_date >= collected_at::date),
    CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100))
);

CREATE INDEX IF NOT EXISTS idx_fare_observations_route_date
    ON fare_observations(origin, destination, travel_date, collected_at);

CREATE INDEX IF NOT EXISTS idx_fare_observations_source_collected
    ON fare_observations(source_id, collected_at);

CREATE INDEX IF NOT EXISTS idx_fare_observations_quality
    ON fare_observations(quality_status, collected_at);

CREATE TABLE IF NOT EXISTS index_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    methodology_version VARCHAR(40) NOT NULL,
    basket_version VARCHAR(40) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    frequency VARCHAR(12) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'published', 'revised', 'rejected')),
    value NUMERIC(14, 6),
    sample_size INTEGER NOT NULL DEFAULT 0,
    coverage_ratio NUMERIC(8, 6),
    calculation_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (period_end >= period_start),
    CHECK (coverage_ratio IS NULL OR (coverage_ratio >= 0 AND coverage_ratio <= 1))
);
