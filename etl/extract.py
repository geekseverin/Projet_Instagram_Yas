# etl/extract.py
import requests, os, json, time
from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID

RAW_DIR = "data/raw"
API_BASE = "https://graph.facebook.com/v19.0"

def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def get_media_list(limit=25):
    url = f"{API_BASE}/{INSTAGRAM_BUSINESS_ID}/media"
    params = {
        "fields": "id,caption,media_type,media_url,timestamp,like_count,comments_count",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
        "limit": limit
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_comments_for_media(media_id, limit=50):
    results = []
    url = f"{API_BASE}/{media_id}/comments"
    params = {
        "fields": "id,text,username,timestamp,like_count",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
        "limit": limit
    }
    while True:
        r = requests.get(url, params=params)
        r.raise_for_status()
        j = r.json()
        results.extend(j.get("data", []))
        paging = j.get("paging", {})
        curs = paging.get("cursors", {}).get("after")
        next_url = paging.get("next")
        if not next_url:
            break
        # follow next (Graph next URL already includes access token)
        url = next_url
        params = {}
        time.sleep(0.2)
    return results

def extract_all(limit_posts=10):
    media = get_media_list(limit=limit_posts)
    posts = []
    for m in media.get("data", []):
        media_id = m["id"]
        comments = get_comments_for_media(media_id)
        m["fetched_comments"] = comments
        posts.append(m)
    os.makedirs(RAW_DIR, exist_ok=True)
    save_json(posts, os.path.join(RAW_DIR, "instagram_raw_posts.json"))
    print(f"[extract] {len(posts)} posts saved to {RAW_DIR}/instagram_raw_posts.json")
    return posts

if __name__ == "__main__":
    extract_all(limit_posts=10)
