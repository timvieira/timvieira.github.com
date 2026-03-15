#!/usr/bin/env python3
"""Tests to verify generated output against reference files.

Reference files:
  ../index.html      - the hand-maintained HTML publications list
  ../cv/cv.bib       - the hand-maintained BibTeX file

The tests compare specific fields to catch data-entry errors in papers.yaml.
"""

import re
import yaml
import difflib
from pathlib import Path
from collections import defaultdict

from build import (
    load_papers, generate_bibtex, generate_bibtex_entry,
    strip_braces, bibtex_author_format, latex_escape,
)

ROOT = Path(__file__).parent
REF_BIB = ROOT / "cv" / "cv.bib"
REF_HTML = ROOT / "index.html"


# ── helpers ──────────────────────────────────────────────────────────


def parse_ref_bibtex(path):
    """Parse reference .bib into dict keyed by cite key."""
    text = path.read_text()
    entries = {}
    # Split on @type{key, patterns
    for m in re.finditer(
        r'@(\w+)\{([^,]+),\s*(.*?)\n\}', text, re.DOTALL
    ):
        etype, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields = {}
        fields['_type'] = etype.lower()
        # Parse field = value pairs, handling nested braces
        for fm in re.finditer(r'(\w+)\s*=\s*', body):
            fname = fm.group(1).lower()
            rest = body[fm.end():]
            if rest.startswith('{'):
                # Find matching closing brace (handle nesting)
                depth = 0
                end = 0
                for i, c in enumerate(rest):
                    if c == '{': depth += 1
                    elif c == '}': depth -= 1
                    if depth == 0:
                        end = i
                        break
                fval = rest[1:end]  # strip outer braces
            elif rest.startswith('"'):
                end = rest.index('"', 1)
                fval = rest[1:end]
            else:
                # bare value (number etc)
                end_match = re.match(r'([^,}\s]+)', rest)
                fval = end_match.group(1) if end_match else ''
            fval = re.sub(r'\s+', ' ', fval).strip()
            fields[fname] = fval
        entries[key] = fields
    return entries


def extract_html_titles(path):
    """Extract publication titles from index.html (skip empty/template entries)."""
    text = path.read_text()
    # Remove HTML comments first to skip template entries
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    titles = []
    for m in re.finditer(
        r'<a\s+class="pub-title"[^>]*>\s*(.*?)\s*</a>',
        text, re.DOTALL
    ):
        title = re.sub(r'\s+', ' ', m.group(1).strip())
        if title:  # skip empty template entries
            titles.append(title)
    return titles


def normalize_title(t):
    """Normalize for comparison: lowercase, resolve LaTeX, collapse whitespace."""
    t = latex_to_unicode(t)
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t


LATEX_TO_UNICODE = {
    '\\"u': 'ü', '\\"o': 'ö', '\\"a': 'ä', '\\"U': 'Ü',
    "\\'e": 'é', "\\'E": 'É', "\\'a": 'á', "\\'o": 'ó',
    '\\~a': 'ã', '\\~n': 'ñ',
    '\\ae': 'æ', '\\AE': 'Æ',
}


def latex_to_unicode(s):
    """Convert LaTeX accent commands to their Unicode equivalents."""
    # Handle {\"u} style
    for latex, uni in LATEX_TO_UNICODE.items():
        s = s.replace('{' + latex + '}', uni)
    # Handle \"u style (without braces)
    for latex, uni in LATEX_TO_UNICODE.items():
        s = s.replace(latex, uni)
    s = s.replace('{', '').replace('}', '')
    return s


def normalize_author_name(name):
    """Normalize author name for comparison, preserving the actual name."""
    name = name.strip()
    name = latex_to_unicode(name)
    if ',' in name:
        parts = name.split(',', 1)
        name = parts[1].strip() + ' ' + parts[0].strip()
    return re.sub(r'\s+', ' ', name).strip().lower()


# ── tests ────────────────────────────────────────────────────────────


def test_yaml_loads():
    """papers.yaml parses without error."""
    papers = load_papers()
    assert len(papers) > 0, "No papers loaded"
    print(f"  OK: loaded {len(papers)} papers")


def test_unique_ids():
    """All paper IDs are unique."""
    papers = load_papers()
    ids = [p["id"] for p in papers]
    dupes = [x for x in ids if ids.count(x) > 1]
    assert not dupes, f"Duplicate IDs: {set(dupes)}"
    print(f"  OK: {len(ids)} unique IDs")


def test_required_fields():
    """Every paper has the required fields."""
    papers = load_papers()
    required = ["id", "title", "authors", "year", "venue", "type", "links"]
    for p in papers:
        for field in required:
            assert field in p, f"Paper {p.get('id', '???')} missing field: {field}"
        assert "url" in p["links"], f"Paper {p['id']} missing links.url"
    print(f"  OK: all {len(papers)} papers have required fields")


