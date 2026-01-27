-- Migration: Initial Supabase Schema for Agent Deen
-- Run this in your Supabase SQL Editor

-- =====================================================
-- Documents table
-- Stores metadata for all ingested PDF documents
-- =====================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'bnm', 'sc_malaysia', 'manual', etc.
    source_url TEXT,
    title TEXT,
    storage_path TEXT NOT NULL,  -- Path in Supabase Storage
    file_size_bytes BIGINT,
    total_pages INTEGER,
    extraction_method TEXT,  -- 'digital' or 'ocr'
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'indexed', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    indexed_at TIMESTAMPTZ,
    UNIQUE(source, filename)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);

-- =====================================================
-- Chat sessions table
-- Stores chat session metadata
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL DEFAULT 'New Chat',
    model TEXT NOT NULL DEFAULT 'ollama',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for listing sessions by recency
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- =====================================================
-- Chat messages table
-- Stores individual messages within chat sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,  -- Citation metadata for assistant messages
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fetching messages by session
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- =====================================================
-- Ingestion history table
-- Logs all document ingestion attempts
-- =====================================================
CREATE TABLE IF NOT EXISTS ingestion_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    type TEXT NOT NULL,  -- 'url', 'upload', 'auto_update'
    source TEXT NOT NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'success', 'failed', 'skipped'
    error_message TEXT,
    chunks_created INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_ingestion_history_created_at ON ingestion_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_history_status ON ingestion_history(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_history_type ON ingestion_history(type);

-- =====================================================
-- Job status table (singleton)
-- Tracks the current background job status
-- =====================================================
CREATE TABLE IF NOT EXISTS job_status (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    status TEXT DEFAULT 'idle',  -- 'idle', 'running', 'completed', 'failed'
    message TEXT,
    progress FLOAT DEFAULT 0.0,
    details JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initialize with default values
INSERT INTO job_status (id, status, message)
VALUES (1, 'idle', 'System ready')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- Storage bucket setup
-- Run this in the Supabase Storage dashboard or via API
-- =====================================================
-- Bucket name: shariah-documents
-- Structure:
--   /{source}/{filename}.pdf
--   - bnm/document1.pdf
--   - sc_malaysia/resolution.pdf
--   - manual/uploaded.pdf

-- Note: Create the storage bucket manually in the Supabase dashboard:
-- 1. Go to Storage
-- 2. Click "New bucket"
-- 3. Name: "shariah-documents"
-- 4. Public: No (we'll use signed URLs)
-- 5. File size limit: 50MB (or as needed)

-- =====================================================
-- Row Level Security (RLS) - Optional
-- Enable for production environments
-- =====================================================

-- For development, you can keep RLS disabled
-- For production, uncomment and configure the policies below:

-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ingestion_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_status ENABLE ROW LEVEL SECURITY;

-- Example: Allow all operations for authenticated users
-- CREATE POLICY "Allow all for authenticated users" ON documents
--     FOR ALL USING (auth.role() = 'authenticated');
