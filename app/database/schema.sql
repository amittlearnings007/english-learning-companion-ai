CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE COLLATE NOCASE,
    meaning TEXT NOT NULL,
    example_sentence TEXT NOT NULL,
    learned_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    frequency INTEGER NOT NULL DEFAULT 0 CHECK (frequency >= 0)
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    correction TEXT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_messages INTEGER NOT NULL DEFAULT 0 CHECK (total_messages >= 0),
    corrections_given INTEGER NOT NULL DEFAULT 0 CHECK (corrections_given >= 0),
    vocabulary_count INTEGER NOT NULL DEFAULT 0 CHECK (vocabulary_count >= 0),
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_vocabulary_learned_date ON vocabulary(learned_date);