# etl/transform.py
import os, json, re
import pandas as pd
from dateutil import parser
from collections import Counter

RAW_PATH = "data/raw/instagram_raw_posts.json"
PROC_DIR = "data/processed"

def clean_text(s):
    if s is None:
        return ""
    # enlever URLs
    s = re.sub(r"http\S+", "", s)
    # garder les emojis (optionnel) et retirer caractères non imprimables
    s = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", s)
    s = s.strip()
    return s

def emoji_summary_from_likes(likes_list):
    # likes_list: list of {id, type}
    c = Counter()
    for l in likes_list or []:
        if l.get("type"):
            c[l["type"]] += 1
    return dict(c)

def transform():
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"{RAW_PATH} introuvable. Exécute d'abord extract.py")
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)

    posts_rows = []
    post_likes_rows = []
    comments_rows = []
    comment_likes_rows = []
    flat_rows = []

    for p in posts:
        pid = p.get("id")
        caption = clean_text(p.get("caption"))
        media_type = p.get("media_type")
        media_url = p.get("media_url")
        created_time = parser.isoparse(p.get("timestamp")) if p.get("timestamp") else None
        like_count = p.get("like_count") or 0
        comments_count = p.get("comments_count") or 0

        posts_rows.append({
            "post_id": pid,
            "caption": caption,
            "media_type": media_type,
            "media_url": media_url,
            "created_time": created_time,
            "like_count": like_count,
            "comments_count": comments_count
        })

        # flatten post as text entry
        flat_rows.append({
            "source_type": "post",
            "source_id": pid,
            "post_id": pid,
            "parent_comment_id": None,
            "user_id": None,
            "text": caption,
            "like_count": like_count,
            "emoji_summary": {},
            "created_time": created_time
        })

        # comments (fetched_comments)
        for c in p.get("fetched_comments", []):
            cid = c.get("id")
            ctext = clean_text(c.get("text"))
            cuser = c.get("username")
            ctime = parser.isoparse(c.get("timestamp")) if c.get("timestamp") else None
            clikes = c.get("like_count") or 0

            comments_rows.append({
                "comment_id": cid,
                "post_id": pid,
                "parent_comment_id": None,
                "user_id": cuser,
                "text": ctext,
                "created_time": ctime,
                "like_count": clikes
            })

            # flat comment
            flat_rows.append({
                "source_type": "comment",
                "source_id": cid,
                "post_id": pid,
                "parent_comment_id": None,
                "user_id": cuser,
                "text": ctext,
                "like_count": clikes,
                "emoji_summary": {},
                "created_time": ctime
            })

            # NOTE: si tu veux récupérer likes par commentaire (emoji), il faut appeler /{comment_id}/likes (non toujours dispo).
            # Ici on ne gère pas reactions emojis détaillées par commentaire (extend si dispo).

    os.makedirs(PROC_DIR, exist_ok=True)
    pd.DataFrame(posts_rows).to_csv(os.path.join(PROC_DIR, "posts.csv"), index=False)
    pd.DataFrame(comments_rows).to_csv(os.path.join(PROC_DIR, "comments.csv"), index=False)
    pd.DataFrame(flat_rows).to_json(os.path.join(PROC_DIR, "flat_texts.json"), orient="records", force_ascii=False, indent=2)
    print(f"[transform] {len(posts_rows)} posts, {len(comments_rows)} comments, {len(flat_rows)} flat rows saved under {PROC_DIR}")
    return True

if __name__ == "__main__":
    transform()
