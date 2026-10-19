
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Precompute hexagonal neighbors: for cell (i, j), the 6 neighbors
    # In a hex grid with axial coordinates, but here we use (row, col)
    # For (i, j), neighbors are:
    # (i-1, j), (i-1, j+1)   -- top row
    # (i, j-1), (i, j+1)     -- same row
    # (i+1, j-1), (i+1, j)   -- bottom row
    # Note: Avoid (i-1, j-1) and (i+1, j+1) as per problem spec
    neighbors_offsets = [
        (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0)
    ]
    
    # Convert to sets for O(1) lookup
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    # Helper: get valid neighbors
    def get_neighbors(r, c):
        for dr, dc in neighbors_offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 10 and 0 <= nc <= 10:
                yield (nr, nc)
    
    # Check if a move wins immediately for me
    def is_winning_move(r, c, color):
        if (r, c) in occupied:
            return False
        # Temporarily place our stone
        temp_me = me_set | {(r, c)}
        return has_path(temp_me, color)
    
    # BFS to check if there's a winning path
    def has_path(stones, color):
        if color == 'b':
            # Black connects top (row 0) to bottom (row 10)
            start_edges = {(r, c) for r, c in stones if r == 0}
            target_edges = {(r, c) for r, c in stones if r == 10}
            if start_edges & target_edges:  # already connected
                return True
            if not start_edges:
                return False
            visited = set(start_edges)
            queue = deque(start_edges)
            while queue:
                r, c = queue.popleft()
                if r == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
        else:  # color == 'w'
            # White connects left (col 0) to right (col 10)
            start_edges = {(r, c) for r, c in stones if c == 0}
            target_edges = {(r, c) for r, c in stones if c == 10}
            if start_edges & target_edges:
                return True
            if not start_edges:
                return False
            visited = set(start_edges)
            queue = deque(start_edges)
            while queue:
                r, c = queue.popleft()
                if c == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False

    # Check for immediate win
    for r in range(11):
        for c in range(11):
            if (r, c) not in occupied:
                if is_winning_move(r, c, color):
                    return (r, c)
    
    # Check for immediate opponent win and block it
    opp_color = 'w' if color == 'b' else 'b'
    for r in range(11):
        for c in range(11):
            if (r, c) not in occupied:
                if is_winning_move(r, c, opp_color):
                    return (r, c)

    # Evaluate moves by connectivity potential and edge proximity
    # Use a scoring function: higher score = better move
    def evaluate_move(r, c):
        score = 0
        
        # 1. Distance to edge (favor moves near target edge)
        if color == 'b':
            dist_to_top = r
            dist_to_bottom = 10 - r
            # Favor being close to either edge (but more towards bottom if middle)
            score += max(dist_to_top, dist_to_bottom) * 0.1  # small incentive
            # But also prefer being at critical positions
            if r == 0 or r == 10:
                score += 5
            if r == 5:  # center row
                score += 3
        else: # color == 'w'
            dist_to_left = c
            dist_to_right = 10 - c
            score += max(dist_to_left, dist_to_right) * 0.1
            if c == 0 or c == 10:
                score += 5
            if c == 5:  # center column
                score += 3
        
        # 2. Number of our stones adjacent (connection potential)
        my_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                my_neighbors += 1
        score += my_neighbors * 2
        
        # 3. Number of opponent stones adjacent (threat/blocking potential)
        opp_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                opp_neighbors += 1
        score -= opp_neighbors * 1.5  # penalize adjacent to opponent (unless blocking)
        
        # 4. Estimate connectivity value using BFS from edges (lightweight)
        # Simulate adding this stone and check connectivity components
        temp_me = me_set | {(r, c)}
        if color == 'b':
            # Count reachable from top and bottom
            visited = set()
            queue = deque()
            # Start from top edge stones
            for sr, sc in temp_me:
                if sr == 0:
                    queue.append((sr, sc))
                    visited.add((sr, sc))
            while queue:
                cr, cc = queue.popleft()
                for nr, nc in get_neighbors(cr, cc):
                    if (nr, nc) in temp_me and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            # Count how many bottom stones are connected
            if any(r == 10 and (r, c) in visited for r, c in temp_me):
                score += 10  # connected to bottom
            else:
                # Add bonus for how many bottom stones we can reach
                bottom_reached = sum(1 for sr, sc in temp_me if sr == 10 and (sr, sc) in visited)
                score += bottom_reached * 2
        else:  # white
            visited = set()
            queue = deque()
            for sr, sc in temp_me:
                if sc == 0:
                    queue.append((sr, sc))
                    visited.add((sr, sc))
            while queue:
                cr, cc = queue.popleft()
                for nr, nc in get_neighbors(cr, cc):
                    if (nr, nc) in temp_me and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            if any(c == 10 and (r, c) in visited for r, c in temp_me):
                score += 10
            else:
                right_reached = sum(1 for sr, sc in temp_me if sc == 10 and (sr, sc) in visited)
                score += right_reached * 2
        
        # 5. Favor moves that complete a bridge or link two components
        # Count how many connected components we have (lightweight approximation)
        # We'll do a simple BFS to see how many components we have and if this move connects two
        if len(me_set) > 1:
            # Create a graph of our stones
            components = []
            visited_components = set()
            for sr, sc in me_set:
                if (sr, sc) not in visited_components:
                    comp = set()
                    queue = deque([(sr, sc)])
                    visited_components.add((sr, sc))
                    comp.add((sr, sc))
                    while queue:
                        cr, cc = queue.popleft()
                        for nr, nc in get_neighbors(cr, cc):
                            if (nr, nc) in me_set and (nr, nc) not in visited_components:
                                visited_components.add((nr, nc))
                                queue.append((nr, nc))
                                comp.add((nr, nc))
                    components.append(comp)
            
            # Check if this move connects two components
            connected_components = 0
            for comp in components:
                if any((nr, nc) in comp for nr, nc in get_neighbors(r, c)):
                    connected_components += 1
            
            if connected_components >= 2:
                score += 8  # big bonus for connecting two components
        
        return score
    
    # Candidate moves: all empty cells
    candidates = [(r, c) for r in range(11) for c in range(11) if (r, c) not in occupied]
    
    if not candidates:
        # Edge case: no moves available (shouldn't happen per constraints)
        return (5, 5)
    
    # Rank candidates by score
    best_move = candidates[0]
    best_score = evaluate_move(*best_move)
    
    for move in candidates[1:]:
        score = evaluate_move(*move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
