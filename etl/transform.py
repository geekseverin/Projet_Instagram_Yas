# etl/transform.py
import os, json, re
import pandas as pd
from dateutil import parser
from collections import Counter

RAW_FILE = "data/raw/instagram_raw_posts.json"
PROC_DIR = "data/processed"

def clean_text(s: str):
    if s is None:
        return ""
    s = re.sub(r"http\S+", "", s)                  # URLs
    s = re.sub(r"\s+", " ", s).strip()             # espaces multiples
    return s

def emoji_summary_from_text(text):
    # simple extraction d'emoji: on prend les symboles non ASCII frequent pour emoji
    em = []
    for ch in text:
        if ord(ch) > 10000 or ord(ch) in range(0x2600,0x3300):
            em.append(ch)
    return dict(Counter(em))

def transform(save_posts_csv=True, save_comments_csv=True, save_flat_json=True):
    if not os.path.exists(RAW_FILE):
        raise FileNotFoundError(f"{RAW_FILE} introuvable. Exécute extract.py d'abord.")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    posts_rows = []
    comments_rows = []
    flat_rows = []

    for p in posts:
        pid = p.get("id")
        caption = clean_text(p.get("caption"))
        created_time = parser.isoparse(p.get("timestamp")) if p.get("timestamp") else None
        like_count = int(p.get("like_count") or 0)
        comments_count = int(p.get("comments_count") or 0)
        posts_rows.append({
            "post_id": pid,
            "caption": caption,
            "media_type": p.get("media_type"),
            "media_url": p.get("media_url"),
            "permalink": p.get("permalink"),
            "created_time": created_time,
            "like_count": like_count,
            "comments_count": comments_count
        })
        # flat entry for post
        flat_rows.append({
            "source_type": "post",
            "source_id": pid,
            "post_id": pid,
            "parent_comment_id": None,
            "username": None,
            "text": caption,
            "like_count": like_count,
            "emoji_summary": emoji_summary_from_text(caption),
            "created_time": created_time
        })

        for c in p.get("fetched_comments", []):
            cid = c.get("id")
            ctext = clean_text(c.get("text"))
            cuser = c.get("username")
            ctime = parser.isoparse(c.get("timestamp")) if c.get("timestamp") else None
            clikes = int(c.get("like_count") or 0)
            comments_rows.append({
                "comment_id": cid,
                "post_id": pid,
                "parent_comment_id": None,
                "username": cuser,
                "text": ctext,
                "like_count": clikes,
                "created_time": ctime
            })
            flat_rows.append({
                "source_type": "comment",
                "source_id": cid,
                "post_id": pid,
                "parent_comment_id": None,
                "username": cuser,
                "text": ctext,
                "like_count": clikes,
                "emoji_summary": emoji_summary_from_text(ctext),
                "created_time": ctime
            })
            # if replies exist in API object, handle them (some simulators store replies)
            for reply in c.get("replies", {}).get("data", []):
                rid = reply.get("id")
                rtext = clean_text(reply.get("text"))
                ruser = reply.get("username")
                rtime = parser.isoparse(reply.get("timestamp")) if reply.get("timestamp") else None
                rlikes = int(reply.get("like_count") or 0)
                comments_rows.append({
                    "comment_id": rid,
                    "post_id": pid,
                    "parent_comment_id": cid,
                    "username": ruser,
                    "text": rtext,
                    "like_count": rlikes,
                    "created_time": rtime
                })
                flat_rows.append({
                    "source_type": "reply",
                    "source_id": rid,
                    "post_id": pid,
                    "parent_comment_id": cid,
                    "username": ruser,
                    "text": rtext,
                    "like_count": rlikes,
                    "emoji_summary": emoji_summary_from_text(rtext),
                    "created_time": rtime
                })

    os.makedirs(PROC_DIR, exist_ok=True)
    if save_posts_csv:
        pd.DataFrame(posts_rows).to_csv(os.path.join(PROC_DIR, "posts.csv"), index=False)
    if save_comments_csv:
        # comments.csv will contain both comments and replies (parent_comment_id set)
        pd.DataFrame(comments_rows).to_csv(os.path.join(PROC_DIR, "comments.csv"), index=False)
    if save_flat_json:
        with open(os.path.join(PROC_DIR, "flat_texts.json"), "w", encoding="utf-8") as f:
            json.dump(flat_rows, f, ensure_ascii=False, indent=2, default=str)
    print(f"[transform] {len(posts_rows)} posts, {len(comments_rows)} comments, {len(flat_rows)} flat rows")
    return True

if __name__ == "__main__":
    transform()
