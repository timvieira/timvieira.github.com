# Research Graph — Semantic Embeddings

## Goal
Compute sentence-transformer embeddings for paper/blog content, project onto theme concept axes, and inject into `research-graph.html`. Items are loaded dynamically from `papers.yaml` and `blog_posts.yaml`.

## Steps

These steps run automatically in the **Build site** GitHub Actions workflow
(`.github/workflows/build-site.yml`). To run them by hand:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run `BLOG_CONTENT=<blog repo>/content python precompute_embeddings.py` — it automatically injects MODEL_DATA (theme projections) into `research-graph.html` for each embedding model in `MODELS` (currently Qwen3-Embedding-0.6B at 2048 and 512 tokens).

Text sources: paper PDFs (local `doc/`, arXiv, or ACL Anthology), blog post
Markdown/notebooks from `$BLOG_CONTENT`, and the linked page for posts with an
`external_url`. Downloads are cached in `.content_cache/`. Embeddings are cached
per item and text hash, so only items whose text changed are re-encoded; an
item whose download failed falls back to its title and is retried next run.

## Validation
Open `research-graph.html` in a browser. Click the "Semantic" button in the mode switcher. Nodes should animate to positions where semantically similar titles cluster together.
