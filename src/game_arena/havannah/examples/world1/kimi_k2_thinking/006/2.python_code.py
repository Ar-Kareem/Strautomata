
import numpy as np
from collections import deque
from typing import Set, Tuple, List

# ----------------------------------------------------------------------
# board geometry constants (15×15 array → side length 8 → offset 7)
BOARD_SIZE = 15
OFFSET = 7                     # (row‑7, col‑7) gives axial coordinates

# ----------------------------------------------------------------------
# pre‑compute the six corner cells (in (row, col) coordinates)
CORNERS = {
    (0, 7),   (7, 0),   (7, 14),
    (14, 7),  (0, 14),  (14, 0)
}

# ----------------------------------------------------------------------
# helper conversions between array indices and axial coordinates
def to_axial(row: int, col: int) -> Tuple[int, int]:
    """(row, col) → (r, c) axial coordinates centred at (0,0)"""
    return row - OFFSET, col - OFFSET

def from_axial(r: int, c: int) -> Tuple[int, int]:
    """(r, c) axial → (row, col) array indices"""
    return r + OFFSET, c + OFFSET

# ----------------------------------------------------------------------
# neighbourhood on the hex grid (six directions)
DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

def neighbours(pos: Tuple[int, int], valid: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """return all valid neighbours of pos"""
    r, c = to_axial(*pos)
    out = []
    for dr, dc in DELTAS:
        nr, nc = r + dr, c + dc
        if -OFFSET <= nr <= OFFSET and -OFFSET <= nc <= OFFSET and -OFFSET <= nr + nc <= OFFSET:
            nb = from_axial(nr, nc)
            if nb in valid:
                out.append(nb)
    return out

# ----------------------------------------------------------------------
# edge membership (excluding corners)
def edge_id(pos: Tuple[int, int]) -> int | None:
    """return a number 0..5 for the edge the cell lies on,
    or None if it is not an edge (or it is a corner)."""
    r, c = to_axial(*pos)
    # corner cells are not considered part of an edge
    if pos in CORNERS:
        return None
    if r == -OFFSET:          # top
        return 0
    if r == OFFSET:           # bottom
        return 1
    if c == -OFFSET:          # left
        return 2
    if c == OFFSET:           # right
        return 3
    if r + c == -OFFSET:      # top‑left diagonal side
        return 4
    if r + c == OFFSET:       # bottom‑right diagonal side
        return 5
    return None

# ----------------------------------------------------------------------
# simple union‑find‑style clustering (BFS for readability)
def clusters(stones: Set[Tuple[int, int]], valid: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
    """return the connected components of stones"""
    visited = set()
    out = []
    for s in stones:
        if s in visited:
            continue
        q = deque([s])
        visited.add(s)
        comp = {s}
        while q:
            cur = q.popleft()
            for nb in neighbours(cur, valid):
                if nb in stones and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
                    comp.add(nb)
        out.append(comp)
    return out

# ----------------------------------------------------------------------
# detect a cycle inside a single component (E ≥ V)
def has_cycle(comp: Set[Tuple[int, int]], valid: Set[Tuple[int, int]]) -> bool:
    """return True if the component contains at least one simple cycle"""
    edge_cnt = 0
    for v in comp:
        for nb in neighbours(v, valid):
            if nb in comp:
                edge_cnt += 1
    edge_cnt //= 2               # each edge counted twice
    return edge_cnt >= len(comp)

# ----------------------------------------------------------------------
# winning test for a set of stones
def is_winner(stones: Set[Tuple[int, int]], valid: Set[Tuple[int, int]]) -> bool:
    """True if stones contain a bridge, fork or ring"""
    for comp in clusters(stones, valid):
        # ---- bridge -------------------------------------------------
        corners_in = sum(1 for c in CORNERS if c in comp)
        if corners_in >= 2:
            return True

        # ---- fork ---------------------------------------------------
        edges_touch = {edge_id(p) for p in comp if edge_id(p) is not None}
        if len(edges_touch) >= 3:
            return True

        # ---- ring (cycle) -------------------------------------------
        if has_cycle(comp, valid):
            return True
    return False

# ----------------------------------------------------------------------
# all legal moves from a given board state
def legal_moves(my_stones: Set[Tuple[int, int]],
                opp_stones: Set[Tuple[int, int]],
                valid: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """return list of empty playable cells"""
    return [p for p in valid if p not in my_stones and p not in opp_stones]

# ----------------------------------------------------------------------
# immediate winning moves for a player
def immediate_wins(player: Set[Tuple[int, int]],
                  opponent: Set[Tuple[int, int]],
                  valid: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """list of moves that make ``player`` win on the spot"""
    empty = legal_moves(player, opponent, valid)
    win_moves = []
    for mv in empty:
        new_player = player | {mv}
        if is_winner(new_player, valid):
            win_moves.append(mv)
    return win_moves

# ----------------------------------------------------------------------
# the policy required by the competition API
def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           valid_mask) -> Tuple[int, int]:
    """
    Return a single legal move for the Havannah board described by
        me          – list of our stones
        opp         – list of opponent stones
        valid_mask  – 15×15 boolean array
    """
    # ---- convenient sets ------------------------------------------------
    my_set = set(me)
    opp_set = set(opp)
    valid = set(zip(*np.where(valid_mask)))

    # pre‑compute neighbour table (tiny board → negligible cost)
    neigh = {p: neighbours(p, valid) for p in valid}

    # ---- 1) immediate win ------------------------------------------------
    win_moves = immediate_wins(my_set, opp_set, valid)
    if win_moves:
        return win_moves[0]

    # ---- 2) block opponent immediate win ---------------------------------
    lose_moves = immediate_wins(opp_set, my_set, valid)   # cells that would let opponent win now
    if lose_moves:
        # block the first such cell
        return lose_moves[0]

    # ---- 3) otherwise evaluate all legal moves ---------------------------
    candidates = legal_moves(my_set, opp_set, valid)

    best_move = candidates[0]          # fallback
    best_score = -1e9

    # helper: create a new cluster after playing at mv (BFS from mv)
    def new_cluster(mv: Tuple[int, int]) -> Set[Tuple[int, int]]:
        cluster = {mv}
        q = deque([mv])
        while q:
            cur = q.popleft()
            for nb in neigh[cur]:
                if nb in my_set and nb not in cluster:
                    cluster.add(nb)
                    q.append(nb)
        return cluster

    for mv in candidates:
        # new state after our move
        new_my = my_set | {mv}
        # ---- a) does the opponent win on the following turn? ----------
        opp_wins_after = immediate_wins(opp_set, new_my, valid)
        # ---- b) features of the new cluster we create ------------------
        clust = new_cluster(mv)
        sz = len(clust)

        # corners touched
        corners_touch = len([c for c in CORNERS if c in clust])

        # edges touched (distinct)
        edges_touch = {edge_id(p) for p in clust if edge_id(p) is not None}
        edge_cnt = len(edges_touch)

        # cycle / ring ?
        cycle = has_cycle(clust, valid)

        # ---- c) build a simple heuristic score -------------------------
        score = 0
        score += sz * 10                     # big clusters are good
        score += corners_touch * 50          # corners are valuable for bridges
        score += edge_cnt * 10               # edges are valuable for forks
        if cycle:
            score += 200                     # a ring is a winning condition
        # adjacency to own / opponent stones
        own_adj = sum(1 for nb in neigh[mv] if nb in my_set)
        opp_adj = sum(1 for nb in neigh[mv] if nb in opp_set)
        score += own_adj * 5
        score += opp_adj * 5
        # central control (Manhattan distance on the array)
        dist_cent = abs(mv[0] - OFFSET) + abs(mv[1] - OFFSET)
        score -= dist_cent * 2
        # extra bonus for being close to completing a fork / bridge
        if edge_cnt >= 2:
            score += 30
        if corners_touch >= 1:
            score += 20
        # heavy penalty if opponent can win on the next turn
        if opp_wins_after:
            score -= 1000

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move
