
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Get all unfired positions
    unfired = []
    hits = []
    
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unfired.append((i, j))
            elif board[i][j] == 1:
                hits.append((i, j))
    
    if not unfired:
        return (0, 0)  # Should never happen in normal game
    
    # If we have hits, try to target around them
    if hits:
        target = find_target_around_hits(board, hits)
        if target and target in unfired:
            return target
    
    # Hunt mode - use probability-based targeting
    return hunt_mode(board, unfired)

def find_target_around_hits(board: List[List[int]], hits: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Find unsunk ships (hits that aren't part of a completed ship)
    active_hits = []
    
    for hit in hits:
        if not is_ship_sunk_at_position(board, hit):
            active_hits.append(hit)
    
    if not active_hits:
        return None
    
    # For each active hit, try to find the ship orientation and target accordingly
    for hit in active_hits:
        row, col = hit
        
        # Check if this hit is part of a line of hits
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        
        for dr, dc in directions:
            # Look for consecutive hits in this direction
            consecutive_hits = [(row, col)]
            r, c = row + dr, col + dc
            
            while 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 1:
                consecutive_hits.append((r, c))
                r += dr
                c += dc
            
            # If we found consecutive hits, target the ends
            if len(consecutive_hits) > 1:
                # Try to extend in the same direction
                end_r, end_c = consecutive_hits[-1]
                next_r, next_c = end_r + dr, end_c + dc
                if 0 <= next_r < 10 and 0 <= next_c < 10 and board[next_r][next_c] == 0:
                    return (next_r, next_c)
                
                # Try to extend in the opposite direction
                start_r, start_c = consecutive_hits[0]
                prev_r, prev_c = start_r - dr, start_c - dc
                if 0 <= prev_r < 10 and 0 <= prev_c < 10 and board[prev_r][prev_c] == 0:
                    return (prev_r, prev_c)
        
        # If no line found, target adjacent cells
        for dr, dc in directions:
            new_r, new_c = row + dr, col + dc
            if 0 <= new_r < 10 and 0 <= new_c < 10 and board[new_r][new_c] == 0:
                return (new_r, new_c)
    
    return None

def is_ship_sunk_at_position(board: List[List[int]], pos: Tuple[int, int]) -> bool:
    # Simple heuristic: if a hit is completely surrounded by misses or edges, assume ship is sunk
    # This is not perfect but works reasonably well
    row, col = pos
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # Check if there are any adjacent unfired cells
    for dr, dc in directions:
        new_r, new_c = row + dr, col + dc
        if 0 <= new_r < 10 and 0 <= new_c < 10 and board[new_r][new_c] == 0:
            return False
    
    return True

def hunt_mode(board: List[List[int]], unfired: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Calculate probability map for ship placement
    ship_lengths = [5, 4, 3, 3, 2]
    sunk_ships = estimate_sunk_ships(board)
    remaining_ships = ship_lengths[sunk_ships:]
    
    if not remaining_ships:
        return random.choice(unfired)
    
    probability = [[0 for _ in range(10)] for _ in range(10)]
    
    # For each remaining ship length, calculate placement probabilities
    for ship_length in remaining_ships:
        # Horizontal placements
        for row in range(10):
            for col in range(10 - ship_length + 1):
                if can_place_ship_horizontal(board, row, col, ship_length):
                    for c in range(col, col + ship_length):
                        probability[row][c] += 1
        
        # Vertical placements
        for row in range(10 - ship_length + 1):
            for col in range(10):
                if can_place_ship_vertical(board, row, col, ship_length):
                    for r in range(row, row + ship_length):
                        probability[r][col] += 1
    
    # Find the unfired cell with highest probability
    best_prob = -1
    best_moves = []
    
    for row, col in unfired:
        if probability[row][col] > best_prob:
            best_prob = probability[row][col]
            best_moves = [(row, col)]
        elif probability[row][col] == best_prob:
            best_moves.append((row, col))
    
    if best_moves:
        return random.choice(best_moves)
    else:
        return random.choice(unfired)

def can_place_ship_horizontal(board: List[List[int]], row: int, col: int, length: int) -> bool:
    for c in range(col, col + length):
        if board[row][c] == -1:  # Can't place ship where we know there's water
            return False
    return True

def can_place_ship_vertical(board: List[List[int]], row: int, col: int, length: int) -> bool:
    for r in range(row, row + length):
        if board[r][col] == -1:  # Can't place ship where we know there's water
            return False
    return True

def estimate_sunk_ships(board: List[List[int]]) -> int:
    # Rough estimate based on number of hits
    # This is a simple heuristic
    total_hits = sum(1 for i in range(10) for j in range(10) if board[i][j] == 1)
    
    # Ship lengths are [5, 4, 3, 3, 2], total = 17
    if total_hits >= 17:
        return 5
    elif total_hits >= 15:
        return 4
    elif total_hits >= 12:
        return 3
    elif total_hits >= 9:
        return 2
    elif total_hits >= 5:
        return 1
    else:
        return 0
