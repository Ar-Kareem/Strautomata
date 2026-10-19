
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy that combines:
    1. Hunt mode: Probabilistic targeting based on ship placement possibilities
    2. Target mode: When a hit is found, systematically destroy the ship
    """
    n = len(board)
    ships = [5, 4, 3, 3, 2]
    
    # Find all hits and determine which ships are still alive
    hits = []
    misses = []
    unknowns = []
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == -1:
                misses.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))
    
    # Target mode: If we have hits, try to sink the ship
    if hits:
        # Find isolated hits (not part of a line yet) or end of lines
        target = find_best_target(board, hits, n)
        if target:
            return target
    
    # Hunt mode: Use probability density for ship placements
    prob_map = calculate_probability_map(board, ships, n)
    
    # Find cell with highest probability
    max_prob = -1
    best_cells = []
    
    for r, c in unknowns:
        if prob_map[r][c] > max_prob:
            max_prob = prob_map[r][c]
            best_cells = [(r, c)]
        elif prob_map[r][c] == max_prob:
            best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback: random unknown cell
    return random.choice(unknowns)


def find_best_target(board, hits, n):
    """Find the best cell to target based on existing hits."""
    targets = []
    
    for r, c in hits:
        # Check all 4 directions
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                # Check if this extends a line of hits
                is_extension = False
                opp_r, opp_c = r - dr, c - dc
                if 0 <= opp_r < n and 0 <= opp_c < n and board[opp_r][opp_c] == 1:
                    is_extension = True
                
                # Prioritize extensions of existing lines
                priority = 2 if is_extension else 1
                targets.append((priority, nr, nc))
    
    if targets:
        # Sort by priority (higher first)
        targets.sort(reverse=True)
        best_priority = targets[0][0]
        best_targets = [(r, c) for p, r, c in targets if p == best_priority]
        return random.choice(best_targets)
    
    return None


def calculate_probability_map(board, ships, n):
    """Calculate probability map based on possible ship placements."""
    prob_map = np.zeros((n, n), dtype=float)
    
    # Estimate which ships are still alive based on hit count
    total_hits = sum(1 for r in range(n) for c in range(n) if board[r][c] == 1)
    
    # Try to identify sunk ships by finding complete ship patterns
    remaining_ships = estimate_remaining_ships(board, ships, n)
    
    # For each remaining ship, count valid placements through each cell
    for ship_len in remaining_ships:
        # Horizontal placements
        for r in range(n):
            for c in range(n - ship_len + 1):
                if can_place_ship(board, r, c, 0, 1, ship_len):
                    for i in range(ship_len):
                        prob_map[r][c + i] += 1
        
        # Vertical placements
        for r in range(n - ship_len + 1):
            for c in range(n):
                if can_place_ship(board, r, c, 1, 0, ship_len):
                    for i in range(ship_len):
                        prob_map[r + i][c] += 1
    
    # Zero out known cells
    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                prob_map[r][c] = 0
    
    return prob_map


def can_place_ship(board, r, c, dr, dc, length):
    """Check if a ship of given length can be placed at position."""
    hit_count = 0
    
    for i in range(length):
        nr, nc = r + i * dr, c + i * dc
        if board[nr][nc] == -1:  # Miss - can't place here
            return False
        if board[nr][nc] == 1:  # Hit
            hit_count += 1
    
    # Ship placement is valid (all cells are 0 or 1, not -1)
    return True


def estimate_remaining_ships(board, ships, n):
    """Estimate which ships are still in play."""
    # Simple heuristic: assume all ships are still active
    # A more sophisticated approach would identify complete sunk ships
    # For now, return all ships
    return ships.copy()
