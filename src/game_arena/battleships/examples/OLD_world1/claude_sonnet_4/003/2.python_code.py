
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Get all unfired positions
    unfired = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    
    if not unfired:
        return (0, 0)  # Shouldn't happen in valid game
    
    # Get all hit positions that are not part of a sunk ship
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    
    # Find unsunk ship segments
    unsunk_hits = []
    for hit in hits:
        if not is_ship_sunk(board, hit):
            unsunk_hits.append(hit)
    
    if unsunk_hits:
        # Target adjacent to unsunk hits
        target = find_best_adjacent_target(board, unsunk_hits)
        if target:
            return target
    
    # No unsunk hits, use hunt mode with probability density
    return hunt_mode(board, unfired)

def is_ship_sunk(board: List[List[int]], hit_pos: Tuple[int, int]) -> bool:
    """Check if the ship containing this hit is completely sunk"""
    r, c = hit_pos
    ship_cells = get_ship_cells(board, r, c)
    
    # Check if all cells of this ship segment have adjacent misses or edges
    for sr, sc in ship_cells:
        # Check all 4 directions for this ship cell
        has_unresolved_direction = False
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = sr + dr, sc + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                if board[nr][nc] == 0:  # Unfired cell adjacent to hit
                    has_unresolved_direction = True
                    break
        
        if has_unresolved_direction:
            return False
    
    return True

def get_ship_cells(board: List[List[int]], start_r: int, start_c: int) -> List[Tuple[int, int]]:
    """Get all connected hit cells forming a ship segment"""
    ship_cells = [(start_r, start_c)]
    visited = {(start_r, start_c)}
    queue = [(start_r, start_c)]
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < 10 and 0 <= nc < 10 and 
                (nr, nc) not in visited and board[nr][nc] == 1):
                visited.add((nr, nc))
                ship_cells.append((nr, nc))
                queue.append((nr, nc))
    
    return ship_cells

def find_best_adjacent_target(board: List[List[int]], unsunk_hits: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Find the best adjacent cell to target for unsunk ships"""
    candidates = []
    
    for r, c in unsunk_hits:
        ship_cells = get_ship_cells(board, r, c)
        
        # If ship has multiple cells, prioritize continuing the line
        if len(ship_cells) > 1:
            # Find the orientation and extend from ends
            ship_cells.sort()
            
            # Check if horizontal or vertical
            if len(set(cell[0] for cell in ship_cells)) == 1:  # Horizontal
                row = ship_cells[0][0]
                min_col = min(cell[1] for cell in ship_cells)
                max_col = max(cell[1] for cell in ship_cells)
                
                # Try extending from both ends
                for col in [min_col - 1, max_col + 1]:
                    if 0 <= col < 10 and board[row][col] == 0:
                        candidates.append((row, col))
            
            elif len(set(cell[1] for cell in ship_cells)) == 1:  # Vertical
                col = ship_cells[0][1]
                min_row = min(cell[0] for cell in ship_cells)
                max_row = max(cell[0] for cell in ship_cells)
                
                # Try extending from both ends
                for row in [min_row - 1, max_row + 1]:
                    if 0 <= row < 10 and board[row][col] == 0:
                        candidates.append((row, col))
        
        # Add all adjacent cells for single hits or as backup
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                candidates.append((nr, nc))
    
    if candidates:
        return random.choice(list(set(candidates)))  # Remove duplicates and pick randomly
    
    return None

def hunt_mode(board: List[List[int]], unfired: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Hunt mode using probability density for ship placement"""
    ship_sizes = [5, 4, 3, 3, 2]
    
    # Calculate probability for each unfired cell
    probabilities = {}
    
    for r, c in unfired:
        prob = 0
        for ship_size in ship_sizes:
            # Check horizontal placements
            for start_col in range(max(0, c - ship_size + 1), min(10 - ship_size + 1, c + 1)):
                if can_place_ship(board, r, start_col, ship_size, horizontal=True):
                    prob += 1
            
            # Check vertical placements
            for start_row in range(max(0, r - ship_size + 1), min(10 - ship_size + 1, r + 1)):
                if can_place_ship(board, start_row, c, ship_size, horizontal=False):
                    prob += 1
        
        probabilities[(r, c)] = prob
    
    # Use checkerboard pattern as tiebreaker for early game
    if len(unfired) > 70:  # Early game
        checkerboard_cells = [pos for pos in unfired if (pos[0] + pos[1]) % 2 == 0]
        if checkerboard_cells:
            unfired = checkerboard_cells
    
    # Find cells with maximum probability
    if probabilities:
        max_prob = max(probabilities[pos] for pos in unfired if pos in probabilities)
        best_cells = [pos for pos in unfired if probabilities.get(pos, 0) == max_prob]
        return random.choice(best_cells)
    
    return random.choice(unfired)

def can_place_ship(board: List[List[int]], start_r: int, start_c: int, size: int, horizontal: bool) -> bool:
    """Check if a ship can be placed at the given position"""
    for i in range(size):
        if horizontal:
            r, c = start_r, start_c + i
        else:
            r, c = start_r + i, start_c
        
        if not (0 <= r < 10 and 0 <= c < 10):
            return False
        
        # Can't place on known misses or hits
        if board[r][c] != 0:
            return False
    
    return True
