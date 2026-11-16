
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah policy that combines structure detection with strategic positioning.
    """
    N = len(valid_mask)
    
    # Get valid moves
    valid_moves = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    occupied = set(me + opp)
    valid_moves = [m for m in valid_moves if m not in occupied]
    
    if not valid_moves:
        # Fallback - should never happen
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in occupied:
                    return (r, c)
    
    # Helper functions for hexagonal neighbors
    def get_neighbors(r, c):
        """Get all 6 hexagonal neighbors"""
        neighbors = [
            (r-1, c), (r+1, c),      # same column
            (r, c-1), (r, c+1),      # left and right column
            (r-1, c-1), (r+1, c+1)   # diagonals
        ]
        return [(nr, nc) for nr, nc in neighbors if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]]
    
    def is_corner(r, c):
        """Check if position is a corner of the hexagonal board"""
        corners = [(0, 0), (0, N-1), (N-1, 0), (N-1, N-1)]
        # Additional corners depend on the exact hex shape
        # For a 15x15 representation, we approximate
        if (r, c) in corners:
            return True
        # Check edges for actual corners
        if r == 0 and c in [0, N-1]:
            return True
        if r == N-1 and c in [0, N-1]:
            return True
        return False
    
    def is_edge(r, c):
        """Check if position is on an edge (not corner)"""
        on_boundary = (r == 0 or r == N-1 or c == 0 or c == N-1)
        return on_boundary and not is_corner(r, c)
    
    def get_connected_component(stones, start):
        """Get all stones connected to start position"""
        stones_set = set(stones)
        if start not in stones_set:
            return set()
        
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        while queue:
            curr = queue.popleft()
            for neighbor in get_neighbors(curr[0], curr[1]):
                if neighbor in stones_set and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return visited
    
    def check_win(stones):
        """Check if stones form a winning structure"""
        if len(stones) < 6:
            return False
        
        stones_set = set(stones)
        # Check connected components
        visited_global = set()
        
        for stone in stones:
            if stone not in visited_global:
                component = get_connected_component(stones, stone)
                visited_global.update(component)
                
                # Check for ring, bridge, fork in this component
                if len(component) >= 6:
                    # Simple check - could be enhanced
                    corners_touched = sum(1 for s in component if is_corner(s[0], s[1]))
                    edges_touched = len(set([edge_type(s[0], s[1]) for s in component if is_edge(s[0], s[1])]))
                    
                    if corners_touched >= 2:  # Potential bridge
                        return True
                    if edges_touched >= 3:  # Potential fork
                        return True
        
        return False
    
    def edge_type(r, c):
        """Determine which edge type (for fork detection)"""
        if r == 0:
            return 0
        if r == N-1:
            return 1
        if c == 0:
            return 2
        if c == N-1:
            return 3
        return -1
    
    def score_move(move, my_stones, opp_stones):
        """Score a potential move"""
        r, c = move
        score = 0.0
        
        # Connectivity to own stones
        my_neighbors = sum(1 for n in get_neighbors(r, c) if n in set(my_stones))
        score += my_neighbors * 15
        
        # Blocking opponent
        opp_neighbors = sum(1 for n in get_neighbors(r, c) if n in set(opp_stones))
        score += opp_neighbors * 12
        
        # Strategic positions
        if is_corner(r, c):
            score += 25
        elif is_edge(r, c):
            score += 15
        
        # Center control early game
        center = N // 2
        dist_to_center = abs(r - center) + abs(c - center)
        if len(my_stones) < 10:
            score += (N - dist_to_center) * 2
        
        # Penalize positions too far from action
        if my_stones:
            min_dist = min(abs(r - mr) + abs(c - mc) for mr, mc in my_stones)
            if min_dist > 3:
                score -= min_dist * 5
        
        return score
    
    # Check for immediate win
    for move in valid_moves:
        if check_win(me + [move]):
            return move
    
    # Check for blocking opponent win
    for move in valid_moves:
        if check_win(opp + [move]):
            return move
    
    # Score all moves
    best_move = max(valid_moves, key=lambda m: score_move(m, me, opp))
    return best_move
