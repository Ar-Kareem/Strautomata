
from typing import List, Optional
import math
import time

ROWS = 6
COLS = 7
WIN_SCORE = 10**9

CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]


def policy(board: List[List[int]]) -> int:
    start = time.perf_counter()
    time_limit = 0.92  # stay safely under 1 second

    try:
        legal = get_legal_moves(board)
        if not legal:
            return 0  # fallback; should not happen in valid games

        # 1) Immediate winning move
        for c in ordered_moves(legal):
            r = get_next_open_row(board, c)
            if r is not None and is_winning_move(board, r, c, 1):
                return c

        # 2) Immediate block of opponent winning move
        opp_wins = []
        for c in ordered_moves(legal):
            r = get_next_open_row(board, c)
            if r is not None and is_winning_move(board, r, c, -1):
                opp_wins.append(c)
        if opp_wins:
            # If multiple, prefer center-most legal blocking move
            for c in CENTER_ORDER:
                if c in opp_wins:
                    return c
            return opp_wins[0]

        # 3) Filter out moves that allow opponent immediate win, if possible
        safe_moves = []
        for c in ordered_moves(legal):
            child = make_move(board, c, 1)
            opp_legal = get_legal_moves(child)
            opp_can_win = False
            for oc in opp_legal:
                rr = get_next_open_row(child, oc)
                if rr is not None and is_winning_move(child, rr, oc, -1):
                    opp_can_win = True
                    break
            if not opp_can_win:
                safe_moves.append(c)

        candidate_moves = safe_moves if safe_moves else ordered_moves(legal)

        # 4) Iterative deepening alpha-beta
        best_move = candidate_moves[0]
        best_score = -math.inf

        # Small opening shortcut: if board is empty, center is optimal
        if is_board_empty(board) and 3 in legal:
            return 3

        depth = 1
        while True:
            if time.perf_counter() - start > time_limit:
                break

            current_best_move = best_move
            current_best_score = -math.inf

            alpha = -math.inf
            beta = math.inf

            for c in ordered_moves(candidate_moves):
                if time.perf_counter() - start > time_limit:
                    raise TimeoutError

                child = make_move(board, c, 1)
                score = minimax(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    start,
                    time_limit,
                )

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = c
                alpha = max(alpha, current_best_score)

            best_move = current_best_move
            best_score = current_best_score
            depth += 1

        return best_move

    except TimeoutError:
        legal = get_legal_moves(board)
        if legal:
            # Prefer tactical / center-safe fallback
            for c in CENTER_ORDER:
                if c in legal:
                    return c
            return legal[0]
        return 0
    except Exception:
        legal = get_legal_moves(board)
        if legal:
            for c in CENTER_ORDER:
                if c in legal:
                    return c
            return legal[0]
        return 0


def ordered_moves(moves: List[int]) -> List[int]:
    s = set(moves)
    return [c for c in CENTER_ORDER if c in s]


def is_board_empty(board: List[List[int]]) -> bool:
    for row in board:
        for v in row:
            if v != 0:
                return False
    return True


def get_legal_moves(board: List[List[int]]) -> List[int]:
    return [c for c in range(COLS) if board[0][c] == 0]


def get_next_open_row(board: List[List[int]], col: int) -> Optional[int]:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def make_move(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    new_board = [row[:] for row in board]
    r = get_next_open_row(new_board, col)
    if r is not None:
        new_board[r][col] = player
    return new_board


def is_winning_move(board: List[List[int]], row: int, col: int, player: int) -> bool:
    # Check whether placing player at (row, col) would create a 4-in-a-row.
    # board[row][col] is assumed empty or ignored; we test virtually.
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1

        rr, cc = row + dr, col + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr += dr
            cc += dc

        rr, cc = row - dr, col - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr -= dr
            cc -= dc

        if count >= 4:
            return True
    return False


def check_winner(board: List[List[int]], player: int) -> bool:
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r][c + 1] == player
                and board[r][c + 2] == player
                and board[r][c + 3] == player
            ):
                return True

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if (
                board[r][c] == player
                and board[r + 1][c] == player
                and board[r + 2][c] == player
                and board[r + 3][c] == player
            ):
                return True

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r + 1][c + 1] == player
                and board[r + 2][c + 2] == player
                and board[r + 3][c + 3] == player
            ):
                return True

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r - 1][c + 1] == player
                and board[r - 2][c + 2] == player
                and board[r - 3][c + 3] == player
            ):
                return True

    return False


def is_terminal(board: List[List[int]]) -> bool:
    return check_winner(board, 1) or check_winner(board, -1) or not get_legal_moves(board)


def evaluate_window(window: List[int]) -> int:
    my_count = window.count(1)
    opp_count = window.count(-1)
    empty_count = window.count(0)

    if my_count == 4:
        return 100000
    if opp_count == 4:
        return -100000

    score = 0

    if my_count == 3 and empty_count == 1:
        score += 120
    elif my_count == 2 and empty_count == 2:
        score += 12
    elif my_count == 1 and empty_count == 3:
        score += 1

    if opp_count == 3 and empty_count == 1:
        score -= 140
    elif opp_count == 2 and empty_count == 2:
        score -= 14
    elif opp_count == 1 and empty_count == 3:
        score -= 1

    return score


def evaluate_board(board: List[List[int]]) -> int:
    if check_winner(board, 1):
        return WIN_SCORE
    if check_winner(board, -1):
        return -WIN_SCORE

    score = 0

    # Center control
    center_col = COLS // 2
    center_array = [board[r][center_col] for r in range(ROWS)]
    score += 10 * center_array.count(1)
    score -= 10 * center_array.count(-1)

    # Slight preference for near-center columns
    col_weights = [3, 4, 5, 7, 5, 4, 3]
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 1:
                score += col_weights[c]
            elif board[r][c] == -1:
                score -= col_weights[c]

    # Horizontal windows
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += evaluate_window(window)

    # Vertical windows
    for r in range(ROWS - 3):
        for c in range(COLS):
            window = [board[r + i][c] for i in range(4)]
            score += evaluate_window(window)

    # Diagonal down-right windows
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window)

    # Diagonal up-right windows
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window)

    # Immediate threat count bonus/penalty
    my_threats = count_immediate_wins(board, 1)
    opp_threats = count_immediate_wins(board, -1)
    score += 250 * my_threats
    score -= 300 * opp_threats

    return score


def count_immediate_wins(board: List[List[int]], player: int) -> int:
    count = 0
    for c in get_legal_moves(board):
        r = get_next_open_row(board, c)
        if r is not None and is_winning_move(board, r, c, player):
            count += 1
    return count


def minimax(
    board: List[List[int]],
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    start: float,
    time_limit: float,
) -> int:
    if time.perf_counter() - start > time_limit:
        raise TimeoutError

    legal = get_legal_moves(board)
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if check_winner(board, 1):
                return WIN_SCORE + depth
            if check_winner(board, -1):
                return -WIN_SCORE - depth
            return 0
        return evaluate_board(board)

    if maximizing:
        value = -math.inf
        for c in ordered_moves(legal):
            child = make_move(board, c, 1)
            value = max(
                value,
                minimax(child, depth - 1, alpha, beta, False, start, time_limit),
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return int(value)
    else:
        value = math.inf
        for c in ordered_moves(legal):
            child = make_move(board, c, -1)
            value = min(
                value,
                minimax(child, depth - 1, alpha, beta, True, start, time_limit),
            )
            beta = min(beta, value)
            if alpha >= beta:
                break
        return int(value)
