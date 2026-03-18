---
name: Run builds after papers.yaml edits
description: Always run build.py and build_graph_data.py after editing papers.yaml — don't just tell the user to do it
type: feedback
---

After editing `papers.yaml`, always run the build steps automatically rather than telling the user to do it.

**Why:** The research graph embeds generated data that must stay in sync with papers.yaml. Forgetting to regenerate breaks the graph.

**How to apply:** After any edit to `papers.yaml`, run `python build.py` and `cd experimental && python build_graph_data.py` immediately.
