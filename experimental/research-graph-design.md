# Research Graph — Design Document

This document describes the visual encoding and layout algorithms used in
`research-graph.html`.

---

## Data

Every item is either a **paper** or a **blog post**, loaded from `papers.yaml`
and `blog_posts.yaml` via `build_graph_data.py`. Each item carries:

| Field     | Description                                    |
|-----------|------------------------------------------------|
| `id`      | Unique string identifier                       |
| `title`   | Full title                                     |
| `kind`    | `"paper"` or `"blog"`                          |
| `year`    | Publication year (integer)                      |
| `themes`  | List of theme keys (e.g. `["parsing", "dp"]`)  |
| `award`   | Optional award string (e.g. `"Best paper"`)    |
| `authors` | Author list (papers only)                      |
| `venue`   | Conference/journal name (papers only)          |
| `url`     | Primary URL                                    |
| `links`   | Map of supplementary links (arXiv, code, etc.) |

### Themes

Each theme has a human-readable label and a fixed color:

| Key            | Label                   | Color     |
|----------------|-------------------------|-----------|
| `parsing`      | Structured Prediction   | <span style="background-color:#3a5a8c;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#3a5a8c</span> |
| `tokenization` | Tokenization            | <span style="background-color:#6a8a52;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#6a8a52</span> |
| `generation`   | Controlled Generation   | <span style="background-color:#8c4a3a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#8c4a3a</span> |
| `beam`         | Beam Search             | <span style="background-color:#3a7a7a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#3a7a7a</span> |
| `gumbel`       | Gumbel Trick            | <span style="background-color:#2a8a6a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#2a8a6a</span> |
| `automata`     | Formal Language Theory  | <span style="background-color:#7a5a8a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#7a5a8a</span> |
| `dp`           | Dynamic Programming     | <span style="background-color:#5a6a7a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#5a6a7a</span> |
| `alignment`    | Alignment               | <span style="background-color:#8a5a6a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#8a5a6a</span> |
| `semantics`    | Language Understanding  | <span style="background-color:#6a6a4a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#6a6a4a</span> |
| `sampling`     | Sampling                | <span style="background-color:#b06030;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#b06030</span> |
| `swor`         | Sampling w/o Replacement| <span style="background-color:#c07848;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#c07848</span> |
| `optimization` | Optimization            | <span style="background-color:#8a7a30;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#8a7a30</span> |
| `autodiff`     | Gradients               | <span style="background-color:#6a4a3a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#6a4a3a</span> |
| `numerical`    | Numerical Methods       | <span style="background-color:#5a7a8a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#5a7a8a</span> |
| `ml`           | Machine Learning        | <span style="background-color:#5a8a6a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#5a8a6a</span> |
| `logic-programming` | Logic Programming | <span style="background-color:#4a7a9a;color:#fff;padding:2px 6px;border-radius:3px;font-family:monospace">#4a7a9a</span> |

---

## Nodes

### Shape, color, and size

All nodes have a uniform radius of **9 px**. The fill color is the node's
**primary theme** (first entry in `themes`). Papers use `fill-opacity: 0.75`,
blogs `0.65`. Award winners get a dashed gold ring (`#9a7b3c`) around the node.

**Labels:** Year label (Source Code Pro, white, centered) + title label below
(Crimson Pro, 8 px papers / 7.5 px italic blogs, theme color at 55% opacity).

---

## Edges

An edge connects two nodes that **share at least one theme**. Edge attributes
are computed as follows.

### Strength

```
kind_factor = 1.0  if same kind (both papers or both blogs)
              0.7  if cross-type (paper ↔ blog)

strength = |shared_themes| × kind_factor
```

An edge is only created if `strength` meets a threshold:

- Same-kind edges: `strength ≥ 0.4`
- Cross-type edges: `strength ≥ 0.55`

Any two nodes sharing at least one theme will be connected (1 × 1.0 = 1.0 ≥ 0.4
for same-kind; 1 × 0.7 = 0.7 ≥ 0.55 for cross-type).

### Visual attributes

<svg width="480" height="90" xmlns="http://www.w3.org/2000/svg" style="background:#faf9f7;border-radius:6px">
  <!-- Same-kind edges -->
  <text x="120" y="16" font-family="sans-serif" font-size="11" fill="#555" text-anchor="middle">Same-kind (solid)</text>
  <line x1="20" y1="35" x2="220" y2="35" stroke="#3a5a8c" stroke-opacity="0.1" stroke-width="0.65"/>
  <text x="235" y="38" font-family="sans-serif" font-size="9" fill="#888">weak</text>
  <line x1="20" y1="55" x2="220" y2="55" stroke="#3a5a8c" stroke-opacity="0.15" stroke-width="1.25"/>
  <text x="235" y="58" font-family="sans-serif" font-size="9" fill="#888">medium</text>
  <line x1="20" y1="75" x2="220" y2="75" stroke="#3a5a8c" stroke-opacity="0.2" stroke-width="2.15"/>
  <text x="235" y="78" font-family="sans-serif" font-size="9" fill="#888">strong</text>
  <!-- Cross-type edges -->
  <text x="390" y="16" font-family="sans-serif" font-size="11" fill="#555" text-anchor="middle">Cross-type (dashed)</text>
  <line x1="300" y1="35" x2="480" y2="35" stroke="#8c4a3a" stroke-opacity="0.1" stroke-width="0.75" stroke-dasharray="3,3"/>
  <line x1="300" y1="55" x2="480" y2="55" stroke="#8c4a3a" stroke-opacity="0.13" stroke-width="1.25" stroke-dasharray="3,3"/>
  <line x1="300" y1="75" x2="480" y2="75" stroke="#8c4a3a" stroke-opacity="0.16" stroke-width="2.0" stroke-dasharray="3,3"/>
