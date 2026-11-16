
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    unknowns = np.where(board_np == 0)
    
    # If there are no unknowns left (shouldn't happen in valid game)
    if len(unknowns[0]) == 0:
        return (0, 0)
    
    # Check if we have any hits that aren't fully sunk yet
    hit_positions = np.where(board_np == 1)
    if len(hit_positions[0]) > 0:
        # Try adjacent cells to existing hits
        adjacent = get_adjacent_targets(board_np, hit_positions)
        if adjacent:
            return adjacent[0]  # Return the first adjacent cell
    
    # If no hits or all adjacent have been tried, use probability density
    prob_map = create_probability_map(board_np)
    return select_max_probability(prob_map, board_np)

def get_adjacent_targets(board, hit_positions):
    # Get all adjacent cells to hits that are unknown
    adjacent = []
    for i in range(len(hit_positions[0])):
        row, col = hit_positions[0][i], hit_positions[1][i]
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            r, c = row + dr, col + dc
            if 0 <= r < 10 and 0 <= c < 10 and board[r, c] == 0:
                adjacent.append((r, c))
    return adjacent

def create_probability_map(board):
    # Initialize probability map
    prob_map = np.zeros((10, 10))
    
    # Ship lengths and counts
    ships = [(5, 1), (4, 1), (3, 2), (2, 1)]
    
    # For each possible ship, calculate possible placements
    for length, count in ships:
        for _ in range(count):
            # Check horizontal placements
            for row in range(10):
                for col in range(10 - length + 1):
                    if np.all(board[row, col:col+length] <= 0):  # Only unknown or hits
                        prob_map[row, col:col+length] += 1
            
            # Check vertical placements
            for col in range(10):
                for row in range(10 - length + 1):
                    if np.all(board[row:row+length, col] <= 0):  # Only unknown or hits
                        prob_map[row:row+length, col] += 1
    
    # Zero out known misses and hits (we shouldn't target these)
    prob_map[board == -1] = 0
    prob_map[board == 1] = 0
    
    return prob_map

def select_max_probability(prob_map, board):
    max_prob = np.max(prob_map)
    if max_prob > 0:
        # Get all positions with max probability
        positions = np.where(prob_map == max_prob)
    else:
        # If all zero (no possible ships?), just pick any unknown cell
        positions = np.where(board == 0)
    
    # Convert to list of (row, col) tuples
    candidates = list(zip(positions[0], positions[1]))
    
    # Return the first candidate (can add more sophisticated selection if needed)
    return candidates[0]
