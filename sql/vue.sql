-- sql/views.sql

-- 1) Distribution globale des sentiments (pratique pour un camembert)
CREATE OR REPLACE VIEW vw_global_sentiment AS
SELECT COALESCE(predicted_sentiment, sentiment_label, 'unknown') AS sentiment,
       COUNT(*) AS cnt
FROM flat_texts
GROUP BY COALESCE(predicted_sentiment, sentiment_label, 'unknown');

-- 2) Sentiments par post
CREATE OR REPLACE VIEW vw_post_sentiment_summary AS
SELECT p.post_id,
       p.caption,
       p.created_time,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'positif' THEN 1 ELSE 0 END) AS positive_count,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'negatif' THEN 1 ELSE 0 END) AS negative_count,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'neutre' THEN 1 ELSE 0 END) AS neutral_count,
       COUNT(f.id) AS total_comments
FROM posts p
LEFT JOIN flat_texts f ON f.post_id = p.post_id
GROUP BY p.post_id, p.caption, p.created_time;

-- 3) Top posts par engagement (likes + comments)
CREATE OR REPLACE VIEW vw_top_posts AS
SELECT p.post_id, p.caption, p.created_time, p.like_count, p.comments_count,
       (COALESCE(p.like_count,0) + COALESCE(p.comments_count,0)) AS engagement_score
FROM posts p
ORDER BY engagement_score DESC;

-- 4) Timeline des sentiments (par semaine)
CREATE OR REPLACE VIEW vw_sentiment_timeline_week AS
SELECT date_trunc('week', COALESCE(f.created_time, p.created_time))::date AS week_start,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'positif' THEN 1 ELSE 0 END) AS positive,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'negatif' THEN 1 ELSE 0 END) AS negative,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'neutre' THEN 1 ELSE 0 END) AS neutral
FROM flat_texts f
LEFT JOIN posts p ON f.post_id = p.post_id
GROUP BY date_trunc('week', COALESCE(f.created_time, p.created_time))
ORDER BY week_start;

-- 5) Top commentateurs
CREATE OR REPLACE VIEW vw_top_commenters AS
SELECT f.username, COUNT(*) AS total_comments,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'positif' THEN 1 ELSE 0 END) AS positive_comments,
       SUM(CASE WHEN COALESCE(f.predicted_sentiment,f.sentiment_label) = 'negatif' THEN 1 ELSE 0 END) AS negative_comments
FROM flat_texts f
WHERE f.source_type IN ('comment','reply')
GROUP BY f.username
ORDER BY total_comments DESC;
