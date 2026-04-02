# Site Redesign: From Blog to Notebook

## Vision

Move away from the chronological "write once, never update" blog model toward a **living notebook**—a curated collection of content that evolves over time, organized by kind rather than date.

## Content Types

The site hosts a spectrum of work that doesn't fit neatly into "blog posts":

- **Notes**—short, informal, frequently updated
- **Tutorials**—polished, instructional, may grow over time
- **Research**—close to actual papers, with citations and formal structure
- **Interactive projects**—standalone interactive visualizations (e.g., Wobbly Table Theorem)

## Architecture Goals

1. **Separate repos for separate projects**—each interactive project (like table-theorem) keeps its own GitHub repo, history, and Pages deployment
2. **Shared styling**—extract a centralized CSS file so all content looks like it belongs to one site (currently ~1,700 lines of CSS are duplicated in every blog post's inline `<style>` block)
3. **Hub, not feed**—the main site becomes a hub that organizes and links to content by type, not just reverse-chronological order
4. **Living documents**—support for "last updated" dates, revision history, content that improves over time

## Open Questions

- What's the taxonomy? Tags? Types? Both?
- How does the existing research graph relate to the new structure?
- Should the homepage, blog index, or a new page serve as the hub?
- What happens to the existing 55 blog posts—do they get reclassified?
- URL structure: `/notes/`, `/tutorials/`, `/projects/` vs. flat `/everything/`?

## Concrete Next Steps

1. **Extract shared CSS** from blog posts into `/css/blog.css`—this unblocks project styling immediately
2. **Add blog-style nav to table-theorem** so it visually belongs to the site
3. **Prototype a hub page** that organizes content by type
4. **Migrate one or two existing posts** to validate the new structure

## Related Work

- The **research graph** (`/experimental/research-graph.html`) already does some of this—semantic grouping of papers and blog posts by theme
- `blog_posts.yaml` and `papers.yaml` already have structured metadata that could power a hub
