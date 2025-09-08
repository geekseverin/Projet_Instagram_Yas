# etl/load.py
import os, json
import pandas as pd
import psycopg2
import psycopg2.extras
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

PROC_DIR = "data/processed"
SCHEMA_SQL_PATH = "sql/schema.sql"

def connect():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

def create_schema(conn):
    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    print("[load] schema ensured")

def load_data():
    conn = connect()
    create_schema(conn)
    cur = conn.cursor()

    posts_df = pd.read_csv(os.path.join(PROC_DIR, "posts.csv"))
    comments_df = pd.read_csv(os.path.join(PROC_DIR, "comments.csv"))
    with open(os.path.join(PROC_DIR, "flat_texts.json"), "r", encoding="utf-8") as f:
        flat_rows = json.load(f)

    # insert posts
    for _, row in posts_df.iterrows():
        cur.execute("""
            INSERT INTO posts(post_id, caption, media_type, media_url, created_time, like_count, comments_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (post_id) DO UPDATE SET caption = EXCLUDED.caption
        """, (row.post_id, row.caption, row.media_type, row.media_url, row.created_time, int(row.like_count or 0), int(row.comments_count or 0)))

    # insert comments
    for _, row in comments_df.iterrows():
        cur.execute("""
            INSERT INTO comments (comment_id, post_id, parent_comment_id, user_id, text, created_time, like_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (comment_id) DO UPDATE SET text = EXCLUDED.text
        """, (row.comment_id, row.post_id, row.parent_comment_id if 'parent_comment_id' in row else None, row.user_id, row.text, row.created_time, int(row.like_count or 0)))

    # insert flat_texts
    for r in flat_rows:
        cur.execute("""
            INSERT INTO flat_texts (source_type, source_id, post_id, parent_comment_id, user_id, text, like_count, emoji_summary, created_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            r.get("source_type"),
            r.get("source_id"),
            r.get("post_id"),
            r.get("parent_comment_id"),
            r.get("user_id"),
            r.get("text"),
            int(r.get("like_count") or 0),
            json.dumps(r.get("emoji_summary") or {}),
            r.get("created_time")
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("[load] data loaded into PostgreSQL")

if __name__ == "__main__":
    load_data()
