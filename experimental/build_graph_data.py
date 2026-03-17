#!/usr/bin/env python3
"""
Build the JS data arrays for research-graph.html from papers.yaml + blog_posts.yaml.

    python build_graph_data.py

Reads:  ../papers.yaml, ../blog_posts.yaml
Writes: updates research-graph.html in-place (replaces the papers/blogs arrays)
"""

import json, re
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
SITE_ROOT = SCRIPT_DIR.parent
HTML_PATH = SCRIPT_DIR / "research-graph.html"


def load_papers():
    raw = yaml.safe_load(open(SITE_ROOT / "papers.yaml"))
    result = []
    for p in raw:
        if not p.get("themes"):
            continue
        last_names = [a.strip().split()[-1] for a in (p.get("authors") or [])]
        title = re.sub(r"[{}]", "", p.get("title", ""))
        note = p.get("note", "")
        award = None
        if note and re.search(r"award|runner.up", note, re.I):
            award = re.sub(r"[^\w\s]", "", note).strip()
        links = p.get("links", {})
        url = links.get("arXiv") or links.get("url", "")
        # Collect all extra links
        extra_links = {}
        for key in ("arXiv", "code", "slides", "video", "poster", "openreview", "data"):
            if links.get(key):
                extra_links[key] = links[key]
        # Custom "other" links
        other_links = links.get("other", [])
        if other_links:
            extra_links["other"] = other_links  # list of {label, url}
        result.append({
            "id": p["id"],
            "title": title,
            "authors": ", ".join(last_names),
            "venue": p.get("venue", ""),
            "year": p["year"],
            "award": award,
            "url": url,
            "themes": p["themes"],
            "links": extra_links if extra_links else None,
        })
    return result


def load_blogs():
    raw = yaml.safe_load(open(SITE_ROOT / "blog_posts.yaml"))
    result = []
    for b in raw:
        tags = b.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
        result.append({
            "id": b["id"],
            "title": b["title"],
            "year": b["year"],
            "tags": tags_str,
            "url": b.get("url", ""),
            "themes": b.get("themes", []),
        })
    return result


def to_js_obj(obj):
    """Convert a dict to a JS object literal string."""
    parts = []
    for k, v in obj.items():
        if v is None:
            continue
        if isinstance(v, (list, dict)):
            parts.append(f"{k}:{json.dumps(v)}")
        elif isinstance(v, int):
            parts.append(f"{k}:{v}")
        else:
            s = str(v).replace("\\", "\\\\").replace("'", "\\'")
            parts.append(f"{k}:'{s}'")
    return "{" + ",".join(parts) + "}"


def generate_js(papers, blogs):
    lines = ["var papers=["]
    for p in papers:
        lines.append("  " + to_js_obj(p) + ",")
    lines.append("];")
    lines.append("var blogs=[")
    for b in blogs:
        lines.append("  " + to_js_obj(b) + ",")
    lines.append("];")
    return "\n".join(lines)


def inject_into_html(js_data):
    html = HTML_PATH.read_text()

    # Find the region to replace: from "var papers=[" through the setup lines
    # up to and including "var N=allNodes.length;"
    start = re.search(r"^(?:// Load papers|var papers\s*=\s*\[)", html, re.MULTILINE)
    end = re.search(r"var N\s*=\s*allNodes\.length;", html)

    if not start or not end:
        print("ERROR: Could not find data markers in HTML")
        return False

    setup = """
papers.forEach(function(p){p.kind='paper';});
blogs.forEach(function(b){b.kind='blog';b.authors='';b.venue=b.tags;});
var allNodes=[].concat(papers,blogs);
var N=allNodes.length;""".strip()

    new_block = js_data + "\n" + setup
    html = html[: start.start()] + new_block + html[end.end() :]
    HTML_PATH.write_text(html)
    return True


def main():
    papers = load_papers()
    blogs = load_blogs()
    print(f"Loaded {len(papers)} papers, {len(blogs)} blog posts")

    js_data = generate_js(papers, blogs)
    if inject_into_html(js_data):
        print(f"Updated {HTML_PATH}")
    else:
        print("Failed to update HTML. Output JS to stdout instead:")
        print(js_data)


if __name__ == "__main__":
    main()