</svg>

| Property         | Same-kind edge                       | Cross-type edge                       |
|------------------|--------------------------------------|---------------------------------------|
| Stroke color     | Color of first shared theme          | Color of first shared theme           |
| Stroke opacity   | `0.05 + strength × 0.025`           | `0.07 + strength × 0.015`            |
| Stroke width     | `0.35 + strength × 0.3`             | `0.5 + strength × 0.25`              |
| Dash pattern     | Solid                                | Dashed (`3,3`)                        |

Cross-type edges are dashed to visually distinguish paper–blog connections
from same-kind connections.

---

## Layout Modes

The visualization offers five layout modes. All graph modes use a D3 force
simulation (`d3.forceSimulation`) with `velocityDecay = 0.55` and
`alphaDecay = 0.015`.

### 1. Force-directed (default)

A standard force-directed layout with edges active:

| Force       | Configuration                                                      |
|-------------|--------------------------------------------------------------------|
| Link        | `distance = (crossType ? 120 : 65) / √strength`; `strength = min(0.4, s × (crossType ? 0.025 : 0.05))` |
| Charge      | Many-body, strength −110                                           |
| Center      | Center of canvas, strength 0.01                                    |
| Collision   | Radius `r + 5`                                                     |
| X-position  | Papers pulled to left (`W × 0.275`), blogs to right (`W × 0.725`), strength 0.055 |
| Y-position  | All pulled to vertical center, strength 0.025                      |

A vertical dashed barrier line separates the paper and blog zones. Zone labels
("PUBLICATIONS" / "BLOG POSTS") are shown at reduced opacity.

### 2. Timeline

Nodes are positioned by year along the x-axis. No link forces.

| Force       | Configuration                                                 |
|-------------|---------------------------------------------------------------|
| X-position  | `x = linearScale(year, [2009, 2025] → [100, W−100])`; strength 0.9 |
| Y-position  | Papers at `H × 0.38`, blogs at `H × 0.62`, with a small jitter `(index % 7 − 3) × 15`; strength 0.25 |
| Charge      | −50                                                           |
| Collision   | Radius `r + 4`                                                |

Year labels and dashed vertical gridlines are drawn for odd years 2009–2025.

### 3. Theme clusters

Nodes cluster around their primary theme's grid position. No link forces.

Active themes are arranged in a 4-column grid. Each theme center is at:

```
col = index mod 4,  row = ⌊index / 4⌋
x = W / (cols + 1) × (col + 1)
y = H / (rows + 1) × (row + 1) + 20
```

| Force       | Configuration                                   |
|-------------|--------------------------------------------------|
| X-position  | Theme center x; strength 0.7                     |
| Y-position  | Theme center y; strength 0.7                     |
| Charge      | −40                                              |
| Collision   | Radius `r + 4`                                   |

Theme names are displayed as labels above each cluster center.

### 4. Semantic (MDS + sliders)

The most complex mode. Items are positioned via **classical multidimensional
scaling (MDS)** on a weighted feature space derived from sentence-transformer
embeddings. See the dedicated section below.

### 5. Cards

A non-graph view. Nodes are rendered as a filterable card grid (CSS grid,
`minmax(280px, 1fr)`). Filterable by kind (paper/blog) and theme. The force
simulation is stopped in this mode.

---

## Semantic Mode: MDS with Interactive Sliders

### Overview

The semantic layout maps high-dimensional embeddings down to 2D positions using
classical MDS. Users control the relative importance of each semantic axis via
sliders, causing the layout to smoothly reconfigure.

### Embedding models

Three pre-computed sentence-transformer models are available (selectable in the
Advanced panel):

| Key       | Model                  | Max tokens |
|-----------|------------------------|------------|
| `nomic`   | nomic-embed-text-v1.5  | 8192       |
| `bge`     | bge-small-en-v1.5      | 512        |
| `minilm`  | all-MiniLM-L6-v2       | 256        |

For each model, the build step (`precompute_embeddings.py`) projects every
item's embedding onto a set of **theme concept axes** plus **PCA residual
dimensions**, producing a matrix `THEME_PROJECTIONS[i][j]` — the projection of
item `i` onto axis `j`.

### Feature construction

For each item $i$ and axis $j$, two features are constructed:

1. **Content projection** (continuous): the item's embedding projected onto the
   theme's concept direction, z-scored to unit variance:

