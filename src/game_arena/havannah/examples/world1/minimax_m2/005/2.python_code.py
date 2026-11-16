
# Havannah policy for a 15x15 hex board
# --------------------------------------------------------------
# The API required by the arena is:
#   def policy(me: list[tuple[int, int]],
#              opp: list[tuple[int, int]],
#              valid_mask) -> tuple[int, int]:
# --------------------------------------------------------------

import sys
from collections import deque, defaultdict

# Board size and radius
N = 15                # board width/height
R = N // 2            # 7 – radius of the hex

# Hex neighbour offsets (row, col)
OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]

# ----------------------------------------------------------------------
# Pre‑computation of neighbour lists, edge type of each cell and the six
# corner coordinates.  Edge types are encoded as:
#   0 – top (row = 0)
#   1 – right (col = N‑1)
#   2 – down‑right (row+col = 3*R)
#   3 – bottom (row = N‑1)
#   4 – left (col = 0)
#   5 – up‑left (row+col = R)
#   -1 – interior cell
#   -2 – corner cell (belongs to two edges)
# ----------------------------------------------------------------------
_neighbor_dict = {}
_edge_type_map = {}
_corners = []

for r in range(N):
    for c in range(N):
        # neighbours inside the board
        nb = []
        for dr, dc in OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                nb.append((nr, nc))
        _neighbor_dict[(r, c)] = nb

        # axial coordinates (ri, ci) and the third coordinate s = -ri-ci
        ri = r - R
        ci = c - R
        s = -ri - ci

        # Which coordinate(s) are at the extreme ±R ?
        matches = []
        if abs(ri) == R:
            matches.append('top' if ri == -R else 'bottom')
        if abs(ci) == R:
            matches.append('left' if ci == -R else 'right')
        if abs(s) == R:
            matches.append('up-left' if s == -R else 'down-right')

        if len(matches) == 0:
            et = -1          # interior
        elif len(matches) == 1:
            # map to the numeric edge id
            mapping = {
                'top': 0,
                'right': 1,
                'down-right': 2,
                'bottom': 3,
                'left': 4,
                'up-left': 5
            }
            et = mapping[matches[0]]
        else:
            et = -2          # corner
            _corners.append((r, c))

        _edge_type_map[(r, c)] = et

# Store the six corners as a set for quick lookup
_CORNER_SET = set(_corners)

# ----------------------------------------------------------------------
# Helper: BFS that returns the whole connected component of `player`
# stones that contains the start cell.
# ----------------------------------------------------------------------
def _connected_component(start, occupied):
    """Return the set of cells reachable from `start` using only cells in
    `occupied` (a set of (r,c))."""
    comp = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for nb in _neighbor_dict[cur]:
            if nb in occupied and nb not in comp:
                comp.add(nb)
                stack.append(nb)
    return comp

# ----------------------------------------------------------------------
# Counting internal edges of a component (undirected, counted once)
# ----------------------------------------------------------------------
def _count_edges(comp):
    e = 0
    for (r, c) in comp:
        for (nr, nc) in _neighbor_dict[(r, c)]:
            if (nr, nc) in comp and (nr, nc) > (r, c):
                e += 1
    return e

# ----------------------------------------------------------------------
# Winning‑condition tests for a given player (1 = us, 2 = opponent)
# ----------------------------------------------------------------------
def _has_bridge(comp):
    """Bridge – at least two corners occupied by the player."""
    return len(_CORNER_SET.intersection(comp)) >= 2

def _has_fork(comp):
    """Fork – component touches three different edge types (corners excluded)."""
    edge_types = set()
    for cell in comp:
        et = _edge_type_map[cell]
        if et >= 0:               # interior edges only
            edge_types.add(et)
    return len(edge_types) >= 3

def _has_ring(comp):
    """Ring – any cycle.  Simple test: |edges| >= |vertices|."""
    if len(comp) < 6:
        return False
    edges = _count_edges(comp)
    return edges >= len(comp)

