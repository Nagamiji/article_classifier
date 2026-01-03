CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    text_input TEXT NOT NULL,
    label_classified VARCHAR(255) NOT NULL,
    feedback BOOLEAN,   -- TRUE = Good, FALSE = Bad, NULL = Not given
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
