-- SQL schema for call_logs table in Supabase PostgreSQL
-- Run this in the Supabase SQL Editor

CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_sid VARCHAR(255) UNIQUE NOT NULL,
    business_id VARCHAR(255) NOT NULL,
    caller_number VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    transcript JSONB,
    summary TEXT,
    sentiment VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_call_logs_business_id ON call_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_started_at ON call_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_call_logs_status ON call_logs(status);
CREATE INDEX IF NOT EXISTS idx_call_logs_call_sid ON call_logs(call_sid);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_call_logs_business_status ON call_logs(business_id, status, started_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function on UPDATE
DROP TRIGGER IF EXISTS update_call_logs_updated_at ON call_logs;
CREATE TRIGGER update_call_logs_updated_at
    BEFORE UPDATE ON call_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;

-- Example RLS policy: Allow all operations for authenticated users
-- Adjust this based on your security requirements
CREATE POLICY "Allow authenticated access" ON call_logs
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Example RLS policy: Allow service role full access (for backend API)
CREATE POLICY "Allow service role full access" ON call_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE call_logs IS 'Stores call logs from the voice agent';
COMMENT ON COLUMN call_logs.call_sid IS 'Twilio unique call identifier';
COMMENT ON COLUMN call_logs.business_id IS 'Business/organization identifier';
COMMENT ON COLUMN call_logs.transcript IS 'JSON array of conversation messages with speaker, text, and timestamp';
COMMENT ON COLUMN call_logs.sentiment IS 'Overall sentiment of the call: positive, neutral, or negative';
COMMENT ON COLUMN call_logs.metadata IS 'Additional metadata in JSON format';
