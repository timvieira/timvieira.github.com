#!/usr/bin/env python3
"""
pip install sentence-transformers umap-learn
python precompute_embeddings.py
"""
import json, numpy as np
from sentence_transformers import SentenceTransformer
from umap import UMAP

titles = [
    # Papers (40) — same order as research-graph.html
    "Fast Controlled Generation from Language Models with Adaptive Weighted Rejection Sampling",
    "Better Estimation of the KL Divergence Between Language Models",
    "Syntactic Control of Language Models by Posterior Inference",
    "Syntactic and Semantic Control of LLMs via Sequential Monte Carlo",
    "The Foundations of Tokenization: Statistical and Computational Concerns",
    "Variational Best-of-N Alignment",
    "Language Models over Canonical Byte-Pair Encodings",
    "From Language Models over Tokens to Language Models over Characters",
    "On the Proper Treatment of Tokenization in Psycholinguistics",
    "Direct Preference Optimization with an Offset",
    "Automating the Analysis and Improvement of Dynamic Programming Algorithms",
    "An Exploration of Left-Corner Transformations",
    "Efficient Algorithms for Recognizing Weighted Tree-Adjoining Languages",
    "Efficient Semiring-Weighted Earley Parsing",
    "A Formal Perspective on Byte-Pair Encoding",
    "On the Intersection of Context-Free and Regular Languages",
    "Algorithms for Weighted Pushdown Automata",
    "Algorithms for Weighted Finite-State Automata with Failure Arcs",
    "Exact Paired-Permutation Testing for Structured Test Statistics",
    "Automating the Analysis of Parsing Algorithms",
    "Searching for More Efficient Dynamic Programs",
    "Conditional Poisson Stochastic Beam Search",
    "Efficient Sampling of Dependency Structures",
    "Efficient Computation of Expectations under Spanning Tree Distributions",
    "On Finding the K-best Non-projective Dependency Trees",
    "Higher-order Derivatives of Weighted Finite-state Machines",
    "If Beam Search is the Answer, What was the Question?",
    "Please Mind the Root: Decoding Arborescences for Dependency Parsing",
    "Best-First Beam Search",
    "Evaluation of Logic Programs with Built-Ins and Aggregation",
    "The Universal Decompositional Semantics Dataset and Decomp Toolkit",
    "Forward-Backward with Failure Arcs for Variable-Order CRFs",
    "Dyna: Toward a Self-Optimizing Declarative Language for ML",
    "Learning to Prune: Exploring the Frontier of Fast and Accurate Parsing",
    "Speed-Accuracy Tradeoffs in Tagging with Variable-Order CRFs",
    "Universal Decompositional Semantics on Universal Dependencies",
    "A Joint Model of Orthography and Morphological Segmentation",
    "Reasoning about Quantities in Natural Language",
    "Grammarless Parsing for Joint Inference",
    "Relation Alignment for Textual Entailment Recognition",
    # Blog posts (39) — same order as research-graph.html
    "Fast rank-one updates to matrix inverse?",
    "On the Distribution of the Smallest Indices",
    "On the Distribution Functions of Order Statistics",
    "Animation of the inverse transform method",
    "Generating truncated random variates",
    "Algorithms for sampling without replacement",
    "The restart acceleration trick",
    "Faster reservoir sampling by waiting",
    "The likelihood-ratio gradient",
    "Steepest ascent",
    "Black-box optimization",
    "Backprop is not just the chain rule",
    "Estimating means in a finite universe",
    "How to test gradient implementations",
    "Counterfactual reasoning and learning from logged data",
    "Heaps for incremental computation",
    "Reversing a sequence with sublinear space",
    "Evaluating nabla f(x) is as fast as f(x)",
    "Fast sigmoid sampling",
    "Sqrt-biased sampling",
    "The optimal proposal distribution is not p",
    "Dimensional analysis of gradient ascent",
    "Gradient-based hyperparameter optimization",
    "Multidimensional array index",
    "Gradient of a product",
    "Multiclass logistic regression and CRFs are the same thing",
    "Conditional random fields as deep learning models?",
    "Log-Real number class",
    "Importance sampling",
    "Numerically stable p-norms",
    "KL-divergence as an objective function",
    "Complex-step derivative",
    "Gumbel-max trick and weighted reservoir sampling",
    "Gumbel-max trick",
    "Rant against grid search",
    "Expected value of a quadratic and the Delta method",
    "Visualizing high-dimensional functions with cross-sections",
    "Exp-normalize trick",
    "Gradient-vector product",
]

assert len(titles) == 79, f"Expected 79, got {len(titles)}"

print(f"Encoding {len(titles)} titles...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(titles, show_progress_bar=True)

print("Running UMAP...")
reducer = UMAP(n_components=2, n_neighbors=12, min_dist=0.15, metric="cosine", random_state=42)
coords = reducer.fit_transform(embeddings)

# Normalize to [0, 1]
for d in range(2):
    mn, mx = coords[:, d].min(), coords[:, d].max()
    coords[:, d] = (coords[:, d] - mn) / (mx - mn)

result = [[round(float(x), 4), round(float(y), 4)] for x, y in coords]

print("\n// Paste this into research-graph.html, replacing the existing SEMANTIC_COORDS line:")
print(f"var SEMANTIC_COORDS = {json.dumps(result)};")
