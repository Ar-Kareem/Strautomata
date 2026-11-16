
import time
import random

ROWS = 6
COLS = 7
MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)
ORDER_INDEX = {c: i for i, c in enumerate(MOVE_ORDER)}

WIN_SCORE = 10**9
TIME_LIMIT = 0.95

EXACT = 0
LOWER = 1
UPPER = 2

# Slightly bottom- and center-favoring positional weights
POS_WEIGHTS = (
    (3, 4, 5, 7, 5, 4, 3),
    (4, 6, 8, 10, 8, 6, 4),
    (5, 8, 11, 13, 11, 8, 5),
    (5, 8, 11, 13, 11, 8, 5),
    (6, 10, 13, 15, 13, 10, 6),
    (7, 11, 14, 16, 14, 11, 7),
)

# Precompute all 4-cell windows
WINDOWS = []
for r in range(ROWS):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
for r in range(ROWS - 3):
    for c in range(COLS):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
for r in range(ROWS - 3):
    for c in range(3, COLS):
        WINDOWS.append(((r, c), (r + 1, c - 1), (r + 2, c - 2), (r + 3, c - 3)))

# Deterministic Zobrist hashing
_rng = random.Random(0)
ZOBRIST = [[[(_rng.getrandbits(64), _rng.getrandbits(64))[i] for i in range(2)] for _ in range(COLS)] for _ in range(ROWS)]

_DEADLINE = 0.0
_NODE_COUNT = 0
_TT = {}


class _Timeout(Exception):
    pass


def _check_win(board, row, col, player):
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


def _legal_moves(heights):
    return [c for c in MOVE_ORDER if heights[c] >= 0]


def _immediate_winning_moves(board, heights, player):
    wins = []
    for c in MOVE_ORDER:
        r = heights[c]
        if r < 0:
            continue
        board[r][c] = player
        heights[c] = r - 1
        if _check_win(board, r, c, player):
            wins.append(c)
        heights[c] = r
        board[r][c] = 0
    return wins


def _evaluate(board, heights):
    score = 0

    # Positional weighting
    for r in range(ROWS):
        br = board[r]
        wr = POS_WEIGHTS[r]
        for c in range(COLS):
            v = br[c]
            if v:
                score += v * wr[c]

    # Pattern scoring
    for window in WINDOWS:
        c1 = 0
        c2 = 0
        empty_r = -1
        empty_c = -1

        for r, c in window:
            v = board[r][c]
            if v == 1:
                c1 += 1
            elif v == -1:
                c2 += 1
            else:
                empty_r, empty_c = r, c

        if c1 and c2:
            continue

        empties = 4 - c1 - c2

        if c1 == 4:
            score += 100000
        elif c2 == 4:
            score -= 100000
        elif c1 == 3 and empties == 1:
            score += 120 if heights[empty_c] == empty_r else 50
        elif c2 == 3 and empties == 1:
            score -= 140 if heights[empty_c] == empty_r else 55
        elif c1 == 2 and empties == 2:
            score += 14
        elif c2 == 2 and empties == 2:
            score -= 16
        elif c1 == 1 and empties == 3:
            score += 2
        elif c2 == 1 and empties == 3:
            score -= 2

    return score


def _ordered_moves_from_heights(heights, preferred=None):
    moves = [c for c in MOVE_ORDER if heights[c] >= 0]
    if preferred in moves:
        return [preferred] + [c for c in moves if c != preferred]
    return moves


def _ordered_subset(moves, preferred=None):
    moves = sorted(moves, key=lambda c: ORDER_INDEX[c])
    if preferred in moves:
        return [preferred] + [c for c in moves if c != preferred]
    return moves


