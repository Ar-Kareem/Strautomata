
import time
import math

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

# Precompute every possible 4-cell line on the board.
WINDOWS = []

# Horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))

# Vertical
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))

# Diagonal down-right
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))

# Diagonal up-right
for r in range(3, ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)))


def legal_moves(board):
    return [c for c in CENTER_ORDER if board[0][c] == 0]


def drop_disc(board, col, player):
    """Drop disc for player into col. Return row used, or -1 if illegal."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            board[r][col] = player
            return r
    return -1


def undo_disc(board, row, col):
    board[row][col] = 0


def is_win_from(board, row, col, player):
    """Fast local win check after placing at row,col."""
    directions = ((1, 0), (0, 1), (1, 1), (1, -1))

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


def has_any_win(board, player):
    for window in WINDOWS:
        if all(board[r][c] == player for r, c in window):
            return True
    return False


def evaluate_window(my_count, opp_count, empty_count):
    if my_count and opp_count:
        return 0

    if my_count == 4:
        return 1_000_000
    if opp_count == 4:
        return -1_000_000

    score = 0

    if my_count == 3 and empty_count == 1:
        score += 120
    elif my_count == 2 and empty_count == 2:
        score += 15
    elif my_count == 1 and empty_count == 3:
        score += 2

    if opp_count == 3 and empty_count == 1:
        score -= 150
    elif opp_count == 2 and empty_count == 2:
        score -= 18
    elif opp_count == 1 and empty_count == 3:
        score -= 2

    return score


def evaluate_board(board):
    """Evaluate from the root/current player's perspective: 1 is us, -1 is opponent."""
    score = 0

    # Center control is important in Connect 4 because it participates in more lines.
    center_count = 0
    for r in range(ROWS):
        if board[r][3] == 1:
            center_count += 1
        elif board[r][3] == -1:
            center_count -= 1
    score += center_count * 8

    # Slight preference for near-center columns.
    column_weights = [1, 2, 3, 4, 3, 2, 1]
    for r in range(ROWS):
        for c in range(COLS):
            score += board[r][c] * column_weights[c]

    # Score every 4-cell window.
    for window in WINDOWS:
        my_count = 0
        opp_count = 0
        empty_count = 0

        for r, c in window:
            v = board[r][c]
            if v == 1:
                my_count += 1
            elif v == -1:
                opp_count += 1
            else:
                empty_count += 1

        score += evaluate_window(my_count, opp_count, empty_count)

    return score


def minimax(board, depth, alpha, beta, maximizing, deadline, table):
    if time.perf_counter() > deadline:
        raise TimeoutError

    key = None
    if depth >= 2:
        key = (tuple(tuple(row) for row in board), depth, maximizing)
        if key in table:
            return table[key]

    moves = legal_moves(board)

    if not moves:
        return 0

    # Terminal check.
    if has_any_win(board, 1):
        return 10_000_000 + depth
    if has_any_win(board, -1):
        return -10_000_000 - depth

    if depth == 0:
        return evaluate_board(board)

    if maximizing:
        value = -math.inf

        for col in moves:
            row = drop_disc(board, col, 1)

            if is_win_from(board, row, col, 1):
                score = 10_000_000 + depth
            else:
                score = minimax(board, depth - 1, alpha, beta, False, deadline, table)

            undo_disc(board, row, col)

            if score > value:
                value = score
            alpha = max(alpha, value)

            if alpha >= beta:
                break

    else:
        value = math.inf

        for col in moves:
            row = drop_disc(board, col, -1)

            if is_win_from(board, row, col, -1):
                score = -10_000_000 - depth
            else:
                score = minimax(board, depth - 1, alpha, beta, True, deadline, table)

            undo_disc(board, row, col)

            if score < value:
                value = score
            beta = min(beta, value)

            if alpha >= beta:
                break

    if key is not None:
        table[key] = value

    return value


def choose_fallback(board):
    moves = legal_moves(board)
    if not moves:
        return 0
    return moves[0]


def policy(board: list[list[int]]) -> int:
    """
    Return a legal column index from 0 to 6.
    The board uses:
      0  = empty
      1  = our disc
     -1  = opponent disc
    """
    moves = legal_moves(board)

    # Absolute safety fallback. In a valid Connect 4 game this should not be empty,
    # but returning 0 keeps the function total.
    if not moves:
        return 0

    best_move = choose_fallback(board)

    # 1. Take an immediate win.
    for col in moves:
        row = drop_disc(board, col, 1)
        win = is_win_from(board, row, col, 1)
        undo_disc(board, row, col)

        if win:
            return col

    # 2. Block opponent's immediate win.
    blocking_moves = []
    for col in moves:
        row = drop_disc(board, col, -1)
        win = is_win_from(board, row, col, -1)
        undo_disc(board, row, col)

        if win:
            blocking_moves.append(col)

    if blocking_moves:
        # If several blocks are possible, prefer the most central.
        return sorted(blocking_moves, key=lambda c: abs(c - 3))[0]

    # 3. Iterative deepening alpha-beta search.
    # Keep a conservative deadline to avoid arena timeouts.
    deadline = time.perf_counter() + 0.90

    # Search depths. Depth 7 is often reachable in ordinary positions; if not,
    # iterative deepening keeps the best result from the last completed depth.
    max_depth = 7

    try:
        for depth in range(1, max_depth + 1):
            table = {}
            current_best = best_move
            current_score = -math.inf
            alpha = -math.inf
            beta = math.inf

            for col in moves:
                if time.perf_counter() > deadline:
                    raise TimeoutError

                row = drop_disc(board, col, 1)

                if is_win_from(board, row, col, 1):
                    score = 10_000_000 + depth
                else:
                    score = minimax(
                        board,
                        depth - 1,
                        alpha,
                        beta,
                        False,
                        deadline,
                        table,
                    )

                undo_disc(board, row, col)

                if score > current_score:
                    current_score = score
                    current_best = col

                alpha = max(alpha, current_score)

            best_move = current_best

    except TimeoutError:
        pass
    except Exception:
        # Never risk returning an illegal move due to an unexpected issue.
        return choose_fallback(board)

    # Final legality guard.
    if 0 <= best_move < COLS and board[0][best_move] == 0:
        return best_move

    return choose_fallback(board)
