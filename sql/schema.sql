-- sql/schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table principale pour les posts
CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    caption TEXT,
    media_type TEXT,
    media_url TEXT,
    permalink TEXT,
    created_time TIMESTAMPTZ,
    like_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table pour les commentaires (inclut les réponses avec parent_comment_id)
CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    post_id TEXT REFERENCES posts(post_id) ON DELETE CASCADE,
    parent_comment_id TEXT REFERENCES comments(comment_id) ON DELETE CASCADE,
    username TEXT,
    text TEXT,
    like_count INT DEFAULT 0,
    created_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table unifiée pour l'analyse de sentiment
CREATE TABLE IF NOT EXISTS flat_texts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_type TEXT CHECK (source_type IN ('post', 'comment', 'reply')),
    source_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    parent_comment_id TEXT,
    username TEXT,
    text TEXT NOT NULL,
    like_count INT DEFAULT 0,
    emoji_summary JSONB DEFAULT '{}',
    created_time TIMESTAMPTZ,
    sentiment_label TEXT CHECK (sentiment_label IN ('positif', 'negatif', 'neutre')),
    predicted_sentiment TEXT CHECK (predicted_sentiment IN ('positif', 'negatif', 'neutre')),
    predicted_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table pour stocker les performances des modèles
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_name TEXT NOT NULL,
    accuracy FLOAT,
    f1_macro FLOAT,
    precision FLOAT,
    recall FLOAT,
    training_samples INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table pour les rapports générés (pour l'envoi par email)
CREATE TABLE IF NOT EXISTS reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    report_name TEXT NOT NULL,
    report_type TEXT CHECK (report_type IN ('daily', 'weekly', 'monthly')),
    file_path TEXT,
    recipients TEXT[], -- Array des emails destinataires
    sent_at TIMESTAMPTZ,
    status TEXT CHECK (status IN ('pending', 'sent', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_flat_texts_post_id ON flat_texts(post_id);
CREATE INDEX IF NOT EXISTS idx_flat_texts_created_time ON flat_texts(created_time);
CREATE INDEX IF NOT EXISTS idx_flat_texts_sentiment ON flat_texts(predicted_sentiment);
CREATE INDEX IF NOT EXISTS idx_posts_created_time ON posts(created_time);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour updated_at
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flat_texts_updated_at BEFORE UPDATE ON flat_texts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();