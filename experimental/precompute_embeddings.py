#!/usr/bin/env python3
"""
Compute semantic embeddings from full document content (paper PDFs + blog text),
then compute theme projections for the research-graph visualization.

    pip install sentence-transformers pymupdf requests einops
    python precompute_embeddings.py [--model MODEL_KEY]

Supported models:
    nomic    nomic-ai/nomic-embed-text-v1.5  (8K context, default)
    bge      BAAI/bge-base-en-v1.5           (512 tokens)
    minilm   all-MiniLM-L6-v2                (256 tokens, fast)
"""

import argparse, json, re, time
from pathlib import Path

import numpy as np
import requests
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SITE_ROOT = SCRIPT_DIR.parent                         # timvieira.github.com/
PAPERS_YAML = SITE_ROOT / "papers.yaml"
DOC_DIR = SITE_ROOT / "doc"
HTML_PATH = SCRIPT_DIR / "research-graph.html"
BLOG_CONTENT = Path("/home/timv/projects/blog/main/content")
CACHE_DIR = SCRIPT_DIR / ".content_cache"
CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
MODELS = {
    "nomic": {
        "name": "nomic-ai/nomic-embed-text-v1.5",
        "trust_remote_code": True,
        "prefix": "search_document: ",  # nomic convention
    },
    "bge": {
        "name": "BAAI/bge-base-en-v1.5",
        "trust_remote_code": False,
        "prefix": "",
    },
    "minilm": {
        "name": "all-MiniLM-L6-v2",
        "trust_remote_code": False,
        "prefix": "",
    },
}

# ---------------------------------------------------------------------------
# Item list — derived from papers.yaml and blog_posts.yaml
# Same filtering/ordering as build_graph_data.py so indices match the HTML.
# ---------------------------------------------------------------------------
BLOGS_YAML = SITE_ROOT / "blog_posts.yaml"

ITEMS = []  # populated by load_items() at startup


def load_items():
    """Build ITEMS list from YAML files (same order as research-graph.html)."""
    items = []
    for p in yaml.safe_load(open(PAPERS_YAML)):
        if not p.get("themes"):
            continue
        title = re.sub(r"[{}]", "", p.get("title", ""))
        items.append({"kind": "paper", "yaml_id": p["id"], "title": title})
    for b in yaml.safe_load(open(BLOGS_YAML)):
        items.append({"kind": "blog", "title": b["title"]})
    return items


# ---------------------------------------------------------------------------
# Load papers.yaml (id → entry with links)
# ---------------------------------------------------------------------------
def load_papers_yaml():
    with open(PAPERS_YAML) as f:
        papers = yaml.safe_load(f)
    return {p["id"]: p for p in papers}


# ---------------------------------------------------------------------------
# PDF text extraction (via pymupdf)
# ---------------------------------------------------------------------------
def extract_pdf_text(pdf_path):
    """Extract text from a PDF file, return first ~3000 words."""
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    text = "\n".join(pages)
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000])
    return text


def download_pdf(url, dest_path):
    """Download a PDF from url to dest_path. Returns True on success."""
    print(f"  Downloading {url} ...")
    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"  WARNING: download failed: {e}")
        return False


def resolve_paper_pdf_url(entry):
    """Given a papers.yaml entry, return (pdf_url, local_path_or_None)."""
    links = entry.get("links", {})

    # 1. Local doc/ file (handles both relative "doc/..." and full URL paths)
    url = links.get("url", "")
    doc_prefix = None
    if url.startswith("doc/"):
        doc_prefix = "doc/"
    elif "timvieira.github.io/doc/" in url:
        doc_prefix = url.split("timvieira.github.io/doc/")[0] + "timvieira.github.io/doc/"
    if doc_prefix and url.endswith(".pdf"):
        filename = url.split("/doc/")[-1]
        local = DOC_DIR / filename
        if local.exists():
            return None, local

    # 2. arXiv
    arxiv_url = links.get("arXiv", "")
    if not arxiv_url:
        if "arxiv.org/abs/" in url:
            arxiv_url = url
        elif "arxiv.org/pdf/" in url:
            arxiv_url = url
    if arxiv_url:
        pdf_url = arxiv_url.replace("/abs/", "/pdf/")
        if not pdf_url.endswith(".pdf"):
            pdf_url += ".pdf"
        return pdf_url, None

    # 3. ACL Anthology
    if "aclanthology.org/" in url:
        acl_id = url.rstrip("/").split("/")[-1]
        return f"https://aclanthology.org/{acl_id}.pdf", None

    # 4. Check doc/ directory for a local PDF matching the venue/year
    year = entry.get("year", "")
    venue = entry.get("venue", "").lower().split()[0] if entry.get("venue") else ""
    for pdf in DOC_DIR.glob("*.pdf"):
        name = pdf.name.lower()
        if str(year) in name and venue in name and "slide" not in name and "poster" not in name:
            return None, pdf

    return None, None


