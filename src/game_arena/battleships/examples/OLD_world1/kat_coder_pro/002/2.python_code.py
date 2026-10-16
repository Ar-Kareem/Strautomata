import numpy as np
from collections import deque
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Enhanced Battleship targeting policy that combines:
    - Hit expansion with ship constraint validation
    - Probability-based cell weighting
    - Pattern detection for ships of known lengths
    - Entropy-based fallback for unknown areas
    """
    n = 10
    grid = np.array(board, dtype=int)
    unknown_mask = (grid == 0)
    known_mask = ~unknown_mask
    
    # Ship lengths to find (descending order)
    ship_lengths = [5, 4, 3, 3, 2]
    
    # If no hits yet, use probability-based approach
    hit_cells = np.where(grid == 1)
    if len(hit_cells[0]) == 0:
        return _probability_target(grid, ship_lengths)
    
    # Try to extend existing hits intelligently
    for hit_row, hit_col in zip(hit_cells[0], hit_cells[1]):
        target = _expand_from_hit(grid, hit_row, hit_col, ship_lengths)
        if target is not None:
            r, c = target
            if unknown_mask[r, c]:
                return (r, c)
    
    # Fallback to probability-based targeting
    return _probability_target(grid, ship_lengths)

def _expand_from_hit(grid: np.ndarray, hit_r: int, hit_c: int, ship_lengths: List[int]) -> Tuple[int, int]:
    """
    Try to extend from a hit in the most likely direction
    """
    n = grid.shape[0]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # Check possible extensions from this hit
    best_extensions = []
    
    for dr, dc in directions:
        # Check both directions along the same axis
        for step in [1, -1]:
            sr, sc = hit_r + dr * step, hit_c + dc * step
            
            # Check if extension is valid
            if not (0 <= sr < n and 0 <= sc < n):
                continue
            
            if grid[sr, sc] != 0:
                continue
                
            # Check if this extension makes sense given ship constraints
            if _is_valid_extension(grid, hit_r, hit_c, dr, dc, step, ship_lengths):
                best_extensions.append((sr, sc))
    
    # Prefer extensions that continue existing hit lines
    if best_extensions:
        # Sort by preference: continue existing lines, then check ship constraints
        extensions_with_score = []
        for r, c in best_extensions:
            score = _extension_score(grid, r, c, hit_r, hit_c, ship_lengths)
            extensions_with_score.append((score, r, c))
        
        extensions_with_score.sort(reverse=True)
        _, best_r, best_c = extensions_with_score[0]
        return (best_r, best_c)
    
    return None

def _is_valid_extension(grid: np.ndarray, hit_r: int, hit_c: int, dr: int, dc: int, step: int, ship_lengths: List[int]) -> bool:
    """
    Check if extending from hit in direction (dr, dc) by step is valid
    """
    n = grid.shape[0]
    
    # Check the extension cell
    ext_r, ext_c = hit_r + dr * step, hit_c + dc * step
    if not (0 <= ext_r < n and 0 <= ext_c < n):
        return False
    
    if grid[ext_r, ext_c] != 0:
        return False
    
    # Check if extension could reasonably form part of a ship
    # Look for other hits along this line
    line_cells = []
    for i in range(-4, 5):  # Check line of up to 9 cells
        r, c = hit_r + dr * i, hit_c + dc * i
        if 0 <= r < n and 0 <= c < n:
            line_cells.append((r, c, grid[r, c]))
    
    # Count hits along this line
    hits_on_line = sum(1 for _, _, val in line_cells if val == 1)
    
    # If we already have hits, prefer continuing the line
    if hits_on_line > 1:
        return True
    
    # Check ship placement constraints
    return _can_place_ship_here(grid, ext_r, ext_c, dr, dc, ship_lengths)

def _can_place_ship_here(grid: np.ndarray, r: int, c: int, dr: int, dc: int, ship_lengths: List[int]) -> bool:
    """
    Check if a ship could be placed with one end at (r,c) in direction (dr,dc)
    """
    n = grid.shape[0]
    
    # Try each ship length
    for length in ship_lengths:
        valid = True
        max_ship_len = length
        
        # Check if ship of this length can fit
        for i in range(max_ship_len):
            sr, sc = r + dr * i, c + dc * i
            if not (0 <= sr < n and 0 <= sc < n):
                valid = False
                break
            if grid[sr, sc] == -1:  # Hit water
                valid = False
                break
        
        if valid:
            return True
    
    return False

def _extension_score(grid: np.ndarray, r: int, c: int, hit_r: int, hit_c: int, ship_lengths: List[int]) -> float:
    """
    Score how good an extension from hit to (r,c) would be
    """
    score = 0.0
    dr, dc = r - hit_r, c - hit_c
    
    # Prefer continuing straight lines
    if dr != 0 and dc != 0:  # Diagonal - less preferred
        score -= 0.5
    elif dr == 0 or dc == 0:  # Straight line - good
        score += 0.5
    
    # Prefer placing ships near edges (reduces placement options)
    edge_proximity = min(r, c, 9-r, 9-c)
    score += 0.1 * edge_proximity
    
    # Penalize being too close to known hits/water
    for i in range(-2, 3):
        for j in range(-2, 3):
            nr, nc = r + i, c + j
            if 0 <= nr < 10 and 0 <= nc < 10 and (i != 0 or j != 0):
                if grid[nr, nc] == -1:  # Near water
                    score -= 0.1
                elif grid[nr, nc] == 1:  # Near hit
                    score += 0.2
    
    return score

def _probability_target(grid: np.ndarray, ship_lengths: List[int]) -> Tuple[int, int]:
    """
    Compute probability-based targeting using ship placement constraints
    """
    n = grid.shape[0]
    prob_grid = np.zeros_like(grid, dtype=float)
    
    # For each unknown cell, count how many ways each ship can be placed through it
    unknown_positions = np.where(grid == 0)
    
    for r, c in zip(unknown_positions[0], unknown_positions[1]):
        count = 0
        
        # Try horizontal placements
        for length in ship_lengths:
            for offset in range(length):
                start_col = c - offset
                if 0 <= start_col <= n - length:
                    # Check if ship can be placed here
                    if _valid_horizontal_placement(grid, r, start_col, length):
                        count += 1
        
        # Try vertical placements
        for length in ship_lengths:
            for offset in range(length):
                start_row = r - offset
                if 0 <= start_row <= n - length:
                    # Check if ship can be placed here
                    if _valid_vertical_placement(grid, start_row, c, length):
                        count += 1
        
        prob_grid[r, c] = count
    
    # Apply strategic weighting
    prob_grid = _apply_strategic_weights(prob_grid, grid)
    
    # Find the best unknown cell with highest probability
    unknown_mask = (grid == 0)
    if not np.any(unknown_mask):
        # Fallback: should not happen in normal play
        return (0, 0)
    
    # Get the best probability
    best_score = -1
    best_pos = None
    
    for r in range(n):
        for c in range(n):
            if unknown_mask[r, c]:
                score = prob_grid[r, c]
                if score > best_score:
                    best_score = score
                    best_pos = (r, c)
    
    if best_pos is None:
        # Emergency fallback
        for r in range(n):
            for c in range(n):
                if grid[r, c] == 0:
                    return (r, c)
    
    return best_pos

def _valid_horizontal_placement(grid: np.ndarray, row: int, start_col: int, length: int) -> bool:
    """Check if a ship can be placed horizontally at (row, start_col) with given length"""
    for c in range(start_col, start_col + length):
        if grid[row, c] == -1:  # Hit water
            return False
    return True

def _valid_vertical_placement(grid: np.ndarray, start_row: int, col: int, length: int) -> bool:
    """Check if a ship can be placed vertically at (start_row, col) with given length"""
    for r in range(start_row, start_row + length):
        if grid[r, col] == -1:  # Hit water
            return False
    return True

def _apply_strategic_weights(prob_grid: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """
    Apply strategic weighting to probability grid:
    - Prefer edges and center patterns
    - Avoid clustering shots too closely
    - Prefer cells that align with existing hits
    """
    n = grid.shape[0]
    weighted_grid = prob_grid.copy()
    
    # Edge preference: cells near edges are slightly more likely
    for r in range(n):
        for c in range(n):
            edge_dist = min(r, c, n-1-r, n-1-c)
            weighted_grid[r, c] += 0.1 * edge_dist
    
    # Penalize cells too close to known water
    for r in range(n):
        for c in range(n):
            if grid[r, c] == -1:
                # Apply penalty to nearby cells
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        nr, nc = r + i, c + j
                        if 0 <= nr < n and 0 <= nc < n:
                            penalty = 0.2 * (3 - max(abs(i), abs(j)))
                            weighted_grid[nr, nc] -= penalty
    
    # Bonus for alignment with existing hits
    hit_positions = np.where(grid == 1)
    for hr, hc in zip(hit_positions[0], hit_positions[1]):
        for r in range(n):
            for c in range(n):
                if r == hr and abs(c - hc) <= 4:  # Same row
                    weighted_grid[r, c] += 0.3
                if c == hc and abs(r - hr) <= 4:  # Same column
                    weighted_grid[r, c] += 0.3
    
    return weighted_grid