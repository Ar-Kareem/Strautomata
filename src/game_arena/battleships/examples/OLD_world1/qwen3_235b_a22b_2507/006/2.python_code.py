
import random
from typing import List, Tuple, Set, Dict, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Smart Battleship targeting policy that combines:
    - Hit detection and follow-up (targeting adjacent cells when a hit is found)
    - Probability-based targeting using ship fitting analysis
    - Avoidance of already fired positions
    
    Args:
        board: 10x10 grid with values -1 (miss), 0 (unknown), 1 (hit)
    
    Returns:
        (row, col) coordinates to fire at
    """
    n = 10
    ships = [5, 4, 3, 3, 2]  # Ship lengths to find
    
    # Find all hits that haven't been fully surrounded by checked positions
    hits = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # If we have hits, try to extend in likely directions
    if hits:
        # Group hits that are connected (same ship)
        ship_segments = group_hits(hits)
        
        # Try to extend from existing hit groups
        for segment in ship_segments:
            target = try_extend_ship(segment, board)
            if target:
                return target
    
    # No promising extensions, use probability-based targeting
    probabilities = calculate_probabilities(board, ships)
    
    # Find all unexplored cells
    candidates = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:  # Unknown cell
                candidates.append(((r, c), probabilities[r][c]))
    
    if not candidates:
        # Fallback: should not happen in normal gameplay
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    return (r, c)
    
    # Sort by probability descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Add slight randomness to avoid predictable patterns
    # Take one of the top 5 options with weighted random selection
    top_candidates = candidates[:min(5, len(candidates))]
    if len(top_candidates) == 1:
        return top_candidates[0][0]
    
    # Extract positions and weights
    positions = [pos for pos, prob in top_candidates]
    weights = [prob for pos, prob in top_candidates]
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    else:
        weights = [1.0 / len(weights)] * len(weights)
    
    # Choose based on weights
    choice = random.choices(positions, weights=weights, k=1)[0]
    return choice

def group_hits(hits: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
    """Group connected hits into potential ship segments."""
    if not hits:
        return []
    
    # Use union-find to group connected hits
    parent = {hit: hit for hit in hits}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        parent[find(x)] = find(y)
    
    # Connect hits that are adjacent
    for i, hit1 in enumerate(hits):
        for hit2 in hits[i+1:]:
            r1, c1 = hit1
            r2, c2 = hit2
            # Check if adjacent (horizontally or vertically)
            if (abs(r1 - r2) + abs(c1 - c2) == 1):
                union(hit1, hit2)
    
    # Group by root parent
    groups = {}
    for hit in hits:
        root = find(hit)
        if root not in groups:
            groups[root] = []
        groups[root].append(hit)
    
    return list(groups.values())

def try_extend_ship(segment: List[Tuple[int, int]], board: List[List[int]]) -> Optional[Tuple[int, int]]:
    """Try to extend a ship segment in logical directions."""
    n = 10
    
    # Sort the segment to determine orientation
    if len(segment) == 1:
        # Single hit - check all four directions
        r, c = segment[0]
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)  # Add randomness
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                return (nr, nc)
        return None
    
    # Multiple hits - determine primary axis
    segment_sorted_h = sorted(segment, key=lambda x: x[1])  # sort by col
    segment_sorted_v = sorted(segment, key=lambda x: x[0])  # sort by row
    
    # Check if horizontal (same row)
    if all(r == segment[0][0] for r, c in segment):
        # Horizontal ship
        min_c, max_c = segment_sorted_h[0][1], segment_sorted_h[-1][1]
        # Try extending left
        if min_c > 0 and board[segment[0][0]][min_c - 1] == 0:
            return (segment[0][0], min_c - 1)
        # Try extending right
        if max_c < n - 1 and board[segment[0][0]][max_c + 1] == 0:
            return (segment[0][0], max_c + 1)
    
    # Check if vertical (same col)
    elif all(c == segment[0][1] for r, c in segment):
        # Vertical ship
        min_r, max_r = segment_sorted_v[0][0], segment_sorted_v[-1][0]
        # Try extending up
        if min_r > 0 and board[min_r - 1][segment[0][1]] == 0:
            return (min_r - 1, segment[0][1])
        # Try extending down
        if max_r < n - 1 and board[max_r + 1][segment[0][1]] == 0:
            return (max_r + 1, segment[0][1])
    
    return None

def calculate_probabilities(board: List[List[int]], ships: List[int]) -> List[List[float]]:
    """Calculate probability of ship occupation for each cell."""
    n = 10
    probabilities = [[0.0 for _ in range(n)] for _ in range(n)]
    
    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue  # Only calculate for unknown cells
                
            # Count how many ways each ship can be placed covering (r,c)
            total_fits = 0
            for ship_len in ships:
                # Horizontal placements
                for offset in range(ship_len):
                    start_c = c - offset
                    if start_c >= 0 and start_c + ship_len <= n:
                        # Check if ship fits horizontally
                        fits = True
                        for k in range(ship_len):
                            if board[r][start_c + k] == -1:  # Miss
                                fits = False
                                break
                            if k != offset and board[r][start_c + k] == 1:  # Another hit not at target
                                # Check if that hit is isolated or part of a pattern
                                has_adjacent = False
                                for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                                    ar, ac = r + dr, start_c + k + dc
                                    if (0 <= ar < n and 0 <= ac < n and 
                                        (ar, ac) != (r, c) and board[ar][ac] == 1):
                                        has_adjacent = True
                                        break
                                if not has_adjacent:
                                    fits = False
                                    break
                        if fits:
                            total_fits += 1
                
                # Vertical placements
                for offset in range(ship_len):
                    start_r = r - offset
                    if start_r >= 0 and start_r + ship_len <= n:
                        # Check if ship fits vertically
                        fits = True
                        for k in range(ship_len):
                            if board[start_r + k][c] == -1:  # Miss
                                fits = False
                                break
                            if k != offset and board[start_r + k][c] == 1:  # Another hit not at target
                                # Check if that hit is isolated or part of a pattern
                                has_adjacent = False
                                for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                                    ar, ac = start_r + k + dr, c + dc
                                    if (0 <= ar < n and 0 <= ac < n and 
                                        (ar, ac) != (r, c) and board[ar][ac] == 1):
                                        has_adjacent = True
                                        break
                                if not has_adjacent:
                                    fits = False
                                    break
                        if fits:
                            total_fits += 1
            
            probabilities[r][c] = float(total_fits)
    
    return probabilities