# ---------------------------------------------------------------------------
# Paper content extraction
# ---------------------------------------------------------------------------
def get_paper_content(item, papers_by_id):
    yaml_id = item["yaml_id"]
    cache_file = CACHE_DIR / f"{yaml_id}.txt"

    if cache_file.exists():
        text = cache_file.read_text()
        if text.strip():
            return text

    entry = papers_by_id.get(yaml_id)
    if entry is None:
        print(f"  WARNING: {yaml_id} not found in papers.yaml")
        return item["title"]

    pdf_url, local_path = resolve_paper_pdf_url(entry)

    if local_path and local_path.exists():
        text = extract_pdf_text(local_path)
    elif pdf_url:
        tmp_pdf = CACHE_DIR / f"{yaml_id}.pdf"
        if not tmp_pdf.exists():
            ok = download_pdf(pdf_url, tmp_pdf)
            if not ok:
                return item["title"]
            time.sleep(1.5)
        text = extract_pdf_text(tmp_pdf)
    else:
        print(f"  WARNING: no PDF source for {yaml_id}, using title only")
        return item["title"]

    text = clean_text(text)
    cache_file.write_text(text)
    return text


# ---------------------------------------------------------------------------
# Blog content extraction
# ---------------------------------------------------------------------------
def build_blog_title_map():
    """Build a case-insensitive title → file path map from blog .md frontmatter."""
    title_to_file = {}
    for md_file in BLOG_CONTENT.glob("*.md"):
        with open(md_file) as f:
            for line in f:
                if line.startswith("title:"):
                    title = line[len("title:"):].strip()
                    title_to_file[title.lower()] = md_file
                    break

    TITLE_ALIASES = {
        "the restart acceleration trick":
            "the restart acceleration trick: a cure for the heavy tail of wasted time",
        "evaluating nabla f(x) is as fast as f(x)":
            "evaluating \u2207f(x) is as fast as f(x)",
        "gradient-based hyperparameter optimization":
            "gradient-based hyperparameter optimization and the implicit function theorem",
        "multiclass logistic regression and crfs are the same thing":
            "multiclass logistic regression and conditional random fields are the same thing",
    }
    for alias, canonical in TITLE_ALIASES.items():
        if canonical in title_to_file:
            title_to_file[alias] = title_to_file[canonical]

    return title_to_file


def extract_notebook_text(ipynb_path, start_cell=0):
    """Extract markdown + code cell sources from a Jupyter notebook."""
    with open(ipynb_path) as f:
        nb = json.load(f)
    parts = []
    for cell in nb.get("cells", [])[start_cell:]:
        if cell.get("cell_type") in ("markdown", "code"):
            source = cell.get("source", [])
            if isinstance(source, list):
                source = "".join(source)
            parts.append(source)
    return "\n\n".join(parts)


def get_blog_content(item, title_map):
    title = item["title"]
    md_file = title_map.get(title.lower())
    if md_file is None:
        print(f"  WARNING: no blog source for '{title}', using title only")
        return title

    with open(md_file) as f:
        content = f.read()

    nb_match = re.search(r'\{%\s*notebook\s+(\S+)\s+cells\[(\d+):\]\s*%\}', content)
    if nb_match:
        nb_filename = nb_match.group(1)
        start_cell = int(nb_match.group(2))
        nb_path = BLOG_CONTENT / nb_filename
        if nb_path.exists():
            return clean_text(extract_notebook_text(nb_path, start_cell))
        else:
            print(f"  WARNING: notebook {nb_path} not found")

    lines = content.split("\n")
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "" and i > 0:
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:])
    return clean_text(body)


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\\(?:textbf|textit|emph|text|mathrm|mathbf|mathcal)\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ---------------------------------------------------------------------------
# Content extraction (shared across models, cached as .txt files)
# ---------------------------------------------------------------------------
def extract_all_content():
    """Extract text content for all items. Returns list of strings."""
    print("Loading papers.yaml...")
    papers_by_id = load_papers_yaml()
    print("Building blog title map...")
    title_map = build_blog_title_map()

    texts = []
    fallback_count = 0
    n = len(ITEMS)
    for i, item in enumerate(ITEMS):
        label = f"[{i+1:2d}/{n}]"
        if item["kind"] == "paper":
            print(f"{label} Paper: {item['title'][:60]}...")
            content = get_paper_content(item, papers_by_id)
        else:
            print(f"{label} Blog:  {item['title'][:60]}...")
            content = get_blog_content(item, title_map)
        if content == item["title"]:
            fallback_count += 1
            print(f"       → FALLBACK to title only")
        texts.append(content)

    print(f"\nContent extraction done. {fallback_count} items fell back to title only.")
    return texts