def _negamax(board, heights, depth, alpha, beta, player, hsh):
    global _NODE_COUNT, _DEADLINE, _TT

    _NODE_COUNT += 1
    if (_NODE_COUNT & 2047) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout

    original_alpha = alpha
    original_beta = beta
    tt_key = (hsh, player)
    entry = _TT.get(tt_key)
    tt_move = None

    if entry is not None:
        entry_depth, flag, value, best_move = entry
        tt_move = best_move
        if entry_depth >= depth:
            if flag == EXACT:
                return value
            if flag == LOWER:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    moves = _ordered_moves_from_heights(heights, tt_move)
    if not moves:
        return 0

    if depth == 0:
        return player * _evaluate(board, heights)

    best_value = -WIN_SCORE
    best_move = moves[0]

    piece_index = 1 if player == 1 else 0

    for c in moves:
        r = heights[c]
        board[r][c] = player
        heights[c] = r - 1
        new_hash = hsh ^ ZOBRIST[r][c][piece_index]

        if _check_win(board, r, c, player):
            value = WIN_SCORE + depth
        else:
            value = -_negamax(board, heights, depth - 1, -beta, -alpha, -player, new_hash)

        heights[c] = r
        board[r][c] = 0

        if value > best_value:
            best_value = value
            best_move = c

        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    if best_value <= original_alpha:
        flag = UPPER
    elif best_value >= original_beta:
        flag = LOWER
    else:
        flag = EXACT

    _TT[tt_key] = (depth, flag, best_value, best_move)
    return best_value


def _root_search(board, heights, depth, hsh, candidate_moves, preferred_move=None):
    global _DEADLINE

    if time.perf_counter() >= _DEADLINE:
        raise _Timeout

    tt_entry = _TT.get((hsh, 1))
    tt_move = tt_entry[3] if tt_entry is not None else None

    preferred = preferred_move if preferred_move in candidate_moves else tt_move
    moves = _ordered_subset(candidate_moves, preferred)

    alpha = -WIN_SCORE
    beta = WIN_SCORE
    best_value = -WIN_SCORE
    best_move = moves[0]

    for c in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout

        r = heights[c]
        board[r][c] = 1
        heights[c] = r - 1
        new_hash = hsh ^ ZOBRIST[r][c][1]

        if _check_win(board, r, c, 1):
            value = WIN_SCORE + depth
        else:
            value = -_negamax(board, heights, depth - 1, -beta, -alpha, -1, new_hash)

        heights[c] = r
        board[r][c] = 0

        if value > best_value:
            best_value = value
            best_move = c

        if value > alpha:
            alpha = value

    _TT[(hsh, 1)] = (depth, EXACT, best_value, best_move)
    return best_value, best_move


def policy(board):
    global _DEADLINE, _NODE_COUNT, _TT

    # Copy to mutable board
    b = [row[:] for row in board]

    # Build heights and hash
    heights = []
    hsh = 0
    for c in range(COLS):
        top_empty = -1
        for r in range(ROWS - 1, -1, -1):
            v = b[r][c]
            if v == 0:
                top_empty = r
                break
        heights.append(top_empty)

    for r in range(ROWS):
        for c in range(COLS):
            v = b[r][c]
            if v == 1:
                hsh ^= ZOBRIST[r][c][1]
            elif v == -1:
                hsh ^= ZOBRIST[r][c][0]

    legal = _legal_moves(heights)
    if not legal:
        return 0  # Should not happen in a valid game

    # 1) Immediate win
    my_wins = _immediate_winning_moves(b, heights, 1)
    if my_wins:
        return my_wins[0]

    # 2) Forced immediate block
    opp_wins = _immediate_winning_moves(b, heights, -1)
    if len(opp_wins) == 1 and opp_wins[0] in legal:
        return opp_wins[0]

    # 3) Avoid moves that give opponent an immediate win, if possible
    safe_moves = []
    for c in legal:
        r = heights[c]
        b[r][c] = 1
        heights[c] = r - 1

        if _check_win(b, r, c, 1):
            opponent_has_win = False
        else:
            opponent_has_win = len(_immediate_winning_moves(b, heights, -1)) > 0

        heights[c] = r
        b[r][c] = 0

        if not opponent_has_win:
            safe_moves.append(c)

    candidates = safe_moves if safe_moves else legal
    best_move = candidates[0]

    # Search
    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODE_COUNT = 0
    _TT = {}

    preferred = best_move
    max_depth = 10

    for depth in range(1, max_depth + 1):
        try:
            value, move = _root_search(b, heights, depth, hsh, candidates, preferred)
            if move in legal:
                best_move = move
                preferred = move
            if value >= WIN_SCORE // 2:
                break
        except _Timeout:
            break

    if best_move in legal:
        return best_move
    return legal[0]
