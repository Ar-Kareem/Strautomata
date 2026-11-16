
import random
import numpy as np
from typing import List, Tuple

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you)
    opponent_arr = np.array(opponent)
    board = you_arr - opponent_arr  # 1 for you, -1 for opponent, 0 for empty

    # Get all empty positions
    empty_positions = [(r, c) for r in range(6) for c in range(6) if board[r][c] == 0]

    # Check for immediate winning moves
    for move in generate_all_moves(empty_positions, board):
        if is_winning_move(move, board, 1):
            return move

    # Check for opponent's immediate winning moves to block
    for move in generate_all_moves(empty_positions, board):
        # Simulate opponent's move
        temp_board = board.copy()
        r, c = int(move.split(',')[0])-1, int(move.split(',')[1])-1
        temp_board[r][c] = -1  # Opponent's marble
        if is_winning_move(move, temp_board, -1):
            # Block by placing our marble there
            return f"{r+1},{c+1},{move.split(',')[2]},{move.split(',')[3]}"

    # Evaluate all possible moves with scoring
    best_move = None
    best_score = -float('inf')

    for move in generate_all_moves(empty_positions, board):
        score = evaluate_move(move, board)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(generate_all_moves(empty_positions, board))

def generate_all_moves(empty_positions: List[Tuple[int, int]], board: np.ndarray) -> List[str]:
    moves = []
    for r, c in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                moves.append(f"{r+1},{c+1},{quad},{direction}")
    return moves

def is_winning_move(move: str, board: np.ndarray, player: int) -> bool:
    # Parse move
    parts = move.split(',')
    r, c = int(parts[0])-1, int(parts[1])-1
    quad = int(parts[2])
    direction = parts[3]

    # Create temporary board
    temp_board = board.copy()
    temp_board[r][c] = player

    # Apply rotation
    temp_board = apply_rotation(temp_board, quad, direction)

    # Check for 5 in a row
    return check_win(temp_board, player)

def apply_rotation(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    # Define quadrant boundaries
    quad_rows = {
        0: slice(0, 3),
        1: slice(0, 3),
        2: slice(3, 6),
        3: slice(3, 6)
    }
    quad_cols = {
        0: slice(0, 3),
        1: slice(3, 6),
        2: slice(0, 3),
        3: slice(3, 6)
    }

    # Extract quadrant
    quadrant = board[quad_rows[quad], quad_cols[quad]]

    # Rotate
    if direction == 'L':
        rotated = np.rot90(quadrant, k=1)  # 90 degrees counter-clockwise
    else:
        rotated = np.rot90(quadrant, k=-1)  # 90 degrees clockwise

    # Place back
    board[quad_rows[quad], quad_cols[quad]] = rotated
    return board

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows
    for row in board:
        if np.sum(row == player) >= 5:
            return True

    # Check columns
    for col in range(6):
        if np.sum(board[:, col] == player) >= 5:
            return True

    # Check diagonals (top-left to bottom-right)
    for i in range(-2, 4):
        diag = np.diagonal(board, offset=i)
        if len(diag) >= 5 and np.sum(diag == player) >= 5:
            return True

    # Check diagonals (top-right to bottom-left)
    for i in range(-2, 4):
        diag = np.diagonal(np.fliplr(board), offset=i)
        if len(diag) >= 5 and np.sum(diag == player) >= 5:
            return True

    return False

def evaluate_move(move: str, board: np.ndarray) -> float:
    parts = move.split(',')
    r, c = int(parts[0])-1, int(parts[1])-1
    quad = int(parts[2])
    direction = parts[3]

    # Create temporary board
    temp_board = board.copy()
    temp_board[r][c] = 1  # Our marble

    # Apply rotation
    temp_board = apply_rotation(temp_board, quad, direction)

    score = 0

    # Score for creating potential lines
    score += count_potential_lines(temp_board, 1) * 10

    # Score for blocking opponent's potential lines
    score += count_potential_lines(temp_board, -1) * -5

    # Center control bonus
    if (r, c) in [(2, 2), (2, 3), (3, 2), (3, 3)]:
        score += 3

    # Quadrant control bonus
    if quad in [0, 3]:  # Top-left and bottom-right are more central
        score += 2

    return score

def count_potential_lines(board: np.ndarray, player: int) -> int:
    count = 0

    # Check rows
    for row in board:
        if np.sum(row == player) == 4 and np.sum(row == 0) == 1:
            count += 1
        if np.sum(row == player) == 3 and np.sum(row == 0) == 2:
            count += 0.5

    # Check columns
    for col in range(6):
        column = board[:, col]
        if np.sum(column == player) == 4 and np.sum(column == 0) == 1:
            count += 1
        if np.sum(column == player) == 3 and np.sum(column == 0) == 2:
            count += 0.5

    # Check diagonals (top-left to bottom-right)
    for i in range(-5, 6):
        diag = np.diagonal(board, offset=i)
        if len(diag) >= 5:
            if np.sum(diag == player) == 4 and np.sum(diag == 0) == 1:
                count += 1
            if np.sum(diag == player) == 3 and np.sum(diag == 0) == 2:
                count += 0.5

    # Check diagonals (top-right to bottom-left)
    for i in range(-5, 6):
        diag = np.diagonal(np.fliplr(board), offset=i)
        if len(diag) >= 5:
            if np.sum(diag == player) == 4 and np.sum(diag == 0) == 1:
                count += 1
            if np.sum(diag == player) == 3 and np.sum(diag == 0) == 2:
                count += 0.5

    return count
