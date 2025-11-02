from typing import List, Dict
import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime

def _safe_to_dt(val):
    if not val:
        return None
    try:
        return parsedate_to_datetime(val) if isinstance(val, str) else datetime(*val[:6])
    except Exception:
        return None

def fetch_rss(urls: List[str], max_items: int = 20) -> List[Dict]:
    items: List[Dict] = []
    for url in urls:
        d = feedparser.parse(url)
        for e in d.entries[:max_items]:
            title = getattr(e, "title", "(sin título)")
            link = getattr(e, "link", "")
            published = _safe_to_dt(getattr(e, "published", None) or getattr(e, "updated", None))
            items.append({
                "title": title,
                "link": link,
                "published": published,
                "source": d.feed.get("title", url)
            })
    items.sort(key=lambda x: (x["published"] or datetime.min, x["title"]), reverse=True)
    return items
