# Linguistic Explorer — Python port
#
# Ports the usable ideas from the Wolfram sketch into real, runnable code:
#   - a linguistic entry dataset
#   - a semantic graph (phoneme <-> word)
#   - a cross-entry word relationship graph
#   - a neural-style feature/activation mapper (genuine numpy math, not decoration)
#   - complexity/frequency clustering (real sklearn, not a Mathematica stub)
#   - a deterministic "turtle path" through phonetic space, distinct from the
#     GPS-based TurtleWalker in turtlewalker_airprogram.py (different domain,
#     kept as a separate class — GlyphWalker — to avoid name collision)
#
# No front-end-only constructs (no Dynamic/PopupMenu/Slider dependencies) —
# this runs headless, in a script, or inside Streamlit.

from dataclasses import dataclass, field
import math

import numpy as np
import networkx as nx
from sklearn.cluster import AgglomerativeClustering


@dataclass
class LinguisticEntry:
    phoneme: str
    pos: str
    words: list[str]
    definition: str
    frequency: float      # 0-1, usage frequency
    complexity: float     # 0-1, linguistic complexity
    origin: str
    semantic_weight: float = 0.75  # 0-1, contribution to semantic clustering


# --- Sample dataset (ported directly from the Wolfram entries) ---

SAMPLE_ENTRIES: list[LinguisticEntry] = [
    LinguisticEntry("un-r", "noun", ["rumps", "amputables"],
                     "Physical objects associated with movement",
                     0.85, 0.70, "Proto-Indo-European", 0.90),
    LinguisticEntry("hun-r", "verb", ["stretches", "integrates"],
                     "To extend or connect",
                     0.92, 0.80, "Germanic", 0.85),
    LinguisticEntry("run-r", "verb", ["stretches", "threads"],
                     "To extend or weave",
                     0.78, 0.60, "Slavic", 0.75),
    LinguisticEntry("um-r", "noun", ["loom", "resides"],
                     "A device or place of residence",
                     0.65, 0.50, "Celtic", 0.60),
    LinguisticEntry("hum-r", "verb", ["creates", "shreds"],
                     "To make or produce",
                     0.88, 0.75, "Italic", 0.80),
    LinguisticEntry("rum-r", "verb", ["creates", "shreds"],
                     "To fabricate or construct",
                     0.72, 0.65, "Balto-Slavic", 0.70),
]


# --- Semantic graphs (real networkx, not a hallucinated Graph[] call) ---

def build_semantic_graph(entries: list[LinguisticEntry]) -> nx.Graph:
    """Phoneme <-> word edges, one bipartite-style graph per entry."""
    g = nx.Graph()
    for entry in entries:
        g.add_node(entry.phoneme, kind="phoneme")
        for w in entry.words:
            g.add_node(w, kind="word")
            g.add_edge(entry.phoneme, w)
    return g


def build_word_graph(entries: list[LinguisticEntry]) -> nx.Graph:
    """Cross-entry word relationships: entries that share a word get linked."""
    g = nx.Graph()
    word_to_entries: dict[str, list[int]] = {}
    for i, entry in enumerate(entries):
        g.add_node(entry.phoneme)
        for w in entry.words:
            word_to_entries.setdefault(w, []).append(i)

    for word, entry_indices in word_to_entries.items():
        for a in range(len(entry_indices)):
            for b in range(a + 1, len(entry_indices)):
                i, j = entry_indices[a], entry_indices[b]
                g.add_edge(entries[i].phoneme, entries[j].phoneme, shared_word=word)

    return g


# --- Neural-style feature mapper (real numpy activations, computed for real) ---

ACTIVATIONS = {
    "sigmoid": lambda x: 1 / (1 + np.exp(-x)),
    "tanh": lambda x: np.tanh(x),
    "relu": lambda x: np.maximum(0, x),
    "linear": lambda x: x,
}


def feature_vector(entry: LinguisticEntry) -> np.ndarray:
    return np.array([
        entry.frequency,
        entry.complexity,
        len(entry.words),
        len(entry.definition),
        entry.semantic_weight,
    ])


def normalized_feature_matrix(entries: list[LinguisticEntry]) -> np.ndarray:
    """
    Min-max normalize each feature column to [0, 1] across the corpus.
    Without this, definition-length (raw values in the 30-50+ range) swamps
    the 0-1 features in the summed input, which is what was saturating
    sigmoid before. A constant column (max == min) is left at 0 rather
    than dividing by zero.
    """
    matrix = np.array([feature_vector(e) for e in entries])
    col_min = matrix.min(axis=0)
    col_max = matrix.max(axis=0)
    col_span = col_max - col_min
    constant_columns = col_span == 0
    safe_span = np.where(constant_columns, 1.0, col_span)  # avoid divide-by-zero
    normalized = (matrix - col_min) / safe_span
    normalized[:, constant_columns] = 0.0  # constant columns carry no information
    return normalized


