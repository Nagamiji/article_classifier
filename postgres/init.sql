CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    text_input TEXT NOT NULL,
    label_classified VARCHAR(255) NOT NULL,
    feedback BOOLEAN,   -- TRUE = Good, FALSE = Bad, NULL = Not given
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ERROR LOGS TABLE (Simple version)
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_message TEXT NOT NULL,
    error_type VARCHAR(50),  -- 'MODEL', 'DB', 'API', 'OTHER'
    endpoint VARCHAR(100),   -- Where error happened
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Add some indexes for better performance
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);
CREATE INDEX idx_predictions_feedback ON predictions(feedback);
CREATE INDEX idx_error_logs_created ON error_logs(created_at DESC);