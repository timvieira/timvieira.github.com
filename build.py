#!/usr/bin/env python3
"""Generate BibTeX and HTML publications list from papers.yaml."""

import yaml
from pathlib import Path

YAML_FILE = Path(__file__).parent / "papers.yaml"


def load_papers(path=YAML_FILE):
    with open(path) as f:
        return yaml.safe_load(f)


def strip_braces(title):
    """Remove BibTeX-style {braces} for HTML/plaintext display."""
    return title.replace("{", "").replace("}", "")


def bibtex_author_format(authors):
    """Convert ['First Last', ...] to BibTeX 'Last, First and Last, First'."""
    parts = []
    for a in authors:
        tokens = a.split()
        if len(tokens) == 1:
            parts.append(tokens[0])
        else:
            last = tokens[-1]
            first = " ".join(tokens[:-1])
            parts.append(f"{last}, {first}")
    return " and ".join(parts)


def latex_escape(s):
    """Escape special characters for LaTeX/BibTeX values."""
    # Handle ü -> {\"u}, é -> {\\'e}, etc.
    replacements = {
        "\u00FC": '{\\"u}',   # ü
        "\u00E9": "{\\'e}",   # é
        "\u00E3": '{\\~a}',   # ã
        "\u00F6": '{\\"o}',   # ö
        "\u00E6": '{\\ae}',   # æ
        "\u00C9": "{\\'E}",   # É
    }
    for char, repl in replacements.items():
        s = s.replace(char, repl)
    return s


def generate_bibtex_entry(paper):
    """Generate a single BibTeX entry from a paper dict."""
    pid = paper["id"]
    ptype = paper.get("type", "misc")
    title = paper["title"]  # Keep braces as-is for BibTeX
    authors = bibtex_author_format(paper["authors"])
    year = paper["year"]
    links = paper.get("links", {})
    url = links.get("url", "")
    extra = paper.get("bibtex", {})

    lines = []
    lines.append(f"@{ptype}{{{pid},")
    lines.append(f"  title = {{{latex_escape(title)}}},")
    lines.append(f"  author = {{{latex_escape(authors)}}},")

    if ptype == "article":
        journal = paper.get("venue_full", "")
        lines.append(f'  journal = {{{latex_escape(journal)}}},')
    elif ptype == "inproceedings":
        booktitle = paper.get("venue_full", "")
        lines.append(f'  booktitle = "{latex_escape(booktitle)}",')
    elif ptype == "phdthesis":
        school = paper.get("venue_full", "")
        lines.append(f'  school = {{{latex_escape(school)}}},')

    lines.append(f"  year = {{{year}}},")

    if url:
        lines.append(f'  url = "{url}",')

    # Extra BibTeX fields
    for key in ["volume", "pages", "doi", "issn", "isbn"]:
        if key in extra:
            lines.append(f"  {key} = {{{extra[key]}}},")

    if "note" in paper:
        lines.append(f'  note = "{paper["note"]}",')

    lines.append("}")
    return "\n".join(lines)


def generate_bibtex(papers):
    """Generate complete BibTeX file content."""
    entries = [generate_bibtex_entry(p) for p in papers]
    return "\n\n".join(entries) + "\n"


def generate_html_entry(paper):
    """Generate a single HTML <li> entry matching the style of index.html."""
    links = paper.get("links", {})
    url = links.get("url", "")
    title = strip_braces(paper["title"])

    # Authors: one per line with trailing commas (except last)
    author_list = list(paper["authors"])
    if "equal_contribution" in paper:
        for idx in paper["equal_contribution"]:
            author_list[idx] = author_list[idx] + "*"

    if len(author_list) <= 3:
        # Short author lists on one line
        author_lines = "                  " + ", ".join(author_list)
    else:
        # One author per line
        parts = []
        for i, a in enumerate(author_list):
            suffix = "," if i < len(author_list) - 1 else ""
            parts.append(f"                  {a}{suffix}")
        author_lines = "\n".join(parts)

    venue = paper.get("venue", "")
    venue_url = paper.get("venue_url") or ""
    note = paper.get("note", "")

    lines = []
    lines.append('           <li style="">')
    lines.append('              <div class="pub">')
    lines.append(f'                <a class="pub-title" href="{url}">')
    lines.append(f'                  {title}')
    lines.append('                </a>')
    lines.append('                <span class="pub-author">')
    lines.append(author_lines)
    lines.append('                </span>')

    # Venue with optional inline note after </a>
    if note:
        lines.append(f'                <a class="pub-venue" href="{venue_url}">{venue}</a>')
        lines.append(f'                ({note})')
    else:
        lines.append(f'                <a class="pub-venue" href="{venue_url}">{venue}</a>')

    lines.append('              </div>')

    # Extras
    extras = []
    if links.get("arXiv"):
        extras.append(f'                <a class="extra arXiv" href="{links["arXiv"]}">arXiv</a>')
    if links.get("code"):
        extras.append(f'                <a class="extra code" href="{links["code"]}">code</a>')
    if links.get("openreview"):
        extras.append(f'                <a class="extra" href="{links["openreview"]}">OpenReview</a>')
    if links.get("slides"):
        extras.append(f'                <a class="extra slides" href="{links["slides"]}">slides</a>')
    if links.get("video"):
        extras.append(f'                <a class="extra video" href="{links["video"]}">video</a>')
    if links.get("poster"):
        extras.append(f'                <a class="extra poster" href="{links["poster"]}">poster</a>')
    if links.get("data"):
        extras.append(f'                <a class="extra data" href="{links["data"]}">data</a>')
    for other in links.get("other", []):
        extras.append(f'                <a class="extra" href="{other["url"]}">{other["label"]}</a>')

    lines.append('              <div class="pub-extras">')
    lines.extend(extras)
    lines.append('              </div>')
    lines.append('           </li>')

    return "\n".join(lines)


def generate_html(papers):
    """Generate HTML publications list."""
    entries = [generate_html_entry(p) for p in papers]
    return "\n\n".join(entries) + "\n"


def generate_index_html(papers, template_path):
    """Generate a full index.html by replacing the publications list in the template."""
    import re
    template = template_path.read_text()

    # Find the <ul> inside <div id="publications"> and replace its contents
    # Pattern: everything between the first <ul> after "publications" and its </ul>
    pattern = re.compile(
        r'(<div id="publications".*?<ul>\s*)'   # prefix up to and including <ul>
        r'(.*?)'                                  # existing list items
        r'(\s*</ul>)',                            # closing </ul>
        re.DOTALL
    )

    pub_html = "\n\n" + generate_html(papers) + "\n          "

    new_html, count = pattern.subn(r'\1' + pub_html + r'\3', template, count=1)
    assert count == 1, "Could not find publications <ul> in template"
    return new_html


if __name__ == "__main__":
    papers = load_papers()
    out_dir = Path(__file__).parent

    bib_path = out_dir / "generated.bib"
    bib_content = generate_bibtex(papers)
    bib_path.write_text(bib_content)
    print(f"Wrote {len(papers)} entries to {bib_path}")

    template_path = out_dir / "index.html"
    if template_path.exists():
        index_path = out_dir / "generated_index.html"
        index_content = generate_index_html(papers, template_path)
        index_path.write_text(index_content)
        print(f"Wrote {index_path}")
