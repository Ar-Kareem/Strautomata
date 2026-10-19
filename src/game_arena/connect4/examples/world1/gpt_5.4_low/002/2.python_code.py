
from typing import List, Tuple, Dict

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10**9


def policy(board: List[List[int]]) -> int:
    # Defensive fallback: always return a legal move.
    legal = legal_moves(board)
    if not legal:
        return 0

    # 1) Immediate winning move.
    for c in ordered_moves(legal):
        r = drop_row(board, c)
        board[r][c] = 1
        won = check_win(board, r, c, 1)
        board[r][c] = 0
        if won:
            return c

    # 2) Block opponent immediate win(s).
    opp_wins = []
    for c in ordered_moves(legal):
        r = drop_row(board, c)
        board[r][c] = -1
        won = check_win(board, r, c, -1)
        board[r][c] = 0
        if won:
            opp_wins.append(c)
    if opp_wins:
        for c in ordered_moves(legal):
            if c in opp_wins:
                return c
        return opp_wins[0]

    empties = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    if empties >= 28:
        max_depth = 6
    elif empties >= 16:
        max_depth = 7
    else:
        max_depth = 9

    tt: Dict[Tuple[Tuple[int, ...], int, int], int] = {}
    best_col = ordered_moves(legal)[0]
    best_score = -INF

    alpha = -INF
    beta = INF

    for c in ordered_moves(legal):
        r = drop_row(board, c)
        board[r][c] = 1

        if check_win(board, r, c, 1):
            score = 1_000_000
        else:
            score = -negamax(board, max_depth - 1, -beta, -alpha, -1, tt)

        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_col = c
        if score > alpha:
            alpha = score

    if best_col in legal:
        return best_col
    return legal[0]


def legal_moves(board: List[List[int]]) -> List[int]:
    return [c for c in range(COLS) if board[0][c] == 0]


def ordered_moves(moves: List[int]) -> List[int]:
    s = set(moves)
    return [c for c in CENTER_ORDER if c in s]


def drop_row(board: List[List[int]], col: int) -> int:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def check_win(board: List[List[int]], row: int, col: int, player: int) -> bool:
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


def negamax(
    board: List[List[int]],
    depth: int,
    alpha: int,
    beta: int,
    player: int,
    tt: Dict[Tuple[Tuple[int, ...], int, int], int],
) -> int:
    legal = legal_moves(board)
    if not legal:
        return 0

    key = (tuple(cell for row in board for cell in row), player, depth)
    if key in tt:
        return tt[key]

    if depth == 0:
        val = evaluate(board, player)
        tt[key] = val
        return val

    best = -INF

    # Strong move ordering: center first, then winning moves, then safe-ish moves.
    moves = ordered_moves(legal)

    for c in moves:
        r = drop_row(board, c)
        board[r][c] = player

        if check_win(board, r, c, player):
            score = 1_000_000 - (9 - depth)
        else:
            score = -negamax(board, depth - 1, -beta, -alpha, -player, tt)

        board[r][c] = 0

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def evaluate(board: List[List[int]], player: int) -> int:
    # Score from current player's perspective.
    me = player
    opp = -player
    score = 0

    # Center control.
    center_col = COLS // 2
    center_count_me = sum(1 for r in range(ROWS) if board[r][center_col] == me)
    center_count_opp = sum(1 for r in range(ROWS) if board[r][center_col] == opp)
    score += 6 * center_count_me
    score -= 6 * center_count_opp

    # Windows of length 4.
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += score_window(window, me, opp)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += score_window(window, me, opp)

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, me, opp)

    # Diagonal down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r + i][c - i] for i in range(4)]
            score += score_window(window, me, opp)

    return score


def score_window(window: List[int], me: int, opp: int) -> int:
    cm = window.count(me)
    co = window.count(opp)
    ce = window.count(0)

    if cm == 4:
        return 100000
    if co == 4:
        return -100000

    if cm == 3 and ce == 1:
        return 120
    if cm == 2 and ce == 2:
        return 18
    if cm == 1 and ce == 3:
        return 2

    if co == 3 and ce == 1:
        return -140
    if co == 2 and ce == 2:
        return -20
    if co == 1 and ce == 3:
        return -2

    return 0
