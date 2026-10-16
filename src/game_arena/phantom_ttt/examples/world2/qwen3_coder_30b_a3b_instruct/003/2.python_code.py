
import random
import math
from typing import List, Tuple
import numpy as np

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Get all empty positions (0s)
    empty_positions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    if len(empty_positions) == 0:
        # No moves left - shouldn't happen in valid game state
        return (0, 0)
    
    # Early game: prefer center, then corners, then edges
    if len(empty_positions) >= 7:
        # Prefer center (1,1)
        if (1, 1) in empty_positions:
            return (1, 1)
        # Then corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for corner in corners:
            if corner in empty_positions:
                return corner
        # Then edges
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for edge in edges:
            if edge in empty_positions:
                return edge
    
    # For later game, use MCTS-based decision
    return mcts_policy(board_np, empty_positions)

def mcts_policy(board: np.ndarray, empty_positions: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Monte Carlo Tree Search policy for later game stages
    n_simulations = 500
    best_move = empty_positions[0]
    best_score = -1
    
    # Try each possible move
    for move in empty_positions:
        total_score = 0
        wins = 0
        
        # Do a number of simulations
        for _ in range(n_simulations):
            # Make a copy of board to simulate
            sim_board = board.copy()
            
            # Try our move
            sim_board[move[0], move[1]] = 1
            
            # Simulate the rest of the game to a terminal state
            result = simulate_game(sim_board)
            
            if result == 1:  # We win
                wins += 1
            elif result == 0:  # Draw
                total_score += 0.5
            else:
                total_score += 0  # Opponent wins
        
        # Calculation of score based on win rate and score
        win_rate = wins / n_simulations
        score = win_rate + total_score / n_simulations
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def simulate_game(board: np.ndarray) -> int:
    """
    Simulate game from current board state until terminal state
    Returns 1 for win, 0 for draw, -1 for loss (for player 1)
    """
    # Create a copy of the board
    board_copy = board.copy()
    
    # Randomly play until game ends
    # We'll assume we're player 1, opponent is player -1
    current_player = 1
    
    # Win checking function
    def check_win(b):
        # Check rows
        for row in b:
            if all(x == 1 for x in row):
                return 1
            if all(x == -1 for x in row):
                return -1
        
        # Check columns
        for col in range(3):
            if all(b[row][col] == 1 for row in range(3)):
                return 1
            if all(b[row][col] == -1 for row in range(3)):
                return -1
        
        # Check diagonals
        if all(b[i][i] == 1 for i in range(3)):
            return 1
        if all(b[i][2-i] == 1 for i in range(3)):
            return 1
        if all(b[i][i] == -1 for i in range(3)):
            return -1
        if all(b[i][2-i] == -1 for i in range(3)):
            return -1
        
        # Check for draw (no empty cells)
        if not any(0 in row for row in b):
            return 0
        
        return None  # Game continues
    
    # Play until terminal state
    while True:
        # Check if game already ended
        result = check_win(board_copy)
        if result is not None:
            return result
        
        # Get available moves
        available = []
        for i in range(3):
            for j in range(3):
                if board_copy[i][j] == 0:
                    available.append((i, j))
        
        if len(available) == 0:
            return 0  # Draw
        
        # Play a random move for current player
        move = random.choice(available)
        board_copy[move[0], move[1]] = current_player
        
        # Switch player
        current_player = -current_player

# Main policy function
def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Get all empty positions (0s)
    empty_positions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    if len(empty_positions) == 0:
        # No moves left - shouldn't happen in valid game state
        return (0, 0)
    
    # Early game: prefer center, then corners, then edges
    if len(empty_positions) >= 7:
        # Prefer center (1,1)
        if (1, 1) in empty_positions:
            return (1, 1)
        # Then corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for corner in corners:
            if corner in empty_positions:
                return corner
        # Then edges
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for edge in edges:
            if edge in empty_positions:
                return edge
    
    # For later game, use MCTS-based decision
    return mcts_policy(board_np, empty_positions)
