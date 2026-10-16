
import random
from typing import Optional

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Battleship targeting policy using hunt/target mode.
    """
    n = len(board)
    
    # Find all hits and classify them
    hits = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # Check if we have any unsunk ships (hits that need follow-up)
    target_mode_shots = get_target_mode_shots(board, hits, n)
    
    if target_mode_shots:
        # Target mode: we have hits to follow up on
        return choose_best_target(target_mode_shots, board, n)
    else:
        # Hunt mode: look for new ships
        return hunt_mode(board, n)


def get_target_mode_shots(board: list[list[int]], hits: list[tuple[int, int]], n: int) -> list[tuple[int, int]]:
    """
    Find cells adjacent to hits that could be part of unsunk ships.
    Prioritize cells that are in line with multiple hits.
    """
    candidates = []
    
    for r, c in hits:
        # Check all 4 directions
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                # Calculate priority based on alignment with other hits
                priority = calculate_priority(nr, nc, hits, board, n)
                candidates.append(((nr, nc), priority))
    
    # Sort by priority (higher is better)
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [pos for pos, _ in candidates]


def calculate_priority(r: int, c: int, hits: list[tuple[int, int]], board: list[list[int]], n: int) -> int:
    """
    Calculate priority for a target cell based on:
    - Number of adjacent hits
    - Whether hits form a line through this cell
    """
    priority = 0
    
    # Count adjacent hits
    adjacent_hits = 0
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 1:
            adjacent_hits += 1
    
    priority += adjacent_hits * 100
    
    # Check if this forms a line with hits
    # Horizontal line
    h_count = 1  # include this cell
    for dc in [1, -1]:
        nc = c + dc
        while 0 <= nc < n and board[r][nc] == 1:
            h_count += 1
            nc += dc
    
    # Vertical line
    v_count = 1
    for dr in [1, -1]:
        nr = r + dr
        while 0 <= nr < n and board[nr][c] == 1:
            v_count += 1
            nr += dr
    
    priority += max(h_count, v_count) * 10
    
    return priority


def choose_best_target(candidates: list[tuple[int, int]], board: list[list[int]], n: int) -> tuple[int, int]:
    """
    Choose the best target from candidates.
    """
    if candidates:
        return candidates[0]
    return hunt_mode(board, n)


def hunt_mode(board: list[list[int]], n: int) -> tuple[int, int]:
    """
    Hunt for new ships using a parity pattern optimized for remaining ships.
    """
    # Get all available cells
    available = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                available.append((r, c))
    
    if not available:
        # Should never happen, but return something valid
        return (0, 0)
    
    # Calculate remaining ship lengths to determine parity
    total_cells = n * n
    fired_cells = sum(1 for r in range(n) for c in range(n) if board[r][c] != 0)
    hit_cells = sum(1 for r in range(n) for c in range(n) if board[r][c] == 1)
    
    # Use checkerboard pattern for efficiency (smallest ship is 2)
    checkerboard = [(r, c) for r, c in available if (r + c) % 2 == 0]
    
    if checkerboard:
        # Use probability density to choose best cell
        best_cell = max(checkerboard, key=lambda pos: calculate_hunt_priority(pos, board, n))
        return best_cell
    
    # Fallback: choose from all available
    best_cell = max(available, key=lambda pos: calculate_hunt_priority(pos, board, n))
    return best_cell


def calculate_hunt_priority(pos: tuple[int, int], board: list[list[int]], n: int) -> float:
    """
    Calculate priority for a cell in hunt mode based on:
    - Number of possible ship placements through this cell
    - Distance from edges (central cells often have higher probability)
    """
    r, c = pos
    ship_lengths = [5, 4, 3, 3, 2]
    
    priority = 0.0
    
    # Count how many ship placements are possible through this cell
    for length in ship_lengths:
        # Horizontal placements
        for start_c in range(max(0, c - length + 1), min(n - length + 1, c + 1)):
            if can_place_ship(board, r, start_c, r, start_c + length - 1, n):
                priority += 1
        
        # Vertical placements
        for start_r in range(max(0, r - length + 1), min(n - length + 1, r + 1)):
            if can_place_ship(board, start_r, c, start_r + length - 1, c, n):
                priority += 1
    
    # Small bonus for central cells
    center_distance = abs(r - n//2) + abs(c - n//2)
    priority += (n - center_distance) * 0.1
    
    return priority


def can_place_ship(board: list[list[int]], r1: int, c1: int, r2: int, c2: int, n: int) -> bool:
    """
    Check if a ship could potentially be placed from (r1,c1) to (r2,c2).
    Returns False if any cell is a known miss.
    """
    if r1 == r2:  # Horizontal
        for c in range(c1, c2 + 1):
            if board[r1][c] == -1:
                return False
    else:  # Vertical
        for r in range(r1, r2 + 1):
            if board[r][c1] == -1:
                return False
    return True
