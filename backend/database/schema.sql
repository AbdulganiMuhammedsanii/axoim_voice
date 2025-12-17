-- Database schema for AI Voice Agent Platform
-- PostgreSQL / Supabase compatible

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    business_hours TEXT,
    after_hours_policy VARCHAR(100),
    services_offered TEXT,
    escalation_phone VARCHAR(50),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Calls table
CREATE TABLE IF NOT EXISTS calls (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    escalated BOOLEAN DEFAULT FALSE NOT NULL,
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_calls_org_id ON calls(org_id);
CREATE INDEX IF NOT EXISTS idx_calls_started_at ON calls(started_at);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);

-- Call transcripts table
CREATE TABLE IF NOT EXISTS call_transcripts (
    id VARCHAR PRIMARY KEY,
    call_id VARCHAR NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    speaker VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_transcripts_call_id ON call_transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON call_transcripts(timestamp);

-- Call intakes table
CREATE TABLE IF NOT EXISTS call_intakes (
    call_id VARCHAR PRIMARY KEY REFERENCES calls(id) ON DELETE CASCADE,
    structured_json JSONB NOT NULL DEFAULT '{}',
    urgency_level VARCHAR(20),
    completed BOOLEAN DEFAULT FALSE NOT NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes are created above with their respective tables

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_intakes_updated_at BEFORE UPDATE ON call_intakes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id VARCHAR PRIMARY KEY,
    call_id VARCHAR REFERENCES calls(id) ON DELETE SET NULL,
    org_id VARCHAR NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    attendee_email VARCHAR(255) NOT NULL,
    attendee_name VARCHAR(255),
    google_calendar_event_id VARCHAR(255),
    google_calendar_link VARCHAR(500),
    calendar_invite_sent BOOLEAN DEFAULT FALSE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    cancelled BOOLEAN DEFAULT FALSE NOT NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appointments_call_id ON appointments(call_id);
CREATE INDEX IF NOT EXISTS idx_appointments_org_id ON appointments(org_id);
CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments(start_time);

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

