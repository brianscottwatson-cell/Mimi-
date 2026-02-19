#!/usr/bin/env python3
"""Generate robots.txt and sitemap.xml for a lead-gen website.

Usage:
    python create_seo_files.py <domain> <pages_json> <output_dir>

Example:
    python create_seo_files.py example.com pages.json client/public/

pages.json format:
    [
        {"url": "/", "priority": "1.0"},
        {"url": "/services", "priority": "0.9"},
        {"url": "/contact", "priority": "0.9"},
        {"url": "/blog", "priority": "0.6"},
        {"url": "/mentions-legales", "priority": "0.3"}
    ]
"""

import json
import os
import sys
from datetime import date


def create_robots_txt(domain: str) -> str:
    return f"""User-agent: *
Allow: /

Sitemap: https://{domain}/sitemap.xml
"""


def create_sitemap_xml(domain: str, pages: list) -> str:
    today = date.today().isoformat()
    urls = ""
    for page in pages:
        url = page["url"].rstrip("/") or "/"
        priority = page.get("priority", "0.5")
        changefreq = "weekly" if float(priority) >= 0.7 else "monthly"
        urls += f"""  <url>
    <loc>https://{domain}{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}</urlset>
"""


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    domain, pages_path, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")

    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    robots_path = os.path.join(output_dir, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(create_robots_txt(domain))
    print(f"Created: {robots_path}")

    sitemap_path = os.path.join(output_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(create_sitemap_xml(domain, pages))
    print(f"Created: {sitemap_path}")

    print(f"\nDone — robots.txt and sitemap.xml for {domain}")


if __name__ == "__main__":
    main()
