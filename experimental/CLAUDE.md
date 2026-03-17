# Research Graph — Semantic Embeddings

## Goal
Compute sentence-transformer embeddings for paper/blog content, project onto theme concept axes, and inject into `research-graph.html`. Items are loaded dynamically from `papers.yaml` and `blog_posts.yaml`.

## Steps

1. Install dependencies:
   ```
   pip install sentence-transformers pymupdf requests einops
   ```

2. Run `precompute_embeddings.py` — it automatically injects MODEL_DATA (theme projections) into `research-graph.html` for all 3 embedding models.

## Validation
Open `research-graph.html` in a browser. Click the "Semantic" button in the mode switcher. Nodes should animate to positions where semantically similar titles cluster together.
