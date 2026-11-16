
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Find all unfired positions
    unfired = []
    hits = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                unfired.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))
    
    if not unfired:
        return (0, 0)  # Should not happen in valid game
    
    # Check if we have any hits to follow up on
    if hits:
        target = find_best_target_near_hits(board, hits, unfired)
        if target:
            return target
    
    # No hits to follow up, use hunt mode with parity + density
    return hunt_mode(board, unfired)

def find_best_target_near_hits(board: List[List[int]], hits: List[Tuple[int, int]], unfired: List[Tuple[int, int]]) -> Tuple[int, int]:
    unfired_set = set(unfired)
    
    # Find ship segments (connected components of hits)
    visited = set()
    segments = []
    
    for hit in hits:
        if hit in visited:
            continue
        
        # Find connected component starting from this hit
        segment = []
        stack = [hit]
        
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            segment.append((r, c))
            
            # Check 4-connected neighbors
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in visited:
                    if board[nr][nc] == 1:
                        stack.append((nr, nc))
        
        if segment:
            segments.append(segment)
    
    # For each segment, find the best continuation
    best_targets = []
    
    for segment in segments:
        if len(segment) == 1:
            # Single hit - try all 4 directions
            r, c = segment[0]
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) in unfired_set:
                    best_targets.append((nr, nc))
        else:
            # Multiple hits - determine orientation and extend
            segment.sort()
            
            # Check if horizontal or vertical
            if len(set(r for r, c in segment)) == 1:
                # Horizontal ship
                row = segment[0][0]
                min_col = min(c for r, c in segment)
                max_col = max(c for r, c in segment)
                
                # Try extending left and right
                for col in [min_col - 1, max_col + 1]:
                    if 0 <= col < 10 and (row, col) in unfired_set:
                        best_targets.append((row, col))
            
            elif len(set(c for r, c in segment)) == 1:
                # Vertical ship
                col = segment[0][1]
                min_row = min(r for r, c in segment)
                max_row = max(r for r, c in segment)
                
                # Try extending up and down
                for row in [min_row - 1, max_row + 1]:
                    if 0 <= row < 10 and (row, col) in unfired_set:
                        best_targets.append((row, col))
    
    if best_targets:
        return random.choice(best_targets)
    
    return None

def hunt_mode(board: List[List[int]], unfired: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Use checkerboard parity for initial search
    parity_targets = []
    other_targets = []
    
    for r, c in unfired:
        if (r + c) % 2 == 0:
            parity_targets.append((r, c))
        else:
            other_targets.append((r, c))
    
    # Calculate ship density for remaining targets
    if parity_targets:
        candidates = parity_targets
    else:
        candidates = other_targets
    
    # Score each candidate by potential ship placements
    scored_candidates = []
    
    for r, c in candidates:
        score = calculate_ship_density(board, r, c)
        scored_candidates.append((score, r, c))
    
    # Sort by score (higher is better) and add some randomness
    scored_candidates.sort(reverse=True)
    
    # Pick from top 20% with some randomness
    top_count = max(1, len(scored_candidates) // 5)
    return (scored_candidates[random.randint(0, top_count - 1)][1], 
            scored_candidates[random.randint(0, top_count - 1)][2])

def calculate_ship_density(board: List[List[int]], row: int, col: int) -> float:
    """Calculate how many possible ship placements could include this cell"""
    score = 0.0
    ship_lengths = [5, 4, 3, 3, 2]
    
    for length in ship_lengths:
        # Check horizontal placements
        for start_col in range(max(0, col - length + 1), min(10 - length + 1, col + 1)):
            if can_place_ship(board, row, start_col, length, True):
                score += 1.0
        
        # Check vertical placements  
        for start_row in range(max(0, row - length + 1), min(10 - length + 1, row + 1)):
            if can_place_ship(board, start_row, col, length, False):
                score += 1.0
    
    return score

def can_place_ship(board: List[List[int]], start_row: int, start_col: int, length: int, horizontal: bool) -> bool:
    """Check if a ship of given length can be placed at the position"""
    for i in range(length):
        if horizontal:
            r, c = start_row, start_col + i
        else:
            r, c = start_row + i, start_col
        
        if not (0 <= r < 10 and 0 <= c < 10):
            return False
        
        # Can't place if we know it's water
        if board[r][c] == -1:
            return False
    
    return True
