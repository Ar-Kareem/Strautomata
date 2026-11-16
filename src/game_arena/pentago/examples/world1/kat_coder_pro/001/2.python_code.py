
import numpy as np
from typing import Tuple, List

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    board = you_board + opp_board
    
    # Get all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empty_positions.append((r, c))
    
    # Try each possible move and evaluate
    best_move = None
    best_score = -float('inf')
    
    for r, c in empty_positions:
        for quad in range(4):
            for rot in ['L', 'R']:
                score = evaluate_move(you_board, opp_board, r, c, quad, rot)
                if score > best_score:
                    best_score = score
                    best_move = f"{r+1},{c+1},{quad},{rot}"
    
    return best_move

def evaluate_move(you: np.ndarray, opp: np.ndarray, r: int, c: int, quad: int, rot: str) -> float:
    # Create copies to simulate the move
    you_copy = you.copy()
    opp_copy = opp.copy()
    
    # Place the piece
    you_copy[r, c] = 1
    
    # Apply rotation
    you_copy = rotate_quadrant(you_copy, quad, rot)
    opp_copy = rotate_quadrant(opp_copy, quad, rot)
    
    # Check for immediate win
    if check_win(you_copy):
        return 1000.0
    
    # Check if opponent wins (bad)
    if check_win(opp_copy):
        return -1000.0
    
    # Evaluate the board position
    score = 0.0
    
    # Count potential winning lines for each player
    you_threats = count_threats(you_copy, opp_copy)
    opp_threats = count_threats(opp_copy, you_copy)
    
    # Favor creating threats and blocking opponent threats
    score += you_threats * 10.0
    score -= opp_threats * 15.0  # Block opponent more aggressively
    
    # Count 3-in-a-row patterns
    you_threes = count_n_in_a_row(you_copy, 3)
    opp_threes = count_n_in_a_row(opp_copy, 3)
    
    score += you_threes * 2.0
    score -= opp_threes * 3.0
    
    # Add some randomness to avoid predictable play
    score += np.random.random() * 0.1
    
    return score

def rotate_quadrant(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    """Rotate a 3x3 quadrant of the board 90 degrees."""
    board_copy = board.copy()
    
    # Define the slice for each quadrant
    if quad == 0:  # Top-left
        rows = slice(0, 3)
        cols = slice(0, 3)
    elif quad == 1:  # Top-right
        rows = slice(0, 3)
        cols = slice(3, 6)
    elif quad == 2:  # Bottom-left
        rows = slice(3, 6)
        cols = slice(0, 3)
    else:  # Bottom-right
        rows = slice(3, 6)
        cols = slice(3, 6)
    
    # Get the sub-board
    sub_board = board_copy[rows, cols].copy()
    
    # Rotate
    if direction == 'L':
        rotated = np.rot90(sub_board, k=1)  # 90 degrees counterclockwise
    else:  # 'R'
        rotated = np.rot90(sub_board, k=3)  # 90 degrees clockwise
    
    # Put it back
    board_copy[rows, cols] = rotated
    
    return board_copy

def check_win(board: np.ndarray) -> bool:
    """Check if the player has 5 or more in a row."""
    # Check horizontal
    for r in range(6):
        for c in range(2):  # Only need to check starting positions 0-1
            if board[r, c] and all(board[r, c+i] == board[r, c] for i in range(5)):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):  # Only need to check starting positions 0-1
            if board[r, c] and all(board[r+i, c] == board[r, c] for i in range(5)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if board[r, c] and all(board[r+i, c+i] == board[r, c] for i in range(5)):
                return True
    
    # Check diagonal (top-right to bottom-left)
    for r in range(2):
        for c in range(4, 6):
            if board[r, c] and all(board[r+i, c-i] == board[r, c] for i in range(5)):
                return True
    
    return False

def count_threats(player_board: np.ndarray, opponent_board: np.ndarray) -> int:
    """Count the number of 4-in-a-row threats (4 consecutive with empty space)."""
    threats = 0
    
    # Check horizontal
    for r in range(6):
        for c in range(3):  # Starting positions for 4-in-a-row
            if is_threat(player_board, opponent_board, [(r, c+i) for i in range(5)]):
                threats += 1
    
    # Check vertical
    for c in range(6):
        for r in range(3):  # Starting positions for 4-in-a-row
            if is_threat(player_board, opponent_board, [(r+i, c) for i in range(5)]):
                threats += 1
    
    # Check diagonal (top-left to bottom-right)
    for r in range(3):
        for c in range(3):
            if is_threat(player_board, opponent_board, [(r+i, c+i) for i in range(5)]):
                threats += 1
    
    # Check diagonal (top-right to bottom-left)
    for r in range(3):
        for c in range(3, 6):
            if is_threat(player_board, opponent_board, [(r+i, c-i) for i in range(5)]):
                threats += 1
    
    return threats

def is_threat(player_board: np.ndarray, opponent_board: np.ndarray, positions: List[Tuple[int, int]]) -> bool:
    """Check if the positions form a 4-in-a-row threat."""
    # Count player pieces and empty spaces
    player_count = 0
    empty_count = 0
    
    for r, c in positions:
        if player_board[r, c] == 1:
            player_count += 1
        elif opponent_board[r, c] == 0:
            empty_count += 1
    
    # Must have exactly 4 player pieces and 1 empty space
    return player_count == 4 and empty_count == 1

def count_n_in_a_row(board: np.ndarray, n: int) -> int:
    """Count the number of n-in-a-row patterns."""
    count = 0
    
    # Check horizontal
    for r in range(6):
        for c in range(7-n):
            if all(board[r, c+i] == 1 for i in range(n)):
                count += 1
    
    # Check vertical
    for c in range(6):
        for r in range(7-n):
            if all(board[r+i, c] == 1 for i in range(n)):
                count += 1
    
    # Check diagonal (top-left to bottom-right)
    for r in range(7-n):
        for c in range(7-n):
            if all(board[r+i, c+i] == 1 for i in range(n)):
                count += 1
    
    # Check diagonal (top-right to bottom-left)
    for r in range(7-n):
        for c in range(n-1, 6):
            if all(board[r+i, c-i] == 1 for i in range(n)):
                count += 1
    
    return count
