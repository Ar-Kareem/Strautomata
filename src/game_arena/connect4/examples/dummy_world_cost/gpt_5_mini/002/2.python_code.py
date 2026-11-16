
import math
import random
from typing import List, Optional, Tuple

ROWS = 6
COLUMNS = 7
WINDOW_LENGTH = 4
PLAYER = 1
OPPONENT = -1

def policy(board: List[List[int]]) -> int:
    """
    Returns the chosen column (0-6) for the current player (1).
    """
    # Defensive copy not strictly needed here but keep board read-only
    board = [row[:] for row in board]

    valid_cols = get_valid_locations(board)
    if not valid_cols:
        # No valid moves, but to be safe return 0
        return 0

    # 1) Immediate winning moves
    for col in valid_cols:
        row = get_next_open_row(board, col)
        if row is None:
            continue
        temp = [r[:] for r in board]
        temp[row][col] = PLAYER
        if winning_move(temp, PLAYER):
            return col

    # 2) Block opponent's immediate winning moves
    opponent_wins = []
    for col in valid_cols:
        row = get_next_open_row(board, col)
        if row is None:
            continue
        temp = [r[:] for r in board]
        temp[row][col] = OPPONENT
        if winning_move(temp, OPPONENT):
            opponent_wins.append(col)
    if opponent_wins:
        # If multiple, pick one of them (best we can do). Prefer center-most.
        return sorted(opponent_wins, key=lambda c: abs(c - COLUMNS // 2))[0]

    # 3) Minimax with alpha-beta
    empties = sum(1 for r in board for v in r if v == 0)
    # adapt depth based on emptiness to manage time
    if empties >= 32:
        depth = 4
    elif empties >= 20:
        depth = 5
    else:
        depth = 6

    col, _ = minimax(board, depth, -math.inf, math.inf, True)
    if col is None:
        # fallback: choose center if available, else random valid
        center = COLUMNS // 2
        if center in valid_cols:
            return center
        return random.choice(valid_cols)
    return col

def get_valid_locations(board: List[List[int]]) -> List[int]:
    valid = []
    for c in range(COLUMNS):
        if board[0][c] == 0:
            valid.append(c)
    return valid

def get_next_open_row(board: List[List[int]], col: int) -> Optional[int]:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def winning_move(board: List[List[int]], piece: int) -> bool:
    # Horizontal
    for r in range(ROWS):
        for c in range(COLUMNS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # Vertical
    for c in range(COLUMNS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # Positive diagonal
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    # Negative diagonal
    for r in range(3, ROWS):
        for c in range(COLUMNS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    return False

def evaluate_window(window: List[int], piece: int) -> int:
    score = 0
    opp_piece = OPPONENT if piece == PLAYER else PLAYER
    count_piece = window.count(piece)
    count_opp = window.count(opp_piece)
    count_empty = window.count(0)

    if count_piece == 4:
        score += 100000
    elif count_piece == 3 and count_empty == 1:
        score += 100
    elif count_piece == 2 and count_empty == 2:
        score += 10

    if count_opp == 3 and count_empty == 1:
        score -= 80
    elif count_opp == 2 and count_empty == 2:
        score -= 5

    return score

def score_position(board: List[List[int]], piece: int) -> int:
    score = 0
    # Center column preference
    center_col = COLUMNS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == piece)
    score += center_count * 6

    # Horizontal
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLUMNS - 3):
            window = row_array[c:c + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Vertical
    for c in range(COLUMNS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Pos diagonal
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # Neg diagonal
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            window = [board[r + 3 - i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board: List[List[int]]) -> bool:
    return winning_move(board, PLAYER) or winning_move(board, OPPONENT) or not any(board[0][c] == 0 for c in range(COLUMNS))

def minimax(board: List[List[int]], depth: int, alpha: float, beta: float, maximizingPlayer: bool) -> Tuple[Optional[int], float]:
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, PLAYER):
                return None, 1e9
            elif winning_move(board, OPPONENT):
                return None, -1e9
            else:
                return None, 0  # draw
        else:
            return None, score_position(board, PLAYER)

    if maximizingPlayer:
        value = -math.inf
        best_col = random.choice(valid_locations)
        # Move ordering: prefer center and then outward
        for col in sorted(valid_locations, key=lambda c: abs(c - COLUMNS // 2)):
            row = get_next_open_row(board, col)
            if row is None:
                continue
            temp = [r[:] for r in board]
            temp[row][col] = PLAYER
            _, new_score = minimax(temp, depth - 1, alpha, beta, False)
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_locations)
        for col in sorted(valid_locations, key=lambda c: abs(c - COLUMNS // 2)):
            row = get_next_open_row(board, col)
            if row is None:
                continue
            temp = [r[:] for r in board]
            temp[row][col] = OPPONENT
            _, new_score = minimax(temp, depth - 1, alpha, beta, True)
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value
