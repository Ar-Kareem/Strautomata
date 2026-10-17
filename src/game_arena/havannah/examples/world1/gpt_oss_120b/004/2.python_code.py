
import random
from typing import List, Tuple
import numpy as np

# ---------- Union‑Find implementation ----------
class UnionFind:
    def __init__(self):
        self.parent = {}          # maps node -> parent
        self.rank = {}            # for union by rank
        self.edge_sets = {}       # maps root -> set of edges touched

    def make_set(self, node, edges):
        self.parent[node] = node
        self.rank[node] = 0
        self.edge_sets[node] = set(edges)

    def find(self, node):
        # Path compression
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        # Union by rank
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.edge_sets[ra].update(self.edge_sets[rb])
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return ra

    def component_edges(self, node):
        return self.edge_sets[self.find(node)]

# ---------- Helper functions ----------
def hex_neighbours(r: int, c: int, N: int = 15) -> List[Tuple[int, int]]:
    """Return the six hex neighbours of (r,c) that are inside the board."""
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
    neigh = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            neigh.append((nr, nc))
    return neigh

def edges_touched(cell: Tuple[int, int]) -> List[str]:
    """Return a list of edge identifiers the cell touches."""
    r, c = cell
    edges = []
    if r == 0:
        edges.append('top')
    if r == 14:
        edges.append('bottom')
    if c == 0:
        edges.append('left')
    if c == 14:
        edges.append('right')
    return edges

# ---------- Main policy ----------
def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           valid_mask) -> Tuple[int, int]:
    """
    Returns a legal move for the current player on a 15x15 Havannah board.
    """
    N = 15  # board size
    occupied = set(me) | set(opp)

    # Pre‑compute UnionFind for our stones
    uf = UnionFind()
    for stone in me:
        uf.make_set(stone, edges_touched(stone))

    # Merge existing neighbour components
    for stone in me:
        for nb in hex_neighbours(*stone, N):
            if nb in me:
                uf.union(stone, nb)

    # Gather all candidate cells
    candidates = []
    valid_np = np.array(valid_mask, dtype=bool)
    for r in range(N):
        for c in range(N):
            if not valid_np[r, c]:
                continue
            if (r, c) in occupied:
                continue
            candidates.append((r, c))

    # Fallback: if no candidates (should not happen) choose first empty
    if not candidates:
        for r in range(N):
            for c in range(N):
                if valid_np[r, c] and (r, c) not in occupied:
                    return (r, c)

    best_score = -10**9
    best_moves = []

    for cand in candidates:
        r, c = cand
        own_adj = 0
        opp_adj = 0
        neighbour_comps = set()

        for nb in hex_neighbours(r, c, N):
            if nb in me:
                own_adj += 1
                neighbour_comps.add(uf.find(nb))
            elif nb in opp:
                opp_adj += 1

        # Simulate merging neighbour components with the new stone
        simulated_edges = set(edges_touched(cand))
        for comp_root in neighbour_comps:
            simulated_edges.update(uf.component_edges(comp_root))

        edge_count = len(simulated_edges)

        # Simple linear scoring function
        score = 10 * edge_count + 2 * own_adj - opp_adj

        if score > best_score:
            best_score = score
            best_moves = [cand]
        elif score == best_score:
            best_moves.append(cand)

    # Random tie‑break among equally good moves
    return random.choice(best_moves)
