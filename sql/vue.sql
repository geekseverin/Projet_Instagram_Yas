-- sql/views_powerbi.sql - Vues optimisées pour Power BI

-- 1) Vue principale pour le dashboard - Métriques globales
CREATE OR REPLACE VIEW vw_dashboard_overview AS
SELECT 
    COUNT(DISTINCT p.post_id) as total_posts,
    COUNT(DISTINCT c.comment_id) as total_comments,
    COALESCE(AVG(p.like_count), 0) as avg_likes_per_post,
    COALESCE(AVG(p.comments_count), 0) as avg_comments_per_post,
    COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) as positive_count,
    COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) as negative_count,
    COUNT(CASE WHEN f.predicted_sentiment = 'neutre' THEN 1 END) as neutral_count,
    ROUND(
        COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(f.predicted_sentiment), 0), 2
    ) as positive_percentage
FROM posts p
LEFT JOIN comments c ON p.post_id = c.post_id
LEFT JOIN flat_texts f ON f.post_id = p.post_id;

-- 2) Distribution des sentiments (pour graphique en secteurs)
CREATE OR REPLACE VIEW vw_sentiment_distribution AS
SELECT 
    COALESCE(predicted_sentiment, 'non_analysé') AS sentiment,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM flat_texts
WHERE text IS NOT NULL AND text != ''
GROUP BY COALESCE(predicted_sentiment, 'non_analysé')
ORDER BY count DESC;

-- 3) Performance des posts avec sentiment
CREATE OR REPLACE VIEW vw_post_performance AS
SELECT 
    p.post_id,
    p.caption,
    p.created_time,
    p.like_count,
    p.comments_count,
    (p.like_count + p.comments_count) AS engagement_total,
    COUNT(f.id) as total_interactions,
    COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) as sentiment_positif,
    COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) as sentiment_negatif,
    COUNT(CASE WHEN f.predicted_sentiment = 'neutre' THEN 1 END) as sentiment_neutre,
    CASE 
        WHEN COUNT(f.id) > 0 THEN
            ROUND(COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) * 100.0 / COUNT(f.id), 2)
        ELSE 0 
    END as pourcentage_positif,
    p.permalink
FROM posts p
LEFT JOIN flat_texts f ON p.post_id = f.post_id
GROUP BY p.post_id, p.caption, p.created_time, p.like_count, p.comments_count, p.permalink
ORDER BY engagement_total DESC;

-- 4) Timeline des sentiments par jour
CREATE OR REPLACE VIEW vw_sentiment_timeline_daily AS
SELECT 
    DATE_TRUNC('day', created_time)::date AS date_jour,
    COUNT(CASE WHEN predicted_sentiment = 'positif' THEN 1 END) AS positif,
    COUNT(CASE WHEN predicted_sentiment = 'negatif' THEN 1 END) AS negatif,
    COUNT(CASE WHEN predicted_sentiment = 'neutre' THEN 1 END) AS neutre,
    COUNT(*) AS total_interactions
FROM flat_texts
WHERE created_time IS NOT NULL
GROUP BY DATE_TRUNC('day', created_time)
ORDER BY date_jour;

-- 5) Timeline des sentiments par semaine (pour tendances)
CREATE OR REPLACE VIEW vw_sentiment_timeline_weekly AS
SELECT 
    DATE_TRUNC('week', created_time)::date AS semaine,
    COUNT(CASE WHEN predicted_sentiment = 'positif' THEN 1 END) AS positif,
    COUNT(CASE WHEN predicted_sentiment = 'negatif' THEN 1 END) AS negatif,
    COUNT(CASE WHEN predicted_sentiment = 'neutre' THEN 1 END) AS neutre,
    COUNT(*) AS total,
    ROUND(AVG(CASE WHEN predicted_sentiment = 'positif' THEN 100.0 ELSE 0 END), 2) AS pct_positif
FROM flat_texts
WHERE created_time IS NOT NULL
GROUP BY DATE_TRUNC('week', created_time)
ORDER BY semaine;

