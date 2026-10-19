
from __future__ import annotations

import time

ROWS = 5
COLS = 6
N = ROWS * COLS

INF = 10**9
MATE = 10**6

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2

TT_LIMIT = 250_000
SOLVED_LIMIT = 150_000

TT = {}
SOLVED = {}

DEADLINE = 0.0
NODES = 0


class _Timeout(Exception):
    pass


_DIRS = ((-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L"))

ADJ = [0] * N
CENTER = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        CENTER[i] = 100 - ((2 * r - (ROWS - 1)) ** 2 + (2 * c - (COLS - 1)) ** 2)
        m = 0
        for dr, dc, _ in _DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                m |= 1 << (rr * COLS + cc)
        ADJ[i] = m

DEG = [x.bit_count() for x in ADJ]

MOVE_ID = [[-1] * N for _ in range(N)]
MOVE_SRC = []
MOVE_DST = []
MOVE_SBIT = []
MOVE_DBIT = []
MOVE_STR = []
MOVE_BONUS = []

for r in range(ROWS):
    for c in range(COLS):
        s = r * COLS + c
        for dr, dc, ch in _DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                d = rr * COLS + cc
                mid = len(MOVE_SRC)
                MOVE_ID[s][d] = mid
                MOVE_SRC.append(s)
                MOVE_DST.append(d)
                MOVE_SBIT.append(1 << s)
                MOVE_DBIT.append(1 << d)
                MOVE_STR.append(f"{r},{c},{ch}")
                MOVE_BONUS.append(
                    4 * CENTER[d] + 2 * CENTER[s] + 15 * (DEG[s] + DEG[d])
                )


def _check_time() -> None:
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise _Timeout()


def _pack(p: int, o: int) -> int:
    return p | (o << N)


def _to_bits(arr) -> int:
    # Nested 5x6 list/array fast path.
    try:
        if len(arr) == ROWS and hasattr(arr[0], "__iter__"):
            b = 0
            for r in range(ROWS):
                row = arr[r]
                for c in range(COLS):
                    if int(row[c]) != 0:
                        b |= 1 << (r * COLS + c)
            return b
    except Exception:
        pass

    # Flat list/array fallback.
    b = 0
    k = 0
    try:
        iterator = arr.flat
    except Exception:
        try:
            iterator = iter(arr)
        except Exception:
            return 0

    for v in iterator:
        if k >= N:
            break

        # If a nested row slipped through, flatten one level.
        if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
            for w in v:
                if k >= N:
                    break
                try:
                    nonzero = int(w) != 0
                except Exception:
                    nonzero = bool(w)
                if nonzero:
                    b |= 1 << k
                k += 1
            continue

        try:
            nonzero = int(v) != 0
        except Exception:
            nonzero = bool(v)
        if nonzero:
            b |= 1 << k
        k += 1

    return b


def _edge_count(p: int, o: int) -> int:
    cnt = 0
    x = p
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb
        cnt += (ADJ[s] & o).bit_count()
    return cnt


def _generate_moves(p: int, o: int) -> list[int]:
    moves = []
    x = p
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb

        t = ADJ[s] & o
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db
            moves.append(MOVE_ID[s][d])
    return moves


def _child_edge_count(p: int, o: int, edges: int, s: int, d: int) -> int:
    # Cross-edge update after moving p-piece s onto o-piece d.
    # Maximum edge reduction on this grid is 7.
    return (
        edges
        - (ADJ[s] & o).bit_count()
        - (ADJ[d] & p).bit_count()
        + 1
        + (ADJ[d] & o).bit_count()
    )


def _child_with_edges(p: int, o: int, edges: int, m: int) -> tuple[int, int, int]:
    s = MOVE_SRC[m]
    d = MOVE_DST[m]
    sb = MOVE_SBIT[m]
    db = MOVE_DBIT[m]
    ce = _child_edge_count(p, o, edges, s, d)
    # Swap perspective: next player becomes "you".
    return o & ~db, (p & ~sb) | db, ce


def _has_immediate_win(p: int, o: int, edges: int = -1) -> bool:
    if edges < 0:
        edges = _edge_count(p, o)
    if edges <= 0 or edges > 7:
        return False

    x = p
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb

        t = ADJ[s] & o
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db
            if _child_edge_count(p, o, edges, s, d) == 0:
                return True
    return False


def _evaluate(p: int, o: int, edges: int = -1) -> int:
    if edges < 0:
        edges = _edge_count(p, o)
    if edges == 0:
        return -MATE

    npieces = p.bit_count()
    opieces = o.bit_count()

    pfront = 0
    ofront = 0
    pdeg2 = 0
    odeg2 = 0

    x = p
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb
        d = (ADJ[s] & o).bit_count()
        if d:
            pfront += 1
        pdeg2 += d * d

    x = o
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb
        d = (ADJ[s] & p).bit_count()
        if d:
            ofront += 1
        odeg2 += d * d

    # Nonterminal tempo + live structural terms.
    score = (
        25
        + 20 * (npieces - opieces)
        + 35 * (pfront - ofront)
        + 18 * (odeg2 - pdeg2)
        + 4 * edges
    )

    # Exact shallow tactics.  A move can remove at most 7 cross-edges, so
    # immediate terminal wins only exist when edges <= 7.  "All moves allow
    # opponent immediate win" can only matter when edges <= 14.
    if edges <= 14:
        safe = 0
        bad = 0
        min_ce = 100

        x = p
        while x:
            sb = x & -x
            s = sb.bit_length() - 1
            x ^= sb

            t = ADJ[s] & o
            while t:
                db = t & -t
                d = db.bit_length() - 1
                t ^= db

                ce = _child_edge_count(p, o, edges, s, d)
                if ce < min_ce:
                    min_ce = ce

                if ce == 0:
                    return MATE - 300

                if ce > 7:
                    safe += 1
                else:
                    cp = o & ~db
                    co = (p & ~sb) | db
                    if _has_immediate_win(cp, co, ce):
                        bad += 1
                    else:
                        safe += 1

        if safe == 0:
            return -MATE + 300

        score += 90 * safe - 140 * bad + 30 * (edges - min_ce) - 8 * min_ce

    elif edges <= 28:
        min_ce = 100
        x = p
        while x:
            sb = x & -x
            s = sb.bit_length() - 1
            x ^= sb

            t = ADJ[s] & o
            while t:
                db = t & -t
                d = db.bit_length() - 1
                t ^= db
                ce = _child_edge_count(p, o, edges, s, d)
                if ce < min_ce:
                    min_ce = ce

        score += 25 * (edges - min_ce) - 5 * min_ce
    else:
        score += 2 * edges

    if score > MATE // 2:
        return MATE // 2
    if score < -MATE // 2:
        return -MATE // 2
    return score


def _children_ordered(
    p: int, o: int, tt_move: int, depth: int, edges: int
) -> list[tuple[int, int, int, int, int]]:
    items = []

    x = p
    while x:
        sb = x & -x
        s = sb.bit_length() - 1
        x ^= sb

        t = ADJ[s] & o
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db

            m = MOVE_ID[s][d]
            ce = _child_edge_count(p, o, edges, s, d)
            cp = o & ~db
            co = (p & ~sb) | db

            sc = MOVE_BONUS[m] - 120 * ce + 30 * (edges - ce)

            if m == tt_move:
                sc += 10_000_000
            if ce == 0:
                sc += 2_000_000
            elif ce <= 7 and _has_immediate_win(cp, co, ce):
                sc -= 1_000_000
            elif ce <= 7:
                sc += 200

            items.append((sc, m, cp, co, ce))

    items.sort(reverse=True)
    return items


def _search(p: int, o: int, depth: int, alpha: int, beta: int, edges: int = -1) -> int:
    _check_time()

    if edges < 0:
        edges = _edge_count(p, o)
    if edges == 0:
        return -MATE

    key = _pack(p, o)
    solved = SOLVED.get(key)
    if solved is not None:
        return MATE - 100 if solved[0] else -MATE + 100

    if depth <= 0:
        return _evaluate(p, o, edges)

    entry = TT.get(key)
    tt_move = -1

    if entry is not None:
        edepth, flag, val, bm = entry
        tt_move = bm
        if edepth >= depth:
            if flag == FLAG_EXACT:
                return val
            if flag == FLAG_LOWER:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    alpha0 = alpha
    beta0 = beta
    best = -INF
    bestm = -1

    for _, m, cp, co, ce in _children_ordered(p, o, tt_move, depth, edges):
        val = -_search(cp, co, depth - 1, -beta, -alpha, ce)

        if val > best:
            best = val
            bestm = m
        if val > alpha:
            alpha = val
            if alpha >= beta:
                break

    if best <= alpha0:
        flag = FLAG_UPPER
    elif best >= beta0:
        flag = FLAG_LOWER
    else:
        flag = FLAG_EXACT

    if len(TT) < TT_LIMIT:
        TT[key] = (depth, flag, best, bestm)

    return best


def _can_win(p: int, o: int, edges: int = -1) -> tuple[bool, int]:
    _check_time()

    key = _pack(p, o)
    old = SOLVED.get(key)
    if old is not None:
        return old

    if edges < 0:
        edges = _edge_count(p, o)

    if edges == 0:
        res = (False, -1)
        if len(SOLVED) < SOLVED_LIMIT:
            SOLVED[key] = res
        return res

    items = _children_ordered(p, o, -1, 99, edges)
    fallback = items[0][1] if items else -1

    for _, m, cp, co, ce in items:
        if ce == 0:
            res = (True, m)
            if len(SOLVED) < SOLVED_LIMIT:
                SOLVED[key] = res
            return res

    for _, m, cp, co, ce in items:
        child_wins, _ = _can_win(cp, co, ce)
        if not child_wins:
            res = (True, m)
            if len(SOLVED) < SOLVED_LIMIT:
                SOLVED[key] = res
            return res

    res = (False, fallback)
    if len(SOLVED) < SOLVED_LIMIT:
        SOLVED[key] = res
    return res


def _initial_order(p: int, o: int, edges: int, moves: list[int]) -> tuple[list[int], int]:
    scored = []

    for m in moves:
        cp, co, ce = _child_with_edges(p, o, edges, m)
        child_solved = SOLVED.get(_pack(cp, co))

        if ce == 0:
            val = 3 * MATE + MOVE_BONUS[m]
        elif child_solved is not None and not child_solved[0]:
            val = 2 * MATE + MOVE_BONUS[m]
        elif child_solved is not None and child_solved[0]:
            val = -2 * MATE + MOVE_BONUS[m]
        else:
            val = -_evaluate(cp, co, ce) + MOVE_BONUS[m] + 35 * (edges - ce) - 4 * ce

        scored.append((val, m))

    scored.sort(reverse=True)
    return [m for _, m in scored], scored[0][1]


def _iterative_root(
    p: int, o: int, edges: int, order: list[int], best: int, total: int
) -> int:
    max_depth = max(1, total)
    depth = 1

    while depth <= max_depth:
        try:
            if time.perf_counter() > DEADLINE:
                raise _Timeout()

            if best in order:
                order = [best] + [m for m in order if m != best]

            alpha = -INF
            local_best = best
            local_score = -INF
            scored = []

            for m in order:
                if time.perf_counter() > DEADLINE:
                    raise _Timeout()

                cp, co, ce = _child_with_edges(p, o, edges, m)
                val = -_search(cp, co, depth - 1, -INF, -alpha, ce)

                scored.append((val, m))

                if val > local_score:
                    local_score = val
                    local_best = m
                if val > alpha:
                    alpha = val

            # Only accept a depth after every root move completed.
            best = local_best
            scored.sort(reverse=True)
            order = [m for _, m in scored]

            # This threshold is only reached by exact terminal/near-terminal tactical proof.
            if local_score >= MATE - 500:
                break

            depth += 1

        except _Timeout:
            break

    return best


def policy(you: list[int], opponent: list[int]) -> str:
    global DEADLINE, NODES

    start = time.perf_counter()
    DEADLINE = start + 0.92
    NODES = 0

    if len(TT) >= TT_LIMIT:
        TT.clear()
    if len(SOLVED) >= SOLVED_LIMIT:
        SOLVED.clear()

    p = _to_bits(you)
    o = _to_bits(opponent) & ~p

    edges = _edge_count(p, o)
    moves = _generate_moves(p, o)

    # Terminal positions should not be queried by the game engine.  There is
    # no legal move in such a state, but return a syntactically valid fallback.
    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return MOVE_STR[moves[0]]

    root_key = _pack(p, o)
    root_solved = SOLVED.get(root_key)
    if root_solved is not None and root_solved[0] and root_solved[1] in moves:
        return MOVE_STR[root_solved[1]]

    # Immediate win, or a previously proven winning child.
    for m in moves:
        cp, co, ce = _child_with_edges(p, o, edges, m)
        if ce == 0:
            return MOVE_STR[m]
        child_solved = SOLVED.get(_pack(cp, co))
        if child_solved is not None and not child_solved[0]:
            return MOVE_STR[m]

    order, best = _initial_order(p, o, edges, moves)

    # Exact solver for endgames / low-branching positions.  Use a short budget
    # unless the position is very small.
    total = (p | o).bit_count()
    if total <= 16 or len(moves) <= 7 or edges <= 10:
        saved_deadline = DEADLINE
        if total <= 13 or len(moves) <= 5 or edges <= 7:
            exact_deadline = saved_deadline
        else:
            exact_deadline = min(saved_deadline, start + 0.40)

        DEADLINE = exact_deadline
        try:
            win, bm = _can_win(p, o, edges)
            if win and bm in moves:
                return MOVE_STR[bm]
        except _Timeout:
            pass
        finally:
            DEADLINE = saved_deadline

    best = _iterative_root(p, o, edges, order, best, total)

    if best not in moves:
        best = moves[0]

    return MOVE_STR[best]
