
import numpy as np
from collections import deque, defaultdict
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    valid_set = set()
    for i in range(15):
        for j in range(15):
            if valid_mask[i][j]:
                valid_set.add((i, j))
    
    # Generate all possible moves
    all_moves = list(valid_set - me_set - opp_set)
    
    if not all_moves:
        return (0, 0)  # Fallback, shouldn't happen in normal gameplay
    
    # Check for immediate win
    for move in all_moves:
        # Simulate placing our stone and check if it creates a win
        new_me = me_set | {move}
        if check_win(new_me, opp_set, move):
            return move
    
    # Check for immediate threat blocking
    for move in all_moves:
        # Simulate opponent placing their stone and check if it creates a win
        new_opp = opp_set | {move}
        if check_win(new_opp, me_set, move):
            return move

    # Heuristic scoring for position evaluation
    def evaluate_position(move):
        row, col = move
        score = 0
        
        # Prefer center positions
        center = (7, 7)
        distance_to_center = abs(row - center[0]) + abs(col - center[1])
        score -= distance_to_center * 0.1
        
        # Prefer positions that create connections
        neighbors = get_hex_neighbors(row, col)
        connected = 0
        for n in neighbors:
            if n in me_set:
                connected += 1
        score += connected * 0.5
        
        # Prefer moves that keep connectivity options
        potential_connections = 0
        for n in neighbors:
            if n in valid_set and n not in me_set and n not in opp_set:
                potential_connections += 1
        score += potential_connections * 0.3
        
        # Avoid positions that would create easy opponent wins (simplified)
        return score
    
    # Score all moves
    scored_moves = [(move, evaluate_position(move)) for move in all_moves]
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Return the highest scoring move
    return scored_moves[0][0]

def get_hex_neighbors(row, col):
    """Get hexagonal neighbors of a position"""
    neighbors = []
    # Hexagonal neighbors: 6 relative positions (up, up-right, down-right, down, down-left, up-left)
    directions = [
        (-1, 0),  # up
        (-1, 1),  # up-right
        (0, 1),   # down-right
        (1, 0),   # down
        (1, -1),  # down-left
        (0, -1)   # up-left
    ]
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 15 and 0 <= new_col < 15:
            neighbors.append((new_row, new_col))
    
    return neighbors

def check_win(me_positions, opp_positions, last_move):
    """Check if placing a stone at last_move creates a win"""
    # This is a simplified win check - in practice this would need to be more sophisticated
    # For ring detection, we'd need to do full connectivity checks
    
    # For now, we do strategic checks only
    return False
