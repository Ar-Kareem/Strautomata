
import random
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)

    # Current player (1) and opponent (-1)
    current_player = 1
    opponent = -1

    # Check for immediate win or block
    move = find_immediate_win_or_block(board_np, current_player)
    if move is not None:
        return move

    move = find_immediate_win_or_block(board_np, opponent)
    if move is not None:
        return move

    # Prioritize center control
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for pos in center_positions:
        if board_np[pos] == 0:
            return pos

    # Prioritize corner control
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for pos in corners:
        if board_np[pos] == 0:
            return pos

    # Prioritize edge control
    edges = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    for pos in edges:
        if board_np[pos] == 0:
            return pos

    # If no high-priority moves, use minimax with alpha-beta pruning
    best_move = minimax(board_np, current_player, depth=3, alpha=-float('inf'), beta=float('inf'))
    if best_move is not None:
        return best_move

    # Fallback: random move
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board_np[i, j] == 0]
    return random.choice(empty_cells)

def find_immediate_win_or_block(board: np.ndarray, player: int) -> Tuple[int, int]:
    # Check rows
    for i in range(4):
        row = board[i, :]
        empty_indices = [j for j in range(4) if row[j] == 0]
        if len(empty_indices) == 1:
            return (i, empty_indices[0])

    # Check columns
    for j in range(4):
        col = board[:, j]
        empty_indices = [i for i in range(4) if col[i] == 0]
        if len(empty_indices) == 1:
            return (empty_indices[0], j)

    # Check diagonals
    diag1 = [board[i, i] for i in range(4)]
    empty_indices = [i for i in range(4) if diag1[i] == 0]
    if len(empty_indices) == 1:
        return (empty_indices[0], empty_indices[0])

    diag2 = [board[i, 3 - i] for i in range(4)]
    empty_indices = [i for i in range(4) if diag2[i] == 0]
    if len(empty_indices) == 1:
        return (empty_indices[0], 3 - empty_indices[0])

    return None

def minimax(board: np.ndarray, player: int, depth: int, alpha: float, beta: float) -> Tuple[int, int]:
    if depth == 0 or is_terminal(board):
        return None

    best_move = None
    best_score = -float('inf') if player == 1 else float('inf')

    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    for move in empty_cells:
        new_board = board.copy()
        new_board[move] = player
        score = minimax_score(new_board, player, depth - 1, alpha, beta, -player)

        if player == 1 and score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)
        elif player == -1 and score < best_score:
            best_score = score
            best_move = move
            beta = min(beta, score)

        if beta <= alpha:
            break

    return best_move

def minimax_score(board: np.ndarray, player: int, depth: int, alpha: float, beta: float, opponent: int) -> float:
    if depth == 0 or is_terminal(board):
        return evaluate_board(board, player)

    best_score = -float('inf') if opponent == 1 else float('inf')

    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    for move in empty_cells:
        new_board = board.copy()
        new_board[move] = opponent
        score = minimax_score(new_board, opponent, depth - 1, alpha, beta, -opponent)

        if opponent == 1 and score > best_score:
            best_score = score
            alpha = max(alpha, score)
        elif opponent == -1 and score < best_score:
            best_score = score
            beta = min(beta, score)

        if beta <= alpha:
            break

    return best_score

def is_terminal(board: np.ndarray) -> bool:
    # Check rows
    for i in range(4):
        row = board[i, :]
        if row[0] != 0 and all(row[0] == x for x in row):
            return True

    # Check columns
    for j in range(4):
        col = board[:, j]
        if col[0] != 0 and all(col[0] == x for x in col):
            return True

    # Check diagonals
    diag1 = [board[i, i] for i in range(4)]
    if diag1[0] != 0 and all(diag1[0] == x for x in diag1):
        return True

    diag2 = [board[i, 3 - i] for i in range(4)]
    if diag2[0] != 0 and all(diag2[0] == x for x in diag2):
        return True

    # Check if board is full
    if all(board[i, j] != 0 for i in range(4) for j in range(4)):
        return True

    return False

def evaluate_board(board: np.ndarray, player: int) -> float:
    # Evaluate the board for the given player (1) or opponent (-1)
    score = 0

    # Check rows
    for i in range(4):
        row = board[i, :]
        if row[0] == player and all(row[0] == x for x in row):
            score += 100
        elif row[0] == -player and all(row[0] == x for x in row):
            score -= 100

    # Check columns
    for j in range(4):
        col = board[:, j]
        if col[0] == player and all(col[0] == x for x in col):
            score += 100
        elif col[0] == -player and all(col[0] == x for x in col):
            score -= 100

    # Check diagonals
    diag1 = [board[i, i] for i in range(4)]
    if diag1[0] == player and all(diag1[0] == x for x in diag1):
        score += 100
    elif diag1[0] == -player and all(diag1[0] == x for x in diag1):
        score -= 100

    diag2 = [board[i, 3 - i] for i in range(4)]
    if diag2[0] == player and all(diag2[0] == x for x in diag2):
        score += 100
    elif diag2[0] == -player and all(diag2[0] == x for x in diag2):
        score -= 100

    # Evaluate center control
    center = board[1:3, 1:3]
    if center[0, 0] == player:
        score += 5
    elif center[0, 0] == -player:
        score -= 5

    if center[0, 1] == player:
        score += 5
    elif center[0, 1] == -player:
        score -= 5

    if center[1, 0] == player:
        score += 5
    elif center[1, 0] == -player:
        score -= 5

    if center[1, 1] == player:
        score += 5
    elif center[1, 1] == -player:
        score -= 5

    # Evaluate corner control
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for pos in corners:
        if board[pos] == player:
            score += 3
        elif board[pos] == -player:
            score -= 3

    # Evaluate edge control
    edges = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    for pos in edges:
        if board[pos] == player:
            score += 1
        elif board[pos] == -player:
            score -= 1

    return score
