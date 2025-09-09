# etl/extract.py
import os, json, time, requests
from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID

RAW_DIR = "data/raw"
API_BASE = "https://graph.facebook.com/v19.0"

def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def get_media_list(limit=25):
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ID:
        raise RuntimeError("IG_ACCESS_TOKEN ou IG_BUSINESS_ID manquant dans config/settings.py")
    url = f"{API_BASE}/{INSTAGRAM_BUSINESS_ID}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
        "limit": limit
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

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
        next_url = paging.get("next")
        if not next_url:
            break
        url = next_url
        params = {}
        time.sleep(0.2)
    return results

def extract_all(limit_posts=20, save_path="data/raw/instagram_raw_posts.json"):
    # récupère les posts et commentaires et sauvegarde en JSON
    try:
        media = get_media_list(limit=limit_posts)
    except Exception as e:
        raise

    posts = []
    for m in media.get("data", []):
        mid = m.get("id")
        comments = []
        try:
            comments = get_comments_for_media(mid)
        except Exception:
            comments = []
        m["fetched_comments"] = comments
        posts.append(m)

    save_json(posts, save_path)
    print(f"[extract] {len(posts)} posts saved to {save_path}")
    return posts

if __name__ == "__main__":
    extract_all(limit_posts=10)
