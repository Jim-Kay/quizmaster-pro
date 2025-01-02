-- Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add settings columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS llm_provider VARCHAR(50) DEFAULT 'openai';
ALTER TABLE users ADD COLUMN IF NOT EXISTS encrypted_openai_key BYTEA;
ALTER TABLE users ADD COLUMN IF NOT EXISTS encrypted_anthropic_key BYTEA;

-- Create an enum type for LLM providers if it doesn't exist
DO $$ BEGIN
    CREATE TYPE llm_provider_type AS ENUM ('openai', 'anthropic');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Alter the column to use the enum type
ALTER TABLE users 
    ALTER COLUMN llm_provider TYPE llm_provider_type 
    USING llm_provider::llm_provider_type;
