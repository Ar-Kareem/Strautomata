
from __future__ import annotations

import time

ROWS = 5
COLS = 6
N = ROWS * COLS

_INF = 10**9
_WIN = 10**6

_EXACT = 0
_LOWER = 1
_UPPER = 2

_BITS = [1 << i for i in range(N)]
_FULL = (1 << N) - 1

_TOP = 0
_BOTTOM = 0
_LEFT = 0
_RIGHT = 0

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        b = 1 << i
        if r == 0:
            _TOP |= b
        if r == ROWS - 1:
            _BOTTOM |= b
        if c == 0:
            _LEFT |= b
        if c == COLS - 1:
            _RIGHT |= b

_NOT_TOP = _FULL ^ _TOP
_NOT_BOTTOM = _FULL ^ _BOTTOM
_NOT_LEFT = _FULL ^ _LEFT
_NOT_RIGHT = _FULL ^ _RIGHT

_ADJ = [[] for _ in range(N)]
_ADJ_MASK = [0] * N
_CENTER_WEIGHT = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        if r > 0:
            _ADJ[i].append((i - COLS, "U"))
        if c < COLS - 1:
            _ADJ[i].append((i + 1, "R"))
        if r < ROWS - 1:
            _ADJ[i].append((i + COLS, "D"))
        if c > 0:
            _ADJ[i].append((i - 1, "L"))

        m = 0
        for j, _ in _ADJ[i]:
            m |= 1 << j
        _ADJ_MASK[i] = m

        # Small deterministic centrality tiebreaker.
        _CENTER_WEIGHT[i] = 12 - abs(2 * r - (ROWS - 1)) - abs(2 * c - (COLS - 1))

_TT = {}
_MAX_TT = 300000

_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _check_time() -> None:
    global _nodes
    _nodes += 1
    if (_nodes & 2047) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()


def _key(y: int, o: int) -> int:
    return y | (o << N)


def _to_mask(board) -> int:
    """Accepts numpy arrays, nested 5x6 lists, or flat length-30 lists."""
    m = 0

    if hasattr(board, "ravel"):
        try:
            flat = board.ravel()
            ln = min(N, len(flat))
            for i in range(ln):
                if int(flat[i]):
                    m |= _BITS[i]
            return m
        except Exception:
            pass

    try:
        if len(board) == ROWS:
            first = board[0]
            if hasattr(first, "__iter__") and not isinstance(first, (int, bool)):
                for r in range(ROWS):
                    row = board[r]
                    for c in range(COLS):
                        if int(row[c]):
                            m |= _BITS[r * COLS + c]
                return m
    except Exception:
        pass

    try:
        for i, v in enumerate(board):
            if i >= N:
                break
            if int(v):
                m |= _BITS[i]
    except Exception:
        pass

    return m


def _neighbor_mask(m: int) -> int:
    return (
        ((m & _NOT_TOP) >> COLS)
        | ((m & _NOT_BOTTOM) << COLS)
        | ((m & _NOT_LEFT) >> 1)
        | ((m & _NOT_RIGHT) << 1)
    ) & _FULL


def _has_moves(y: int, o: int) -> bool:
    return bool(
        (((y & _NOT_TOP) >> COLS) & o)
        | (((y & _NOT_BOTTOM) << COLS) & o)
        | (((y & _NOT_LEFT) >> 1) & o)
        | (((y & _NOT_RIGHT) << 1) & o)
    )


def _legal_count(y: int, o: int) -> int:
    return (
        ((((y & _NOT_TOP) >> COLS) & o).bit_count())
        + ((((y & _NOT_BOTTOM) << COLS) & o).bit_count())
        + ((((y & _NOT_LEFT) >> 1) & o).bit_count())
        + ((((y & _NOT_RIGHT) << 1) & o).bit_count())
    )


