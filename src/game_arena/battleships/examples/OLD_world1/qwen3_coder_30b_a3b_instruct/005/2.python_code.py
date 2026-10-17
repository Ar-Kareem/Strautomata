
import numpy as np
from collections import defaultdict
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    n = len(board)
    
    # Find all previously fired positions
    fired_positions = set()
    for i in range(n):
        for j in range(n):
            if board[i, j] != 0:
                fired_positions.add((i, j))
    
    # Find all hits
    hits = []
    for i in range(n):
        for j in range(n):
            if board[i, j] == 1:
                hits.append((i, j))
    
    # If no hits, use random strategy with some bias towards center
    if not hits:
        # Prefer center positions to start with
        center_range = 3
        available_positions = []
        for i in range(n):
            for j in range(n):
                if (i, j) not in fired_positions:
                    # Bias towards center
                    center_dist = max(abs(i - n//2), abs(j - n//2))
                    if center_dist <= center_range:
                        available_positions.append((i, j, center_dist))
        
        if available_positions:
            available_positions.sort(key=lambda x: x[2])  # Sort by distance from center
            return available_positions[0][:2]
        else:
            # Fallback to random
            for i in range(n):
                for j in range(n):
                    if (i, j) not in fired_positions:
                        return (i, j)
    
    # If we have hits, try to find adjacent cells to continue targeting
    # Look for hits that are part of a known ship segment
    # First, try to extend existing hit chains
    
    # Try to find a hit that has unfired adjacent cells
    for i, j in hits:
        # Check all adjacent cells (up, down, left, right)
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < n and (ni, nj) not in fired_positions:
                return (ni, nj)
    
    # If no adjacent unfired cells to hits, fall back to random from available cells
    available_positions = []
    for i in range(n):
        for j in range(n):
            if (i, j) not in fired_positions:
                available_positions.append((i, j))
    
    if available_positions:
        # Pick a random one
        return random.choice(available_positions)
    
    # If for some reason we still haven't found a position
    # Just return the first unfired cell
    for i in range(n):
        for j in range(n):
            if (i, j) not in fired_positions:
                return (i, j)
    
    # Fallback - should not happen
    return (0, 0)
