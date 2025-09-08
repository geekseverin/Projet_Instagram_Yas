-- sql/schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS posts (
  post_id TEXT PRIMARY KEY,
  caption TEXT,
  media_type TEXT,
  media_url TEXT,
  created_time TIMESTAMP,
  like_count INT,
  comments_count INT
);

CREATE TABLE IF NOT EXISTS post_likes (
  like_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  post_id TEXT REFERENCES posts(post_id),
  user_id TEXT,
  emoji TEXT
);

CREATE TABLE IF NOT EXISTS comments (
  comment_id TEXT PRIMARY KEY,
  post_id TEXT REFERENCES posts(post_id),
  parent_comment_id TEXT,
  user_id TEXT,
  text TEXT,
  created_time TIMESTAMP,
  like_count INT
);

CREATE TABLE IF NOT EXISTS comment_likes (
  like_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  comment_id TEXT REFERENCES comments(comment_id),
  user_id TEXT,
  emoji TEXT
);

-- table aplatie pour ML
CREATE TABLE IF NOT EXISTS flat_texts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  source_type TEXT,    -- 'post'|'comment'|'reply'
  source_id TEXT,
  post_id TEXT,
  parent_comment_id TEXT,
  user_id TEXT,
  text TEXT,
  like_count INT DEFAULT 0,
  emoji_summary JSONB,
  created_time TIMESTAMP,
  sentiment_label TEXT -- peut rester NULL avant l'annotation
);