def _player_wins(board, player):
    """True iff `player` already has a winning structure on `board`."""
    occupied = set()
    for r in range(N):
        for c in range(N):
            if board[r][c] == player:
                occupied.add((r, c))
    visited = set()
    for cell in occupied:
        if cell in visited:
            continue
        comp = _connected_component(cell, occupied)
        visited.update(comp)
        if _has_bridge(comp) or _has_fork(comp) or _has_ring(comp):
            return True
    return False

# ----------------------------------------------------------------------
# Heuristic evaluation for a candidate move (our stone placed at `mv`).
# The score is a linear combination of many local features.
# ----------------------------------------------------------------------
def _heuristic(board, mv, my_set, opp_set):
    r, c = mv
    # Build the new set of our stones with the candidate added
    new_my = set(my_set)
    new_my.add(mv)

    # Component that contains the new stone
    comp = _connected_component(mv, new_my)
    sz = len(comp)
    edges = _count_edges(comp)

    # Base score – centre preference (smaller distance → larger score)
    dist = (r - R) * (r - R) + (c - R) * (c - R)
    score = 20 - dist

    # Edge / corner bonus
    et = _edge_type_map[mv]
    if et >= 0:          # on a non‑corner edge
        score += 5
    if et == -2:         # a corner
        score += 10

    # Size bonus – reward larger connected components
    score += sz * 2

    # Distinct edge types inside the component (fork potential)
    edge_types = set()
    for cell in comp:
        et2 = _edge_type_map[cell]
        if et2 >= 0:
            edge_types.add(et2)
    if len(edge_types) >= 2:
        score += 10 * len(edge_types)

    # Corner connections – very valuable for bridges
    corners_in_comp = _CORNER_SET.intersection(comp)
    if len(corners_in_comp) >= 2:
        score += 50
    elif len(corners_in_comp) == 1:
        score += 10

    # Ring potential – cycle creation
    if sz >= 6 and edges >= sz:
        score += 30

    # Defensive value – adjacent opponent stones
    opp_adj = sum(1 for nb in _neighbor_dict[mv] if nb in opp_set)
    score += opp_adj * 4

    # Mobility – avoid overly blocked moves
    empty_adj = sum(1 for nb in _neighbor_dict[mv] if board[nb[0]][nb[1]] == 0)
    if empty_adj < 2:
        score -= (2 - empty_adj) * 2

    return score

# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(me, opp, valid_mask):
    # ------------------------------------------------------------------
    # Convert inputs to fast data structures
    # ------------------------------------------------------------------
    me_set = set(me)
    opp_set = set(opp)
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 2

    # ------------------------------------------------------------------
    # 1) Immediate winning move for us?
    # ------------------------------------------------------------------
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c] or board[r][c] != 0:
                continue
            mv = (r, c)
            board2 = [row[:] for row in board]
            board2[r][c] = 1
            if _player_wins(board2, 1):
                return mv

    # ------------------------------------------------------------------
    # 2) Immediate winning move for opponent?  Block one of them.
    # ------------------------------------------------------------------
    opp_win_moves = []
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c] or board[r][c] != 0:
                continue
            mv = (r, c)
            board2 = [row[:] for row in board]
            board2[r][c] = 2
            if _player_wins(board2, 2):
                opp_win_moves.append(mv)

    if opp_win_moves:
        best = None
        best_score = -10**9
        for mv in opp_win_moves:
            # Give a big “block” bonus while still evaluating the rest
            s = _heuristic(board, mv, me_set, opp_set) + 1000
            if s > best_score:
                best_score = s
                best = mv
        return best

    # ------------------------------------------------------------------
    # 3) No immediate threats – evaluate every legal move.
    # ------------------------------------------------------------------
    best_move = None
    best_score = -10**9
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c] or board[r][c] != 0:
                continue
            mv = (r, c)
            s = _heuristic(board, mv, me_set, opp_set)
            if s > best_score:
                best_score = s
                best_move = mv

    # Safety fallback – should never happen because a legal move exists
    if best_move is None:
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and board[r][c] == 0:
                    return (r, c)
    return best_move
