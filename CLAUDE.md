# Project: timvieira.github.com

## After editing `papers.yaml`

Regenerate all dependent files:

```
python build.py                              # -> cv/cv.bib, generated_index.html
cd experimental && python build_graph_data.py # -> experimental/research-graph.html
```

## After changing `experimental/research-graph.html`

Keep `experimental/research-graph-design.md` in sync with any changes to the
visualization's data model, visual encoding, layout algorithms, interaction
behavior, or semantic mode.
