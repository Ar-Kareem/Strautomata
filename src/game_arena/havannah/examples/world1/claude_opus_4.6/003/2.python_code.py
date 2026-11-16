
import numpy as np
import time
import random
from collections import deque

def policy(me, opp, valid_mask):
    valid_mask = np.array(valid_mask)
    N = valid_mask.shape[0]  # 15
    me_set = set(me)
    opp_set = set(opp)
    
    valid_moves = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c] and (r,c) not in me_set and (r,c) not in opp_set]
    
    if not valid_moves:
        # fallback
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    def neighbors(r, c):
        return [(r-1,c),(r+1,c),(r,c-1),(r,c+1),(r-1,c+1),(r+1,c-1)]
    
    def valid_neighbors(r, c):
        return [(nr,nc) for nr,nc in neighbors(r,c) if 0<=nr<N and 0<=nc<N and valid_mask[nr][nc]]
    
    # Havannah board properties
    board_size = (N + 1) // 2  # 8 for 15x15
    
    corners = set()
    edges_cells = {}  # edge_id -> set of cells (excluding corners)
    
    # Identify corners and edges for hex board
    # For a size-8 Havannah on 15x15 grid, corners are the 6 extreme points
    all_valid = [(r,c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    
    # Find corners: cells on boundary with exactly 2 valid neighbors
    boundary = set()
    for r,c in all_valid:
        vn = valid_neighbors(r,c)
        if len(vn) < 6:
            boundary.add((r,c))
    
    for r,c in boundary:
        vn = [(nr,nc) for nr,nc in valid_neighbors(r,c) if (nr,nc) in boundary]
        if len(vn) <= 2:
            # Could be corner - corners have exactly 2 boundary neighbors
            all_vn = valid_neighbors(r,c)
            if len(all_vn) <= 3:
                corners.add((r,c))
    
    # More robust corner detection
    corners = set()
    # For standard hex board size s on (2s-1)x(2s-1) grid:
    s = board_size  # 8
    # The 6 corners of the hex board:
    corners = {(0,0), (0, s-1), (s-1, 0), (s-1, N-1), (N-1, s-1), (N-1, N-1)}
    # Filter to valid
    corners = {c for c in corners if 0<=c[0]<N and 0<=c[1]<N and valid_mask[c[0]][c[1]]}
    
    # Edges: boundary cells grouped by which side they're on (excluding corners)
    # 6 edges between consecutive corners
    def get_boundary_edges():
        edge_map = {}
        for r,c in boundary:
            if (r,c) in corners:
                continue
            # Determine which edge based on position
            if r == 0:
                edge_map.setdefault(0, set()).add((r,c))
            elif c == 0 and r < s:
                edge_map.setdefault(1, set()).add((r,c))
            elif c == 0 and r >= s-1:
                # bottom-left region
                edge_map.setdefault(2, set()).add((r,c))
            elif r == N-1:
                edge_map.setdefault(3, set()).add((r,c))
            elif c == N-1 and r >= s-1:
                edge_map.setdefault(4, set()).add((r,c))
            elif c == N-1 and r < s:
                edge_map.setdefault(5, set()).add((r,c))
            else:
                # Diagonal edges
                # top-right: r + c == s-1 (for r>0, c>0)
                # bottom-left: r + c == N-1 + s - 1
                # Actually need to figure out hex board edge membership
                pass
        return edge_map
    
    # Proper edge identification for hex board
    def identify_edge(r, c):
        """Return edge id (0-5) or -1 if not on edge, None if corner"""
        if (r,c) in corners:
            return None
        if (r,c) not in boundary:
            return -1
        # Top edge: r=0
        if r == 0:
            return 0
        # Top-right edge: c = N-1 - ... actually let me think about hex geometry
        # For the upper half (r < s-1): left boundary is c=0, right boundary is c = s-1+r
        # For the lower half (r >= s-1): left boundary is c=r-s+1, right boundary is c=N-1
        if r < s - 1:
            if c == 0:
                return 5  # upper-left edge
            if c == s - 1 + r:
                return 1  # upper-right edge
        elif r == s - 1:
            if c == 0:
                return 5
            if c == N - 1:
                return 1
        else:  # r > s-1
            if c == r - s + 1:
                return 4  # lower-left edge
            if c == N - 1:
                return 2  # lower-right edge
        if r == N - 1:
            return 3  # bottom edge
        return -1
    
    # Recompute boundary properly
    boundary = set()
    for r, c in all_valid:
        vn = valid_neighbors(r, c)
        if len(vn) < 6:
            boundary.add((r, c))
    
    # Recompute corners: the 6 corners of hex board
    # Top-left: (0,0), Top-right: (0, s-1), 
    # Mid-left: (s-1, 0), Mid-right: (s-1, N-1)
    # Bot-left: (N-1, s-1), Bot-right: (N-1, N-1)
    corners = set()
    for r,c in boundary:
        bn = [(nr,nc) for nr,nc in valid_neighbors(r,c) if (nr,nc) in boundary]
        all_n = valid_neighbors(r,c)
        if len(all_n) <= 3:
            corners.add((r,c))
    
    edge_cells = {}
    for r,c in boundary:
        if (r,c) in corners:
            continue
        eid = identify_edge(r,c)
        if eid is not None and eid >= 0:
            edge_cells.setdefault(eid, set()).add((r,c))
    
    def get_connected_components(stones_set):
        visited = set()
        components = []
        for s in stones_set:
            if s in visited:
                continue
            comp = set()
            queue = deque([s])
            while queue:
                cur = queue.popleft()
                if cur in comp:
                    continue
                comp.add(cur)
                visited.add(cur)
                for nr, nc in neighbors(*cur):
                    if (nr,nc) in stones_set and (nr,nc) not in comp:
                        queue.append((nr,nc))
            components.append(comp)
        return components
    
    def check_win(stones_set):
        if len(stones_set) < 6:
            # Minimum for any winning structure is debatable, but skip tiny sets
            pass
        components = get_connected_components(stones_set)
        for comp in components:
            # Check bridge: connects 2 corners
            comp_corners = comp & corners
            if len(comp_corners) >= 2:
                return True
            # Check fork: connects 3 edges
            touched_edges = set()
            for r,c in comp:
                eid = identify_edge(r,c)
                if eid is not None and eid >= 0:
                    touched_edges.add(eid)
            if len(touched_edges) >= 3:
                return True
            # Check ring: a cycle enclosing at least one cell
            if check_ring(comp):
                return True
        return False
    
    def check_ring(comp):
        if len(comp) < 6:
            return False
        # A ring exists if there's a cell not in comp that is completely surrounded
        # by comp cells. Check cells adjacent to comp.
        # More precisely: ring = cycle in the component graph
        # Simple check: for each cell adjacent to comp but not in comp,
        # check if all its valid neighbors are in comp
        candidates = set()
        for r,c in comp:
            for nr,nc in neighbors(r,c):
                if 0<=nr<N and 0<=nc<N and valid_mask[nr][nc] and (nr,nc) not in comp:
                    candidates.add((nr,nc))
        for r,c in candidates:
            vn = valid_neighbors(r,c)
            if all((nr,nc) in comp for nr,nc in vn):
                return True
        return False
    
    # Check immediate win
    for move in valid_moves:
        test_set = me_set | {move}
        if check_win(test_set):
            return move
    
    # Check immediate block
    blocking_moves = []
    for move in valid_moves:
        test_set = opp_set | {move}
        if check_win(test_set):
            blocking_moves.append(move)
    
    if len(blocking_moves) == 1:
        return blocking_moves[0]
    if len(blocking_moves) > 1:
        # Multiple threats - try to block the most critical
        # Pick one that also helps us
        return blocking_moves[0]
    
    # MCTS
    start_time = time.time()
    time_limit = 0.85
    
    # Prioritize moves near existing stones and center
    center = N // 2
    
    def move_priority(move):
        r, c = move
        dist_center = abs(r - center) + abs(c - center)
        near_me = sum(1 for nr,nc in neighbors(r,c) if (nr,nc) in me_set)
        near_opp = sum(1 for nr,nc in neighbors(r,c) if (nr,nc) in opp_set)
        on_edge = 1 if (r,c) in boundary else 0
        on_corner = 2 if (r,c) in corners else 0
        return -dist_center + near_me * 3 + near_opp * 2 + on_corner + on_edge
    
    # If early game, play near center
    if len(me) == 0:
        return (center, center) if valid_mask[center][center] else valid_moves[0]
    
    # Sort moves by priority for better MCTS
    scored_moves = sorted(valid_moves, key=move_priority, reverse=True)
    top_moves = scored_moves[:min(40, len(scored_moves))]
    
    wins = {m: 0 for m in top_moves}
    visits = {m: 0 for m in top_moves}
    total_visits = 0
    
    def quick_check_win(stones_set):
        """Faster approximate win check for rollouts"""
        components = get_connected_components(stones_set)
        for comp in components:
            comp_corners = comp & corners
            if len(comp_corners) >= 2:
                return True
            touched_edges = set()
            for r,c in comp:
                eid = identify_edge(r,c)
                if eid is not None and eid >= 0:
                    touched_edges.add(eid)
            if len(touched_edges) >= 3:
                return True
        return False
    
    while time.time() - start_time < time_limit:
        # Select move using UCB1
        best_move = None
        best_ucb = -float('inf')
        for m in top_moves:
            if visits[m] == 0:
                best_move = m
                break
            ucb = wins[m] / visits[m] + 1.414 * (np.log(total_visits) / visits[m]) ** 0.5
            if ucb > best_ucb:
                best_ucb = ucb
                best_move = m
        
        # Rollout
        my_stones = me_set | {best_move}
        opp_stones = set(opp_set)
        remaining = [m for m in valid_moves if m != best_move]
        random.shuffle(remaining)
        
        my_turn = False  # opponent moves next
        result = 0
        
        max_rollout = min(40, len(remaining))
        for i in range(max_rollout):
            move = remaining[i]
            if my_turn:
                my_stones.add(move)
            else:
                opp_stones.add(move)
            
            # Check win every few moves
            if i >= 5 and i % 3 == 0:
                if my_turn and quick_check_win(my_stones):
                    result = 1
                    break
                elif not my_turn and quick_check_win(opp_stones):
                    result = -1
                    break
            my_turn = not my_turn
        
        if result == 0:
            # Heuristic evaluation
            my_comps = get_connected_components(my_stones)
            opp_comps = get_connected_components(opp_stones)
            my_max = max(len(c) for c in my_comps) if my_comps else 0
            opp_max = max(len(c) for c in opp_comps) if opp_comps else 0
            result = 1 if my_max >= opp_max else -1
        
        wins[best_move] += (1 if result > 0 else 0)
        visits[best_move] += 1
        total_visits += 1
    
    # Pick best move
    best_move = max(top_moves, key=lambda m: wins[m] / max(visits[m], 1))
    return best_move