def test_bibtex_titles_match_reference():
    """Titles in papers.yaml match those in the reference cv.bib."""
    if not REF_BIB.exists():
        print("  SKIP: reference bib not found")
        return

    papers = load_papers()
    ref = parse_ref_bibtex(REF_BIB)

    yaml_by_norm_title = {}
    for p in papers:
        nt = normalize_title(p["title"])
        yaml_by_norm_title[nt] = p

    matched = 0
    missing = []
    for key, fields in ref.items():
        ref_title = fields.get("title", "")
        nt = normalize_title(ref_title)
        if nt in yaml_by_norm_title:
            matched += 1
        else:
            # Try fuzzy match
            best = difflib.get_close_matches(nt, yaml_by_norm_title.keys(), n=1, cutoff=0.8)
            if best:
                matched += 1
            else:
                missing.append((key, ref_title))

    if missing:
        print(f"  WARNING: {len(missing)} ref bib entries not found in YAML:")
        for key, title in missing:
            print(f"    - {key}: {title}")
    print(f"  OK: {matched}/{len(ref)} reference bib titles matched")


def test_bibtex_authors_match_reference():
    """Author lists match between YAML and reference bib."""
    if not REF_BIB.exists():
        print("  SKIP: reference bib not found")
        return

    papers = load_papers()
    ref = parse_ref_bibtex(REF_BIB)

    yaml_by_norm_title = {}
    for p in papers:
        nt = normalize_title(p["title"])
        yaml_by_norm_title[nt] = p

    mismatches = []
    for key, fields in ref.items():
        ref_title = normalize_title(fields.get("title", ""))

        # Find matching YAML entry
        yaml_paper = yaml_by_norm_title.get(ref_title)
        if not yaml_paper:
            best = difflib.get_close_matches(ref_title, yaml_by_norm_title.keys(), n=1, cutoff=0.8)
            if best:
                yaml_paper = yaml_by_norm_title[best[0]]

        if not yaml_paper:
            continue

        # Compare author lists
        ref_authors_raw = fields.get("author", "")
        ref_authors = [normalize_author_name(a) for a in re.split(r'\s+and\s+', ref_authors_raw)]
        yaml_authors = [normalize_author_name(a) for a in yaml_paper["authors"]]

        # Compare sets (order may differ)
        ref_set = set(ref_authors)
        yaml_set = set(yaml_authors)

        if ref_set != yaml_set:
            # Check if difference is just abbreviation (e.g. "David A. Smith" vs "David Smith")
            # Be lenient: check last names match
            ref_lasts = {a.split()[-1] for a in ref_set}
            yaml_lasts = {a.split()[-1] for a in yaml_set}
            if ref_lasts != yaml_lasts:
                mismatches.append((key, ref_set - yaml_set, yaml_set - ref_set))

    if mismatches:
        print(f"  WARNING: {len(mismatches)} author mismatches:")
        for key, only_ref, only_yaml in mismatches:
            print(f"    {key}:")
            if only_ref:
                print(f"      ref only: {only_ref}")
            if only_yaml:
                print(f"      yaml only: {only_yaml}")
    else:
        print(f"  OK: all matched author lists agree")


def test_html_titles_match_reference():
    """Titles in papers.yaml cover all titles in reference index.html."""
    if not REF_HTML.exists():
        print("  SKIP: reference HTML not found")
        return

    papers = load_papers()
    ref_titles = extract_html_titles(REF_HTML)

    yaml_norm_titles = {normalize_title(p["title"]) for p in papers}

    matched = 0
    missing = []
    for rt in ref_titles:
        nt = normalize_title(rt)
        if nt in yaml_norm_titles:
            matched += 1
        else:
            best = difflib.get_close_matches(nt, yaml_norm_titles, n=1, cutoff=0.8)
            if best:
                matched += 1
            else:
                missing.append(rt)

    if missing:
        print(f"  WARNING: {len(missing)} HTML titles not found in YAML:")
        for t in missing:
            print(f"    - {t}")
    print(f"  OK: {matched}/{len(ref_titles)} HTML reference titles matched")


def test_bibtex_roundtrip():
    """Generated BibTeX can be parsed back."""
    papers = load_papers()
    bib = generate_bibtex(papers)

    # Simple check: count @type{ entries
    entry_count = len(re.findall(r'^@\w+\{', bib, re.MULTILINE))
    assert entry_count == len(papers), \
        f"Expected {len(papers)} entries, got {entry_count}"
    print(f"  OK: {entry_count} BibTeX entries generated and parseable")


