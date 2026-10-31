#!/usr/bin/env python3
"""
List published blog posts that are missing from blog_posts.yaml.

    python check_blog_posts.py [BLOG_CONTENT_DIR]

The directory defaults to $BLOG_CONTENT (the blog repo's content/ folder).
Exits with status 1 if any posts are missing, so CI flags them.
"""

import os, sys
from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parent.parent
BLOGS_YAML = SITE_ROOT / "blog_posts.yaml"

if len(sys.argv) > 1:
    os.environ["BLOG_CONTENT"] = sys.argv[1]

# Import after setting BLOG_CONTENT, which the module reads at import time.
from precompute_embeddings import BLOG_CONTENT, TITLE_ALIASES, read_frontmatter


def main():
    if not BLOG_CONTENT.is_dir():
        sys.exit(f"Blog content folder not found: {BLOG_CONTENT}")

    listed = set()
    for b in yaml.safe_load(open(BLOGS_YAML)):
        title = b["title"].lower()
        listed.add(TITLE_ALIASES.get(title, title))

    missing = []
    for md_file in sorted(BLOG_CONTENT.glob("*.md")):
        meta = read_frontmatter(md_file)
        title = meta.get("title")
        if not title or meta.get("status", "").lower() == "draft":
            continue
        if title.lower() not in listed:
            missing.append((meta.get("date", "?"), title, md_file.name))

    if not missing:
        print("All published blog posts are in blog_posts.yaml.")
        return
    print(f"{len(missing)} published blog post(s) missing from blog_posts.yaml:")
    for date, title, name in sorted(missing, reverse=True):
        print(f"  {date}  {title}  ({name})")
    print("Add them to blog_posts.yaml (with themes) so they appear in the research graph.")
    sys.exit(1)


if __name__ == "__main__":
    main()
