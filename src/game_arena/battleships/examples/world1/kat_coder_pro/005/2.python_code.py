
import numpy as np
from typing import List, Tuple, Dict, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Main policy function that determines the next shot location.
    
    Args:
        board: 10x10 grid representing opponent's board state
               0: unknown, -1: miss, 1: hit
    
    Returns:
        Tuple (row, col) of next shot coordinates
    """
    
    # Convert to numpy for easier manipulation
    board_array = np.array(board)
    
    # Define ship lengths
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Check if we're in hunt mode (have recent hits to follow up on)
    hunt_moves = get_hunt_moves(board_array)
    
    if hunt_moves:
        # If multiple hunt options, pick the one with highest base probability
        return select_best_hunt_move(hunt_moves, board_array)
    
    # Calculate probability map for all unknown cells
    prob_map = calculate_probability_map(board_array, ship_lengths)
    
    # Select best move based on probability
    return select_best_move(prob_map, board_array)


def get_hunt_moves(board: np.ndarray) -> List[Tuple[int, int]]:
    """
    Find adjacent cells to hits that could continue sinking a ship.
    Returns list of potential hunt moves sorted by priority.
    """
    hunt_moves = []
    hit_positions = np.where(board == 1)
    
    if len(hit_positions[0]) == 0:
        return hunt_moves
    
    # Find the most recent hit (assuming hits are added in order)
    # For simplicity, we'll consider all hits
    for i in range(len(hit_positions[0])):
        row, col = hit_positions[0][i], hit_positions[1][i]
        
        # Check adjacent cells (up, down, left, right)
        candidates = [(row-1, col), (row+1, col), (row, col-1), (row, col+1)]
        
        for r, c in candidates:
            if 0 <= r < 10 and 0 <= c < 10 and board[r, c] == 0:
                if (r, c) not in hunt_moves:
                    hunt_moves.append((r, c))
    
    return hunt_moves


def select_best_hunt_move(hunt_moves: List[Tuple[int, int]], 
                         board: np.ndarray) -> Tuple[int, int]:
    """
    Select the best hunt move from available options.
    """
    if len(hunt_moves) == 1:
        return hunt_moves[0]
    
    # Calculate base probability for each hunt move
    ship_lengths = [5, 4, 3, 3, 2]
    prob_map = calculate_probability_map(board, ship_lengths)
    
    best_move = hunt_moves[0]
    best_score = 0
    
    for move in hunt_moves:
        r, c = move
        score = prob_map[r, c]
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def calculate_probability_map(board: np.ndarray, 
                             ship_lengths: List[int]) -> np.ndarray:
    """
    Calculate probability map showing likelihood of each cell containing a ship.
    """
    prob_map = np.zeros((10, 10))
    
    # For each ship length, calculate all possible placements
    for ship_len in ship_lengths:
        # Horizontal placements
        for row in range(10):
            for start_col in range(11 - ship_len):
                # Check if this placement is valid
                if is_valid_placement(board, row, start_col, ship_len, horizontal=True):
                    # Add probability to each cell in this potential ship
                    for col_offset in range(ship_len):
                        prob_map[row, start_col + col_offset] += 1
        
        # Vertical placements  
        for col in range(10):
            for start_row in range(11 - ship_len):
                # Check if this placement is valid
                if is_valid_placement(board, start_row, col, ship_len, horizontal=False):
                    # Add probability to each cell in this potential ship
                    for row_offset in range(ship_len):
                        prob_map[start_row + row_offset, col] += 1
    
    # Apply edge bias - central cells are slightly more likely
    center_bias = np.zeros((10, 10))
    for r in range(10):
        for c in range(10):
            # Distance from center (4.5, 4.5)
            dist = np.sqrt((r - 4.5)**2 + (c - 4.5)**2)
            # Closer to center gets higher bias (inverse relationship)
            center_bias[r, c] = max(0, 1.0 - dist / 7.0)
    
    # Combine probability with center bias
    prob_map = prob_map * (1 + 0.1 * center_bias)
    
    # Set probability to 0 for already fired cells
    prob_map[board != 0] = 0
    
    return prob_map


def is_valid_placement(board: np.ndarray, start_row: int, start_col: int, 
                      ship_len: int, horizontal: bool) -> bool:
    """
    Check if a ship of given length can be placed at the specified position.
    """
    # Check boundaries
    if horizontal:
        if start_col + ship_len > 10:
            return False
        
        # Check if any cell in the ship path is already known to be water or hit
        for col_offset in range(ship_len):
            if board[start_row, start_col + col_offset] == -1:
                return False
    else:
        if start_row + ship_len > 10:
            return False
        
        # Check if any cell in the ship path is already known to be water or hit
        for row_offset in range(ship_len):
            if board[start_row + row_offset, start_col] == -1:
                return False
    
    return True


def select_best_move(prob_map: np.ndarray, board: np.ndarray) -> Tuple[int, int]:
    """
    Select the move with highest probability.
    """
    # Find all unknown cells
    unknown_mask = (board == 0)
    
    if not np.any(unknown_mask):
        # Fallback - should not happen in normal gameplay
        for r in range(10):
            for c in range(10):
                if board[r, c] == 0:
                    return (r, c)
    
    # Get the maximum probability among unknown cells
    max_prob = np.max(prob_map[unknown_mask])
    
    # Find all cells with maximum probability
    best_cells = np.where((prob_map == max_prob) & unknown_mask)
    
    # If multiple cells have same probability, use a tiebreaker
    if len(best_cells[0]) > 1:
        # Prefer central cells as tiebreaker
        best_options = list(zip(best_cells[0], best_cells[1]))
        return select_central_cell(best_options)
    
    return (best_cells[0][0], best_cells[1][0])


def select_central_cell(candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Among equally probable cells, select the one closest to center.
    """
    center = (4.5, 4.5)
    best_cell = candidates[0]
    min_dist = float('inf')
    
    for cell in candidates:
        dist = np.sqrt((cell[0] - center[0])**2 + (cell[1] - center[1])**2)
        if dist < min_dist:
            min_dist = dist
            best_cell = cell
    
    return best_cell