-- 6) Top utilisateurs par engagement
CREATE OR REPLACE VIEW vw_top_users AS
SELECT 
    f.username,
    COUNT(*) AS total_interactions,
    SUM(f.like_count) AS total_likes,
    COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) AS interactions_positives,
    COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) AS interactions_negatives,
    ROUND(
        COUNT(CASE WHEN f.predicted_sentiment = 'positif' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(f.predicted_sentiment), 0), 2
    ) AS pourcentage_positif
FROM flat_texts f
WHERE f.username IS NOT NULL AND f.source_type != 'post'
GROUP BY f.username
HAVING COUNT(*) > 1
ORDER BY total_interactions DESC
LIMIT 20;

-- 7) Posts avec le plus d'engagement négatif (alertes)
CREATE OR REPLACE VIEW vw_negative_alerts AS
SELECT 
    p.post_id,
    p.caption,
    p.created_time,
    p.permalink,
    COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) AS reactions_negatives,
    COUNT(f.id) AS total_reactions,
    ROUND(
        COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(f.id), 0), 2
    ) AS pourcentage_negatif
FROM posts p
LEFT JOIN flat_texts f ON p.post_id = f.post_id
GROUP BY p.post_id, p.caption, p.created_time, p.permalink
HAVING COUNT(CASE WHEN f.predicted_sentiment = 'negatif' THEN 1 END) > 0
ORDER BY pourcentage_negatif DESC, reactions_negatives DESC;

-- 8) Analyse des émojis les plus utilisés
CREATE OR REPLACE VIEW vw_emoji_analysis AS
WITH emoji_counts AS (
    SELECT 
        key as emoji,
        SUM(value::int) as usage_count
    FROM flat_texts f,
    LATERAL jsonb_each_text(f.emoji_summary) 
    WHERE emoji_summary != '{}'
    GROUP BY key
)
SELECT 
    emoji,
    usage_count,
    ROUND(usage_count * 100.0 / SUM(usage_count) OVER(), 2) as percentage
FROM emoji_counts
ORDER BY usage_count DESC
LIMIT 20;

-- 9) Rapport mensuel pour l'email
CREATE OR REPLACE VIEW vw_monthly_report AS
WITH monthly_stats AS (
    SELECT 
        DATE_TRUNC('month', created_time)::date AS mois,
        COUNT(DISTINCT post_id) as posts_count,
        COUNT(*) as total_interactions,
        COUNT(CASE WHEN predicted_sentiment = 'positif' THEN 1 END) as positif,
        COUNT(CASE WHEN predicted_sentiment = 'negatif' THEN 1 END) as negatif,
        COUNT(CASE WHEN predicted_sentiment = 'neutre' THEN 1 END) as neutre,
        AVG(like_count) as avg_likes
    FROM flat_texts
    WHERE created_time >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')
    GROUP BY DATE_TRUNC('month', created_time)
)
SELECT 
    mois,
    posts_count,
    total_interactions,
    positif,
    negatif,
    neutre,
    ROUND(positif * 100.0 / NULLIF(total_interactions, 0), 2) as pct_positif,
    ROUND(negatif * 100.0 / NULLIF(total_interactions, 0), 2) as pct_negatif,
    ROUND(avg_likes, 1) as moyenne_likes
FROM monthly_stats
ORDER BY mois DESC;

-- 10) Vue pour les KPIs Power BI
CREATE OR REPLACE VIEW vw_kpi_summary AS
SELECT 
    'total_posts' as metric_name,
    COUNT(DISTINCT post_id)::text as metric_value,
    'Posts publiés' as metric_label
FROM flat_texts WHERE source_type = 'post'
UNION ALL
SELECT 
    'total_interactions' as metric_name,
    COUNT(*)::text as metric_value,
    'Interactions totales' as metric_label
FROM flat_texts
UNION ALL
SELECT 
    'sentiment_score' as metric_name,
    ROUND(
        COUNT(CASE WHEN predicted_sentiment = 'positif' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(predicted_sentiment), 0), 1
    )::text || '%' as metric_value,
    'Score sentiment positif' as metric_label
FROM flat_texts
UNION ALL
SELECT 
    'avg_engagement' as metric_name,
    ROUND(AVG(like_count + comments_count), 0)::text as metric_value,
    'Engagement moyen par post' as metric_label
FROM posts;