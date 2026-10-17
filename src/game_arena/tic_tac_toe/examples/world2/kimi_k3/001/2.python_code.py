
import time

N = 4
CELLS = N * N
FULL = (1 << CELLS) - 1

WIN_MASKS = []
for r in range(N):
    WIN_MASKS.append(sum(1 << (r * N + c) for c in range(N)))
for c in range(N):
    WIN_MASKS.append(sum(1 << (r * N + c) for r in range(N)))
WIN_MASKS.append(sum(1 << (i * N + i) for i in range(N)))
WIN_MASKS.append(sum(1 << (i * N + (N - 1 - i)) for i in range(N)))

POPCNT = [0] * (1 << CELLS)
for i in range(1, 1 << CELLS):
    POPCNT[i] = POPCNT[i >> 1] + (i & 1)

CELL_LINES = [[] for _ in range(CELLS)]
for lm in WIN_MASKS:
    x = lm
    while x:
        b = x & -x
        CELL_LINES[b.bit_length() - 1].append(lm)
        x -= b

POS_WEIGHT = []
for r in range(N):
    for c in range(N):
        if 1 <= r <= 2 and 1 <= c <= 2:
            POS_WEIGHT.append(6)
        elif r in (0, N - 1) and c in (0, N - 1):
            POS_WEIGHT.append(4)
        else:
            POS_WEIGHT.append(1)

ATTACK = (0, 2, 45, 1100)
DEFEND = (0, 2, 60, 1500)
INF = 10 ** 9
WIN_SCORE = 10 ** 7
TT = {}
DEADLINE = 0.0


class _Timeout(Exception):
    pass


def _has_line(mask: int) -> bool:
    for lm in WIN_MASKS:
        if (mask & lm) == lm:
            return True
    return False


def _line_value(cur: int, opp: int) -> int:
    s = 0
    pc = POPCNT
    for lm in WIN_MASKS:
        c = pc[cur & lm]
        o = pc[opp & lm]
        if c:
            if o == 0:
                s += ATTACK[c]
        elif o:
            s -= DEFEND[o]
    return s


def _threat_count(cur: int, opp: int, m: int):
    nc = cur | (1 << m)
    threes = 0
    twos = 0
    for lm in CELL_LINES[m]:
        if POPCNT[opp & lm] == 0:
            c = POPCNT[nc & lm]
            if c == 3:
                threes += 1
            elif c == 2:
                twos += 1
    return threes, twos


def _ordered_moves(cur: int, opp: int, tt_move: int = -1):
    empty = FULL & ~(cur | opp)

    opp_win = set()
    x = empty
    while x:
        b = x & -x
        m = b.bit_length() - 1
        x -= b
        if _has_line(opp | b):
            opp_win.add(m)

    scored = []
    x = empty
    while x:
        b = x & -x
        m = b.bit_length() - 1
        x -= b
        nc = cur | b

        if _has_line(nc):
            sc = 100_000_000
        else:
            sc = POS_WEIGHT[m]
            if m in opp_win:
                sc += 5_000_000
            elif opp_win:
                sc -= 1_000_000

            threes, twos = _threat_count(cur, opp, m)
            sc += threes * 25_000 + twos * 350
            if threes >= 2:
                sc += 400_000

            # If the opponent could play here and make a fork, prefer taking it.
            if _threat_count(opp, cur, m)[0] >= 2:
                sc += 300_000

        if m == tt_move:
            sc += 50_000_000
        scored.append((sc, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _search(cur: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    if time.perf_counter() > DEADLINE:
        raise _Timeout

    key = (cur, opp)
    ent = TT.get(key)
    tt_move = -1
    if ent is not None:
        val, d, flag, bm = ent
        tt_move = bm
        if d >= depth:
            if flag == 0:
                return val
            if flag == 1 and val > alpha:
                alpha = val
            elif flag == 2 and val < beta:
                beta = val
            if alpha >= beta:
                return val

    moves = _ordered_moves(cur, opp, tt_move)
    if not moves:
        return 0

    a0, b0 = alpha, beta
    best = -INF
    best_m = moves[0]

    for m in moves:
        nc = cur | (1 << m)

        # A win now is best for the side to move.
        if _has_line(nc):
            val = WIN_SCORE - ply
            TT[key] = (val, depth, 0, m)
            return val

        if depth == 1:
            val = _line_value(nc, opp)
        else:
            val = -_search(opp, nc, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
            best_m = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= a0:
        flag = 2
    elif best >= b0:
        flag = 1
    else:
        flag = 0
    TT[key] = (best, depth, flag, best_m)
    return best


def _root_search(cur: int, opp: int, depth: int, preferred: int):
    if time.perf_counter() > DEADLINE:
        raise _Timeout

    moves = _ordered_moves(cur, opp, preferred)
    if not moves:
        return 0, -1

    alpha = -INF
    beta = INF
    best_val = -INF
    best_m = moves[0]

    for m in moves:
        nc = cur | (1 << m)
        if _has_line(nc):
            return WIN_SCORE, m
        if depth == 1:
            val = _line_value(nc, opp)
        else:
            val = -_search(opp, nc, depth - 1, -beta, -alpha, 1)

        if val > best_val:
            best_val = val
            best_m = m
        if val > alpha:
            alpha = val

        # Any forced win is enough; do not risk timing out on later root moves.
        if best_val >= WIN_SCORE - 1000:
            return best_val, best_m

    return best_val, best_m


def policy(board: list[list[int]]) -> tuple[int, int]:
    global DEADLINE
    TT.clear()

    cur = 0
    opp = 0
    for r in range(N):
        row = board[r]
        base = r * N
        for c in range(N):
            v = row[c]
            if v == 1:
                cur |= 1 << (base + c)
            elif v == -1:
                opp |= 1 << (base + c)

    empty = FULL & ~(cur | opp)
    if empty == 0:
        return (0, 0)

    # Reasonable even-board opening.
    if cur == 0 and opp == 0:
        return (1, 1)

    # Immediate win.
    x = empty
    while x:
        b = x & -x
        m = b.bit_length() - 1
        x -= b
        if _has_line(cur | b):
            return (m // N, m % N)

    # Immediate block; if several, choose the most useful blocking square.
    opp_wins = set()
    x = empty
    while x:
        b = x & -x
        m = b.bit_length() - 1
        x -= b
        if _has_line(opp | b):
            opp_wins.add(m)

    DEADLINE = time.perf_counter() + 0.92
    moves0 = _ordered_moves(cur, opp, -1)

    if opp_wins:
        for m in moves0:
            if m in opp_wins:
                return (m // N, m % N)

    # A move making two open threes wins on the next move.
    for m in moves0:
        if _threat_count(cur, opp, m)[0] >= 2:
            return (m // N, m % N)

    best_m = moves0[0]
    max_depth = POPCNT[empty]

    for depth in range(1, max_depth + 1):
        try:
            _, mv = _root_search(cur, opp, depth, best_m)
            if mv != -1:
                best_m = mv
        except _Timeout:
            break

    return (best_m // N, best_m % N)
