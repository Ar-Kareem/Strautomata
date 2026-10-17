
import sys
from time import perf_counter

sys.setrecursionlimit(10000)

ROWS = 6
COLS = 7
KEY_SHIFT = 49

MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)
ORDER_BONUS = (0, 2, 4, 6, 4, 2, 0)
COLUMN_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)

POS_PATTERN = (0, 1, 7, 40, 0)
NEG_PATTERN = (0, 1, 8, 50, 0)

WIN_SCORE = 1_000_000
INF = 10**18

EXACT = 0
LOWER = 1
UPPER = 2

BOTTOM_MASKS = [1 << (c * 7) for c in range(COLS)]
TOP_MASKS = [1 << (c * 7 + ROWS - 1) for c in range(COLS)]
COLUMN_MASKS = [((1 << ROWS) - 1) << (c * 7) for c in range(COLS)]

FULL_MASK = 0
for cm in COLUMN_MASKS:
    FULL_MASK |= cm

WINDOW_MASKS = []

# Horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + r)
        WINDOW_MASKS.append(m)

# Vertical
for c in range(COLS):
    for r in range(ROWS - 3):
        m = 0
        for i in range(4):
            m |= 1 << (c * 7 + r + i)
        WINDOW_MASKS.append(m)

# Diagonal up-right
for c in range(COLS - 3):
    for r in range(ROWS - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + (r + i))
        WINDOW_MASKS.append(m)

# Diagonal down-right
for c in range(COLS - 3):
    for r in range(3, ROWS):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + (r - i))
        WINDOW_MASKS.append(m)


class SearchTimeout(Exception):
    pass


_TT = {}
_HISTORY = [0] * COLS
_DEADLINE = 0.0
_NODES = 0


def tt_key(p, o):
    return p | (o << KEY_SHIFT)


def has_four(pos):
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True
    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True
    m = pos & (pos >> 8)
    if m & (m >> 16):
        return True
    return False


def can_play(mask, col):
    return (mask & TOP_MASKS[col]) == 0


def move_mask(mask, col):
    return (mask + BOTTOM_MASKS[col]) & COLUMN_MASKS[col]


def board_to_bitboards(board):
    p = 0
    o = 0
    for r in range(ROWS):
        br = board[r]
        bit_row = ROWS - 1 - r  # input row 5 is bottom -> bit row 0
        for c in range(COLS):
            v = br[c]
            if v == 0:
                continue
            b = 1 << (c * 7 + bit_row)
            if v == 1:
                p |= b
            elif v == -1:
                o |= b
    return p, o, p | o


def ordered_moves(p, mask, tt_move=None):
    moves = []
    for c in MOVE_ORDER:
        if can_play(mask, c):
            m = move_mask(mask, c)
            if has_four(p | m):
                return [(c, m)], True
            score = _HISTORY[c] + ORDER_BONUS[c]
            if c == tt_move:
                score += 1_000_000_000
            moves.append((score, c, m))
    moves.sort(key=lambda x: x[0], reverse=True)
    return [(c, m) for score, c, m in moves], False


def evaluate(p, o, mask):
    score = 0

    # Prefer central columns.
    for c in range(COLS):
        cm = COLUMN_MASKS[c]
        score += COLUMN_WEIGHTS[c] * ((p & cm).bit_count() - (o & cm).bit_count())

    # Penalize states where the opponent would have many immediate winning drops
    # if they were to move; this captures dangerous threat density.
    opp_wins = 0
    for c in MOVE_ORDER:
        if can_play(mask, c):
            m = move_mask(mask, c)
            if has_four(o | m):
                opp_wins += 1
    if opp_wins:
        score -= 250 * opp_wins * opp_wins

    # Pattern scoring over all 4-cell windows.
    for w in WINDOW_MASKS:
        pc = (p & w).bit_count()
        oc = (o & w).bit_count()
        if pc and oc:
            continue
        if pc:
            score += POS_PATTERN[pc]
        elif oc:
            score -= NEG_PATTERN[oc]

    return score


def choose_fallback(p, o, mask):
    legal = [c for c in MOVE_ORDER if can_play(mask, c)]
    if not legal:
        return 0

    # Immediate win.
    for c in legal:
        if has_four(p | move_mask(mask, c)):
            return c

    # Forced single block.
    opp_wins = [c for c in legal if has_four(o | move_mask(mask, c))]
    if len(opp_wins) == 1:
        return opp_wins[0]

    # Prefer moves that do not allow an immediate opponent win.
    safe = []
    for c in legal:
        m = move_mask(mask, c)
        mask2 = mask | m
        opponent_can_win = False
        for d in MOVE_ORDER:
            if can_play(mask2, d) and has_four(o | move_mask(mask2, d)):
                opponent_can_win = True
                break
        if not opponent_can_win:
            safe.append(c)

    return safe[0] if safe else legal[0]


def negamax(p, o, mask, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() > _DEADLINE:
        raise SearchTimeout

    if has_four(o):
        return -WIN_SCORE - depth

    if mask == FULL_MASK:
        return 0

    orig_alpha = alpha
    orig_beta = beta

    key = tt_key(p, o)
    tt_move = None
    entry = _TT.get(key)
    if entry is not None:
        edepth, flag, val, best_move = entry
        tt_move = best_move
        if edepth >= depth:
            if flag == EXACT:
                return val
            if flag == LOWER:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves, winning = ordered_moves(p, mask, tt_move)
    if winning:
        return WIN_SCORE + depth

    if depth == 0:
        return evaluate(p, o, mask)

    best_val = -INF
    best_move = moves[0][0] if moves else None

    for c, m in moves:
        val = -negamax(o, p | m, mask | m, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = c
        if val > alpha:
            alpha = val
        if alpha >= beta:
            _HISTORY[c] += depth * depth
            break

    if best_move is None:
        return 0

    flag = EXACT
    if best_val <= orig_alpha:
        flag = UPPER
    elif best_val >= orig_beta:
        flag = LOWER

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def search_root(p, o, mask, depth, guess_move):
    key = tt_key(p, o)
    tt_move = guess_move
    entry = _TT.get(key)
    if entry is not None:
        tt_move = entry[3]

    moves, winning = ordered_moves(p, mask, tt_move)
    if not moves:
        return 0, 0

    if winning:
        move = moves[0][0]
        val = WIN_SCORE + depth
        _TT[key] = (depth, EXACT, val, move)
        return move, val

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = moves[0][0]

    for c, m in moves:
        val = -negamax(o, p | m, mask | m, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = c
        if val > alpha:
            alpha = val

    _TT[key] = (depth, EXACT, best_val, best_move)
    return best_move, best_val


def policy(board):
    global _TT, _HISTORY, _DEADLINE, _NODES

    p, o, mask = board_to_bitboards(board)
    legal = [c for c in MOVE_ORDER if can_play(mask, c)]

    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0]

    # Strong opening default.
    if mask == 0:
        return 3

    fallback = choose_fallback(p, o, mask)

    _TT = {}
    _HISTORY = [0] * COLS
    _NODES = 0
    _DEADLINE = perf_counter() + 0.93

    best_move = fallback
    empties = ROWS * COLS - mask.bit_count()

    for depth in range(1, empties + 1):
        try:
            move, score = search_root(p, o, mask, depth, best_move)
            best_move = move
            if score >= WIN_SCORE:
                break
        except SearchTimeout:
            break

    if can_play(mask, best_move):
        return best_move

    if can_play(mask, fallback):
        return fallback

    for c in MOVE_ORDER:
        if can_play(mask, c):
            return c

    return 0
