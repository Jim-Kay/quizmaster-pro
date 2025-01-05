-- Create LogLevel enum type if it doesn't exist
DO $$ BEGIN
    CREATE TYPE loglevel AS ENUM ('debug', 'info', 'warning', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create flow_logs table
CREATE TABLE IF NOT EXISTS flow_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id uuid NOT NULL REFERENCES flow_executions(id) ON DELETE CASCADE,
    timestamp timestamptz NOT NULL DEFAULT now(),
    level loglevel NOT NULL,
    message text NOT NULL,
    log_metadata jsonb,
    CONSTRAINT fk_flow_execution FOREIGN KEY (execution_id) REFERENCES flow_executions(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_flow_logs_execution_id ON flow_logs(execution_id);
CREATE INDEX IF NOT EXISTS ix_flow_logs_timestamp ON flow_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_flow_logs_level ON flow_logs(level);
