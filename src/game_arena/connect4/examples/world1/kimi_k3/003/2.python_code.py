
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)
MOVE_BIAS = (0, 4, 16, 40, 16, 4, 0)

BOTTOM_MASK = tuple(1 << (7 * c) for c in range(COLS))
COL_MASK = tuple(((1 << ROWS) - 1) << (7 * c) for c in range(COLS))
FULL_MASK = 0
for _m in COL_MASK:
    FULL_MASK |= _m
COL_W = (3, 4, 5, 8, 5, 4, 3)


def _make_windows():
    masks = []

    # Horizontal
    for h in range(ROWS):
        for c in range(COLS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h)
            masks.append(m)

    # Vertical
    for c in range(COLS):
        for h in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << (c * 7 + h + i)
            masks.append(m)

    # Diagonal up-right
    for c in range(COLS - 3):
        for h in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h + i)
            masks.append(m)

    # Diagonal down-right
    for c in range(COLS - 3):
        for h in range(3, ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h - i)
            masks.append(m)

    return tuple(masks)


WINDOWS = _make_windows()
MY_W = (0, 1, 12, 150, 0)
OPP_W = (0, 2, 20, 220, 0)

INF = 10 ** 15
WIN = 10 ** 12
TT_LIMIT = 200000
TIME_LIMIT = 0.90
EXACT, LOWER, UPPER = 0, 1, 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _won(pos):
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


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout


def _evaluate(my, opp, heights, ply):
    my_win = 0
    opp_win = 0
    for c in ORDER:
        h = heights[c]
        if h < 6:
            bit = BOTTOM_MASK[c] << h
            if _won(my | bit):
                my_win += 1
            if _won(opp | bit):
                opp_win += 1

    if my_win:
        return (WIN >> 1) - ply * 16 + my_win * 2048
    if opp_win > 1:
        return -(WIN >> 1) + ply * 16 - opp_win * 2048

    score = 0
    if opp_win:
        score -= 250000

    for mask in WINDOWS:
        mb = (my & mask).bit_count()
        ob = (opp & mask).bit_count()
        if mb:
            if ob:
                continue
            score += MY_W[mb]
        elif ob:
            score -= OPP_W[ob]

    for c in range(COLS):
        d = (my & COL_MASK[c]).bit_count() - (opp & COL_MASK[c]).bit_count()
        if d:
            score += d * COL_W[c]

    return score


def _ordered_moves(my, opp, heights, tt_move):
    legal = []
    opp_win_mask = 0

    for c in ORDER:
        h = heights[c]
        if h < 6:
            bit = BOTTOM_MASK[c] << h
            legal.append((c, bit))
            if _won(opp | bit):
                opp_win_mask |= 1 << c

    scored = []
    for c, bit in legal:
        v = MOVE_BIAS[c]
        if c == tt_move:
            v += 1_000_000_000
        if _won(my | bit):
            v += 500_000_000
        elif (opp_win_mask >> c) & 1:
            v += 250_000_000
        scored.append((v, c))

    scored.sort(reverse=True)
    return [c for _, c in scored]


def _negamax(my, opp, heights, depth, alpha, beta, ply):
    _check_time()

    if _won(opp):
        return -WIN + ply
    if (my | opp) == FULL_MASK:
        return 0

    alpha0 = alpha
    beta0 = beta
    key = my | (opp << 49)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        ed, es, ef, eb = entry
        if ed >= depth:
            if ef == EXACT:
                return es
            if ef == LOWER:
                if es > alpha:
                    alpha = es
            else:
                if es < beta:
                    beta = es
            if alpha >= beta:
                return es
        tt_move = eb

    if depth <= 0:
        return _evaluate(my, opp, heights, ply)

    moves = _ordered_moves(my, opp, heights, tt_move)
    if not moves:
        return 0

    best = -INF
    best_move = moves[0]

    for c in moves:
        bit = BOTTOM_MASK[c] << heights[c]
        heights[c] += 1
        my ^= bit

        if _won(my):
            score = WIN - (ply + 1)
        else:
            score = -_negamax(opp, my, heights, depth - 1, -beta, -alpha, ply + 1)

        my ^= bit
        heights[c] -= 1

        if score > best:
            best = score
            best_move = c
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break

    if best <= alpha0:
        flag = UPPER
    elif best >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    if len(_TT) >= TT_LIMIT:
        _TT.clear()
    _TT[key] = (depth, best, flag, best_move)
    return best


def policy(board: list[list[int]]) -> int:
    global _DEADLINE, _NODES

    my = 0
    opp = 0
    heights = [0] * COLS

    for c in range(COLS):
        h = 0
        for r in range(ROWS - 1, -1, -1):
            v = board[r][c]
            if v == 0:
                break
            if v == 1:
                my |= BOTTOM_MASK[c] << h
            else:
                opp |= BOTTOM_MASK[c] << h
            h += 1
        heights[c] = h

    legal = [c for c in ORDER if heights[c] < ROWS]
    if not legal:
        return 0

    # Immediate win.
    for c in legal:
        if _won(my | (BOTTOM_MASK[c] << heights[c])):
            return int(c)

    # Forced single block.
    opp_wins = [c for c in legal if _won(opp | (BOTTOM_MASK[c] << heights[c]))]
    if len(opp_wins) == 1:
        return int(opp_wins[0])

    best = _ordered_moves(my, opp, heights, -1)[0]

    if len(_TT) >= TT_LIMIT:
        _TT.clear()
    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODES = 0

    empties = ROWS * COLS - sum(heights)
    max_depth = empties if empties < ROWS * COLS else ROWS * COLS

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _DEADLINE:
                break

            alpha = -INF
            beta = INF
            cur_best = best
            cur_score = -INF

            for c in _ordered_moves(my, opp, heights, best):
                bit = BOTTOM_MASK[c] << heights[c]
                heights[c] += 1
                my ^= bit

                if _won(my):
                    score = WIN - 1
                else:
                    score = -_negamax(opp, my, heights, depth - 1, -beta, -alpha, 1)

                my ^= bit
                heights[c] -= 1

                if score > cur_score:
                    cur_score = score
                    cur_best = c
                if score > alpha:
                    alpha = score

            best = cur_best
            if cur_score > (WIN >> 2) or cur_score < -(WIN >> 2):
                break
    except _Timeout:
        pass

    return int(best)
