
import time

ROWS = 6
COLS = 7
ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10 ** 12
WIN_SCORE = 10 ** 9

# Precompute all 4-cell windows.
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

POSITION_WEIGHTS = [
    [3, 4, 5, 7, 5, 4, 3],
    [4, 6, 8, 10, 8, 6, 4],
    [5, 8, 11, 13, 11, 8, 5],
    [5, 8, 11, 13, 11, 8, 5],
    [4, 6, 8, 10, 8, 6, 4],
    [3, 4, 5, 7, 5, 4, 3],
]


def _compute_heights(board):
    """heights[c] is the row index where the next disc lands, or -1 if full."""
    heights = [-1] * COLS
    for c in range(COLS):
        for r in range(ROWS - 1, -1, -1):
            if board[r][c] == 0:
                heights[c] = r
                break
    return heights


def _legal_moves(heights):
    return [c for c in ORDER if heights[c] >= 0]


def _is_win_from(board, r, c, player):
    if r < 0 or c < 0:
        return False

    directions = ((0, 1), (1, 0), (1, 1), (1, -1))

    for dr, dc in directions:
        count = 1

        rr, cc = r + dr, c + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr += dr
            cc += dc

        rr, cc = r - dr, c - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr -= dr
            cc -= dc

        if count >= 4:
            return True

    return False


def _count_immediate_wins(board, heights, player):
    count = 0
    for c in ORDER:
        r = heights[c]
        if r >= 0:
            board[r][c] = player
            if _is_win_from(board, r, c, player):
                count += 1
            board[r][c] = 0
    return count


def _evaluate(board, heights):
    score = 0

    # Positional control, especially center control.
    for r in range(ROWS):
        row = board[r]
        weights = POSITION_WEIGHTS[r]
        for c in range(COLS):
            score += row[c] * weights[c]

    # Window-based evaluation.
    for window in WINDOWS:
        own = 0
        opp = 0
        empty = 0

        for r, c in window:
            v = board[r][c]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1
            else:
                empty += 1

        if own and opp:
            continue

        if own == 4:
            score += 1000000
        elif own == 3 and empty == 1:
            score += 120
        elif own == 2 and empty == 2:
            score += 18
        elif own == 1 and empty == 3:
            score += 2

        if opp == 4:
            score -= 1000000
        elif opp == 3 and empty == 1:
            score -= 150
        elif opp == 2 and empty == 2:
            score -= 22
        elif opp == 1 and empty == 3:
            score -= 2

    # Immediate threats at the frontier.
    own_threats = _count_immediate_wins(board, heights, 1)
    opp_threats = _count_immediate_wins(board, heights, -1)

    if own_threats >= 2:
        score += 5000
    elif own_threats == 1:
        score += 700

    if opp_threats >= 2:
        score -= 7000
    elif opp_threats == 1:
        score -= 900

    return score


def policy(board: list[list[int]]) -> int:
    start = time.perf_counter()
    deadline = start + 0.92

    heights = _compute_heights(board)
    legal = _legal_moves(heights)

    # Absolute fallback: always return a legal move if one exists.
    if not legal:
        return 0

    fallback = legal[0]

    # 1. Immediate win.
    for c in legal:
        r = heights[c]
        board[r][c] = 1
        won = _is_win_from(board, r, c, 1)
        board[r][c] = 0
        if won:
            return c

    # 2. Immediate block.
    opponent_wins = []
    for c in legal:
        r = heights[c]
        board[r][c] = -1
        won = _is_win_from(board, r, c, -1)
        board[r][c] = 0
        if won:
            opponent_wins.append(c)

    if len(opponent_wins) == 1:
        return opponent_wins[0]
    elif len(opponent_wins) > 1:
        # Usually lost, but still return a legal blocking attempt.
        return opponent_wins[0]

    nodes = 0

    def out_of_time():
        return time.perf_counter() >= deadline

    def alphabeta(depth, alpha, beta, player, last_r, last_c, last_player):
        nonlocal nodes

        nodes += 1
        if (nodes & 1023) == 0 and out_of_time():
            raise TimeoutError

        if last_r >= 0 and _is_win_from(board, last_r, last_c, last_player):
            if last_player == 1:
                return WIN_SCORE + depth
            else:
                return -WIN_SCORE - depth

        if depth <= 0:
            return _evaluate(board, heights)

        moves = _legal_moves(heights)
        if not moves:
            return 0

        if player == 1:
            value = -INF
            for c in moves:
                r = heights[c]
                board[r][c] = 1
                heights[c] -= 1
                try:
                    score = alphabeta(depth - 1, alpha, beta, -1, r, c, 1)
                finally:
                    heights[c] += 1
                    board[r][c] = 0

                if score > value:
                    value = score
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = INF
            for c in moves:
                r = heights[c]
                board[r][c] = -1
                heights[c] -= 1
                try:
                    score = alphabeta(depth - 1, alpha, beta, 1, r, c, -1)
                finally:
                    heights[c] += 1
                    board[r][c] = 0

                if score < value:
                    value = score
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    def root_search(depth):
        best_col = fallback
        best_val = -INF
        alpha = -INF
        beta = INF

        for c in _legal_moves(heights):
            if out_of_time():
                raise TimeoutError

            r = heights[c]
            board[r][c] = 1
            heights[c] -= 1
            try:
                val = alphabeta(depth - 1, alpha, beta, -1, r, c, 1)
            finally:
                heights[c] += 1
                board[r][c] = 0

            if val > best_val:
                best_val = val
                best_col = c

            if best_val > alpha:
                alpha = best_val

        return best_col, best_val

    # Iterative deepening. Later positions can be searched deeper.
    stones = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] != 0)
    empties = ROWS * COLS - stones

    if empties > 30:
        max_depth = 7
    elif empties > 18:
        max_depth = 8
    elif empties > 10:
        max_depth = 10
    else:
        max_depth = 12

    best = fallback

    for depth in range(1, max_depth + 1):
        try:
            col, val = root_search(depth)
            best = col

            # If a forced win is found, no need to continue.
            if val >= WIN_SCORE // 2:
                break
        except TimeoutError:
            break
        except Exception:
            # Safety: never fail to return a legal move.
            break

    if best in legal:
        return best

    return fallback