def activation_profile(entry: LinguisticEntry, corpus: list[LinguisticEntry] | None = None) -> dict[str, float]:
    """
    Apply each activation function to the entry's normalized, summed feature
    vector. Normalization is computed relative to `corpus` (defaults to the
    single entry's own dataset context via SAMPLE_ENTRIES) so sigmoid/tanh
    actually differentiate entries instead of all saturating near 1.0.
    """
    if corpus is None:
        corpus = SAMPLE_ENTRIES
    normalized = normalized_feature_matrix(corpus)
    index = corpus.index(entry) if entry in corpus else None
    if index is None:
        # Entry isn't part of the reference corpus — normalize against itself + corpus
        normalized = normalized_feature_matrix(corpus + [entry])
        index = len(corpus)
    total = float(np.sum(normalized[index]))
    return {name: float(fn(total)) for name, fn in ACTIVATIONS.items()}


def connections_matrix(entries: list[LinguisticEntry]) -> np.ndarray:
    """Pairwise L1 distance between entries' feature vectors."""
    vectors = np.array([feature_vector(e) for e in entries])
    n = len(entries)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i, j] = float(np.sum(np.abs(vectors[i] - vectors[j])))
    return matrix


# --- Clustering (real sklearn, replaces the Wolfram FindClusters stub) ---

def cluster_entries(entries: list[LinguisticEntry], n_clusters: int = 3) -> dict[int, list[str]]:
    """Cluster entries by (complexity, frequency) using agglomerative clustering."""
    n_clusters = min(n_clusters, len(entries))
    points = np.array([[e.complexity, e.frequency] for e in entries])
    model = AgglomerativeClustering(n_clusters=n_clusters)
    labels = model.fit_predict(points)

    clusters: dict[int, list[str]] = {}
    for entry, label in zip(entries, labels):
        clusters.setdefault(int(label), []).append(entry.phoneme)
    return clusters


# --- GlyphWalker: deterministic turtle path through phonetic space ---
# Kept separate from TurtleWalker (turtlewalker_airprogram.py), which walks
# real GPS coordinates. This walks an abstract 2D plane derived from each
# entry's complexity/frequency — a stylistic visualization, not a claim
# about real phonetic geometry.

@dataclass
class GlyphWalker:
    position: tuple[float, float] = (0.0, 0.0)
    heading_degrees: float = 0.0
    pen_down: bool = True
    history: list[tuple[float, float]] = field(default_factory=list)

    def forward(self, distance: float) -> tuple[float, float]:
        rad = math.radians(self.heading_degrees)
        x, y = self.position
        self.position = (x + distance * math.cos(rad), y + distance * math.sin(rad))
        if self.pen_down:
            self.history.append(self.position)
        return self.position

    def turn(self, degrees: float) -> None:
        self.heading_degrees += degrees

    def walk_entries(self, entries: list[LinguisticEntry]) -> list[tuple[float, float]]:
        """
        Deterministic path: each entry advances the walker forward by
        (frequency * 10) and turns by (complexity * 90) degrees. Same
        entries always produce the same path.
        """
        self.history = [self.position]
        for entry in entries:
            self.turn(entry.complexity * 90)
            self.forward(entry.frequency * 10)
        return self.history


# --- Self-test when run directly ---

if __name__ == "__main__":
    print("Semantic graph nodes:", build_semantic_graph(SAMPLE_ENTRIES).number_of_nodes())
    print("Word graph edges:", build_word_graph(SAMPLE_ENTRIES).number_of_edges())

    print("\nActivation profiles (normalized):")
    for e in SAMPLE_ENTRIES:
        print(f"  {e.phoneme}: {activation_profile(e, SAMPLE_ENTRIES)}")

    print("\nConnections matrix:")
    print(connections_matrix(SAMPLE_ENTRIES).round(2))

    print("\nClusters:", cluster_entries(SAMPLE_ENTRIES))

    walker = GlyphWalker()
    path = walker.walk_entries(SAMPLE_ENTRIES)
    print("\nGlyph path:")
    for p in path:
        print(f"  ({p[0]:.2f}, {p[1]:.2f})")