def test_strip_braces():
    assert strip_braces("{K}-best") == "K-best"
    assert strip_braces("Hello {World}") == "Hello World"
    assert strip_braces("No braces") == "No braces"
    print("  OK: strip_braces")


def test_bibtex_author_format():
    assert bibtex_author_format(["Tim Vieira"]) == "Vieira, Tim"
    assert bibtex_author_format(["Tim Vieira", "Jason Eisner"]) == \
        "Vieira, Tim and Eisner, Jason"
    assert bibtex_author_format(["Aaron Steven White"]) == "White, Aaron Steven"
    print("  OK: bibtex_author_format")


def test_bibtex_entry_types():
    """Verify article entries use journal, inproceedings use booktitle."""
    papers = load_papers()
    for p in papers:
        bib = generate_bibtex_entry(p)
        if p["type"] == "article":
            assert "journal" in bib, f"{p['id']}: article missing journal"
            assert "booktitle" not in bib, f"{p['id']}: article has booktitle"
        elif p["type"] == "inproceedings":
            assert "booktitle" in bib, f"{p['id']}: inproceedings missing booktitle"
            assert "journal" not in bib, f"{p['id']}: inproceedings has journal"
    print(f"  OK: entry type/field consistency")


def test_years_reasonable():
    """All years are in reasonable range."""
    papers = load_papers()
    for p in papers:
        assert 2005 <= p["year"] <= 2030, \
            f"{p['id']}: year {p['year']} out of range"
    print(f"  OK: all years in range")


def test_paper_count():
    """Verify we have at least as many papers as in the reference files."""
    papers = load_papers()
    ref_bib = parse_ref_bibtex(REF_BIB) if REF_BIB.exists() else {}
    ref_html_titles = extract_html_titles(REF_HTML) if REF_HTML.exists() else []

    # We should have at least as many as the references
    print(f"  INFO: YAML has {len(papers)} papers")
    print(f"  INFO: Reference bib has {len(ref_bib)} entries")
    print(f"  INFO: Reference HTML has {len(ref_html_titles)} entries")

    if ref_bib:
        # YAML should contain all non-blog bib entries
        assert len(papers) >= len(ref_bib) - 4, \
            f"YAML ({len(papers)}) has fewer papers than bib ({len(ref_bib)})"
    if ref_html_titles:
        assert len(papers) >= len(ref_html_titles), \
            f"YAML ({len(papers)}) has fewer papers than HTML ({len(ref_html_titles)})"
    print(f"  OK: paper count is consistent")


def test_bibtex_special_chars():
    """Verify LaTeX escaping of special characters."""
    papers = load_papers()
    bib = generate_bibtex(papers)

    # Check Schütze is properly escaped
    if any("Sch" in a for p in papers for a in p["authors"]):
        assert '{\\"u}' in bib, "Schütze should be escaped as {\\\"u}"
        print("  OK: Schütze properly escaped")

    # Check Vésteinn is properly escaped
    if any("Vé" in a or "\u00E9" in a for p in papers for a in p["authors"]):
        assert "{\\'e}" in bib, "é should be escaped as {\\'e}"
        print("  OK: é properly escaped")


def test_no_double_braces_in_titles():
    """Titles shouldn't have double braces like {{word}}."""
    papers = load_papers()
    for p in papers:
        assert "{{" not in p["title"], \
            f"{p['id']}: double braces in title: {p['title']}"
    print(f"  OK: no double braces in titles")


def parse_html_entries(path):
    """Parse each <li> pub entry from index.html into structured dicts."""
    text = path.read_text()
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Extract the publications <ul> block
    m = re.search(r'<div id="publications".*?<ul>(.*?)</ul>', text, re.DOTALL)
    if not m:
        return []
    ul_content = m.group(1)
    entries = []
    for li in re.finditer(r'<li[^>]*>(.*?)</li>', ul_content, re.DOTALL):
        body = li.group(1)
        entry = {}
        # Title
        tm = re.search(r'<a\s+class="pub-title"[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', body, re.DOTALL)
        if tm:
            entry['url'] = tm.group(1).strip()
            entry['title'] = re.sub(r'\s+', ' ', tm.group(2)).strip()
        if not entry.get('title'):
            continue
        # Authors
        am = re.search(r'<span\s+class="pub-author"[^>]*>\s*(.*?)\s*</span>', body, re.DOTALL)
        if am:
            raw = am.group(1).strip()
            authors = [a.strip().rstrip(',') for a in re.split(r',\s*\n\s*|,\s+', raw) if a.strip()]
            entry['authors'] = authors
        # Venue
        vm = re.search(r'<a\s+class="pub-venue"[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', body, re.DOTALL)
        if vm:
            entry['venue_url'] = vm.group(1).strip()
            entry['venue_text'] = re.sub(r'\s+', ' ', vm.group(2)).strip()
        # Extra links
        entry['extras'] = {}
        for em in re.finditer(r'<a\s+class="(?:extra|pub-award)[^"]*"[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', body, re.DOTALL):
            label = re.sub(r'\s+', ' ', em.group(2)).strip()
            entry['extras'][label.lower()] = em.group(1).strip()
        entries.append(entry)
    return entries


