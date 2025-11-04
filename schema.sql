-- Tabel pentru întrebări
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru căutare rapidă după tip
CREATE INDEX idx_questions_type ON questions(type);

-- Index pentru sortare după data creării
CREATE INDEX idx_questions_created ON questions(created_at DESC);

-- Trigger pentru actualizarea automată a updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_questions_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Tabel pentru statistici (opțional)
CREATE TABLE question_stats (
    id SERIAL PRIMARY KEY,
    question_type VARCHAR(50) NOT NULL,
    total_generated INTEGER DEFAULT 0,
    last_generated TIMESTAMP,
    UNIQUE(question_type)
);

-- Inserare tipuri de întrebări
INSERT INTO question_stats (question_type, total_generated) VALUES
    ('n-queens', 0),
    ('hanoi', 0),
    ('coloring', 0),
    ('knight', 0);