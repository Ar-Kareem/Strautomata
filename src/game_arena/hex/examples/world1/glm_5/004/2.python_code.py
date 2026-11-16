
import time
from collections import deque

SIZE = 11

def get_neighbors(r, c):
    """Yield valid neighbors for a hex cell (r, c)."""
    for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            yield nr, nc

def bfs_dist(me_set, opp_set, start_edge, end_edge):
    """
    Calculate the minimum number of stones needed to connect start_edge to end_edge.
    Uses 0-1 BFS. 
    My stones have cost 0, empty cells cost 1, opponent stones are blocked.
    """
    dist = {}
    dq = deque()
    
    # Initialize queue with start edge cells
    for r, c in start_edge:
        if (r, c) in opp_set:
            continue
        d = 0 if (r, c) in me_set else 1
        if (r, c) not in dist or d < dist[(r, c)]:
            dist[(r, c)] = d
            if d == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))
                
    target_set = set(end_edge)
    
    while dq:
        r, c = dq.popleft()
        
        if (r, c) in target_set:
            return dist[(r, c)]
            
        current_d = dist[(r, c)]
        
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            
            cost = 0 if (nr, nc) in me_set else 1
            nd = current_d + cost
            
            if (nr, nc) not in dist or nd < dist[(nr, nc)]:
                dist[(nr, nc)] = nd
                if cost == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))
                    
    return float('inf')

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.time()
    
    me_set = set(me)
    opp_set = set(opp)
    
    # Define edges based on color
    if color == 'b': # Black connects Top (0) and Bottom (10)
        my_start = [(0, c) for c in range(SIZE)]
        my_end = [(SIZE-1, c) for c in range(SIZE)]
        opp_start = [(r, 0) for r in range(SIZE)] # White connects Left (0) and Right (10)
        opp_end = [(r, SIZE-1) for r in range(SIZE)]
    else: # White
        my_start = [(r, 0) for r in range(SIZE)]
        my_end = [(r, SIZE-1) for r in range(SIZE)]
        opp_start = [(0, c) for c in range(SIZE)]
        opp_end = [(SIZE-1, c) for c in range(SIZE)]

    # Find all empty cells
    all_empty = []
    for r in range(SIZE):
        for c in range(SIZE):
            if (r, c) not in me_set and (r, c) not in opp_set:
                all_empty.append((r, c))
                
    if not all_empty:
        return (0, 0) # Should not happen in a valid game

    # 1. Immediate Win Check
    # If I can win in 1 move, do it.
    for move in all_empty:
        me_set.add(move)
        d = bfs_dist(me_set, opp_set, my_start, my_end)
        me_set.remove(move)
        if d == 0:
            return move

    # 2. Immediate Block Check
    # If opponent can win in 1 move, block it.
    for move in all_empty:
        opp_set.add(move)
        d = bfs_dist(opp_set, me_set, opp_start, opp_end)
        opp_set.remove(move)
        if d == 0:
            return move
            
    # 3. Opening Move
    if not me and not opp:
        return (SIZE // 2, SIZE // 2)
    
    # 4. Alpha-Beta Search
    # Evaluation function
    def evaluate():
        m_d = bfs_dist(me_set, opp_set, my_start, my_end)
        o_d = bfs_dist(opp_set, me_set, opp_start, opp_end)
        
        if m_d == 0: return 10000
        if o_d == 0: return -10000
        if m_d == float('inf'): return -10000
        if o_d == float('inf'): return 10000
        
        return (o_d * 10) - (m_d * 10)

    # Generate candidates (moves near existing stones)
    candidates = set()
    if not me and not opp:
        candidates.add((SIZE//2, SIZE//2))
    else:
        for r, c in me:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                    candidates.add((nr, nc))
        for r, c in opp:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                    candidates.add((nr, nc))
    
    if not candidates:
        candidates = set(all_empty) # Fallback

    # Sort candidates by a greedy heuristic to improve pruning
    def score_move(move):
        me_set.add(move)
        score = evaluate()
        me_set.remove(move)
        return score

    sorted_candidates = sorted(list(candidates), key=score_move, reverse=True)
    
    # Limit branching factor to save time
    search_moves = sorted_candidates[:15] 

    best_move = search_moves[0] if search_moves else all_empty[0]
    
    def alphabeta(depth, alpha, beta, maximizing_player):
        if time.time() - start_time > 0.8:
            return evaluate(), None

        if depth == 0:
            return evaluate(), None
        
        # Generate local candidates for recursion
        local_candidates = set()
        # Optimization: Only consider neighbors of current stones at this node
        # To keep it simple and fast, we use the passed 'search_moves' only at root?
        # No, recursive nodes should ideally re-generate relevant neighbors.
        # However, re-calculating neighbors every node is costly in Python.
        # We use a simplified candidate generation: neighbors of stones.
        
        current_me = me_set
        current_opp = opp_set
        
        sources = current_me.union(current_opp)
        for r, c in sources:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in current_me and (nr, nc) not in current_opp:
                    local_candidates.add((nr, nc))
        
        if not local_candidates:
            return evaluate(), None
            
        moves = list(local_candidates)
        
        # Simple move ordering for inner nodes: center preference or random to avoid overhead
        # Actually, no sorting is faster for inner nodes if BFS is expensive.
        
        best_val = float('-inf') if maximizing_player else float('inf')
        best_m = None
        
        if maximizing_player:
            for move in moves:
                me_set.add(move)
                val, _ = alphabeta(depth - 1, alpha, beta, False)
                me_set.remove(move)
                
                if val > best_val:
                    best_val = val
                    best_m = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_m
        else:
            for move in moves:
                opp_set.add(move)
                val, _ = alphabeta(depth - 1, alpha, beta, True)
                opp_set.remove(move)
                
                if val < best_val:
                    best_val = val
                    best_m = move
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_m

    # Run search with depth 2
    # Depth 2 = My move, Opp move, Evaluate.
    _, move = alphabeta(2, float('-inf'), float('inf'), True)
    
    if move:
        return move
        
    return best_move