$$\text{content}_{ij} = w_j \cdot \frac{p_{ij} - \bar{p}_j}{\sigma_j}$$

2. **Theme membership** (categorical): a centered binary indicator — +1 if item
   $i$ belongs to theme $j$, −1 otherwise:

$$\text{membership}_{ij} = w_j \cdot m_{ij}, \quad m_{ij} \in \{-1, +1\}$$

Here $w_j$ is the slider weight for axis $j$ (default 1.0, range [0, 5]).

The full feature vector for item $i$ is the concatenation of all content and
membership pairs:

$$\mathbf{f}_i = [\ w_1 \tilde{p}_{i1},\ w_1 m_{i1},\ w_2 \tilde{p}_{i2},\ w_2 m_{i2},\ \ldots\ ]$$

where $\tilde{p}_{ij}$ denotes the z-scored content projection.

### Slider effect

Each slider controls the weight $w_j$ for one semantic axis. The weight
multiplies both the content projection and membership indicator for that axis:

- **$w_j = 0$**: axis $j$ is collapsed — items that differ only on this axis
  will overlap.
- **$w_j = 1$** (default): axis $j$ contributes at its natural scale.
- **$w_j > 1$**: axis $j$ is amplified — items are spread further apart along
  this distinction.

For example, setting the "Paper vs Blog" slider to 0 causes publications and
blog posts to intermix; cranking "Structured Prediction" to 2 fans out parsing
papers.

### Classical MDS

Given the weighted feature matrix $\mathbf{F} \in \mathbb{R}^{n \times 2k}$,
classical MDS proceeds as follows:

1. **Pairwise Euclidean distances**:

$$D_{ij} = \|\mathbf{f}_i - \mathbf{f}_j\|_2$$

2. **Double centering** to form the Gram-like matrix $\mathbf{B}$:

$$B_{ij} = -\tfrac{1}{2}\left(D_{ij}^2 - \bar{D}_{i\cdot}^2 - \bar{D}_{\cdot j}^2 + \bar{D}_{\cdot\cdot}^2\right)$$

   where $\bar{D}_{i\cdot}^2$ is the mean of squared distances in row $i$,
   $\bar{D}_{\cdot j}^2$ is the column mean, and $\bar{D}_{\cdot\cdot}^2$ is
   the grand mean.

3. **Top-2 eigenvectors** of $\mathbf{B}$ via power iteration (200 iterations,
   with matrix deflation for the second eigenvector):

$$\mathbf{B} \approx \lambda_1 \mathbf{v}_1 \mathbf{v}_1^\top + \lambda_2 \mathbf{v}_2 \mathbf{v}_2^\top$$

4. **2D coordinates**:

$$x_i = v_{1,i} \sqrt{\lambda_1}, \qquad y_i = v_{2,i} \sqrt{\lambda_2}$$

5. **Normalization**: coordinates are linearly scaled to fill the canvas with
   80 px padding.

### Procrustes alignment

When sliders change, MDS is recomputed. Since eigenvectors are only defined up
to sign and rotation, the new coordinates are aligned to the previous frame
using a two-step Procrustes procedure:

1. **Sign correction**: flip each axis if its correlation with the previous
   frame is negative.
2. **Optimal rotation**: find the angle $\theta$ that minimizes the sum of
   squared differences between the aligned and target coordinates, via:

$$\theta = \arctan2\!\left(\sum_i (t_{i,y} s_{i,x} - t_{i,x} s_{i,y}),\; \sum_i (t_{i,x} s_{i,x} + t_{i,y} s_{i,y})\right)$$

   Then apply the rotation:

$$\begin{bmatrix} x_i' \\ y_i' \end{bmatrix} = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix} \begin{bmatrix} x_i \\ y_i \end{bmatrix}$$

This prevents the layout from flipping or jumping when a slider is nudged.

### Force simulation in semantic mode

The MDS coordinates are used as target positions, not direct placements. A D3
force simulation guides nodes to their targets:

| Force       | Configuration                        |
|-------------|--------------------------------------|
| X-position  | MDS x-coordinate; strength 0.85      |
| Y-position  | MDS y-coordinate; strength 0.85      |
| Charge      | −30                                  |
| Collision   | Radius `r + 4`                       |
| Links       | Disabled                             |

The high strength (0.85) ensures nodes closely track their MDS targets while
the collision force prevents overlap.

---

## Interaction

| Action                  | Effect                                                |
|-------------------------|-------------------------------------------------------|
| Hover node              | Tooltip with title, authors, venue, themes            |
| Click node              | Pin: detail panel slides in from right (or bottom on mobile) |
| Click pinned node       | Unpin                                                 |
| Escape / click empty    | Unpin                                                 |
| Click legend theme      | Filter: dim all nodes not in that theme               |
| Click legend again      | Clear filter                                          |
| Drag node               | Temporarily fix position (`fx`, `fy`)                 |
| Scroll / pinch          | Zoom (d3.zoom, extent [0.3, 5])                       |
| Drag canvas             | Pan                                                   |
| Slider panel drag-bar   | Desktop: reposition panel. Mobile: swipe drawer open/close |
