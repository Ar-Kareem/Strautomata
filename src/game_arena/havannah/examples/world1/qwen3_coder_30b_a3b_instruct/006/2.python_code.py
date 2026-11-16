
import numpy as np
import random
from collections import deque
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)
    valid_positions = [(i, j) for i in range(15) for j in range(15) if valid_mask[i][j]]
    
    # Check for immediate winning moves
    for pos in valid_positions:
        if pos in me_set or pos in opp_set:
            continue
        # Temporarily place our stone
        new_me = me_set | {pos}
        if check_win(pos, new_me, opp_set, valid_mask):
            return pos
    
    # Check for blocking opponent's winning move
    for pos in valid_positions:
        if pos in me_set or pos in opp_set:
            continue
        # Temporarily place opponent's stone
        new_opp = opp_set | {pos}
        if check_win(pos, me_set, new_opp, valid_mask):
            return pos
    
    # Otherwise, use heuristic approach
    # Start by focusing on center of board
    center = (7, 7)
    center_neighbors = get_hex_neighbors(center[0], center[1], valid_mask)
    
    # Prefer positions near center with good connectivity
    candidates = []
    
    # Prioritize valid board positions with good connection potential
    for pos in valid_positions:
        connectivity_score = 0
        neighbor_count = 0
        
        # Check hex neighbors
        for neighbor in get_hex_neighbors(pos[0], pos[1], valid_mask):
            if neighbor in me_set:
                connectivity_score += 1
                neighbor_count += 1
            elif neighbor in opp_set:
                neighbor_count += 1
            else:
                # Empty position, could be good for expansion
                connectivity_score += 0.1
        
        # Prefer positions that are not just isolated
        if neighbor_count > 0:
            candidates.append((pos, connectivity_score))
    
    # Sort by score
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Pick top candidates with some randomness to add variance
    if candidates:
        # Evaluate a few top candidates
        top_candidates = candidates[:min(3, len(candidates))]
        best_move = max(top_candidates, key=lambda x: x[1])[0]
        
        # Adjust to center favored moves
        if len(me) == 0 and len(opp) == 0:
            # Opening move - prefer corner/edge
            corner_positions = [(0,0), (0,14), (14,0), (14,14), (7,0), (7,14), (0,7), (14,7)]
            for corner in corner_positions:
                if corner in valid_mask and valid_mask[corner[0]][corner[1]] and corner not in me_set and corner not in opp_set:
                    return corner
            # Fallback to center        
            return (7, 7)
            
        return best_move
    
    # Fallback to any valid position
    for pos in valid_positions:
        if pos not in me_set and pos not in opp_set:
            return pos
    
    # Should never happen, but just in case
    return (7, 7)

def get_hex_neighbors(row, col, valid_mask):
    """Get all valid hex neighbors of a position"""
    neighbors = []
    # Hex neighbors in order: up left, up right, right, down right, down left, left
    directions = [(-1, -1), (-1, 1), (0, 2), (1, 1), (1, -1), (0, -2)]
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 15 and 0 <= new_col < 15 and valid_mask[new_row][new_col]:
            neighbors.append((new_row, new_col))
    
    return neighbors

def check_win(pos, me_set, opp_set, valid_mask):
    """Check if placing a stone at pos win for me - simplified """
    # This is a skeleton - full implementation would be very complex
    # For now we implement limited version of winning checks
    
    # Simplified check for fork (a rough heuristic)
    # A fork connects 3 edges (excluding corners)
    # Actually, let's focus on finding bridges and rings for now
    
    # Bridge check: can we connect opposite corners?
    # Simple bridge heuristic: If we're close to connecting two corners
    # This is a placeholder - full implementation would be complex
    return False  # Placeholder for complete implementation
