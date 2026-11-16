
import numpy as np
from collections import deque

# Board size
N = 15

# Precompute neighbors for each cell
def compute_neighbors():
    neighbors = {}
    directions_even = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)]
    directions_odd = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, 1)]
    for r in range(N):
        for c in range(r + 1):
            dirs = directions_even if r % 2 == 0 else directions_odd
            neigh = []
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc <= nr:
                    neigh.append((nr, nc))
            neighbors[(r, c)] = neigh
    return neighbors

NEIGHBORS = compute_neighbors()

# Corners of the board
CORNERS = {(0, 0), (N-1, 0), (N-1, N-1), (0, 0), (N-1, 0), (N-1, N-1)}  # unique
CORNERS = {(0, 0), (N-1, 0), (N-1, N-1)}

# Edge classification
def edge_of(cell):
    r, c = cell
    if cell in CORNERS:
        return 'corner'
    if c == 0:
        return 'left'
    if c == r:
        return 'right'
    if r == N - 1:
        return 'bottom'
    return 'none'

# Simple BFS to check connectivity
def connected_component(stones, start, target_set):
    if start not in stones:
        return set()
    visited = set()
    q = deque([start])
    visited.add(start)
    found = set()
    while q:
        cur = q.popleft()
        if cur in target_set:
            found.add(cur)
        for nb in NEIGHBORS[cur]:
            if nb in stones and nb not in visited:
                visited.add(nb)
                q.append(nb)
    return found

# Check if adding (r,c) to 'stones' creates a win
def creates_win(stones, move):
    r, c = move
    new_stones = set(stones) | {move}
    
    # Bridge check: connects any two corners
    corner_hits = set()
    for corner in CORNERS:
        if corner in new_stones:
            comp = connected_component(new_stones, corner, CORNERS)
            corner_hits |= comp
    if len(corner_hits & CORNERS) >= 2:
        return True
    
    # Fork check: connects any 3 edges (excluding corners)
    edge_types = {'left', 'right', 'bottom'}
    edge_connections = set()
    for stone in new_stones:
        e = edge_of(stone)
        if e in edge_types:
            comp = connected_component(new_stones, stone, {s for s in new_stones if edge_of(s) in edge_types})
            for s in comp:
                edge_connections.add(edge_of(s))
            if len(edge_connections) >= 3:
                return True
    
    # Ring check (simplified): If new cell touches at least 3 of our stones that form a cycle around an empty cell
    # More rigorous implementation possible, but simplified for time
    # A ring exists if there's a cycle that encloses at least one empty cell not in the cycle
    # We'll skip precise ring detection for speed; rely on bridge/fork mainly.
    
    return False

# Check for immediate winning moves
def immediate_win(me, opp, valid_mask):
    for r in range(N):
        for c in range(r + 1):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                if creates_win(me, (r, c)):
                    return (r, c)
    return None

# Heuristic score for a move
def score_move(me, opp, move):
    r, c = move
    new_me = set(me) | {move}
    score = 0
    
    # Proximity to corners
    dists = [abs(r - cr) + abs(c - cc) for (cr, cc) in CORNERS]
    score -= min(dists) * 2
    
    # Connectivity to edges
    edge_hits = set()
    for stone in new_me:
        e = edge_of(stone)
        if e in {'left', 'right', 'bottom'}:
            comp = connected_component(new_me, stone, {s for s in new_me if edge_of(s) in {'left', 'right', 'bottom'}})
            for s in comp:
                edge_hits.add(edge_of(s))
    score += len(edge_hits) * 5
    
    # Center control
    score -= abs(r - N//2) + abs(c - r//2)
    
    # Ring potential (simplified heuristic: prefer moves that connect 2+ of our stones)
    connections = sum(1 for nb in NEIGHBORS[(r, c)] if nb in me)
    score += connections * 3
    
    # Block opponent wins
    if creates_win(opp, move):
        score += 1000
    
    return score

def policy(me, opp, valid_mask):
    me_set = set(me)
    opp_set = set(opp)
    
    # 1. Win immediately if possible
    win_move = immediate_win(me_set, opp_set, valid_mask)
    if win_move:
        return win_move
    
    # 2. Block opponent immediate win
    op_win_move = immediate_win(opp_set, me_set, valid_mask)
    if op_win_move:
        return op_win_move
    
    # 3. Heuristic search over valid moves
    best_score = -999999
    best_move = None
    for r in range(N):
        for c in range(r + 1):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                sc = score_move(me_set, opp_set, (r, c))
                # 1-ply lookahead: also consider opponent's best response to our move
                new_me = me_set | {(r, c)}
                opp_best = max(
                    (score_move(opp_set, new_me, (rr, cc)) 
                     for rr in range(N) for cc in range(rr+1)
                     if valid_mask[rr][cc] and (rr, cc) not in new_me and (rr, cc) not in opp_set),
                    default=0
                )
                sc -= opp_best * 0.2
                if sc > best_score:
                    best_score = sc
                    best_move = (r, c)
    
    return best_move if best_move else (N//2, N//4)
