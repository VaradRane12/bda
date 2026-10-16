"""
Step 1: Download Wikipedia hourly pageview files.

Wikimedia publishes one file per hour here:
    https://dumps.wikimedia.org/other/pageviews/

Each file is ~60 MB (gzip) and holds ~6.5 million rows like:
    en Virat_Kohli 2453 0
    (language) (page title) (views in that hour) (unused)

Usage:
    python download_data.py                       # default: 3 days from START_DATE
    python download_data.py --start 2026-09-25 --days 7
"""

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests

# Official mirror in Sweden: same files, much faster than dumps.wikimedia.org
BASE_URL = "https://ftp.acc.umu.se/mirror/wikimedia.org/other/pageviews"
# BASE_URL = "https://dumps.wikimedia.org/other/pageviews"   # official source (slow)
DATA_DIR = "data/raw"
START_DATE = "2026-09-28"
DAYS = 3
# Wikimedia rejects requests without a descriptive User-Agent (403 Forbidden)
HEADERS = {"User-Agent": "BDA-MiniProject/1.0 (student project; python-requests)"}


def file_url(hour):
    name = f"pageviews-{hour:%Y%m%d-%H}0000.gz"
    return f"{BASE_URL}/{hour:%Y}/{hour:%Y-%m}/{name}", name


def download(hour):
    url, name = file_url(hour)
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        return f"skip  {name} (already downloaded)"

    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path + ".part", "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    os.rename(path + ".part", path)  # only keep complete files
    return f"done  {name}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=START_DATE, help="first day, YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=DAYS, help="how many days to download")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    start = datetime.strptime(args.start, "%Y-%m-%d")
    hours = [start + timedelta(hours=h) for h in range(args.days * 24)]

    print(f"Downloading {len(hours)} hourly files ({args.days} days) into {DATA_DIR}/ ...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, msg in enumerate(pool.map(download, hours), 1):
            print(f"[{i}/{len(hours)}] {msg}")

    total = sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in os.listdir(DATA_DIR))
    print(f"\nTotal on disk: {total / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
