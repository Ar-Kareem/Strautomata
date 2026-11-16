
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move (row, col) for a 4x4 Tic Tac Toe game.
    Uses minimax with alpha-beta pruning and symmetry/positional heuristics.
    """
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    empty_cells = np.argwhere(board_np == 0)

    # Check if current player can win immediately
    for cell in empty_cells:
        row, col = cell
        if can_win(board_np, row, col, 1):
            return (row, col)

    # Check if opponent can win next turn and block
    for cell in empty_cells:
        row, col = cell
        if can_win(board_np, row, col, -1):
            return (row, col)

    # If no immediate win/block, use minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for cell in empty_cells:
        row, col = cell
        # Simulate move
        new_board = board_np.copy()
        new_board[row, col] = 1
        score = minimax(new_board, 3, False, alpha, beta)  # Depth limit = 3 (4 layers total)
        new_board[row, col] = 0  # Undo move

        if score > best_score:
            best_score = score
            best_move = (row, col)
        elif score == best_score:
            # Random tiebreaker to avoid deterministic behavior
            if random.choice([True, False]):
                best_move = (row, col)

    return best_move

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
    """
    Minimax algorithm with alpha-beta pruning.
    Returns the best score for the current player (1) or opponent (-1).
    """
    empty_cells = np.argwhere(board == 0)
    if len(empty_cells) == 0 or depth == 0:
        return evaluate_board(board)

    if is_maximizing:
        best_score = -float('inf')
        for cell in empty_cells:
            row, col = cell
            board[row, col] = 1
            score = minimax(board, depth - 1, False, alpha, beta)
            board[row, col] = 0
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float('inf')
        for cell in empty_cells:
            row, col = cell
            board[row, col] = -1
            score = minimax(board, depth - 1, True, alpha, beta)
            board[row, col] = 0
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score

def evaluate_board(board: np.ndarray) -> float:
    """
    Evaluates the board state using heuristics:
    - Immediate wins/threats
    - Symmetry
    - Corner/edge control
    """
    score = 0
    empty_cells = np.argwhere(board == 0)

    # Check if current player wins
    for cell in empty_cells:
        row, col = cell
        if can_win(board, row, col, 1):
            score += 1000
        elif can_win(board, row, col, -1):
            score -= 1000

    # Symmetry heuristic (prefer symmetric boards)
    symmetry_score = evaluate_symmetry(board)
    score += symmetry_score

    # Positional control heuristic (corners > edges > center)
    for cell in empty_cells:
        row, col = cell
        if is_corner(row, col):
            score += 10
        elif is_edge(row, col):
            score += 5
        else:
            score += 1

    return score

def can_win(board: np.ndarray, row: int, col: int, player: int) -> bool:
    """
    Checks if placing 'player' at (row, col) results in a win.
    """
    # Directions: rows, columns, diagonals, anti-diagonals
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 0
        for i in range(-3, 4):
            r, c = row + i, col + i
            if 0 <= r < 4 and 0 <= c < 4:
                if board[r, c] == player:
                    count += 1
                elif board[r, c] == 0:
                    count += 1
            if count == 4:
                return True
    return False

def evaluate_symmetry(board: np.ndarray) -> float:
    """
    Evaluates board symmetry. Higher score for more symmetric boards.
    """
    # Check horizontal symmetry
    for i in range(4):
        if np.array_equal(board[i, :], board[i, ::-1]):
            return 100  # Perfect symmetry (unlikely in 4x4)

    # Check vertical symmetry
    for j in range(4):
        if np.array_equal(board[:, j], board[:, j][::-1]):
            return 100

    # Check diagonal symmetry (main diagonals)
    if np.array_equal(board.diagonal(), board.diagonal()[::-1]):
        return 50
    if np.array_equal(np.fliplr(board).diagonal(), board.diagonal()[::-1]):
        return 50

    # Check anti-diagonal symmetry
    if np.array_equal(np.flipud(board).diagonal(), board.diagonal()):
        return 50
    if np.array_equal(np.fliplr(np.flipud(board)).diagonal(), board.diagonal()):
        return 50

    return 0  # No symmetry

def is_corner(row: int, col: int) -> bool:
    """Returns True if (row, col) is a corner cell."""
    return (row == 0 or row == 3) and (col == 0 or col == 3)

def is_edge(row: int, col: int) -> bool:
    """Returns True if (row, col) is an edge cell (not corner or center)."""
    return (row == 1 or row == 2) and (col == 0 or col == 3 or col == 1 or col == 2) or \
           (col == 1 or col == 2) and (row == 0 or row == 3 or row == 1 or row == 2)
