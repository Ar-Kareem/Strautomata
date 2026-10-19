
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opponent_set = set(opponent)
    
    # If no stones, take center
    if not me and not opponent:
        return (10, 10)
    
    # Get all empty positions
    empty_positions = []
    for row in range(1, 20):
        for col in range(1, 20):
            if (row, col) not in me_set and (row, col) not in opponent_set:
                empty_positions.append((row, col))
    
    # If no empty positions, pass
    if not empty_positions:
        return (0, 0)
    
    # Basic scoring function
    def score_position(row, col):
        score = 0
        
        # Prefer center positions
        center_distance = abs(row - 10) + abs(col - 10)
        score -= center_distance * 0.5
        
        # Prefer positions near existing stones (for connectivity)
        nearby_stones = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if (r, c) in me_set:
                    nearby_stones += 1
        score += nearby_stones * 2
        
        # Prefer positions that are not immediately adjacent to opponent stones
        adjacent_opponent = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if (r, c) in opponent_set:
                    adjacent_opponent += 1
        score -= adjacent_opponent * 0.5
        
        # Prefer positions that can create eyes or connect to existing groups
        # (Simplified eye consideration)
        if (row, col) in [(5,5), (5,15), (15,5), (15,15)]:
            score += 1  # Prefer corners if no better option
            
        return score
    
    # Score all empty positions
    scores = []
    for pos in empty_positions:
        scores.append((score_position(pos[0], pos[1]), pos))
    
    # Sort by score in descending order
    scores.sort(reverse=True)
    
    # Return the best position
    if scores:
        return scores[0][1]
    
    # Fallback: pass if no position found to be better
    return (0, 0)
