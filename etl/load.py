# etl/load.py
import os, json
import pandas as pd
import psycopg2
import psycopg2.extras
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

SCHEMA_SQL = "sql/schema.sql"
PROC_DIR = "data/processed"

def connect():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def ensure_schema(conn):
    with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
        sql = f.read()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    print("[load] Schema ensured")

def load():
    conn = connect()
    ensure_schema(conn)
    cur = conn.cursor()

    posts_csv = os.path.join(PROC_DIR, "posts.csv")
    comments_csv = os.path.join(PROC_DIR, "comments.csv")
    flat_json = os.path.join(PROC_DIR, "flat_texts.json")

    if os.path.exists(posts_csv):
        posts_df = pd.read_csv(posts_csv)
        for _, r in posts_df.iterrows():
            cur.execute("""
                INSERT INTO posts (post_id, caption, media_type, media_url, permalink, created_time, like_count, comments_count)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (post_id) DO UPDATE SET
                  caption=EXCLUDED.caption,
                  media_type=EXCLUDED.media_type,
                  media_url=EXCLUDED.media_url,
                  permalink=EXCLUDED.permalink,
                  created_time=EXCLUDED.created_time,
                  like_count=EXCLUDED.like_count,
                  comments_count=EXCLUDED.comments_count;
            """, (r.post_id, r.caption, r.media_type, r.media_url, r.permalink, r.created_time, int(r.like_count or 0), int(r.comments_count or 0)))
    if os.path.exists(comments_csv):
        comments_df = pd.read_csv(comments_csv)
        for _, r in comments_df.iterrows():
            cur.execute("""
                INSERT INTO comments (comment_id, post_id, parent_comment_id, username, text, like_count, created_time)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (comment_id) DO UPDATE SET
                  text=EXCLUDED.text,
                  like_count=EXCLUDED.like_count;
            """, (r.comment_id, r.post_id, r.parent_comment_id if 'parent_comment_id' in r and not pd.isna(r.parent_comment_id) else None, r.username, r.text, int(r.like_count or 0), r.created_time))
    if os.path.exists(flat_json):
        with open(flat_json, "r", encoding="utf-8") as f:
            flat_rows = json.load(f)
        for r in flat_rows:
            cur.execute("""
                INSERT INTO flat_texts (source_type, source_id, post_id, parent_comment_id, username, text, like_count, emoji_summary, created_time)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (
                r.get("source_type"),
                r.get("source_id"),
                r.get("post_id"),
                r.get("parent_comment_id"),
                r.get("username"),
                r.get("text"),
                int(r.get("like_count") or 0),
                json.dumps(r.get("emoji_summary") or {}),
                r.get("created_time")
            ))
    conn.commit()
    cur.close()
    conn.close()
    print("[load] Data loaded into PostgreSQL")
