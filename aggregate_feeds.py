import json
import feedparser
import requests
import datetime
import time

INPUT_FEEDS = "feeds.json"
OUTPUT_NEWS = "news.json"
ITEMS_PER_FEED = 5       # how many items to pull per feed
TOTAL_MAX_ITEMS = 100    # cap total items
TIMEOUT = 10             # seconds to wait per feed

def iso8601(dt_struct):
    """Convert time.struct_time to ISO8601 string."""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", dt_struct)
    except Exception:
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_feed(url, source_title):
    """Fetch a feed with timeout and error handling."""
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as e:
        print(f"⚠️ Skipping {source_title}: {e}")
        return None

def aggregate():
    with open(INPUT_FEEDS, "r", encoding="utf-8") as f:
        feeds = json.load(f)["feeds"]

    all_items = []
    for feed_meta in feeds:
        url = feed_meta["xmlUrl"]
        source_title = feed_meta.get("title", "Unknown Source")
        print(f"🔎 Fetching {source_title} ({url})...")
        d = fetch_feed(url, source_title)
        if not d:
            continue

        for entry in d.entries[:ITEMS_PER_FEED]:
            published_parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            published_iso = iso8601(published_parsed) if published_parsed else ""

            all_items.append({
                "source": d.feed.get("title", source_title),
                "title": getattr(entry, "title", "Untitled"),
                "link": getattr(entry, "link", ""),
                "published": published_iso,
                "summary": getattr(entry, "summary", "")
            })

    # Sort newest-first
    def parse_date(x):
        try:
            return datetime.datetime.fromisoformat(x.replace("Z", "+00:00"))
        except Exception:
            return datetime.datetime.min

    all_items.sort(key=lambda x: parse_date(x.get("published", "")), reverse=True)
    all_items = all_items[:TOTAL_MAX_ITEMS]

    with open(OUTPUT_NEWS, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote {len(all_items)} items to {OUTPUT_NEWS}")

if __name__ == "__main__":
    aggregate()