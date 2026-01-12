import requests
from bs4 import BeautifulSoup
from grabwebdata import try_scrape_recipe
from pathlib import Path 
import time
import json
import random
def fetch_sitemap_urls(sitemap_url):
    headers = {
        "User-Agent": "EducationalScraper/1.0"
    }

    resp = requests.get(sitemap_url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "xml")
    return [loc.text.strip() for loc in soup.find_all("loc")]


def is_valid_recipe(soup):
    return (
        soup.find("div", class_="wprm-entry-content") is not None
        and soup.find("div", class_="wprm-entry-nutrition") is not None
    )


def crawl_sitemap(urls, out_dir="recipes"):
    Path(out_dir).mkdir(exist_ok=True)

    for i, url in enumerate(urls, 1):
        if url[-1] == '/':
            print(f"[{i}/{len(urls)}] Scraping {url}")

            recipe = try_scrape_recipe(url)

            if recipe:
                slug = url.rstrip("/").split("/")[-1]
                path = Path(out_dir) / f"{slug}.json"

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(recipe, f, indent=2, ensure_ascii=False)

                print(f"  ✔ Saved {path.name}")
            else:
                print(f"  ↷ Skipped")

            time.sleep(random.randint(3,5) + random.random())  # rate limiting (important)
urls = fetch_sitemap_urls("https://www.recipetineats.com/post-sitemap.xml")
crawl_sitemap(urls)