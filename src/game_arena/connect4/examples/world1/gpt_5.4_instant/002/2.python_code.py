
from math import inf

ROWS = 6
COLS = 7
ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    heights = [0] * COLS
    legal = []
    for c in range(COLS):
        r = playable_row(board, c)
        if r != -1:
            legal.append(c)
            heights[c] = r
        else:
            heights[c] = -1

    if not legal:
        return 0

    # 1) Immediate win
    for c in ORDER:
        if c in legal:
            r = heights[c]
            board[r][c] = 1
            w = is_win(board, r, c, 1)
            board[r][c] = 0
            if w:
                return c

    # 2) Immediate block
    opp_wins = []
    for c in ORDER:
        if c in legal:
            r = heights[c]
            board[r][c] = -1
            w = is_win(board, r, c, -1)
            board[r][c] = 0
            if w:
                opp_wins.append(c)
    if opp_wins:
        # If multiple blocks exist, prefer center-most among them.
        for c in ORDER:
            if c in opp_wins:
                return c

    # 3) Safe moves: do not allow opponent immediate win
    safe_moves = []
    for c in ORDER:
        if c not in legal:
            continue
        r = heights[c]
        board[r][c] = 1
        opp_can_win = False
        for oc in ORDER:
            rr = playable_row(board, oc)
            if rr != -1:
                board[rr][oc] = -1
                if is_win(board, rr, oc, -1):
                    opp_can_win = True
                    board[rr][oc] = 0
                    break
                board[rr][oc] = 0
        board[r][c] = 0
        if not opp_can_win:
            safe_moves.append(c)

    candidates = safe_moves if safe_moves else [c for c in ORDER if c in legal]

    # 4) Minimax with alpha-beta
    # Depth chosen to balance speed and strength.
    depth = 5
    best_col = candidates[0]
    best_score = -inf

    alpha = -inf
    beta = inf

    for c in candidates:
        r = playable_row(board, c)
        board[r][c] = 1
        if is_win(board, r, c, 1):
            score = 10**9
        else:
            score = minimax(board, depth - 1, alpha, beta, False)
        board[r][c] = 0

        # Small tie-break by center preference
        score += center_bias(c)

        if score > best_score:
            best_score = score
            best_col = c
        alpha = max(alpha, best_score)

    return best_col


def playable_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def is_win(board, r, c, player):
    return (
        count_dir(board, r, c, 0, 1, player) + count_dir(board, r, c, 0, -1, player) - 1 >= 4 or
        count_dir(board, r, c, 1, 0, player) + count_dir(board, r, c, -1, 0, player) - 1 >= 4 or
        count_dir(board, r, c, 1, 1, player) + count_dir(board, r, c, -1, -1, player) - 1 >= 4 or
        count_dir(board, r, c, 1, -1, player) + count_dir(board, r, c, -1, 1, player) - 1 >= 4
    )


def count_dir(board, r, c, dr, dc, player):
    cnt = 0
    rr, cc = r, c
    while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
        cnt += 1
        rr += dr
        cc += dc
    return cnt


def minimax(board, depth, alpha, beta, maximizing):
    legal = [c for c in ORDER if board[0][c] == 0]

    if not legal:
        return 0

    if depth == 0:
        return evaluate(board)

    if maximizing:
        value = -inf
        for c in legal:
            r = playable_row(board, c)
            board[r][c] = 1
            if is_win(board, r, c, 1):
                score = 10**8 + depth
            else:
                score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            value = max(value, score)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = inf
        for c in legal:
            r = playable_row(board, c)
            board[r][c] = -1
            if is_win(board, r, c, -1):
                score = -10**8 - depth
            else:
                score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            value = min(value, score)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def evaluate(board):
    score = 0

    # Center control
    center_col = 3
    center_count_self = sum(1 for r in range(ROWS) if board[r][center_col] == 1)
    center_count_opp = sum(1 for r in range(ROWS) if board[r][center_col] == -1)
    score += 6 * center_count_self
    score -= 6 * center_count_opp

    # Evaluate all windows of length 4
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += eval_window(window)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += eval_window(window)

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += eval_window(window)

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += eval_window(window)

    # Bonus for immediate threats available next move
    score += 15 * count_immediate_wins(board, 1)
    score -= 18 * count_immediate_wins(board, -1)

    return score


def eval_window(window):
    self_count = window.count(1)
    opp_count = window.count(-1)
    empty_count = window.count(0)

    if self_count and opp_count:
        return 0

    if self_count == 4:
        return 100000
    if opp_count == 4:
        return -100000

    if self_count == 3 and empty_count == 1:
        return 120
    if self_count == 2 and empty_count == 2:
        return 18
    if self_count == 1 and empty_count == 3:
        return 2

    if opp_count == 3 and empty_count == 1:
        return -140
    if opp_count == 2 and empty_count == 2:
        return -20
    if opp_count == 1 and empty_count == 3:
        return -2

    return 0


def count_immediate_wins(board, player):
    cnt = 0
    for c in range(COLS):
        r = playable_row(board, c)
        if r == -1:
            continue
        board[r][c] = player
        if is_win(board, r, c, player):
            cnt += 1
        board[r][c] = 0
    return cnt


def center_bias(c):
    return [0, 1, 2, 3, 2, 1, 0][c]
