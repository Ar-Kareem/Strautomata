
import heapq
from typing import List, Tuple, Set, Optional

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    R, C = 11, 11
    me_set = set(me)
    opp_set = set(opp)
    
    # Directions for Hex neighbors (based on prompt description)
    # Neighbors of (r, c) are (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
    NEIGHBORS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

    def get_neighbors(r: int, c: int):
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C:
                yield nr, nc

    # Dijkstra to find shortest path cost and one of the shortest paths
    # Returns (cost, set_of_path_cells)
    def dijkstra(my_stones: Set[Tuple[int, int]], opp_stones: Set[Tuple[int, int]], is_black: bool):
        start_nodes = []
        # Initialize distances with infinity
        dist = [[float('inf')] * C for _ in range(R)]
        parent = [[None] * C for _ in range(R)]
        
        # Black connects Top (row 0) to Bottom (row 10)
        # White connects Left (col 0) to Right (col 10)
        if is_black:
            # Source is row 0
            for c in range(C):
                if (0, c) in opp_stones: continue
                cost = 0 if (0, c) in my_stones else 1
                dist[0][c] = cost
                heapq.heappush(start_nodes, (cost, 0, c))
        else:
            # Source is col 0
            for r in range(R):
                if (r, 0) in opp_stones: continue
                cost = 0 if (r, 0) in my_stones else 1
                dist[r][0] = cost
                heapq.heappush(start_nodes, (cost, r, 0))
        
        target_node = None
        
        while start_nodes:
            d, r, c = heapq.heappop(start_nodes)
            
            if d > dist[r][c]: continue
            
            # Check target
            if is_black:
                if r == R - 1:
                    target_node = (r, c)
                    break
            else:
                if c == C - 1:
                    target_node = (r, c)
                    break
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_stones: continue
                
                weight = 0 if (nr, nc) in my_stones else 1
                nd = d + weight
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    parent[nr][nc] = (r, c)
                    heapq.heappush(start_nodes, (nd, nr, nc))
        
        if target_node is None:
            return float('inf'), set()
            
        # Backtrack to find path cells
        path_cells = set()
        curr = target_node
        while curr is not None:
            path_cells.add(curr)
            r, c = curr
            # Only add empty cells to path set for candidate generation
            # But for distance calc we need the path structure
            curr = parent[r][c]
            
        return dist[target_node[0]][target_node[1]], path_cells

    is_black = (color == 'b')
    
    # Determine empty cells
    all_cells = {(r, c) for r in range(R) for c in range(C)}
    occupied = me_set | opp_set
    empty_cells = list(all_cells - occupied)
    
    # 1. Opening Move
    if not me_set:
        # If we are Black (first move), play center (5,5)
        # If we are White, and center is taken, play adjacent.
        center = (5, 5)
        if center not in opp_set:
            return center
        else:
            # Play an adjacent move
            for dr, dc in NEIGHBORS:
                nr, nc = center[0] + dr, center[1] + dc
                if (nr, nc) not in opp_set:
                    return (nr, nc)

    # Pre-calc initial distances and paths for candidate selection
    d_me, path_me = dijkstra(me_set, opp_set, is_black)
    d_opp, path_opp = dijkstra(opp_set, me_set, not is_black)
    
    # 2. Immediate Win
    # If distance is 0, we have already connected (shouldn't happen)
    # If distance is 1, we can win with one move on the path.
    if d_me == 1:
        # The winning move is the empty cell on the path
        # We can iterate empty cells to find which one reduces distance to 0
        best_move = None
        for r, c in empty_cells:
            # Check if this move wins
            # Temporarily add to me_set
            new_me = me_set | {(r, c)}
            # Check connection simply: if I have a stone at row 10 (black) or col 10 (white) connected to start
            # Simplified: Re-run dijkstra with 0 cost for this stone
            # But easiest: if the path cost was 1, it means there is exactly 1 empty cell separating connections.
            # Placing that cell makes cost 0.
            # We scan the path cells
            if (r, c) in path_me and (r, c) not in me_set:
                 # Validate
                 new_d, _ = dijkstra(new_me, opp_set, is_black)
                 if new_d == 0:
                     return (r, c)
    
    # 3. Candidate Generation
    # Consider neighbors of existing stones, and cells on critical paths
    candidates = set()
    
    # Add neighbors of all stones (local tactics)
    for r, c in (me_set | opp_set):
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in occupied:
                candidates.add((nr, nc))
                
    # Add cells on shortest paths (global strategy)
    for r, c in path_me:
        if (r, c) not in occupied:
            candidates.add((r, c))
    for r, c in path_opp:
        if (r, c) not in occupied:
            candidates.add((r, c))
            
    # If no candidates (empty board start handled above, but just in case), pick center
    if not candidates:
        candidates.add((5, 5))

    # 4. Depth 2 Search (Minimax)
    # We evaluate state by: opp_distance - my_distance
    # We want to maximize this score.
    
    best_score = -float('inf')
    best_move = list(candidates)[0] # Default
    
    # Sort candidates to check potentially better moves first (heuristic optimization)
    # Center-bias
    candidates = sorted(list(candidates), key=lambda x: abs(x[0]-5) + abs(x[1]-5))

    for m1 in candidates:
        # My move
        new_me_1 = me_set | {m1}
        
        # Check immediate win again inside loop (faster check)
        # If placing m1 makes me win, score is inf
        # Dijkstra handles this, but we can shortcut if m1 is on target edge? No, need connectivity.
        
        # Opponent's turn (they try to minimize my advantage / maximize theirs)
        # Opponent moves: we should check their best response.
        # To save time, we can check if opponent has immediate threat (dist 1) and assume they block it?
        # Or just evaluate terminal state after m1?
        # Let's do a full depth-2 if time permits, or just depth 1 evaluation with threat check.
        
        # Current evaluation for m1:
        # Score = d_opp_after - d_me_after
        # If opponent has a winning move (d_opp_after == 1), they will take it.
        # So we must check if our move allows opponent to win immediately.
        
        d_me_1, _ = dijkstra(new_me_1, opp_set, is_black)
        
        # Check opponent's best response
        # For speed, we approximate opponent's best move by looking at their distance reduction or our blocking.
        # But for a robust policy, we simulate opponent's best depth-1 move.
        
        # Opponent tries to minimize (d_opp - d_me), i.e., maximize d_me and minimize d_opp.
        # Wait, score is (d_opp - d_me).
        # Opponent wants score to be low.
        
        opp_candidates = set()
        for r, c in (new_me_1 | opp_set):
             for nr, nc in get_neighbors(r, c):
                 if (nr, nc) not in new_me_1 and (nr, nc) not in opp_set:
                     opp_candidates.add((nr, nc))
        
        # Prune opponent candidates if too many
        if len(opp_candidates) > 20:
            # Pick some relevant ones
            _, opp_path = dijkstra(opp_set, new_me_1, not is_black)
            opp_candidates = {p for p in opp_path if p not in (new_me_1 | opp_set)}
            if not opp_candidates: opp_candidates = {list(occupied)[0]} # fallback, shouldn't happen
        
        min_score_m1 = float('inf')
        
        # If opponent can win immediately (dist 1), they will.
        # Current opp dist with new_me_1 board
        current_opp_d, _ = dijkstra(opp_set, new_me_1, not is_black)
        if current_opp_d == 1:
            # Opponent wins next. This move m1 is bad unless we win first (checked d_me_1).
            # If d_me_1 > 0 and current_opp_d == 1, we lose.
            score = -10000 # Huge penalty
            if score > best_score: # We look for max, so this will be ignored unless all moves lose
                best_score = score
                best_move = m1
            continue

        for m2 in opp_candidates:
            new_opp_2 = opp_set | {m2}
            
            d_me_2, _ = dijkstra(new_me_1, new_opp_2, is_black)
            d_opp_2, _ = dijkstra(new_opp_2, new_me_1, not is_black)
            
            score = d_opp_2 - d_me_2
            
            # Opponent minimizes score
            if score < min_score_m1:
                min_score_m1 = score
                
        # I maximize score
        # Add small random noise or center preference to break ties
        # Using deterministic tie-breaking: distance to center
        tie_breaker = -(abs(m1[0]-5) + abs(m1[1]-5)) * 0.001
        final_score = min_score_m1 + tie_breaker
        
        if final_score > best_score:
            best_score = final_score
            best_move = m1
            
    return best_move
