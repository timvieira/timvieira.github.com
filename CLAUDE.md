# Project: timvieira.github.com

## After editing `papers.yaml` or `blog_posts.yaml`

The **Build site** workflow (`.github/workflows/build-site.yml`) regenerates all
dependent files, including the semantic embeddings, on every push to `master`
that touches these files, and commits the results back to `master`. Pull before
editing locally.

To regenerate by hand instead:

```
python build.py                                  # -> cv/cv.bib, generated_index.html
cp generated_index.html index.html               # promote regenerated publications list
cd experimental && python build_graph_data.py    # -> experimental/research-graph.html
BLOG_CONTENT=<blog repo>/content python precompute_embeddings.py   # -> semantic embeddings
```

The embeddings are matched to graph nodes by position, so after adding or
removing a paper or blog post, `research-graph.html` is wrong in semantic mode
until `precompute_embeddings.py` has run.

## New blog posts

Each published post in the blog repo (`timvieira/blog`) needs an entry in
`blog_posts.yaml`, with themes, to appear in the research graph.
`python experimental/check_blog_posts.py <blog repo>/content` lists any that
are missing; the workflow runs it on every build and every Monday, and fails
if posts are missing.

## After changing `experimental/research-graph.html`

Keep `experimental/research-graph-design.md` in sync with any changes to the
visualization's data model, visual encoding, layout algorithms, interaction
behavior, or semantic mode.
