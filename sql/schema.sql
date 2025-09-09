-- sql/schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    caption TEXT,
    media_type TEXT,
    media_url TEXT,
    permalink TEXT,
    created_time TIMESTAMPTZ,
    like_count INT,
    comments_count INT
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id TEXT PRIMARY KEY,
    post_id TEXT REFERENCES posts(post_id),
    parent_comment_id TEXT,
    username TEXT,
    text TEXT,
    like_count INT,
    created_time TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS comment_replies (
    reply_id TEXT PRIMARY KEY,
    comment_id TEXT REFERENCES comments(comment_id),
    username TEXT,
    text TEXT,
    like_count INT,
    created_time TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS flat_texts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_type TEXT,    -- 'post'|'comment'|'reply'
    source_id TEXT,
    post_id TEXT,
    parent_comment_id TEXT,
    username TEXT,
    text TEXT,
    like_count INT,
    emoji_summary JSONB,
    created_time TIMESTAMPTZ,
    sentiment_label TEXT,         -- (optionnel) label manuel
    predicted_sentiment TEXT,     -- prédiction du modèle
    predicted_score FLOAT         -- score/confiance si dispo
);

CREATE TABLE IF NOT EXISTS model_performance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_name TEXT,
    accuracy FLOAT,
    f1_macro FLOAT,
    precision FLOAT,
    recall FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
