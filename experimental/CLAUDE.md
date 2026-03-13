# Research Graph — Semantic Embeddings

## Goal
Compute real sentence-transformer embeddings for 79 paper/blog titles, run UMAP to get 2D coordinates, and inject them into `research-graph.html`.

## Steps

1. Install dependencies:
   ```
   pip install sentence-transformers umap-learn
   ```

2. Run `precompute_embeddings.py` — it outputs a line like:
   ```
   var SEMANTIC_COORDS = [[0.1234,0.5678], ...];
   ```

3. In `research-graph.html`, find the existing line starting with `var SEMANTIC_COORDS =` and replace it with the output from step 2.

4. Verify the replacement: the SEMANTIC_COORDS array must have exactly 79 entries (40 papers + 39 blog posts), matching the order of nodes in the HTML.

## Validation
Open `research-graph.html` in a browser. Click the "Semantic" button in the mode switcher. Nodes should animate to positions where semantically similar titles cluster together.
