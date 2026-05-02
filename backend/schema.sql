-- Enable pgvector extension for document embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    gmail_token JSONB,
    outlook_token JSONB,
    followupboss_api_key TEXT,
    slack_webhook_url TEXT,
    morning_brief_time TIME DEFAULT '07:45:00',
    timezone TEXT DEFAULT 'America/Chicago',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deals table
CREATE TABLE IF NOT EXISTS deals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id UUID NOT NULL,
    address TEXT NOT NULL,
    state VARCHAR(2) DEFAULT 'TX',
    stage VARCHAR(50) NOT NULL,
    purchase_price DECIMAL(12,2),
    earnest_money DECIMAL(10,2),
    option_fee DECIMAL(10,2),
    option_period_days INTEGER,
    acceptance_date DATE,
    closing_date DATE,
    risk_score DECIMAL(5,2) DEFAULT 0,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    last_scored_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Parties table
CREATE TABLE IF NOT EXISTS parties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    last_responded_at TIMESTAMPTZ,
    avg_response_hours DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deadlines table
CREATE TABLE IF NOT EXISTS deadlines (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    deadline_date DATE NOT NULL,
    days_from_acceptance INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    extracted_from TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    type VARCHAR(100),
    extracted_text TEXT,
    extraction_confidence DECIMAL(4,3),
    is_signed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id),
    gmail_thread_id TEXT,
    gmail_message_id TEXT,
    sender_email TEXT NOT NULL,
    sender_name TEXT,
    subject TEXT,
    body TEXT,
    received_at TIMESTAMPTZ,
    sentiment_score DECIMAL(4,3),
    sentiment_label VARCHAR(50),
    urgency_level VARCHAR(20),
    is_deal_relevant BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Draft queue table
CREATE TABLE IF NOT EXISTS draft_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    recipient_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    purpose VARCHAR(100),
    tone VARCHAR(30),
    status VARCHAR(20) DEFAULT 'pending',
    agent_edited_body TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ
);

-- Audit events table
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    deal_id UUID,
    agent_id UUID,
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);