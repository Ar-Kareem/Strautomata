import random
import copy
from typing import List, Tuple, Optional

ROWS = 6
COLS = 7
WINDOW_LENGTH = 4
MAX_DEPTH = 4  # Minimax search depth


def policy(board: List[List[int]]) -> int:
    """
    Choose a column (0..6) to drop a disc for the current player (marked 1) on a 6x7 Connect-4 board.
    Strategy:
      1. If there is an immediate winning move, play it.
      2. If the opponent has an immediate winning move, block it.
      3. Use depth-limited Minimax with alpha-beta pruning and a heuristic evaluation to pick a good move.
      4. Prefer center columns when scores tie.
    """
    valid_cols = get_valid_locations(board)
    if not valid_cols:
        # No legal moves (shouldn't happen in normal play), choose 0 as fallback
        return 0

    # 1) Immediate win
    for col in valid_cols:
        row = get_next_open_row(board, col)
        if row is None:
            continue
        tmp = make_move(board, row, col, 1)
        if winning_move(tmp, 1):
            return col

    # 2) Immediate block opponent win
    for col in valid_cols:
        row = get_next_open_row(board, col)
        if row is None:
            continue
        tmp = make_move(board, row, col, -1)
        if winning_move(tmp, -1):
            return col

    # 3) Minimax with alpha-beta
    score, chosen_col = minimax(board, MAX_DEPTH, -float("inf"), float("inf"), True)
    if chosen_col is None:
        # fallback: pick center-most valid column
        return pick_center(valid_cols)
    return chosen_col


def get_valid_locations(board: List[List[int]]) -> List[int]:
    """Return list of column indices that are not full."""
    valid = []
    for col in range(COLS):
        if board[0][col] == 0:
            valid.append(col)
    return valid


def get_next_open_row(board: List[List[int]], col: int) -> Optional[int]:
    """Return the row index (0..ROWS-1) where a disc would land in the column, or None if full."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def make_move(board: List[List[int]], row: int, col: int, piece: int) -> List[List[int]]:
    """Return a new board with the piece dropped into (row,col)."""
    new_board = [r.copy() for r in board]
    new_board[row][col] = piece
    return new_board


def winning_move(board: List[List[int]], piece: int) -> bool:
    """Check whether the given piece has a connect-4 on the board."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # Positive diagonal (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    # Negative diagonal (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    return False


def is_terminal_node(board: List[List[int]]) -> bool:
    return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_locations(board)) == 0


def minimax(board: List[List[int]], depth: int, alpha: float, beta: float, maximizingPlayer: bool) -> Tuple[float, Optional[int]]:
    """
    Minimax with alpha-beta pruning.
    Returns (score, column).
    """
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, 1):
                return (float("inf"), None)
            elif winning_move(board, -1):
                return (-float("inf"), None)
            else:  # Draw
                return (0, None)
        else:
            return (score_position(board, 1), None)

    if maximizingPlayer:
        value = -float("inf")
        best_col = random.choice(valid_locations)
        # Order moves to prefer center (improves pruning)
        ordered_cols = sorted(valid_locations, key=lambda c: abs(c - COLS // 2))
        for col in ordered_cols:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            child = make_move(board, row, col, 1)
            new_score, _ = minimax(child, depth - 1, alpha, beta, False)
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_col
    else:
        value = float("inf")
        best_col = random.choice(valid_locations)
        ordered_cols = sorted(valid_locations, key=lambda c: abs(c - COLS // 2))
        for col in ordered_cols:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            child = make_move(board, row, col, -1)
            new_score, _ = minimax(child, depth - 1, alpha, beta, True)
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_col


def score_window(window: List[int], piece: int) -> int:
    """Score a list of length 4 for the given piece."""
    score = 0
    opp_piece = -piece
    count_piece = window.count(piece)
    count_opp = window.count(opp_piece)
    count_empty = window.count(0)

    if count_piece == 4:
        score += 10000
    elif count_piece == 3 and count_empty == 1:
        score += 100
    elif count_piece == 2 and count_empty == 2:
        score += 5

    if count_opp == 3 and count_empty == 1:
        score -= 80  # immediate threat; prioritize blocking
    elif count_opp == 2 and count_empty == 2:
        score -= 4

    return score


def score_position(board: List[List[int]], piece: int) -> int:
    """Evaluate board favorability for the given piece."""
    score = 0

    # Score center column
    center_array = [board[r][COLS // 2] for r in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 6

    # Horizontal
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLS - 3):
            window = row_array[c:c + WINDOW_LENGTH]
            score += score_window(window, piece)

    # Vertical
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + WINDOW_LENGTH]
            score += score_window(window, piece)

    # Positive diagonal (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(WINDOW_LENGTH)]
            score += score_window(window, piece)

    # Negative diagonal (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += score_window(window, piece)

    return score


def pick_center(valid_cols: List[int]) -> int:
    """Pick the column closest to center among valid columns."""
    return min(valid_cols, key=lambda c: (abs(c - COLS // 2), c))


# Example simple test when running as a script (won't execute on import)
if __name__ == "__main__":
    # Empty board example
    empty_board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    print("Chosen column on empty board:", policy(empty_board))