# ---------------------------------------------------------------------------
# Embedding with per-model caching
# ---------------------------------------------------------------------------
def get_embeddings(model_key, texts):
    """Load or compute embeddings for the given model. Returns (79, D) array."""
    model_info = MODELS[model_key]
    cache_file = CACHE_DIR / f"embeddings_{model_key}.npz"
    item_keys = [it.get("yaml_id", it["title"]) for it in ITEMS]

    cached = {}
    if cache_file.exists():
        data = np.load(cache_file)
        cached = {k: data[k] for k in data.files}

    uncached = [i for i, k in enumerate(item_keys) if k not in cached]

    if uncached:
        print(f"\n[{model_key}] {len(uncached)} items need encoding, {len(item_keys) - len(uncached)} cached.")
        print(f"[{model_key}] Loading {model_info['name']}...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_info["name"], trust_remote_code=model_info["trust_remote_code"])

        prefix = model_info["prefix"]
        encode_texts = [prefix + texts[i] for i in uncached]
        print(f"[{model_key}] Encoding {len(encode_texts)} documents...")
        new_embeds = model.encode(encode_texts, show_progress_bar=True)
        for idx, emb in zip(uncached, new_embeds):
            cached[item_keys[idx]] = emb

        np.savez(cache_file, **cached)
        print(f"[{model_key}] Saved {len(cached)} embeddings to cache.")
    else:
        print(f"[{model_key}] All {len(item_keys)} embeddings loaded from cache.")

    return np.array([cached[k] for k in item_keys])


# ---------------------------------------------------------------------------
# Theme projections
# ---------------------------------------------------------------------------
def get_theme_order():
    """Derive theme order from the THEMES dict in research-graph.html."""
    html = HTML_PATH.read_text()
    m = re.search(r"var THEMES\s*=\s*\{(.*?)\};", html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find THEMES definition in research-graph.html")
    # 'algorithms' is too generic to be a useful semantic axis — exclude it
    return [t for t in re.findall(r"(\w+)\s*:\s*\{", m.group(1)) if t != "algorithms"]


def parse_node_themes():
    """Parse theme lists for each node from research-graph.html."""
    html_text = (SCRIPT_DIR / "research-graph.html").read_text()
    node_themes = []
    for m in re.finditer(r"themes:\[([^\]]*)\]", html_text):
        themes = [t.strip().strip("'\"") for t in m.group(1).split(",")]
        node_themes.append(themes)
    n = len(ITEMS)
    assert len(node_themes) >= n, f"Expected ≥{n} theme lists, got {len(node_themes)}"
    return node_themes[:n]


def compute_theme_projections(raw_embeddings):
    """Compute theme concept projections from raw embeddings.

    Returns (theme_names, projections) where projections is (79, k) array.
    Style direction is computed from raw embeddings; theme directions from debiased.
    """
    # Style direction from raw embeddings
    paper_mask = np.array([it["kind"] == "paper" for it in ITEMS])
    mean_paper = raw_embeddings[paper_mask].mean(axis=0)
    mean_blog = raw_embeddings[~paper_mask].mean(axis=0)
    style_dir = mean_paper - mean_blog
    style_dir = style_dir / np.linalg.norm(style_dir)

    # Debias for theme directions
    proj_onto_style = raw_embeddings @ style_dir
    debiased = raw_embeddings - np.outer(proj_onto_style, style_dir)

    # Theme directions from debiased embeddings
    global_mean = debiased.mean(axis=0)
    node_themes = parse_node_themes()

    theme_names = []
    theme_dirs = []
    for theme in get_theme_order():
        mask = np.array([theme in nt for nt in node_themes])
        if mask.sum() < 2:
            continue
        centroid = debiased[mask].mean(axis=0)
        direction = centroid - global_mean
        norm = np.linalg.norm(direction)
        if norm < 1e-8:
            continue
        theme_names.append(theme)
        theme_dirs.append(direction / norm)

    # Style from raw
    theme_names.append("style")
    theme_dirs.append(style_dir)

    theme_dirs_mat = np.array(theme_dirs)
    # Theme projections from debiased, style from raw
    theme_proj = debiased @ theme_dirs_mat[:-1].T
    style_proj = raw_embeddings @ style_dir
    all_proj = np.column_stack([theme_proj, style_proj.reshape(-1, 1)])

    # Residual PCA: project out all theme+style directions, then PCA on the residual
    # These capture semantic structure not aligned with any named theme
    n_residual = 10
    all_dirs = theme_dirs_mat  # (k, D)
    # Orthogonalize theme directions via QR for clean projection
    Q, _ = np.linalg.qr(all_dirs.T)  # (D, k) orthonormal basis of theme subspace
    # Project out the theme subspace from debiased embeddings
    residual = debiased - debiased @ Q @ Q.T
    # PCA on the residual
    U, S, Vt = np.linalg.svd(residual - residual.mean(axis=0), full_matrices=False)
    # Take top n_residual components
    n_residual = min(n_residual, len(S))
    residual_proj = U[:, :n_residual] * S[:n_residual]  # (79, n_residual)

    for i in range(n_residual):
        theme_names.append(f"dim{i+1}")
    all_proj = np.column_stack([all_proj, residual_proj])

    return theme_names, all_proj


# ---------------------------------------------------------------------------
# HTML injection
# ---------------------------------------------------------------------------
def inject_model_data(model_results):
    """Replace the MODEL_DATA block in research-graph.html with new data."""
    html = HTML_PATH.read_text()

    # Find the MODEL_DATA block: from "var MODEL_DATA = {" to the closing "};"
    start = re.search(r"var MODEL_DATA\s*=\s*\{", html)
    # Find the matching close: "};" on its own line after MODEL_DATA
    # We need to find the end of the object — scan for "};" after balanced braces
    if not start:
        raise RuntimeError("Could not find 'var MODEL_DATA = {' in HTML")

    depth = 0
    end_pos = None
    for i in range(start.start(), len(html)):
        if html[i] == '{':
            depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                # Expect ";" after
                end_pos = i + 1
                if end_pos < len(html) and html[end_pos] == ';':
                    end_pos += 1
                break
    if end_pos is None:
        raise RuntimeError("Could not find end of MODEL_DATA block")

    # Build new MODEL_DATA block
    lines = ["var MODEL_DATA = {"]
    for mk, data in model_results.items():
        lines.append(f"  '{mk}': {{")
        lines.append(f"    THEME_PROJ_NAMES: {json.dumps(data['THEME_PROJ_NAMES'])},")
        lines.append(f"    THEME_PROJECTIONS: {json.dumps(data['THEME_PROJECTIONS'])}")
        lines.append("  },")
    lines.append("};")

    html = html[:start.start()] + "\n".join(lines) + html[end_pos:]
    HTML_PATH.write_text(html)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global ITEMS
    ITEMS = load_items()
    print(f"Loaded {len(ITEMS)} items ({sum(1 for i in ITEMS if i['kind']=='paper')} papers, "
          f"{sum(1 for i in ITEMS if i['kind']=='blog')} blogs)")

    parser = argparse.ArgumentParser(description="Compute embeddings for research graph")
    parser.add_argument("--model", choices=list(MODELS.keys()), default=None,
                        help="Model to use (default: all models)")
    args = parser.parse_args()

    model_keys = [args.model] if args.model else list(MODELS.keys())

    # Extract content (shared across models)
    # Check if any model needs encoding
    item_keys = [it.get("yaml_id", it["title"]) for it in ITEMS]
    need_content = False
    for mk in model_keys:
        cache_file = CACHE_DIR / f"embeddings_{mk}.npz"
        if cache_file.exists():
            data = np.load(cache_file)
            cached_keys = set(data.files)
            if all(k in cached_keys for k in item_keys):
                continue
        need_content = True
        break

    texts = extract_all_content() if need_content else [it["title"] for it in ITEMS]

    model_results = {}
    for mk in model_keys:
        embeddings = get_embeddings(mk, texts)

        # Theme projections (includes debiasing internally)
        theme_names, theme_proj = compute_theme_projections(embeddings)
        theme_proj_list = [[round(float(v), 4) for v in row] for row in theme_proj]

        model_results[mk] = {
            "THEME_PROJ_NAMES": theme_names,
            "THEME_PROJECTIONS": theme_proj_list,
        }
        print(f"[{mk}] Done ({len(theme_names)} theme axes)")

    # Inject into HTML
    inject_model_data(model_results)
    print(f"Updated {HTML_PATH}")


if __name__ == "__main__":
    main()
