import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import * as d3 from "d3";

// ── Real data from timvieira.github.io ─────────────────────────────────────
const ITEMS = [
  // ═══ BLOG POSTS ═══
  { id: 1, title: "Gumbel-Max Trick", date: "2014-07-31", tags: ["sampling", "gumbel"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2014/07/31/gumbel-max-trick/", desc: "Sampling from categorical distributions using Gumbel perturbations and argmax, avoiding explicit normalization." },
  { id: 2, title: "Gumbel-Max Trick & Weighted Reservoir Sampling", date: "2014-08-01", tags: ["sampling", "gumbel", "reservoir-sampling"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2014/08/01/gumbel-max-trick-and-weighted-reservoir-sampling/", desc: "Connecting weighted reservoir sampling with the Gumbel-max trick via randomized keys and argmax." },
  { id: 3, title: "Complex-Step Derivative", date: "2014-08-07", tags: ["calculus", "numerical"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2014/08/07/complex-step-derivative/", desc: "Using complex arithmetic to compute derivatives without subtraction cancellation issues." },
  { id: 4, title: "Exp-Normalize Trick", date: "2014-02-11", tags: ["numerical"], topic: "Numerical", type: "blog", url: "https://timvieira.github.io/blog/post/2014/02/11/exp-normalize-trick/", desc: "Numerically stable computation of softmax and related normalizations via shifting by the max." },
  { id: 5, title: "Gradient-Vector Product", date: "2014-02-10", tags: ["calculus"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2014/02/10/gradient-vector-product/", desc: "Efficiently computing Hessian-vector products without materializing the full Hessian matrix." },
  { id: 6, title: "Visualizing High-Dim Functions", date: "2014-02-12", tags: ["visualization"], topic: "Numerical", type: "blog", url: "https://timvieira.github.io/blog/post/2014/02/12/visualizing-high-dimensional-functions-with-cross-sections/", desc: "Techniques for understanding high-dimensional optimization landscapes via 1D and 2D slices." },
  { id: 7, title: "Expected Value of a Quadratic & Delta Method", date: "2014-07-21", tags: ["statistics"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2014/07/21/expected-value-of-a-quadratic-and-the-delta-method/", desc: "Computing expectations of quadratic forms and applying the Delta method for variance estimation." },
  { id: 8, title: "Rant Against Grid Search", date: "2014-07-22", tags: ["hyperparameter-optimization"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2014/07/22/rant-against-grid-search/", desc: "Why grid search is wasteful and random search is almost always better for hyperparameter tuning." },
  { id: 9, title: "KL-Divergence as an Objective Function", date: "2014-10-06", tags: ["statistics", "machine-learning"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2014/10/06/kl-divergence-as-an-objective-function/", desc: "Asymmetries in forward vs reverse KL and their implications for model fitting and variational inference." },
  { id: 10, title: "Numerically Stable p-Norms", date: "2014-11-10", tags: ["numerical"], topic: "Numerical", type: "blog", url: "https://timvieira.github.io/blog/post/2014/11/10/numerically-stable-p-norms/", desc: "Avoiding overflow and underflow when computing p-norms through careful rescaling." },
  { id: 11, title: "Importance Sampling", date: "2014-12-21", tags: ["statistics", "importance-sampling", "sampling"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2014/12/21/importance-sampling/", desc: "From basic importance weights to self-normalized estimators, effective sample size, and off-policy evaluation." },
  { id: 12, title: "Log-Real Number Class", date: "2015-02-01", tags: ["numerical", "datastructures"], topic: "Numerical", type: "blog", url: "https://timvieira.github.io/blog/post/2015/02/01/log-real-number-class/", desc: "A data structure for representing real numbers in log-space, supporting negative values and arithmetic." },
  { id: 13, title: "CRFs as Deep Learning Models?", date: "2015-02-05", tags: ["machine-learning", "deep-learning"], topic: "NLP", type: "blog", url: "https://timvieira.github.io/blog/post/2015/02/05/conditional-random-fields-as-deep-learning-models/", desc: "Viewing conditional random fields through the lens of deep learning architectures." },
  { id: 14, title: "Logistic Regression & CRFs Are the Same", date: "2015-04-29", tags: ["machine-learning", "crf"], topic: "NLP", type: "blog", url: "https://timvieira.github.io/blog/post/2015/04/29/multiclass-logistic-regression-and-conditional-random-fields-are-the-same-thing/", desc: "Showing the equivalence between multiclass logistic regression and CRFs on sequence labeling." },
  { id: 15, title: "Gradient of a Product", date: "2015-07-29", tags: ["calculus", "automatic-differentiation", "datastructures"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2015/07/29/gradient-of-a-product/", desc: "Computing gradients of products of functions efficiently using forward-backward and divide-and-conquer." },
  { id: 16, title: "Multidimensional Array Index", date: "2016-01-17", tags: ["datastructures"], topic: "Algorithms", type: "blog", url: "https://timvieira.github.io/blog/post/2016/01/17/multidimensional-array-index/", desc: "Bijective mapping between tuples and flat indices for multidimensional arrays via mixed-radix encoding." },
  { id: 17, title: "Gradient-Based Hyperparameter Optimization", date: "2016-03-05", tags: ["calculus", "hyperparameter-optimization"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2016/03/05/gradient-based-hyperparameter-optimization-and-the-implicit-function-theorem/", desc: "Using the implicit function theorem to differentiate through the solution of an optimization problem." },
  { id: 18, title: "Dimensional Analysis of Gradient Ascent", date: "2016-05-27", tags: ["optimization", "calculus"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2016/05/27/dimensional-analysis-of-gradient-ascent/", desc: "Why the step-size parameter in gradient descent has complicated units and is hard to set a priori." },
  { id: 19, title: "Optimal Proposal Distribution Is Not p", date: "2016-05-28", tags: ["statistics", "sampling", "importance-sampling"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2016/05/28/the-optimal-proposal-distribution-is-not-p/", desc: "The variance-minimizing proposal depends on the function being estimated, not just the target." },
  { id: 20, title: "Sqrt-Biased Sampling", date: "2016-06-28", tags: ["sampling", "decision-making"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2016/06/28/sqrt-biased-sampling/", desc: "Optimal exploration under limited samples by allocating proportional to the square root of variance." },
  { id: 21, title: "Fast Sigmoid Sampling", date: "2016-07-04", tags: ["sampling", "gumbel"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2016/07/04/fast-sigmoid-sampling/", desc: "Efficiently sampling Bernoulli random variables from sigmoid distributions via precomputed logit transforms." },
  { id: 22, title: "Evaluating ∇f(x) Is as Fast as f(x)", date: "2016-09-25", tags: ["calculus", "automatic-differentiation"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2016/09/25/evaluating-fx-is-as-fast-as-fx/", desc: "The fundamental theorem of AD: reverse-mode computes gradients at constant overhead." },
  { id: 23, title: "Reversing a Sequence with Sublinear Space", date: "2016-10-01", tags: ["algorithms", "automatic-differentiation"], topic: "Algorithms", type: "blog", url: "https://timvieira.github.io/blog/post/2016/10/01/reversing-a-sequence-with-sublinear-space/", desc: "Memory-efficient backpropagation through time using checkpointing and log-space sequence reversal." },
  { id: 24, title: "Heaps for Incremental Computation", date: "2016-11-21", tags: ["sampling", "datastructures"], topic: "Algorithms", type: "blog", url: "https://timvieira.github.io/blog/post/2016/11/21/heaps-for-incremental-computation/", desc: "Using heap data structures for efficient updates to aggregates like sums and products." },
  { id: 25, title: "Counterfactual Reasoning & Logged Data", date: "2016-12-19", tags: ["counterfactual-reasoning", "importance-sampling"], topic: "RL", type: "blog", url: "https://timvieira.github.io/blog/post/2016/12/19/counterfactual-reasoning-and-learning-from-logged-data/", desc: "Using importance sampling for off-policy evaluation, counterfactual estimation, and learning from logs." },
  { id: 26, title: "How to Test Gradient Implementations", date: "2017-04-21", tags: ["testing", "calculus"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2017/04/21/how-to-test-gradient-implementations/", desc: "Finite-difference checks, complex-step verification, and best practices for gradient testing." },
  { id: 27, title: "Estimating Means in a Finite Universe", date: "2017-07-03", tags: ["sampling", "statistics", "reservoir-sampling"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2017/07/03/estimating-means-in-a-finite-universe/", desc: "Connections between sampling with and without replacement for population mean estimation." },
  { id: 28, title: "Backprop Is Not Just the Chain Rule", date: "2017-08-18", tags: ["calculus", "automatic-differentiation", "lagrange-multipliers"], topic: "Autodiff", type: "blog", url: "https://timvieira.github.io/blog/post/2017/08/18/backprop-is-not-just-the-chain-rule/", desc: "Backpropagation as a dynamic programming algorithm, connected to Lagrange multipliers and the adjoint method." },
  { id: 29, title: "Black-Box Optimization", date: "2018-03-16", tags: ["optimization", "calculus"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2018/03/16/black-box-optimization/", desc: "Ascent directions when you can't compute gradients: finite differences, random search, and more." },
  { id: 30, title: "Steepest Ascent", date: "2019-04-19", tags: ["optimization"], topic: "Optimization", type: "blog", url: "https://timvieira.github.io/blog/post/2019/04/19/steepest-ascent/", desc: "Understanding optimization algorithms as steepest ascent under different norms and metrics." },
  { id: 31, title: "The Likelihood-Ratio Gradient", date: "2019-04-20", tags: ["optimization", "rl"], topic: "RL", type: "blog", url: "https://timvieira.github.io/blog/post/2019/04/20/the-likelihood-ratio-gradient/", desc: "REINFORCE and the score function estimator: deriving policy gradients from first principles." },
  { id: 32, title: "Faster Reservoir Sampling by Waiting", date: "2019-06-11", tags: ["sampling", "reservoir-sampling", "gumbel"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2019/06/11/faster-reservoir-sampling-by-waiting/", desc: "Skipping elements in reservoir sampling using exponential waiting times for O(k log(n/k)) runtime." },
  { id: 33, title: "The Restart Acceleration Trick", date: "2019-09-06", tags: ["statistics", "algorithms"], topic: "Algorithms", type: "blog", url: "https://timvieira.github.io/blog/post/2019/09/06/the-restart-acceleration-trick-a-cure-for-the-heavy-tail-of-wasted-time/", desc: "A cure for heavy-tailed runtimes: restart strategies that dramatically improve expected completion time." },
  { id: 34, title: "Algorithms for Sampling Without Replacement", date: "2019-09-16", tags: ["sampling", "algorithms", "gumbel"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2019/09/16/algorithms-for-sampling-without-replacement/", desc: "Comprehensive treatment of SWoR: Gumbel top-k, priority sampling, and exponential race algorithms." },
  { id: 35, title: "Animation of the Inverse Transform Method", date: "2020-06-30", tags: ["sampling", "statistics"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2020/06/30/animation-of-the-inverse-transform-method/", desc: "Visual notebook animating the inverse CDF method for generating random variates." },
  { id: 36, title: "Generating Truncated Random Variates", date: "2020-06-30", tags: ["sampling", "statistics"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2020/06/30/generating-truncated-random-variates/", desc: "Efficient algorithms for sampling from truncated distributions via rejection and inverse CDF methods." },
  { id: 37, title: "Distribution Functions of Order Statistics", date: "2021-03-18", tags: ["sampling-without-replacement", "statistics"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2021/03/18/on-the-distribution-functions-of-order-statistics/", desc: "Deriving distribution functions for order statistics from independent random variables." },
  { id: 38, title: "Distribution of the Smallest Indices", date: "2021-03-20", tags: ["sampling-without-replacement", "statistics"], topic: "Sampling", type: "blog", url: "https://timvieira.github.io/blog/post/2021/03/20/on-the-distribution-of-the-smallest-indices/", desc: "PMF of the Gumbel sorting scheme and inclusion probabilities for bottom-k sampling." },
  { id: 39, title: "Fast Rank-One Updates to Matrix Inverse", date: "2021-03-25", tags: ["numerical", "efficiency"], topic: "Numerical", type: "blog", url: "https://timvieira.github.io/blog/post/2021/03/25/fast-rank-one-updates-to-matrix-inverse/", desc: "The Sherman-Morrison formula and practical considerations for incremental matrix inverse updates." },

  // ═══ SELECTED PAPERS ═══
  { id: 101, title: "LMs over Canonical BPE", date: "2025-07-01", tags: ["tokenization", "language-models"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2506.07956", desc: "Defining language models over canonical byte-pair encodings for principled character-level modeling. ICML 2025." },
  { id: 102, title: "From Token LMs to Character LMs", date: "2025-07-01", tags: ["tokenization", "language-models"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2412.03719", desc: "Marginalizing over tokenizations to build character-level LMs from token-level ones. ICML 2025." },
  { id: 103, title: "Syntactic & Semantic Control of LLMs via SMC", date: "2025-05-01", tags: ["language-models", "sampling", "smc"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2504.13139", desc: "Sequential Monte Carlo for enforcing constraints on LLM generation. ICLR 2025 Oral." },
  { id: 104, title: "Variational Best-of-N Alignment", date: "2025-05-01", tags: ["language-models", "optimization", "rl"], topic: "RL", type: "paper", url: "https://arxiv.org/abs/2407.06057", desc: "A variational framework for best-of-N sampling in LLM alignment. ICLR 2025." },
  { id: 105, title: "Foundations of Tokenization", date: "2025-05-01", tags: ["tokenization", "formal-languages"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2407.11606", desc: "Statistical and computational concerns in tokenization theory. ICLR 2025." },
  { id: 106, title: "Fast Controlled Generation via Rejection Sampling", date: "2025-06-01", tags: ["language-models", "sampling"], topic: "Sampling", type: "paper", url: "https://arxiv.org/abs/2504.05410", desc: "Efficient constrained generation from language models. CoLM 2025 Outstanding Paper." },
  { id: 107, title: "Better KL Divergence Estimation Between LMs", date: "2025-12-01", tags: ["statistics", "language-models"], topic: "Sampling", type: "paper", url: "https://arxiv.org/abs/2504.10637", desc: "Improved estimators for KL divergence between language models. NeurIPS 2025." },
  { id: 108, title: "DPO with an Offset", date: "2024-08-01", tags: ["language-models", "optimization", "rl"], topic: "RL", type: "paper", url: "https://arxiv.org/abs/2402.10571", desc: "ODPO: extending DPO with an offset for better preference learning. Findings of ACL 2024." },
  { id: 109, title: "If Beam Search Is the Answer, What Was the Question?", date: "2020-11-01", tags: ["algorithms", "nlp"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2010.02650", desc: "Formalizing beam search through uniform information density. EMNLP 2020 Honorable Mention." },
  { id: 110, title: "Best-First Beam Search", date: "2020-07-01", tags: ["algorithms", "nlp"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2007.03909", desc: "An optimal-certificate beam search variant that searches best-first. TACL 2020." },
  { id: 111, title: "Learning to Prune", date: "2017-04-01", tags: ["nlp", "structured-prediction"], topic: "NLP", type: "paper", url: "https://doi.org/10.1162/tacl_a_00060", desc: "Exploring the frontier of fast and accurate parsing through learned pruning. TACL 2017." },
  { id: 112, title: "Semiring-Weighted Earley Parsing", date: "2023-07-01", tags: ["algorithms", "formal-languages"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2307.02982", desc: "Generalizing Earley's algorithm to arbitrary semirings. ACL 2023." },
  { id: 113, title: "Left-Corner Transformations", date: "2023-12-01", tags: ["formal-languages", "nlp"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2311.16258", desc: "Systematic study of left-corner grammar transformations. EMNLP 2023." },
  { id: 114, title: "Algorithms for Weighted Pushdown Automata", date: "2022-12-01", tags: ["formal-languages", "algorithms"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2210.06884", desc: "General-purpose algorithms for weighted pushdown automata. EMNLP 2022." },
  { id: 115, title: "Expectations under Spanning Tree Distributions", date: "2021-06-01", tags: ["algorithms", "structured-prediction"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2008.12988", desc: "Efficient expectation computation under spanning tree distributions. TACL 2021." },
  { id: 116, title: "Searching for More Efficient DPs", date: "2021-11-01", tags: ["algorithms", "dynamic-programming"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2109.06966", desc: "Automated analysis and improvement of dynamic programming algorithms. EMNLP 2021." },
  { id: 117, title: "PhD: Automating DP Analysis", date: "2023-06-01", tags: ["dynamic-programming", "nlp", "algorithms"], topic: "Algorithms", type: "paper", url: "https://timvieira.github.io/doc/2023-timv-dissertation.pdf", desc: "Automating the analysis and improvement of dynamic programming with NLP applications. Dissertation 2023." },
  { id: 118, title: "Variable-Order CRFs & Structured Sparsity", date: "2016-11-01", tags: ["nlp", "crf"], topic: "NLP", type: "paper", url: "https://aclanthology.org/D16-1206/", desc: "Speed-accuracy tradeoffs with variable-order CRFs and structured sparsity. EMNLP 2016." },
  { id: 119, title: "Dyna: Self-Optimizing ML Language", date: "2017-06-01", tags: ["dynamic-programming", "programming-languages"], topic: "Algorithms", type: "paper", url: "https://timvieira.github.io/doc/2017-mapl-dyna.pdf", desc: "A declarative language for ML that automatically optimizes dynamic programs. MAPL 2017." },
  { id: 120, title: "Syntactic Control by Posterior Inference", date: "2025-07-01", tags: ["language-models", "nlp"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2506.07154", desc: "Controlling LM syntax through posterior inference over parse structures. Findings of ACL 2025." },
  { id: 121, title: "WFSAs with Failure Arcs", date: "2022-12-01", tags: ["formal-languages", "algorithms"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2301.06862", desc: "Algorithms for weighted finite-state automata with failure arcs. EMNLP 2022." },
  { id: 122, title: "On Proper Treatment of Tokenization in Psycholinguistics", date: "2024-11-01", tags: ["tokenization", "nlp"], topic: "NLP", type: "paper", url: "https://arxiv.org/abs/2410.02691", desc: "How tokenization choices affect psycholinguistic evaluations of LMs. EMNLP 2024." },
  { id: 123, title: "Conditional Poisson Stochastic Beam Search", date: "2021-11-01", tags: ["algorithms", "sampling"], topic: "Algorithms", type: "paper", url: "https://arxiv.org/abs/2109.11034", desc: "Beam search with Poisson sampling for unbiased sequence selection. EMNLP 2021." },
];

const TOPICS = ["Sampling", "Optimization", "Autodiff", "NLP", "Algorithms", "Numerical", "RL"];
const TOPIC_COLORS = {
  Sampling: "#e8a838", Optimization: "#e85d4a", Autodiff: "#4ac9e8",
  NLP: "#7ce84a", Algorithms: "#c084fc", Numerical: "#94a3b8", RL: "#f472b6",
};

const ALL_TAGS = [...new Set(ITEMS.flatMap((e) => e.tags))].sort();
const VIEWS = [
  { id: "graph", label: "Knowledge Graph", icon: "⬡" },
  { id: "constellation", label: "Constellation", icon: "✦" },
  { id: "timeline", label: "Timeline", icon: "━" },
  { id: "treemap", label: "Treemap", icon: "▦" },
  { id: "embedding", label: "Embedding Space", icon: "◎" },
  { id: "cards", label: "Card Wall", icon: "▤" },
];

function hash2d(s, seed = 0) {
  let h = seed;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  const x = ((Math.sin(h) * 43758.5453) % 1 + 1) % 1;
  const y = ((Math.sin(h * 127.1 + 311.7) * 43758.5453) % 1 + 1) % 1;
  return { x, y };
}
ITEMS.forEach((e) => { const p = hash2d(e.title, e.id); e.x2d = p.x; e.y2d = p.y; });

function EssayPanel({ essay, onClose }) {
  if (!essay) return null;
  return (
    <div style={{ position: "absolute", top: 16, right: 16, width: 330, maxHeight: "calc(100% - 32px)", background: "rgba(14,14,20,0.97)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 14, padding: 24, zIndex: 100, backdropFilter: "blur(16px)", overflowY: "auto", animation: "slideIn 0.2s ease-out" }}>
      <button onClick={onClose} style={{ position: "absolute", top: 12, right: 14, background: "none", border: "none", color: "#666", fontSize: 18, cursor: "pointer", lineHeight: 1 }}>✕</button>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
        <span style={{ fontSize: 9, letterSpacing: 2, color: TOPIC_COLORS[essay.topic], textTransform: "uppercase", fontFamily: "var(--mono)" }}>{essay.topic}</span>
        <span style={{ fontSize: 9, padding: "2px 7px", borderRadius: 4, background: essay.type === "paper" ? "rgba(124,232,74,0.12)" : "rgba(232,168,56,0.12)", color: essay.type === "paper" ? "#7ce84a" : "#e8a838", fontFamily: "var(--mono)" }}>{essay.type}</span>
      </div>
      <h3 style={{ margin: "0 0 8px", fontFamily: "var(--serif)", fontSize: 19, color: "#f0ece4", lineHeight: 1.35, fontWeight: 400 }}>{essay.title}</h3>
      <div style={{ fontSize: 11, color: "#666", marginBottom: 14, fontFamily: "var(--mono)" }}>{essay.date}</div>
      <p style={{ fontSize: 13, color: "#aaa", lineHeight: 1.65, margin: "0 0 16px" }}>{essay.desc}</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 16 }}>
        {essay.tags.map((t) => (<span key={t} style={{ fontSize: 9, padding: "3px 8px", borderRadius: 4, background: "rgba(255,255,255,0.05)", color: "#888", fontFamily: "var(--mono)" }}>{t}</span>))}
      </div>
      <a href={essay.url} target="_blank" rel="noreferrer" style={{ display: "inline-block", fontSize: 11, color: "#e8a838", textDecoration: "none", borderBottom: "1px solid rgba(232,168,56,0.3)", fontFamily: "var(--mono)" }}>Read →</a>
    </div>
  );
}

function KnowledgeGraph({ onSelect }) {
  const svgRef = useRef(null);
  const links = useMemo(() => {
    const l = [];
    for (let i = 0; i < ITEMS.length; i++) for (let j = i + 1; j < ITEMS.length; j++) {
      const shared = ITEMS[i].tags.filter((t) => ITEMS[j].tags.includes(t));
      if (shared.length > 0) l.push({ source: ITEMS[i].id, target: ITEMS[j].id, strength: shared.length });
    }
    return l;
  }, []);
  useEffect(() => {
    const svg = d3.select(svgRef.current); const W = svgRef.current.clientWidth; const H = svgRef.current.clientHeight;
    svg.selectAll("*").remove();
    const nodes = ITEMS.map((e) => ({ ...e }));
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const edgeData = links.filter((l) => nodeMap.has(l.source) && nodeMap.has(l.target)).map((l) => ({ source: nodeMap.get(l.source), target: nodeMap.get(l.target), strength: l.strength }));
    const sim = d3.forceSimulation(nodes).force("link", d3.forceLink(edgeData).distance(55).strength((d) => d.strength * 0.12)).force("charge", d3.forceManyBody().strength(-100)).force("center", d3.forceCenter(W / 2, H / 2)).force("collision", d3.forceCollide(18));
    const g = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.15, 4]).on("zoom", (e) => g.attr("transform", e.transform)));
    const link = g.selectAll("line").data(edgeData).join("line").attr("stroke", "rgba(255,255,255,0.03)").attr("stroke-width", (d) => Math.min(d.strength, 2));
    const node = g.selectAll("circle").data(nodes).join("circle").attr("r", (d) => d.type === "paper" ? 7 : 5).attr("fill", (d) => TOPIC_COLORS[d.topic]).attr("opacity", 0.85).attr("stroke", (d) => d.type === "paper" ? "#fff2" : "none").attr("stroke-width", 1.5).style("cursor", "pointer").on("click", (e, d) => onSelect(d.id))
      .call(d3.drag().on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }).on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; }).on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));
    const label = g.selectAll("text").data(nodes).join("text").text((d) => d.title.length > 22 ? d.title.slice(0, 20) + "…" : d.title).attr("font-size", 7).attr("fill", "#666").attr("font-family", "var(--mono)").attr("dx", 10).attr("dy", 3).style("pointer-events", "none");
    sim.on("tick", () => { link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y); node.attr("cx", (d) => d.x).attr("cy", (d) => d.y); label.attr("x", (d) => d.x).attr("y", (d) => d.y); });
    return () => sim.stop();
  }, [links, onSelect]);
  return <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />;
}

function Constellation({ onSelect }) {
  const canvasRef = useRef(null); const posRef = useRef([]); const starsRef = useRef([]); const animRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current; const ctx = canvas.getContext("2d");
    const W = canvas.parentElement.clientWidth; const H = canvas.parentElement.clientHeight;
    canvas.width = W * 2; canvas.height = H * 2; canvas.style.width = W + "px"; canvas.style.height = H + "px"; ctx.scale(2, 2);
    if (!starsRef.current.length) starsRef.current = Array.from({ length: 280 }, () => ({ x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.1, tw: Math.random() * Math.PI * 2 }));
    const pad = 45;
    posRef.current = ITEMS.map((e) => ({ ...e, px: pad + e.x2d * (W - pad * 2), py: pad + e.y2d * (H - pad * 2) }));
    const links = [];
    for (let i = 0; i < ITEMS.length; i++) for (let j = i + 1; j < ITEMS.length; j++) if (ITEMS[i].topic === ITEMS[j].topic) { const dx = posRef.current[i].px - posRef.current[j].px; const dy = posRef.current[i].py - posRef.current[j].py; if (Math.sqrt(dx * dx + dy * dy) < 160) links.push([i, j]); }
    let t = 0;
    function draw() {
      t += 0.012; ctx.fillStyle = "#060610"; ctx.fillRect(0, 0, W, H);
      const grd = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.55); grd.addColorStop(0, "rgba(25,15,45,0.2)"); grd.addColorStop(1, "rgba(6,6,16,0)"); ctx.fillStyle = grd; ctx.fillRect(0, 0, W, H);
      starsRef.current.forEach((s) => { ctx.fillStyle = `rgba(200,210,255,${0.2 + 0.3 * Math.sin(t + s.tw)})`; ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill(); });
      ctx.strokeStyle = "rgba(255,255,255,0.05)"; ctx.lineWidth = 0.7;
      links.forEach(([i, j]) => { ctx.beginPath(); ctx.moveTo(posRef.current[i].px, posRef.current[i].py); ctx.lineTo(posRef.current[j].px, posRef.current[j].py); ctx.stroke(); });
      posRef.current.forEach((e) => { const col = TOPIC_COLORS[e.topic]; const sz = e.type === "paper" ? 16 : 12; const glow = ctx.createRadialGradient(e.px, e.py, 0, e.px, e.py, sz); glow.addColorStop(0, col + "55"); glow.addColorStop(1, col + "00"); ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(e.px, e.py, sz, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = col; ctx.beginPath(); ctx.arc(e.px, e.py, e.type === "paper" ? 3.5 : 2.5, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = "rgba(255,255,255,0.35)"; ctx.font = "7px 'JetBrains Mono', monospace"; ctx.fillText(e.title.length > 20 ? e.title.slice(0, 18) + "…" : e.title, e.px + 8, e.py + 3); });
      animRef.current = requestAnimationFrame(draw);
    }
    draw(); return () => cancelAnimationFrame(animRef.current);
  }, []);
  const handleClick = useCallback((e) => { const rect = canvasRef.current.getBoundingClientRect(); const x = e.clientX - rect.left, y = e.clientY - rect.top; const hit = posRef.current.find((ep) => Math.hypot(ep.px - x, ep.py - y) < 18); if (hit) onSelect(hit.id); }, [onSelect]);
  return <canvas ref={canvasRef} onClick={handleClick} style={{ cursor: "crosshair", display: "block" }} />;
}

function Timeline({ onSelect }) {
  const svgRef = useRef(null);
  useEffect(() => {
    const svg = d3.select(svgRef.current); const W = svgRef.current.clientWidth; const H = svgRef.current.clientHeight; svg.selectAll("*").remove();
    const g = svg.append("g"); svg.call(d3.zoom().scaleExtent([0.3, 5]).on("zoom", (e) => g.attr("transform", e.transform)));
    const sorted = [...ITEMS].sort((a, b) => new Date(a.date) - new Date(b.date));
    const xScale = d3.scaleTime().domain(d3.extent(sorted, (d) => new Date(d.date))).range([100, W - 60]);
    g.append("line").attr("x1", 80).attr("y1", H / 2).attr("x2", W - 40).attr("y2", H / 2).attr("stroke", "rgba(255,255,255,0.08)");
    d3.timeYear.range(new Date("2014-01-01"), new Date("2026-01-01")).forEach((yr) => { const x = xScale(yr); g.append("line").attr("x1", x).attr("y1", H / 2 - 8).attr("x2", x).attr("y2", H / 2 + 8).attr("stroke", "rgba(255,255,255,0.1)"); g.append("text").attr("x", x).attr("y", H / 2 + 24).text(yr.getFullYear()).attr("text-anchor", "middle").attr("fill", "#444").attr("font-size", 9).attr("font-family", "var(--mono)"); });
    const topicY = {}; TOPICS.forEach((t, i) => { topicY[t] = (i % 2 === 0 ? -1 : 1) * (32 + Math.floor(i / 2) * 38); });
    sorted.forEach((e, idx) => { const x = xScale(new Date(e.date)); const baseY = topicY[e.topic]; const jitter = ((idx * 7) % 5 - 2) * 10; const y = H / 2 + baseY + jitter;
      g.append("line").attr("x1", x).attr("y1", H / 2).attr("x2", x).attr("y2", y).attr("stroke", "rgba(255,255,255,0.03)").attr("stroke-dasharray", "2,3");
      g.append("circle").attr("cx", x).attr("cy", y).attr("r", e.type === "paper" ? 5 : 4).attr("fill", TOPIC_COLORS[e.topic]).attr("opacity", 0.85).style("cursor", "pointer").on("click", () => onSelect(e.id));
      g.append("text").attr("x", x).attr("y", y + (baseY < 0 ? -10 : 13)).text(e.title.length > 14 ? e.title.slice(0, 12) + "…" : e.title).attr("text-anchor", "middle").attr("fill", "#666").attr("font-size", 6.5).attr("font-family", "var(--mono)").style("pointer-events", "none");
    });
  }, [onSelect]);
  return <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />;
}

function Treemap({ onSelect }) {
  const svgRef = useRef(null);
  useEffect(() => {
    const svg = d3.select(svgRef.current); const W = svgRef.current.clientWidth; const H = svgRef.current.clientHeight; svg.selectAll("*").remove();
    const hierarchy = { name: "All", children: TOPICS.map((t) => ({ name: t, children: ITEMS.filter((e) => e.topic === t).map((e) => ({ name: e.title, value: e.desc.length + 40, essay: e })) })).filter((t) => t.children.length > 0) };
    const root = d3.hierarchy(hierarchy).sum((d) => d.value || 0).sort((a, b) => b.value - a.value);
    d3.treemap().size([W, H]).padding(3).paddingTop(22).round(true)(root);
    svg.selectAll("g.topic").data(root.children).join("g").each(function(d) { const g = d3.select(this); g.append("rect").attr("x", d.x0).attr("y", d.y0).attr("width", d.x1 - d.x0).attr("height", d.y1 - d.y0).attr("fill", TOPIC_COLORS[d.data.name] + "10").attr("stroke", TOPIC_COLORS[d.data.name] + "25").attr("rx", 4); g.append("text").attr("x", d.x0 + 5).attr("y", d.y0 + 14).text(d.data.name.toUpperCase()).attr("font-size", 8).attr("fill", TOPIC_COLORS[d.data.name]).attr("font-family", "var(--mono)").attr("letter-spacing", 1.5); });
    const leaves = svg.selectAll("g.leaf").data(root.leaves()).join("g");
    leaves.append("rect").attr("x", (d) => d.x0).attr("y", (d) => d.y0).attr("width", (d) => d.x1 - d.x0).attr("height", (d) => d.y1 - d.y0).attr("fill", (d) => TOPIC_COLORS[d.parent.data.name] + "20").attr("stroke", (d) => TOPIC_COLORS[d.parent.data.name] + "12").attr("rx", 3).style("cursor", "pointer").on("click", (ev, d) => onSelect(d.data.essay.id)).on("mouseenter", function() { d3.select(this).attr("fill", (d) => TOPIC_COLORS[d.parent.data.name] + "40"); }).on("mouseleave", function() { d3.select(this).attr("fill", (d) => TOPIC_COLORS[d.parent.data.name] + "20"); });
    leaves.append("text").attr("x", (d) => d.x0 + 3).attr("y", (d) => d.y0 + 12).text((d) => { const max = Math.floor((d.x1 - d.x0) / 5.2); return d.data.name.length > max ? d.data.name.slice(0, max - 1) + "…" : d.data.name; }).attr("font-size", 8.5).attr("fill", "#bbb").attr("font-family", "var(--serif)").style("pointer-events", "none");
  }, [onSelect]);
  return <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />;
}

function EmbeddingSpace({ onSelect }) {
  const svgRef = useRef(null);
  useEffect(() => {
    const svg = d3.select(svgRef.current); const W = svgRef.current.clientWidth; const H = svgRef.current.clientHeight; svg.selectAll("*").remove();
    const g = svg.append("g"); svg.call(d3.zoom().scaleExtent([0.3, 6]).on("zoom", (e) => g.attr("transform", e.transform)));
    const pad = 45; const xS = d3.scaleLinear().domain([0, 1]).range([pad, W - pad]); const yS = d3.scaleLinear().domain([0, 1]).range([pad, H - pad]);
    for (let i = 0; i <= 10; i++) { const x = pad + (i / 10) * (W - pad * 2), y = pad + (i / 10) * (H - pad * 2); g.append("line").attr("x1", x).attr("y1", pad).attr("x2", x).attr("y2", H - pad).attr("stroke", "rgba(255,255,255,0.02)"); g.append("line").attr("x1", pad).attr("y1", y).attr("x2", W - pad).attr("y2", y).attr("stroke", "rgba(255,255,255,0.02)"); }
    TOPICS.forEach((t) => { const es = ITEMS.filter((e) => e.topic === t); if (!es.length) return; g.append("text").attr("x", xS(d3.mean(es, (e) => e.x2d))).attr("y", yS(d3.mean(es, (e) => e.y2d)) + 45).text(t).attr("text-anchor", "middle").attr("fill", TOPIC_COLORS[t] + "35").attr("font-size", 9).attr("font-family", "var(--mono)"); });
    ITEMS.forEach((e) => { const x = xS(e.x2d), y = yS(e.y2d), r = e.type === "paper" ? 6 : 4.5;
      g.append("circle").attr("cx", x).attr("cy", y).attr("r", r).attr("fill", TOPIC_COLORS[e.topic]).attr("opacity", 0.75).attr("stroke", e.type === "paper" ? "#fff2" : "none").attr("stroke-width", 1).style("cursor", "pointer").on("click", () => onSelect(e.id)).on("mouseenter", function() { d3.select(this).attr("r", r + 3).attr("opacity", 1); }).on("mouseleave", function() { d3.select(this).attr("r", r).attr("opacity", 0.75); });
      g.append("text").attr("x", x + r + 4).attr("y", y + 3).text(e.title.length > 22 ? e.title.slice(0, 20) + "…" : e.title).attr("font-size", 7).attr("fill", "#666").attr("font-family", "var(--mono)").style("pointer-events", "none");
    });
  }, [onSelect]);
  return <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />;
}

function CardWall({ onSelect, selected }) {
  const [activeTopic, setActiveTopic] = useState(null);
  const [typeFilter, setTypeFilter] = useState(null);
  const filtered = ITEMS.filter((e) => { if (activeTopic && e.topic !== activeTopic) return false; if (typeFilter && e.type !== typeFilter) return false; return true; }).sort((a, b) => new Date(b.date) - new Date(a.date));
  const chip = (active, color) => ({ padding: "4px 11px", borderRadius: 6, border: active ? `1px solid ${color || "#fff3"}` : "1px solid transparent", background: active ? (color ? color + "22" : "rgba(255,255,255,0.1)") : "rgba(255,255,255,0.03)", color: active ? (color || "#ddd") : "#666", fontSize: 11, cursor: "pointer", fontFamily: "var(--mono)", transition: "all 0.15s" });
  return (
    <div style={{ height: "100%", overflow: "auto", padding: "14px 18px" }}>
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 12 }}>
        <button onClick={() => { setActiveTopic(null); setTypeFilter(null); }} style={chip(!activeTopic && !typeFilter)}>All ({ITEMS.length})</button>
        <button onClick={() => setTypeFilter(typeFilter === "blog" ? null : "blog")} style={chip(typeFilter === "blog", "#e8a838")}>Blog ({ITEMS.filter(e => e.type === "blog").length})</button>
        <button onClick={() => setTypeFilter(typeFilter === "paper" ? null : "paper")} style={chip(typeFilter === "paper", "#7ce84a")}>Papers ({ITEMS.filter(e => e.type === "paper").length})</button>
        <span style={{ width: 1, background: "#333", margin: "0 2px" }} />
        {TOPICS.map((t) => (<button key={t} onClick={() => { setActiveTopic(activeTopic === t ? null : t); }} style={chip(activeTopic === t, TOPIC_COLORS[t])}>{t}</button>))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 10 }}>
        {filtered.map((e) => (
          <div key={e.id} onClick={() => onSelect(e.id)} style={{ background: selected === e.id ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.02)", border: `1px solid ${selected === e.id ? TOPIC_COLORS[e.topic] + "40" : "rgba(255,255,255,0.04)"}`, borderRadius: 10, padding: 15, cursor: "pointer", transition: "all 0.2s" }}
            onMouseEnter={(ev) => { ev.currentTarget.style.background = "rgba(255,255,255,0.045)"; ev.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={(ev) => { ev.currentTarget.style.background = selected === e.id ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.02)"; ev.currentTarget.style.transform = ""; }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
              <span style={{ fontSize: 8, color: TOPIC_COLORS[e.topic], letterSpacing: 1.5, textTransform: "uppercase", fontFamily: "var(--mono)" }}>{e.topic}</span>
              <span style={{ fontSize: 8, padding: "2px 6px", borderRadius: 3, background: e.type === "paper" ? "rgba(124,232,74,0.1)" : "rgba(255,255,255,0.04)", color: e.type === "paper" ? "#7ce84a" : "#666", fontFamily: "var(--mono)" }}>{e.type === "paper" ? "📄 paper" : "blog"}</span>
            </div>
            <div style={{ fontSize: 14, fontFamily: "var(--serif)", color: "#e8e4dc", lineHeight: 1.4, marginBottom: 5 }}>{e.title}</div>
            <div style={{ fontSize: 10, color: "#555", fontFamily: "var(--mono)", marginBottom: 6 }}>{e.date}</div>
            <div style={{ fontSize: 11.5, color: "#888", lineHeight: 1.5 }}>{e.desc.slice(0, 100)}…</div>
          </div>
        ))}
      </div>
      {!filtered.length && <div style={{ textAlign: "center", color: "#555", padding: 60, fontFamily: "var(--mono)", fontSize: 13 }}>No items match.</div>}
    </div>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center", alignItems: "center" }}>
      {TOPICS.map((t) => (<div key={t} style={{ display: "flex", alignItems: "center", gap: 4 }}><div style={{ width: 7, height: 7, borderRadius: "50%", background: TOPIC_COLORS[t] }} /><span style={{ fontSize: 9, color: "#555", fontFamily: "var(--mono)" }}>{t}</span></div>))}
      <span style={{ width: 1, height: 10, background: "#333" }} />
      <span style={{ fontSize: 9, color: "#555", fontFamily: "var(--mono)" }}>● blog · ◉ paper</span>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("graph");
  const [selectedId, setSelectedId] = useState(null);
  const selectedItem = ITEMS.find((e) => e.id === selectedId) || null;
  const handleSelect = useCallback((id) => setSelectedId(id), []);
  return (
    <div style={{ "--mono": "'JetBrains Mono', 'SF Mono', monospace", "--serif": "'Playfair Display', Georgia, serif", width: "100vw", height: "100vh", background: "#0a0a12", color: "#e8e4dc", fontFamily: "var(--serif)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
      <style>{`@keyframes slideIn { from { opacity: 0; transform: translateX(12px); } to { opacity: 1; transform: translateX(0); } } ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 3px; }`}</style>
      <div style={{ padding: "16px 20px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 3 }}>
          <h1 style={{ margin: 0, fontSize: 20, fontFamily: "var(--serif)", fontWeight: 400 }}>Graduate Descent</h1>
          <span style={{ fontSize: 10, color: "#555", fontFamily: "var(--mono)" }}>Tim Vieira · ETH Zürich</span>
        </div>
        <p style={{ margin: "2px 0 10px", fontSize: 10, color: "#444", fontFamily: "var(--mono)" }}>{ITEMS.filter(e => e.type === "blog").length} blog posts · {ITEMS.filter(e => e.type === "paper").length} papers · {TOPICS.length} topics · 2014–2025</p>
        <div style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
          {VIEWS.map((v) => (<button key={v.id} onClick={() => { setView(v.id); setSelectedId(null); }} style={{ padding: "5px 12px", borderRadius: 6, border: view === v.id ? "1px solid rgba(232,168,56,0.25)" : "1px solid rgba(255,255,255,0.06)", background: view === v.id ? "rgba(232,168,56,0.08)" : "rgba(255,255,255,0.02)", color: view === v.id ? "#e8a838" : "#666", fontSize: 10, cursor: "pointer", fontFamily: "var(--mono)", transition: "all 0.15s", display: "flex", alignItems: "center", gap: 5 }}><span style={{ fontSize: 11 }}>{v.icon}</span> {v.label}</button>))}
        </div>
      </div>
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {view === "graph" && <KnowledgeGraph onSelect={handleSelect} />}
        {view === "constellation" && <Constellation onSelect={handleSelect} />}
        {view === "timeline" && <Timeline onSelect={handleSelect} />}
        {view === "treemap" && <Treemap onSelect={handleSelect} />}
        {view === "embedding" && <EmbeddingSpace onSelect={handleSelect} />}
        {view === "cards" && <CardWall onSelect={handleSelect} selected={selectedId} />}
        <EssayPanel essay={selectedItem} onClose={() => setSelectedId(null)} />
      </div>
      {view !== "cards" && <div style={{ padding: "7px 20px", borderTop: "1px solid rgba(255,255,255,0.05)" }}><Legend /></div>}
    </div>
  );
}
