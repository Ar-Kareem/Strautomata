
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Build set of occupied cells for quick lookup
    occupied = set(me) | set(opp)
    
    # Define neighbor offsets for hex grid
    # For cell (i, j), neighbors are:
    # (i-1, j), (i-1, j+1)
    # (i, j-1), (i, j+1)
    # (i+1, j-1), (i+1, j)
    neighbors_offsets = [
        (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0)
    ]
    
    def get_neighbors(r, c):
        """Return all valid hex neighbors of (r, c)"""
        for dr, dc in neighbors_offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 10 and 0 <= nc <= 10:
                yield (nr, nc)
    
    def bfs_connects(starts, ends):
        """Check if any stone in `starts` can reach any stone in `ends` using BFS"""
        if not starts:
            return False
        visited = set(starts)
        queue = deque(starts)
        
        while queue:
            r, c = queue.popleft()
            if (r, c) in ends:
                return True
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and (nr, nc) in occupied:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False
    
    def get_edge_cells(color):
        """Return set of edge cells for the given color"""
        if color == 'b':  # Black: top to bottom
            return {(0, j) for j in range(11)} | {(10, j) for j in range(11)}
        else:  # White: left to right
            return {(i, 0) for i in range(11)} | {(i, 10) for i in range(11)}
    
    def count_adjacent_friends(r, c, player_stones):
        """Count how many of the 6 neighbors are occupied by player"""
        return sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in player_stones)
    
    def is_imminent_loss(color):
        """Check if opponent is one move away from winning"""
        opp_stones = set(opp)
        target_edges = get_edge_cells(color)
        
        # Try placing a stone at each empty cell and see if opponent would win
        for r in range(11):
            for c in range(11):
                if (r, c) in occupied:
                    continue
                # Simulate opponent placing here
                opp_stones.add((r, c))
                if bfs_connects(opp_stones & target_edges, opp_stones & target_edges):
                    # Opponent would connect if they play here
                    opp_stones.remove((r, c))
                    return (r, c)
                opp_stones.remove((r, c))
        return None
    
    # First, check if opponent has an imminent win -- block it
    blocking_move = is_imminent_loss('b' if color == 'w' else 'w')
    if blocking_move is not None:
        return blocking_move
    
    # Define target edges for current player
    target_edges = get_edge_cells(color)
    player_stones = set(me)
    
    # If we are the first to move, play in the center for maximum influence
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    
    # If we have no stones yet, and opponent played somewhere, try to mirror or take center
    if len(me) == 0:
        # Try to take center if available
        if (5, 5) not in occupied:
            return (5, 5)
        # Else, take a symmetric position if opponent played on edge
        op = opp[0]
        # For white (left-right), mirror vertically if opponent is on left edge
        if color == 'w' and op[1] == 0:
            return (op[0], 10)
        # For black (top-bottom), mirror horizontally if opponent is on top edge
        elif color == 'b' and op[0] == 0:
            return (10, op[1])
        # Else take a good neighbor of opponent's move
        for nr, nc in get_neighbors(op[0], op[1]):
            if (nr, nc) not in occupied:
                return (nr, nc)
    
    # Evaluate empty cells for the best move
    best_score = -1
    best_move = None
    
    # Heuristic scoring function
    def evaluate_move(r, c):
        score = 0
        # Bonus for connecting to own edge
        if (r, c) in target_edges:
            score += 5
        
        # Count adjacent friendly stones
        adj_friends = count_adjacent_friends(r, c, player_stones)
        score += adj_friends * 3
        
        # Proximity to opponent's stones (penalize being isolated)
        adj_opp = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in set(opp))
        score -= adj_opp * 0.5
        
        # Prefer central positions
        center_dist = abs(r - 5) + abs(c - 5)
        score += (10 - center_dist) * 0.2
        
        # If this move could create a bridge across a gap, give bonus
        # Check connectivity to both edges (if we have stones near both)
        # This is a simplified version: if we already have a stone near one edge,
        # and this move connects to the other edge or a stone near it, boost score
        if adj_friends > 0:
            # Simulate adding this stone and see if it helps connect (BFS)
            test_stones = player_stones | {(r, c)}
            test_edges = test_stones & target_edges
            if len(test_edges) > 0 and bfs_connects(test_edges, test_edges):
                score += 15  # Winning move
            else:
                # Still potentially useful: check if it connects two components
                # We'll do a BFS with this new stone to see if it links multiple edge regions
                # Use BFS from all stones to see if any path exists after this move
                if bfs_connects(test_stones & target_edges, test_stones & target_edges):
                    score += 8

        return score
    
    # Score each empty cell
    candidates = []
    for r in range(11):
        for c in range(11):
            if (r, c) not in occupied:
                score = evaluate_move(r, c)
                candidates.append((score, r, c))
    
    # Sort by score descending
    candidates.sort(reverse=True)
    
    # Return the highest scoring move
    if candidates:
        return (candidates[0][1], candidates[0][2])
    
    # Fallback: should not happen since there's always at least one empty cell
    for r in range(11):
        for c in range(11):
            if (r, c) not in occupied:
                return (r, c)
    
    # If somehow no move found, raise error (should never reach here)
    raise RuntimeError("No legal move available")
