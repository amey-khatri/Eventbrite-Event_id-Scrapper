# pip install requests bs4 lxml
import random
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import certifi

import os
import json
from datetime import datetime, timezone
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into environment

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "test")
COLL_NAME = os.getenv("COLL_NAME", "event_ids")


def upsert_event_ids(ids):
    """Idempotently upsert event IDs into Mongo."""
    if not ids:
        return 0
    client = MongoClient(MONGO_URI,
                         tlsCAFile=certifi.where(),  # <- fixes SSL: CERTIFICATE_VERIFY_FAILED
                         serverSelectionTimeoutMS=30000)
    coll = client[DB_NAME][COLL_NAME]

    ops = [
        UpdateOne(
            {"ev_id": str(eid)},  # use event_id as the _id
            {"$set": {"last_seen_at": datetime.now()},
             "$setOnInsert": {"first_seen_at": datetime.now()}},
            upsert=True
        )
        for eid in ids
    ]

    result = coll.bulk_write(ops, ordered=False)
    client.close()
    # result.upserted_count is only inserts; modified_count is updates
    return (result.upserted_count or 0) + (result.modified_count or 0)


CITY_SLUG = "canada--toronto"
BASE = "https://www.eventbrite.ca"
# Widen coverage by hitting several stable listing variants
SEED_PATHS = [
    f"/d/{CITY_SLUG}/all-events/?page={{page}}",
    f"/d/{CITY_SLUG}/today/?page={{page}}",
    f"/d/{CITY_SLUG}/this-week/?page={{page}}",
    f"/d/{CITY_SLUG}/this-weekend/?page={{page}}",
    f"/d/{CITY_SLUG}/next-week/?page={{page}}",
    f"/d/{CITY_SLUG}/free--events/?page={{page}}",
]

MAX_PAGES_PER_SEED = 20  # tune how deep you want to crawl
REQUEST_TIMEOUT = 20
EVENT_ID_RE = re.compile(r"/e/[^/]*-(\d+)(?:/|$)")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; EB-Scraper/1.0)",
    "Accept-Language": "en-CA,en;q=0.9",
})


def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            # back off on rate limiting or server hiccups
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}")
            r.raise_for_status()
            return r.text, r.url
        except Exception:
            if i == retries - 1:
                return None, url
            time.sleep(0.8 * (2 ** i) + random.random() * 0.4)
    return None, url


def extract_event_ids(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    ids = set()

    # 1) Anchor href pattern: /e/<slug>-<event_id>
    for a in soup.select('a[href*="/e/"]'):
        href = a.get("href") or ""
        full = urljoin(page_url, href)
        m = EVENT_ID_RE.search(full)
        if m:
            ids.add(m.group(1))

        # 2) data-event-id (belt and suspenders)
        deid = a.get("data-event-id")
        if deid and deid.isdigit():
            ids.add(deid)

    # 3) Any element with data-event-id
    for el in soup.select("[data-event-id]"):
        v = el.get("data-event-id")
        if v and v.isdigit():
            ids.add(v)

    return ids


def generate_seed_urls():
    for path in SEED_PATHS:
        for page in range(1, MAX_PAGES_PER_SEED + 1):
            yield urljoin(BASE, path.format(page=page))


def scrape_event_ids():
    all_ids = set()
    pages_crawled = 0

    for url in generate_seed_urls():
        html, final_url = fetch(url)
        pages_crawled += 1
        if not html:
            # skip if this page failed after retries
            time.sleep(0.2)
            continue

        ids = extract_event_ids(html, final_url)
        all_ids.update(ids)

        # tiny, jittered delay to be polite
        time.sleep(0.05 + random.random() * 0.1)

        # Optional early-exit heuristic: stop a seed if a page returns 0 IDs
        # (disabled globally here because we’re interleaving seeds)

    print(f"Pages crawled: {pages_crawled}")
    print(f"Unique event IDs found: {len(all_ids)}")
    return sorted(all_ids, key=int)


def main():
    ids = scrape_event_ids()

    changed = upsert_event_ids(ids)
    print(f"Upserted {len(ids)} IDs (changed {changed}) to {DB_NAME}.{COLL_NAME}")


if __name__ == "__main__":
    main()
