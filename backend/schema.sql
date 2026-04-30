-- DealMind AI Database Schema
-- Run this SQL to create all required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents (users) table
CREATE TABLE IF NOT EXISTS agents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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

-- Core deal record
CREATE TABLE IF NOT EXISTS deals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
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

-- All parties in a deal
CREATE TABLE IF NOT EXISTS parties (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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

-- All deadlines extracted from contracts
CREATE TABLE IF NOT EXISTS deadlines (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    deadline_date DATE NOT NULL,
    days_from_acceptance INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    extracted_from TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- All documents associated with a deal
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    type VARCHAR(100),
    extracted_text TEXT,
    extraction_confidence DECIMAL(4,3),
    is_signed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    embedding vector(1536)
);

-- All emails matched to deals
CREATE TABLE IF NOT EXISTS emails (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task queue for agent
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    type VARCHAR(50),
    assigned_to_role VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'open',
    due_date DATE,
    created_by VARCHAR(20) DEFAULT 'AI',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- AI-drafted emails waiting for approval
CREATE TABLE IF NOT EXISTS draft_queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    recipient_party_id UUID REFERENCES parties(id),
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

-- Immutable audit trail
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    deal_id UUID,
    agent_id UUID,
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,
    previous_hash TEXT,
    event_hash TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_deals_agent_id ON deals(agent_id);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage);
CREATE INDEX IF NOT EXISTS idx_parties_deal_id ON parties(deal_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_deal_id ON deadlines(deal_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_deadline_date ON deadlines(deadline_date);
CREATE INDEX IF NOT EXISTS idx_documents_deal_id ON documents(deal_id);
CREATE INDEX IF NOT EXISTS idx_emails_deal_id ON emails(deal_id);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_tasks_deal_id ON tasks(deal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_draft_queue_deal_id ON draft_queue(deal_id);
CREATE INDEX IF NOT EXISTS idx_draft_queue_status ON draft_queue(status);
CREATE INDEX IF NOT EXISTS idx_audit_events_deal_id ON audit_events(deal_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp);

-- Enable pgvector extension if not already enabled (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: For local development without pgvector extension, 
-- comment out the embedding column in documents table above
-- and remove the vector extension line