def test_html_detailed_field_comparison():
    """Compare every field of every entry between YAML and reference HTML."""
    if not REF_HTML.exists():
        print("  SKIP: reference HTML not found")
        return

    papers = load_papers()
    ref_entries = parse_html_entries(REF_HTML)

    # Build lookup by normalized title
    yaml_by_title = {}
    for p in papers:
        nt = normalize_title(p["title"])
        yaml_by_title[nt] = p

    issues = []
    checked = 0

    for ref in ref_entries:
        nt = normalize_title(ref['title'])
        yp = yaml_by_title.get(nt)
        if not yp:
            best = difflib.get_close_matches(nt, yaml_by_title.keys(), n=1, cutoff=0.8)
            if best:
                yp = yaml_by_title[best[0]]
        if not yp:
            issues.append(f"  NOT FOUND: {ref['title']}")
            continue
        checked += 1
        pid = yp['id']

        # Compare authors
        if ref.get('authors') and yp.get('authors'):
            ref_auth = [normalize_author_name(a.rstrip('*')) for a in ref['authors']]
            yaml_auth = [normalize_author_name(a) for a in yp['authors']]
            if ref_auth != yaml_auth:
                # Check if it's just ordering or name variants
                if set(ref_auth) != set(yaml_auth):
                    issues.append(f"  {pid}: AUTHOR MISMATCH")
                    issues.append(f"    ref:  {ref['authors']}")
                    issues.append(f"    yaml: {yp['authors']}")

        # Compare primary URL
        ref_url = ref.get('url', '')
        yaml_url = yp.get('links', {}).get('url', '')
        if ref_url and yaml_url and ref_url != yaml_url:
            issues.append(f"  {pid}: URL differs")
            issues.append(f"    ref:  {ref_url}")
            issues.append(f"    yaml: {yaml_url}")

        # Compare extra links (arXiv, code, etc.)
        yaml_links = yp.get('links', {})
        ref_extras = ref.get('extras', {})

        # Check arXiv
        if 'arxiv' in ref_extras:
            yaml_arxiv = yaml_links.get('arXiv', '')
            if yaml_arxiv and ref_extras['arxiv'] != yaml_arxiv:
                issues.append(f"  {pid}: arXiv URL differs")
                issues.append(f"    ref:  {ref_extras['arxiv']}")
                issues.append(f"    yaml: {yaml_arxiv}")
        elif yaml_links.get('arXiv'):
            issues.append(f"  {pid}: YAML has arXiv but ref does not")

        # Check code
        ref_code = ref_extras.get('code') or ref_extras.get('project page')
        yaml_code = yaml_links.get('code', '')
        if ref_code and yaml_code:
            if ref_code != yaml_code:
                issues.append(f"  {pid}: code URL differs")
                issues.append(f"    ref:  {ref_code}")
                issues.append(f"    yaml: {yaml_code}")
        elif ref_code and not yaml_code:
            issues.append(f"  {pid}: ref has code link but YAML does not: {ref_code}")
        elif yaml_code and not ref_code:
            issues.append(f"  {pid}: YAML has code link but ref does not: {yaml_code}")

        # Check venue URL
        ref_venue_url = ref.get('venue_url', '')
        yaml_venue_url = yp.get('venue_url') or ''
        if ref_venue_url and yaml_venue_url:
            # Normalize trailing slashes
            if ref_venue_url.rstrip('/') != yaml_venue_url.rstrip('/'):
                issues.append(f"  {pid}: venue URL differs")
                issues.append(f"    ref:  {ref_venue_url}")
                issues.append(f"    yaml: {yaml_venue_url}")

    if issues:
        print(f"  Found {len(issues)} issues across {checked} entries:")
        for issue in issues:
            print(issue)
    else:
        print(f"  OK: all fields match across {checked} entries")


if __name__ == "__main__":
    tests = [
        test_yaml_loads,
        test_unique_ids,
        test_required_fields,
        test_strip_braces,
        test_bibtex_author_format,
        test_bibtex_entry_types,
        test_bibtex_roundtrip,
        test_years_reasonable,
        test_no_double_braces_in_titles,
        test_paper_count,
        test_bibtex_titles_match_reference,
        test_bibtex_authors_match_reference,
        test_html_titles_match_reference,
        test_html_detailed_field_comparison,
        test_bibtex_special_chars,
    ]

    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            print(f"\n{name}:")
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed:
        exit(1)
