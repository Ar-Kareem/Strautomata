
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board = np.array(board, dtype=int)
    rows, cols = 6, 7

    # Check for immediate winning move
    winning_move = find_winning_move(board, 1)
    if winning_move is not None:
        return winning_move

    # Check for opponent's immediate winning move and block it
    opponent_winning_move = find_winning_move(board, -1)
    if opponent_winning_move is not None:
        return opponent_winning_move

    # Evaluate all legal moves using a heuristic
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return -1  # Should not happen per problem constraints

    # Use minimax with alpha-beta pruning to choose the best move
    best_score = -float('inf')
    best_move = None

    for col in legal_moves:
        new_board = make_move(board, col, 1)
        score = minimax(new_board, 0, False, -float('inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = col

    return best_move

def find_winning_move(board: np.ndarray, player: int) -> int:
    """Check if the player can win in the next move."""
    for col in range(7):
        if board[0][col] != 0:
            continue  # Column is full
        new_board = make_move(board, col, player)
        if check_win(new_board, player):
            return col
    return None

def get_legal_moves(board: np.ndarray) -> list[int]:
    """Return list of legal columns (not full)."""
    return [col for col in range(7) if board[0][col] == 0]

def make_move(board: np.ndarray, col: int, player: int) -> np.ndarray:
    """Make a move on the board and return the new board."""
    new_board = board.copy()
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the player has won."""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if (board[row][col] == player and
                board[row][col+1] == player and
                board[row][col+2] == player and
                board[row][col+3] == player):
                return True

    # Check vertical
    for row in range(3):
        for col in range(7):
            if (board[row][col] == player and
                board[row+1][col] == player and
                board[row+2][col] == player and
                board[row+3][col] == player):
                return True

    # Check diagonal (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            if (board[row][col] == player and
                board[row+1][col+1] == player and
                board[row+2][col+2] == player and
                board[row+3][col+3] == player):
                return True

    # Check diagonal (bottom-left to top-right)
    for row in range(3, 6):
        for col in range(4):
            if (board[row][col] == player and
                board[row-1][col+1] == player and
                board[row-2][col+2] == player and
                board[row-3][col+3] == player):
                return True

    return False

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    """Minimax with alpha-beta pruning to evaluate the best move."""
    if check_win(board, 1):
        return 1000 - depth
    if check_win(board, -1):
        return depth - 1000

    if depth == 0:
        return evaluate_board(board)

    if is_maximizing:
        best_score = -float('inf')
        legal_moves = get_legal_moves(board)
        for col in legal_moves:
            new_board = make_move(board, col, 1)
            score = minimax(new_board, depth - 1, False, alpha, beta)
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float('inf')
        legal_moves = get_legal_moves(board)
        for col in legal_moves:
            new_board = make_move(board, col, -1)
            score = minimax(new_board, depth - 1, True, alpha, beta)
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score

def evaluate_board(board: np.ndarray) -> int:
    """Evaluate the board using a heuristic."""
    score = 0
    center_col = 3
    center_weight = 0.5

    # Evaluate horizontal, vertical, and diagonal lines
    for row in range(6):
        for col in range(7):
            if board[row][col] == 1:
                # Horizontal
                score += evaluate_line(board, row, col, 0, 1) * 1.5
                # Vertical
                score += evaluate_line(board, row, col, 1, 0) * 1.5
                # Diagonal (top-left to bottom-right)
                score += evaluate_line(board, row, col, 1, 1) * 1.2
                # Diagonal (bottom-left to top-right)
                score += evaluate_line(board, row, col, 1, -1) * 1.2

            elif board[row][col] == -1:
                # Opponent's pieces reduce our score
                score -= evaluate_line(board, row, col, 0, 1) * 1.5
                score -= evaluate_line(board, row, col, 1, 0) * 1.5
                score -= evaluate_line(board, row, col, 1, 1) * 1.2
                score -= evaluate_line(board, row, col, 1, -1) * 1.2

    # Prefer center columns
    for col in range(7):
        if board[0][col] == 0:  # Column is not full
            if col == center_col:
                score += center_weight
            elif col == center_col - 1 or col == center_col + 1:
                score += center_weight * 0.5

    return score

def evaluate_line(board: np.ndarray, row: int, col: int, dr: int, dc: int) -> int:
    """Evaluate a line (horizontal, vertical, or diagonal) starting at (row, col)."""
    score = 0
    opponent = -1
    my_piece = 1

    for i in range(4):
        r, c = row + i * dr, col + i * dc
        if 0 <= r < 6 and 0 <= c < 7:
            if board[r][c] == my_piece:
                score += 1
            elif board[r][c] == opponent:
                score -= 1
        else:
            break

    # Bonus for open lines (empty cells at the end)
    if score > 0:
        for i in range(4):
            r, c = row + i * dr, col + i * dc
            if 0 <= r < 6 and 0 <= c < 7:
                if board[r][c] == 0:
                    score += 0.1
            else:
                break

    return score
