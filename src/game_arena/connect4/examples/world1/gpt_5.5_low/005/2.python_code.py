
import time

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN_SCORE = 100_000_000

class TimeoutSearch(Exception):
    pass


def policy(board: list[list[int]]) -> int:
    """
    Return a legal column for the current player.
    Board encoding:
      1  = our discs
     -1  = opponent discs
      0  = empty
    """
    legal = [c for c in CENTER_ORDER if board[0][c] == 0]
    if not legal:
        return 0  # Should never happen in a valid non-full game.

    fallback = legal[0]

    # 1. Play an immediate win if available.
    for c in legal:
        r = drop_row(board, c)
        board[r][c] = 1
        won = is_win_from(board, r, c, 1)
        board[r][c] = 0
        if won:
            return c

    # 2. Block opponent's immediate win if needed.
    for c in legal:
        r = drop_row(board, c)
        board[r][c] = -1
        won = is_win_from(board, r, c, -1)
        board[r][c] = 0
        if won:
            return c

    deadline = time.perf_counter() + 0.92
    best_move = fallback

    # Iterative deepening: keep the best fully completed search.
    try:
        depth = 1
        while depth <= 42:
            move, _ = root_search(board, depth, deadline)
            if move is not None:
                best_move = move
            depth += 1
    except TimeoutSearch:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        return fallback

    if board[0][best_move] == 0:
        return best_move
    return fallback


def root_search(board, depth, deadline):
    best_move = None
    best_score = -10**18
    alpha = -10**18
    beta = 10**18

    for c in ordered_legal_moves(board):
        if time.perf_counter() > deadline:
            raise TimeoutSearch()

        r = drop_row(board, c)
        board[r][c] = 1

        if is_win_from(board, r, c, 1):
            score = WIN_SCORE + depth
        else:
            score = minimax(board, depth - 1, alpha, beta, -1, deadline)

        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = c

        alpha = max(alpha, best_score)

    return best_move, best_score


def minimax(board, depth, alpha, beta, turn, deadline):
    if time.perf_counter() > deadline:
        raise TimeoutSearch()

    legal = ordered_legal_moves(board)

    if depth == 0 or not legal:
        return evaluate(board)

    if turn == 1:
        value = -10**18

        for c in legal:
            r = drop_row(board, c)
            board[r][c] = 1

            if is_win_from(board, r, c, 1):
                score = WIN_SCORE + depth
            else:
                score = minimax(board, depth - 1, alpha, beta, -1, deadline)

            board[r][c] = 0

            if score > value:
                value = score
            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return value

    else:
        value = 10**18

        for c in legal:
            r = drop_row(board, c)
            board[r][c] = -1

            if is_win_from(board, r, c, -1):
                score = -WIN_SCORE - depth
            else:
                score = minimax(board, depth - 1, alpha, beta, 1, deadline)

            board[r][c] = 0

            if score < value:
                value = score
            beta = min(beta, value)
            if alpha >= beta:
                break

        return value


def ordered_legal_moves(board):
    return [c for c in CENTER_ORDER if board[0][c] == 0]


def drop_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def is_win_from(board, row, col, player):
    # Check the four directions that can make a connect-four.
    for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
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


def evaluate(board):
    """
    Static evaluation from our perspective.
    Positive is good for player 1, negative is good for player -1.
    """
    score = 0

    # Center control is important in Connect 4.
    center_count = 0
    for r in range(ROWS):
        if board[r][3] == 1:
            center_count += 1
        elif board[r][3] == -1:
            center_count -= 1
    score += center_count * 6

    # Evaluate every possible group of 4.
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += score_window(
                board[r][c],
                board[r][c + 1],
                board[r][c + 2],
                board[r][c + 3],
            )

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            score += score_window(
                board[r][c],
                board[r + 1][c],
                board[r + 2][c],
                board[r + 3][c],
            )

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += score_window(
                board[r][c],
                board[r + 1][c + 1],
                board[r + 2][c + 2],
                board[r + 3][c + 3],
            )

    # Diagonal down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            score += score_window(
                board[r][c],
                board[r + 1][c - 1],
                board[r + 2][c - 2],
                board[r + 3][c - 3],
            )

    # Extra tactical awareness: playable immediate threats.
    score += playable_threat_score(board)

    return score


def score_window(a, b, c, d):
    vals = (a, b, c, d)
    ours = 0
    opps = 0
    empties = 0

    for v in vals:
        if v == 1:
            ours += 1
        elif v == -1:
            opps += 1
        else:
            empties += 1

    if ours and opps:
        return 0

    if ours == 4:
        return WIN_SCORE
    if opps == 4:
        return -WIN_SCORE

    if ours == 3 and empties == 1:
        return 120
    if ours == 2 and empties == 2:
        return 15
    if ours == 1 and empties == 3:
        return 1

    if opps == 3 and empties == 1:
        return -150
    if opps == 2 and empties == 2:
        return -18
    if opps == 1 and empties == 3:
        return -1

    return 0


def playable_threat_score(board):
    """
    Reward moves that are currently playable and create wins;
    penalize opponent's currently playable winning drops.
    """
    score = 0

    for c in range(COLS):
        if board[0][c] != 0:
            continue

        r = drop_row(board, c)

        board[r][c] = 1
        if is_win_from(board, r, c, 1):
            score += 900
        board[r][c] = 0

        board[r][c] = -1
        if is_win_from(board, r, c, -1):
            score -= 1000
        board[r][c] = 0

    return score
