
import numpy as np
import time
import random
from collections import deque

def policy(me, opp, valid_mask):
    valid_mask = np.array(valid_mask)
    N = valid_mask.shape[0]
    board_size = (N + 1) // 2  # For 15x15, base size is 8
    
    me_set = set(me)
    opp_set = set(opp)
    
    valid_moves = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    if not valid_moves:
        # Fallback
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                yield (nr, nc)
    
    # Identify corners and edges
    corners = set()
    edges = {}  # cell -> edge_id (0-5), corners not part of edges
    
    # For hex board in 2D array, find corners and edges
    # Corners are the 6 extreme points of the hexagonal board
    # For a board of size s (base), N = 2*s - 1
    s = board_size
    # Corners: (0,0), (0,s-1), (s-1,0), (s-1,N-1), (N-1,s-1), (N-1,N-1)
    corner_list = [(0, 0), (0, s-1), (s-1, 0), (s-1, N-1), (N-1, s-1), (N-1, N-1)]
    corners = set(corner_list)
    
    # Edges: 6 edges between consecutive corners
    # Edge 0: top row (0, c) for c in 1..s-2
    # Edge 1: top-right: (r, s-1+r) for r in 1..s-2  
    # Edge 2: bottom-right: (s-1+i, N-1) for i in 1..s-2
    # Edge 3: bottom row: (N-1, c) for c in s..N-2
    # Edge 4: bottom-left: (N-1-i, s-1-i-1)... let me think differently
    
    # Let me identify edges by border cells
    def get_border_cells():
        border = set()
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    n_count = sum(1 for _ in neighbors(r, c))
                    if n_count < 6:
                        border.add((r, c))
        return border
    
    border = get_border_cells()
    
    def assign_edges():
        # Edge cells = border - corners
        edge_cells = border - corners
        # Assign edge IDs by grouping connected border cells between corners
        edge_map = {}
        edge_id = 0
        visited = set()
        for corner in corner_list:
            for nb in neighbors(*corner):
                if nb in edge_cells and nb not in visited:
                    # BFS along edge cells
                    queue = deque([nb])
                    visited.add(nb)
                    group = []
                    while queue:
                        cell = queue.popleft()
                        group.append(cell)
                        edge_map[cell] = edge_id
                        for nb2 in neighbors(*cell):
                            if nb2 in edge_cells and nb2 not in visited:
                                visited.add(nb2)
                                queue.append(nb2)
                    edge_id += 1
        return edge_map
    
    edge_map = assign_edges()
    
    def get_components(stones):
        if not stones:
            return []
        stone_set = set(stones)
        visited = set()
        components = []
        for s in stones:
            if s not in visited:
                comp = set()
                queue = deque([s])
                visited.add(s)
                while queue:
                    cell = queue.popleft()
                    comp.add(cell)
                    for nb in neighbors(*cell):
                        if nb in stone_set and nb not in visited:
                            visited.add(nb)
                            queue.append(nb)
                components.append(comp)
        return components
    
    def check_win(stones_set):
        if len(stones_set) < 3:
            return False
        components = get_components(list(stones_set))
        for comp in components:
            # Check bridge: connects 2 corners
            comp_corners = corners & comp
            if len(comp_corners) >= 2:
                return True
            # Check fork: connects 3 edges
            comp_edges = set()
            for cell in comp:
                if cell in edge_map:
                    comp_edges.add(edge_map[cell])
            if len(comp_edges) >= 3:
                return True
            # Check ring
            if check_ring(comp, stones_set):
                return True
        return False
    
    def check_ring(comp, stones_set):
        # A ring exists if there's a cell (empty or not) completely surrounded
        # by a connected component. We check if the complement of the component
        # has multiple connected components considering hex adjacency.
        # More precisely: consider all cells NOT in comp. If they form more than
        # one connected component (using hex adjacency + board boundary as connections),
        # then there's a ring.
        if len(comp) < 6:
            return False
        
        # Find all valid cells not in comp
        non_comp = set()
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in comp:
                    non_comp.add((r, c))
        
        # Also add a virtual "outside" node connected to all border cells not in comp
        # If any non-comp cell can't reach the outside, there's a ring
        # BFS from border non-comp cells
        reachable = set()
        queue = deque()
        for cell in non_comp:
            if cell in border:
                queue.append(cell)
                reachable.add(cell)
        
        while queue:
            cell = queue.popleft()
            for nb in neighbors(*cell):
                if nb in non_comp and nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)
        
        return len(reachable) < len(non_comp)
    
    # Check immediate wins
    for move in valid_moves:
        new_me = me_set | {move}
        if check_win(new_me):
            return move
    
    # Check immediate blocks
    for move in valid_moves:
        new_opp = opp_set | {move}
        if check_win(new_opp):
            return move
    
    # MCTS
    start_time = time.time()
    move_scores = {m: 0 for m in valid_moves}
    move_visits = {m: 0 for m in valid_moves}
    
    # Simple random rollout MCTS
    iterations = 0
    while time.time() - start_time < 0.7 and iterations < 5000:
        # Select move
        move = random.choice(valid_moves)
        
        # Simulate
        my_stones = me_set | {move}
        opp_stones = set(opp_set)
        remaining = [m for m in valid_moves if m != move]
        random.shuffle(remaining)
        
        turn = 1  # opponent's turn
        result = 0
        for i, m in enumerate(remaining[:30]):
            if turn == 1:
                opp_stones.add(m)
            else:
                my_stones.add(m)
            turn = 1 - turn
        
        # Heuristic eval: count connections
        my_comps = get_components(list(my_stones))
        opp_comps = get_components(list(opp_stones))
        my_score = max((len(c) for c in my_comps), default=0)
        opp_score = max((len(c) for c in opp_comps), default=0)
        result = 1 if my_score > opp_score else 0
        
        move_scores[move] += result
        move_visits[move] += 1
        iterations += 1
    
    # Pick best move
    best_move = max(valid_moves, key=lambda m: move_scores[m] / (move_visits[m] + 1e-9))
    return best_move