def _gen_moves(y: int, o: int):
    moves = []
    yy = y
    while yy:
        lsb = yy & -yy
        src = lsb.bit_length() - 1
        for dst, d in _ADJ[src]:
            if o & _BITS[dst]:
                moves.append((src, dst, d))
        yy ^= lsb
    return moves


def _child(y: int, o: int, move):
    src, dst, _ = move
    sb = _BITS[src]
    db = _BITS[dst]
    moved_y = (y ^ sb) | db
    new_o = o ^ db
    # Return next state from the next player-to-move perspective.
    return new_o, moved_y


def _move_to_str(move) -> str:
    src, _, d = move
    return f"{src // COLS},{src % COLS},{d}"


def _immediate_winning_move(y: int, o: int, moves=None):
    if moves is None:
        moves = _gen_moves(y, o)
    for m in moves:
        cy, co = _child(y, o, m)
        if not _has_moves(cy, co):
            return m
    return None


def _active_masks(y: int, o: int):
    """Pieces in occupied components that contain at least one cross-color edge."""
    occ = y | o
    seed = (y & _neighbor_mask(o)) | (o & _neighbor_mask(y))
    active = seed
    while True:
        grown = active | (_neighbor_mask(active) & occ)
        if grown == active:
            break
        active = grown
    return y & active, o & active


def _quick_eval(y: int, o: int) -> int:
    my = y.bit_count()
    opp = o.bit_count()
    ny = _neighbor_mask(y)
    no = _neighbor_mask(o)
    vuln_y = (y & no).bit_count()
    vuln_o = (o & ny).bit_count()
    safe_y = my - vuln_y
    safe_o = opp - vuln_o
    return 120 * (my - opp) + 30 * (vuln_o - vuln_y) + 16 * (safe_y - safe_o)


def _static_eval(y: int, o: int) -> int:
    ay, ao = _active_masks(y, o)

    my = ay.bit_count()
    opp = ao.bit_count()

    ny = _neighbor_mask(ay)
    no = _neighbor_mask(ao)

    vuln_y = (ay & no).bit_count()
    vuln_o = (ao & ny).bit_count()

    safe_y = my - vuln_y
    safe_o = opp - vuln_o

    edges = _legal_count(ay, ao)
    mat = my - opp

    score = 130 * mat
    score += 45 * (safe_y - safe_o)
    score += 35 * (vuln_o - vuln_y)

    # If ahead in active material, prefer simpler positions; if behind, keep play alive.
    if mat >= 0:
        score += 35 - 2 * edges
    else:
        score -= 35
        score += 2 * edges

    # Tiny normal-play parity hint.
    score += 5 if (edges & 1) else -5

    # Dead monochrome components usually do not matter, but use them as a tiny tiebreak.
    score += 2 * ((y ^ ay).bit_count() - (o ^ ao).bit_count())

    return score


def _evaluate_leaf(y: int, o: int) -> int:
    moves = _gen_moves(y, o)
    total = (y | o).bit_count()

    if not moves:
        return -_WIN - total

    for m in moves:
        cy, co = _child(y, o, m)
        if not _has_moves(cy, co):
            return _WIN + total - 1

    score = _static_eval(y, o)

    # In small tactical positions, avoid moves that allow an immediate reply win.
    if len(moves) <= 8:
        safe = 0
        danger = 0
        for m in moves:
            cy, co = _child(y, o, m)
            if _immediate_winning_move(cy, co) is None:
                safe += 1
            else:
                danger += 1
        score += 90 * safe - 160 * danger
        if safe == 0:
            score -= 20000

    return score


