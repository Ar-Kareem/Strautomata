
import numpy as np
from collections import defaultdict

class ShipTracker:
    def __init__(self):
        self.ship_lengths = [5, 4, 3, 3, 2]
        self.ship_counts = defaultdict(int)
        for length in self.ship_lengths:
            self.ship_counts[length] += 1
    
    def get_possible_ships(self):
        return self.ship_lengths.copy()

def create_probability_grid(board):
    size = len(board)
    prob_grid = np.zeros((size, size))
    possible_ships = ShipTracker().get_possible_ships()
    
    for length in possible_ships:
        for i in range(size):
            for j in range(size):
                # Check horizontal placement
                if j + length <= size:
                    valid = True
                    for k in range(length):
                        if board[i][j+k] == -1:  # Has a miss in ship area
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            if board[i][j+k] == 0:  # Only boost unknown cells
                                prob_grid[i][j+k] += 1
                
                # Check vertical placement
                if i + length <= size:
                    valid = True
                    for k in range(length):
                        if board[i+k][j] == -1:
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            if board[i+k][j] == 0:
                                prob_grid[i+k][j] += 1
    return prob_grid

def find_adjacent_hits(board):
    hits = []
    size = len(board)
    for i in range(size):
        for j in range(size):
            if board[i][j] == 1:
                hits.append((i, j))
    
    adjacent_unknowns = []
    for i, j in hits:
        for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < size and 0 <= nj < size:
                if board[ni][nj] == 0:
                    adjacent_unknowns.append((ni, nj))
    
    return adjacent_unknowns

def policy(board):
    size = len(board)
    
    # First look for adjacent cells to existing hits
    adjacent_targets = find_adjacent_hits(board)
    if adjacent_targets:
        # Choose the target with highest probability
        prob_grid = create_probability_grid(board)
        max_prob = -1
        best_target = adjacent_targets[0]
        for target in adjacent_targets:
            i, j = target
            if prob_grid[i][j] > max_prob:
                max_prob = prob_grid[i][j]
                best_target = target
        return best_target
    
    # If no adjacent hits, use probability density
    prob_grid = create_probability_grid(board)
    
    # Find all unknown cells
    unknown_cells = []
    for i in range(size):
        for j in range(size):
            if board[i][j] == 0:
                unknown_cells.append((i, j))
    
    if not unknown_cells:
        return (0, 0)  # Shouldn't happen in valid game
    
    # Find highest probability unknown cell
    max_prob = -1
    best_target = unknown_cells[0]
    for cell in unknown_cells:
        i, j = cell
        if prob_grid[i][j] > max_prob:
            max_prob = prob_grid[i][j]
            best_target = cell
    
    return best_target
