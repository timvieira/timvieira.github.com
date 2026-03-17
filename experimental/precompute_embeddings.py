#!/usr/bin/env python3
"""
Compute semantic embeddings from full document content (paper PDFs + blog text),
then project to 2D with UMAP for the research-graph visualization.

    pip install sentence-transformers umap-learn pymupdf requests einops
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
# Item list — same 79 entries, same order as research-graph.html
# ---------------------------------------------------------------------------
# fmt: off
ITEMS = [
    # ---- Papers (40) ----
    {"kind": "paper", "yaml_id": "lipkin-etal-2025-controlled-gen",     "title": "Fast Controlled Generation from Language Models with Adaptive Weighted Rejection Sampling"},
    {"kind": "paper", "yaml_id": "amini-etal-2025-kl-divergence",      "title": "Better Estimation of the KL Divergence Between Language Models"},
    {"kind": "paper", "yaml_id": "xefteri-etal-2025-syntactic-posterior","title": "Syntactic Control of Language Models by Posterior Inference"},
    {"kind": "paper", "yaml_id": "loula-etal-2025-smc-control",        "title": "Syntactic and Semantic Control of LLMs via Sequential Monte Carlo"},
    {"kind": "paper", "yaml_id": "gastaldi-etal-2025-foundations-tokenization", "title": "The Foundations of Tokenization: Statistical and Computational Concerns"},
    {"kind": "paper", "yaml_id": "amini-etal-2025-vbon",               "title": "Variational Best-of-N Alignment"},
    {"kind": "paper", "yaml_id": "vieira-etal-2025-canonical-bpe",     "title": "Language Models over Canonical Byte-Pair Encodings"},
    {"kind": "paper", "yaml_id": "vieira-etal-2025-tokens-chars",      "title": "From Language Models over Tokens to Language Models over Characters"},
    {"kind": "paper", "yaml_id": "giulianelli-etal-2024-psycho-tokenization", "title": "On the Proper Treatment of Tokenization in Psycholinguistics"},
    {"kind": "paper", "yaml_id": "amini-etal-2024-odpo",               "title": "Direct Preference Optimization with an Offset"},
    {"kind": "paper", "yaml_id": "vieira-2023-dissertation",           "title": "Automating the Analysis and Improvement of Dynamic Programming Algorithms"},
    {"kind": "paper", "yaml_id": "opedal-etal-2023-left-corner",       "title": "An Exploration of Left-Corner Transformations"},
    {"kind": "paper", "yaml_id": "butoi-etal-2023-tag",                "title": "Efficient Algorithms for Recognizing Weighted Tree-Adjoining Languages"},
    {"kind": "paper", "yaml_id": "opedal-etal-2023-earley",            "title": "Efficient Semiring-Weighted Earley Parsing"},
    {"kind": "paper", "yaml_id": "zouhar-etal-2023-formal-bpe",        "title": "A Formal Perspective on Byte-Pair Encoding"},
    {"kind": "paper", "yaml_id": "pasti-etal-2023-bar-hillel",         "title": "On the Intersection of Context-Free and Regular Languages"},
    {"kind": "paper", "yaml_id": "butoi-etal-2022-wpda",               "title": "Algorithms for Weighted Pushdown Automata"},
    {"kind": "paper", "yaml_id": "svete-etal-2022-failure-arcs",       "title": "Algorithms for Weighted Finite-State Automata with Failure Arcs"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2022-exact",            "title": "Exact Paired-Permutation Testing for Structured Test Statistics"},
    {"kind": "paper", "yaml_id": "vieira-etal-2021-automate-dp",       "title": "Automating the Analysis of Parsing Algorithms"},
    {"kind": "paper", "yaml_id": "vieira-etal-2021-searching",         "title": "Searching for More Efficient Dynamic Programs"},
    {"kind": "paper", "yaml_id": "meister-etal-2021-conditional",      "title": "Conditional Poisson Stochastic Beam Search"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2021-sampling",         "title": "Efficient Sampling of Dependency Structures"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2021-efficient",        "title": "Efficient Computation of Expectations under Spanning Tree Distributions"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2021-finding",          "title": "On Finding the K-best Non-projective Dependency Trees"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2021-higher",           "title": "Higher-order Derivatives of Weighted Finite-state Machines"},
    {"kind": "paper", "yaml_id": "meister-etal-2020-beam-answer",      "title": "If Beam Search is the Answer, What was the Question?"},
    {"kind": "paper", "yaml_id": "zmigrod-etal-2020-please",           "title": "Please Mind the Root: Decoding Arborescences for Dependency Parsing"},
    {"kind": "paper", "yaml_id": "meister-etal-2020-best-first",       "title": "Best-First Beam Search"},
    {"kind": "paper", "yaml_id": "francislandau-etal-2020-wrla",       "title": "Evaluation of Logic Programs with Built-Ins and Aggregation"},
    {"kind": "paper", "yaml_id": "white-etal-2020-universal",          "title": "The Universal Decompositional Semantics Dataset and Decomp Toolkit"},
    {"kind": "paper", "yaml_id": "vieira-etal-2018-failure",           "title": "Forward-Backward with Failure Arcs for Variable-Order CRFs"},
    {"kind": "paper", "yaml_id": "vieira-etal-2017-dyna",              "title": "Dyna: Toward a Self-Optimizing Declarative Language for ML"},
    {"kind": "paper", "yaml_id": "vieira-etal-2017-learning-to-prune", "title": "Learning to Prune: Exploring the Frontier of Fast and Accurate Parsing"},
    {"kind": "paper", "yaml_id": "vieira-etal-2016-speed",             "title": "Speed-Accuracy Tradeoffs in Tagging with Variable-Order CRFs"},
    {"kind": "paper", "yaml_id": "white-etal-2016-universal",          "title": "Universal Decompositional Semantics on Universal Dependencies"},
    {"kind": "paper", "yaml_id": "cotterell-etal-2016-joint",          "title": "A Joint Model of Orthography and Morphological Segmentation"},
    {"kind": "paper", "yaml_id": "roy-etal-2015-reasoning",            "title": "Reasoning about Quantities in Natural Language"},
    {"kind": "paper", "yaml_id": "naradowsky-etal-2012-grammarless",   "title": "Grammarless Parsing for Joint Inference"},
    {"kind": "paper", "yaml_id": "sammons-etal-2009-relational",       "title": "Relation Alignment for Textual Entailment Recognition"},
    # ---- Blog posts (39) ----
    {"kind": "blog", "title": "Fast rank-one updates to matrix inverse?"},
    {"kind": "blog", "title": "On the Distribution of the Smallest Indices"},
    {"kind": "blog", "title": "On the Distribution Functions of Order Statistics"},
    {"kind": "blog", "title": "Animation of the inverse transform method"},
    {"kind": "blog", "title": "Generating truncated random variates"},
    {"kind": "blog", "title": "Algorithms for sampling without replacement"},
    {"kind": "blog", "title": "The restart acceleration trick"},
    {"kind": "blog", "title": "Faster reservoir sampling by waiting"},
    {"kind": "blog", "title": "The likelihood-ratio gradient"},
    {"kind": "blog", "title": "Steepest ascent"},
    {"kind": "blog", "title": "Black-box optimization"},
    {"kind": "blog", "title": "Backprop is not just the chain rule"},
    {"kind": "blog", "title": "Estimating means in a finite universe"},
    {"kind": "blog", "title": "How to test gradient implementations"},
    {"kind": "blog", "title": "Counterfactual reasoning and learning from logged data"},
    {"kind": "blog", "title": "Heaps for incremental computation"},
    {"kind": "blog", "title": "Reversing a sequence with sublinear space"},
    {"kind": "blog", "title": "Evaluating nabla f(x) is as fast as f(x)"},
    {"kind": "blog", "title": "Fast sigmoid sampling"},
    {"kind": "blog", "title": "Sqrt-biased sampling"},
    {"kind": "blog", "title": "The optimal proposal distribution is not p"},
    {"kind": "blog", "title": "Dimensional analysis of gradient ascent"},
    {"kind": "blog", "title": "Gradient-based hyperparameter optimization"},
    {"kind": "blog", "title": "Multidimensional array index"},
    {"kind": "blog", "title": "Gradient of a product"},
    {"kind": "blog", "title": "Multiclass logistic regression and CRFs are the same thing"},
    {"kind": "blog", "title": "Conditional random fields as deep learning models?"},
    {"kind": "blog", "title": "Log-Real number class"},
    {"kind": "blog", "title": "Importance sampling"},
    {"kind": "blog", "title": "Numerically stable p-norms"},
    {"kind": "blog", "title": "KL-divergence as an objective function"},
    {"kind": "blog", "title": "Complex-step derivative"},
    {"kind": "blog", "title": "Gumbel-max trick and weighted reservoir sampling"},
    {"kind": "blog", "title": "Gumbel-max trick"},
    {"kind": "blog", "title": "Rant against grid search"},
    {"kind": "blog", "title": "Expected value of a quadratic and the Delta method"},
    {"kind": "blog", "title": "Visualizing high-dimensional functions with cross-sections"},
    {"kind": "blog", "title": "Exp-normalize trick"},
    {"kind": "blog", "title": "Gradient-vector product"},
]
# fmt: on

assert len(ITEMS) == 79, f"Expected 79, got {len(ITEMS)}"


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
    """Extract text content for all 79 items. Returns list of strings."""
    print("Loading papers.yaml...")
    papers_by_id = load_papers_yaml()
    print("Building blog title map...")
    title_map = build_blog_title_map()

    texts = []
    fallback_count = 0
    for i, item in enumerate(ITEMS):
        label = f"[{i+1:2d}/79]"
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
THEME_ORDER = [
    "parsing", "tokenization", "generation", "trees", "beam",
    "automata", "dp", "alignment", "semantics", "sampling",
    "optimization", "autodiff", "numerical", "ml",
]


def parse_node_themes():
    """Parse theme lists for each node from research-graph.html."""
    html_text = (SCRIPT_DIR / "research-graph.html").read_text()
    node_themes = []
    for m in re.finditer(r"themes:\[([^\]]*)\]", html_text):
        themes = [t.strip().strip("'\"") for t in m.group(1).split(",")]
        node_themes.append(themes)
    assert len(node_themes) >= 79, f"Expected ≥79 theme lists, got {len(node_themes)}"
    return node_themes[:79]


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
    for theme in THEME_ORDER:
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
# Main
# ---------------------------------------------------------------------------
def main():
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

    for mk in model_keys:
        embeddings = get_embeddings(mk, texts)

        # Debias
        paper_mask = np.array([it["kind"] == "paper" for it in ITEMS])
        mean_paper = embeddings[paper_mask].mean(axis=0)
        mean_blog = embeddings[~paper_mask].mean(axis=0)
        style_dir = mean_paper - mean_blog
        style_dir = style_dir / np.linalg.norm(style_dir)
        proj = embeddings @ style_dir
        debiased = embeddings - np.outer(proj, style_dir)

        # UMAP
        print(f"\n[{mk}] Running UMAP...")
        from umap import UMAP
        reducer = UMAP(n_components=2, n_neighbors=12, min_dist=0.15, metric="cosine", random_state=42)
        coords = reducer.fit_transform(debiased)

        for d in range(2):
            mn, mx = coords[:, d].min(), coords[:, d].max()
            coords[:, d] = (coords[:, d] - mn) / (mx - mn)

        result = [[round(float(x), 4), round(float(y), 4)] for x, y in coords]

        print(f"\n// [{mk}] Paste into research-graph.html:")
        print(f"var SEMANTIC_COORDS = {json.dumps(result)};")

        # Theme projections
        theme_names, theme_proj = compute_theme_projections(embeddings)
        theme_proj_list = [[round(float(v), 4) for v in row] for row in theme_proj]

        print(f"\n// [{mk}] Theme projection data ({len(theme_names)} concept axes):")
        print(f"var THEME_PROJ_NAMES = {json.dumps(theme_names)};")
        print(f"var THEME_PROJECTIONS = {json.dumps(theme_proj_list)};")

    if len(model_keys) > 1:
        print("\n// Summary: embeddings cached for", ", ".join(model_keys))
        print("// Re-run with --model KEY to output just one model's data")


if __name__ == "__main__":
    main()