def _move_order_value(y: int, o: int, move, depth: int, root: bool) -> int:
    cy, co = _child(y, o, move)
    total = (y | o).bit_count()

    if not _has_moves(cy, co):
        return _WIN + total

    opp_edges = _legal_count(cy, co)

    # Desirability for the current player is negative child evaluation.
    val = -(_quick_eval(cy, co) // 2)
    val -= 60 * opp_edges

    src, dst, _ = move

    # The moved piece is ours in the child opponent-mask co.
    attackers = (_ADJ_MASK[dst] & cy).bit_count()
    support = (_ADJ_MASK[dst] & co).bit_count()
    val -= 24 * attackers
    val += 8 * support

    val += _CENTER_WEIGHT[dst] - _CENTER_WEIGHT[src]

    # Expensive tactical ordering mainly at root / promising small branches.
    if root or (depth >= 3 and opp_edges <= 12):
        if _immediate_winning_move(cy, co) is not None:
            val -= 250000

    return val


def _ordered_moves(y: int, o: int, ttbest=None, depth: int = 1, root: bool = False, moves=None):
    ms = _gen_moves(y, o) if moves is None else list(moves)

    if len(ms) <= 1:
        return ms

    if depth <= 1 and not root:
        if ttbest in ms:
            ms.remove(ttbest)
            ms.insert(0, ttbest)
        return ms

    def k(m):
        v = _move_order_value(y, o, m, depth, root)
        if ttbest is not None and m == ttbest:
            v += 100000000
        return v

    ms.sort(key=k, reverse=True)
    return ms


def _search(y: int, o: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    total = (y | o).bit_count()

    if not _has_moves(y, o):
        return -_WIN - total

    if depth <= 0:
        return _evaluate_leaf(y, o)

    key = _key(y, o)
    alpha0 = alpha
    beta0 = beta

    entry = _TT.get(key)
    ttbest = None
    if entry is not None:
        edepth, flag, val, mv = entry
        ttbest = mv
        if edepth >= depth:
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                if val > alpha:
                    alpha = val
            elif flag == _UPPER:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves = _ordered_moves(y, o, ttbest, depth, False)
    if not moves:
        return -_WIN - total

    best_val = -_INF
    best_move = moves[0]

    for m in moves:
        cy, co = _child(y, o, m)

        if not _has_moves(cy, co):
            val = _WIN + total - 1
        else:
            val = -_search(cy, co, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha0:
        flag = _UPPER
    elif best_val >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_search(y: int, o: int, depth: int):
    _check_time()

    moves = _gen_moves(y, o)
    total = (y | o).bit_count()

    if not moves:
        return -_WIN - total, None

    entry = _TT.get(_key(y, o))
    ttbest = entry[3] if entry is not None else None

    moves = _ordered_moves(y, o, ttbest, depth, True, moves)

    alpha = -_INF
    beta = _INF

    best_val = -_INF
    best_move = moves[0]

    for m in moves:
        _check_time()

        cy, co = _child(y, o, m)

        if not _has_moves(cy, co):
            val = _WIN + total - 1
        else:
            val = -_search(cy, co, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    _TT[_key(y, o)] = (depth, _EXACT, best_val, best_move)
    return best_val, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    global _deadline, _nodes, _TT

    y = _to_mask(you)
    o = _to_mask(opponent)

    # Inputs should be disjoint; this is just defensive.
    o &= ~y

    moves = _gen_moves(y, o)

    # If called on a terminal state, no legal move exists. The engine should not do this.
    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return _move_to_str(moves[0])

    # Exact tactical win: take it immediately.
    win = _immediate_winning_move(y, o, moves)
    if win is not None:
        return _move_to_str(win)

    if len(_TT) > _MAX_TT:
        _TT.clear()

    _deadline = time.perf_counter() + 0.84
    _nodes = 0

    # Legal fallback before any timed search.
    try:
        best = _ordered_moves(y, o, None, 2, True, moves)[0]
    except Exception:
        best = moves[0]

    total = (y | o).bit_count()
    max_depth = min(total, N)

    for depth in range(1, max_depth + 1):
        try:
            val, mv = _root_search(y, o, depth)
            if mv is not None:
                best = mv

            # A forced tactical win was found.
            if val >= _WIN:
                break

            if time.perf_counter() > _deadline - 0.025:
                break

        except _Timeout:
            break
        except Exception:
            # Never risk returning no move because of an unexpected issue.
            break

    return _move_to_str(best)
