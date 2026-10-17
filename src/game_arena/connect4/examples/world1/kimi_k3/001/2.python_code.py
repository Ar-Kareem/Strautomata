
import time

DIRS = (1, 7, 6, 8)          # vertical, horizontal, two diagonals (7-bit column stride)
ORDER = (3, 2, 4, 1, 5, 0, 6)  # center-first move ordering
INF = 1 << 30
WIN = 1 << 24

VALID = 0
CENTER = 0
NEAR = 0
for _c in range(7):
    for _r in range(6):
        VALID |= 1 << (_c * 7 + _r)
for _r in range(6):
    CENTER |= 1 << (21 + _r)                       # column 3
    NEAR |= (1 << (14 + _r)) | (1 << (28 + _r))    # columns 2 and 4

try:
    _popc = int.bit_count
except AttributeError:
    def _popc(x):
        return bin(x).count("1")


class _Timeout(Exception):
    pass


TT = {}


def _won(bb):
    for d in DIRS:
        x = bb & (bb >> d)
        if x & (x >> (2 * d)):
            return True
    return False


def _side(bb, empty, playable):
    s = 0
    for d in DIRS:
        two = bb & (bb >> d)
        three = two & (two >> d)
        if three:
            ends = ((three >> d) | (three << (3 * d))) & empty
            if ends:
                s += 8 * _popc(ends) + 100 * _popc(ends & playable)
        s += _popc(((two >> d) | (two << (2 * d))) & empty)
    return s


def _eval(my, opp, heights):
    empty = VALID & ~(my | opp)
    playable = 0
    for c in ORDER:
        h = heights[c]
        if h < 6:
            playable |= 1 << (7 * c + h)
    s = _side(my, empty, playable) - _side(opp, empty, playable)
    s += 3 * (_popc(my & CENTER) - _popc(opp & CENTER))
    s += _popc(my & NEAR) - _popc(opp & NEAR)
    return s


def _negamax(my, opp, heights, depth, alpha, beta, ply, deadline, cnt):
    cnt[0] += 1
    if (cnt[0] & 2047) == 0 and time.perf_counter() >= deadline:
        raise _Timeout()
    key = (my << 49) | opp
    e = TT.get(key)
    if e is not None and e[0] >= depth:
        f = e[2]
        v = e[1]
        if f == 0 or (f == 1 and v <= alpha) or (f == 2 and v >= beta):
            return v
    if depth <= 0:
        return _eval(my, opp, heights)
    a0 = alpha
    best = -INF
    bm = -1
    children = []
    for c in ORDER:
        h = heights[c]
        if h < 6:
            my2 = my | (1 << (7 * c + h))
            ce = TT.get((opp << 49) | my2)
            children.append(((-ce[1]) if ce else 0, c, my2, h))
    if not children:
        return 0
    children.sort(key=lambda t: t[0], reverse=True)
    for _, c, my2, h in children:
        if _won(my2):
            v = WIN - ply
        else:
            heights[c] = h + 1
            v = -_negamax(opp, my2, heights, depth - 1, -beta, -alpha,
                          ply + 1, deadline, cnt)
            heights[c] = h
        if v > best:
            best = v
            bm = c
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= a0:
        f = 1
    elif best >= beta:
        f = 2
    else:
        f = 0
    if len(TT) > 3000000:
        TT.clear()
    TT[key] = (depth, best, f, bm)
    return best


def policy(board):
    try:
        my = 0
        opp = 0
        heights = [0] * 7
        for c in range(7):
            base = 7 * c
            cntv = 0
            for r in range(5, -1, -1):  # bottom row (index 5) up to top (index 0)
                v = board[r][c]
                if v == 0:
                    break
                if v == 1:
                    my |= 1 << (base + 5 - r)
                else:
                    opp |= 1 << (base + 5 - r)
                cntv += 1
            heights[c] = cntv

        legal = [c for c in ORDER if heights[c] < 6]
        if not legal:
            return 3
        if len(legal) == 1:
            return legal[0]

        # Play an immediate win if one exists.
        for c in legal:
            if _won(my | (1 << (7 * c + heights[c]))):
                return c

        best = legal[0]
        start = time.perf_counter()
        deadline = start + 0.88
        cnt = [0]
        key = (my << 49) | opp
        try:
            for depth in range(1, 43):
                _negamax(my, opp, heights, depth, -INF, INF, 0, deadline, cnt)
                e = TT.get(key)
                if e is not None and e[3] >= 0:
                    best = e[3]
                if time.perf_counter() >= deadline:
                    break
        except _Timeout:
            pass
        return best
    except Exception:
        # Absolute fallback: first non-full column.
        try:
            for c in ORDER:
                if board[0][c] == 0:
                    return c
        except Exception:
            pass
        return 3
