
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

MATE = 1_000_000
INF = 2_000_000_000
EXACT_DEPTH = 64
TIME_LIMIT = 0.90

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2

_BIT = [1 << i for i in range(N)]
_NEI = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        m = 0
        if r > 0:
            m |= _BIT[(r - 1) * COLS + c]
        if r + 1 < ROWS:
            m |= _BIT[(r + 1) * COLS + c]
        if c > 0:
            m |= _BIT[r * COLS + c - 1]
        if c + 1 < COLS:
            m |= _BIT[r * COLS + c + 1]
        _NEI[i] = m

_DEG = [x.bit_count() for x in _NEI]

_EDGE_ID = [-1] * (N * N)
_FROM = []
_TO = []
_FROM_BIT = []
_TO_BIT = []
_MOVE_STR = []

_DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in _DIRS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                e = len(_FROM)
                _FROM.append(i)
                _TO.append(j)
                _FROM_BIT.append(_BIT[i])
                _TO_BIT.append(_BIT[j])
                _MOVE_STR.append(f"{r},{c},{ch}")
                _EDGE_ID[i * N + j] = e

# Central/high-degree squares are a little more valuable for tie-breaking.
_CELL_WEIGHT = []
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        doubled_center_distance = abs(2 * r - (ROWS - 1)) + abs(2 * c - (COLS - 1))
        _CELL_WEIGHT.append(4 * _DEG[i] - doubled_center_distance)

_NEI = tuple(_NEI)
_DEG = tuple(_DEG)
_EDGE_ID = tuple(_EDGE_ID)
_FROM = tuple(_FROM)
_TO = tuple(_TO)
_FROM_BIT = tuple(_FROM_BIT)
_TO_BIT = tuple(_TO_BIT)
_MOVE_STR = tuple(_MOVE_STR)
_CELL_WEIGHT = tuple(_CELL_WEIGHT)

_TT = {}
_IMM_CACHE = {}
_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _board_to_bits(board):
    bits = 0

    try:
        first = board[0]
        try:
            len(first)
            nested = True
        except Exception:
            nested = False

        if nested:
            for r in range(ROWS):
                row = board[r]
                for c in range(COLS):
                    idx = r * COLS + c
                    try:
                        if row[c]:
                            bits |= _BIT[idx]
                    except Exception:
                        if board[r, c]:
                            bits |= _BIT[idx]
            return bits
        else:
            for i in range(N):
                if board[i]:
                    bits |= _BIT[i]
            return bits
    except Exception:
        pass

    try:
        flat = board.ravel()
        for i in range(N):
            if flat[i]:
                bits |= _BIT[i]
        return bits
    except Exception:
        pass

    # Very defensive generic fallback.
    try:
        idx = 0
        for row in board:
            try:
                it = iter(row)
                for v in it:
                    if idx < N and v:
                        bits |= _BIT[idx]
                    idx += 1
                    if idx >= N:
                        break
            except TypeError:
                if idx < N and row:
                    bits |= _BIT[idx]
                idx += 1
            if idx >= N:
                break
    except Exception:
        pass

    return bits


def _key(me, opp):
    return me | (opp << N)


def _gen_moves(me, opp):
    moves = []
    x = me
    while x:
        b = x & -x
        i = b.bit_length() - 1
        t = _NEI[i] & opp
        while t:
            tb = t & -t
            j = tb.bit_length() - 1
            moves.append(_EDGE_ID[i * N + j])
            t ^= tb
        x ^= b
    return moves


def _legal_count(me, opp):
    cnt = 0
    x = me
    while x:
        b = x & -x
        cnt += (_NEI[b.bit_length() - 1] & opp).bit_count()
        x ^= b
    return cnt


def _apply(me, opp, move):
    fb = _FROM_BIT[move]
    tb = _TO_BIT[move]
    moved_me = (me ^ fb) | tb
    reduced_opp = opp ^ tb
    # Swap perspective: next player owns reduced_opp.
    return reduced_opp, moved_me


def _neighbor_union(bits):
    res = 0
    x = bits
    while x:
        b = x & -x
        res |= _NEI[b.bit_length() - 1]
        x ^= b
    return res


def _frontier_count(a, b):
    return (a & _neighbor_union(b)).bit_count()


def _weighted_sum(bits):
    s = 0
    x = bits
    while x:
        b = x & -x
        s += _CELL_WEIGHT[b.bit_length() - 1]
        x ^= b
    return s


def _active_counts(me, opp):
    occ = me | opp
    rem = occ
    active_me = 0
    active_opp = 0
    active_components = 0

    while rem:
        start = rem & -rem
        comp = 0
        frontier = start

        while frontier:
            comp |= frontier
            nxt = _neighbor_union(frontier) & occ & ~comp
            frontier = nxt

        rem &= ~comp
        cm = (comp & me).bit_count()
        co = (comp & opp).bit_count()
        if cm and co:
            active_components += 1
            active_me += cm
            active_opp += co

    return active_me, active_opp, active_components


def _has_terminal_move(me, opp):
    k = _key(me, opp)
    cached = _IMM_CACHE.get(k)
    if cached is not None:
        return cached == 1

    moves = _gen_moves(me, opp)

    # A single clobber move can only remove cross-edges incident to its
    # source/target pair. On this grid that is at most 7, so >7 legal moves
    # cannot be reduced to zero in one move.
    if not moves or len(moves) > 7:
        _IMM_CACHE[k] = 0
        return False

    for m in moves:
        cme, copp = _apply(me, opp, m)
        if _legal_count(cme, copp) == 0:
            _IMM_CACHE[k] = 1
            return True

    _IMM_CACHE[k] = 0
    return False


def _token_value(me, opp, moves):
    # Exact solver for positions where every active component is just one
    # isolated adjacent opposing pair. Then the game is simply parity.
    k = len(moves)
    if k == 0 or k > 15:
        return None

    occ = me | opp
    seen = 0

    for m in moves:
        i = _FROM[m]
        j = _TO[m]
        bi = _FROM_BIT[m]
        bj = _TO_BIT[m]
        pair = bi | bj

        if seen & pair:
            return None
        if (_NEI[i] & occ) != bj:
            return None
        if (_NEI[j] & occ) != bi:
            return None

        seen |= pair

    remaining = occ.bit_count() - k
    if k & 1:
        return MATE + remaining
    return -MATE - remaining


def _forced_loss_in_two(me, opp, moves, total):
    # Exact: if every legal move lets the opponent end the game immediately.
    if len(moves) > 14:
        return None

    for m in moves:
        cme, copp = _apply(me, opp, m)
        cm = _legal_count(cme, copp)
        if cm == 0:
            return None
        if cm > 7:
            return None
        if not _has_terminal_move(cme, copp):
            return None

    return -MATE - (total - 2)


def _should_extend(move_count, total):
    return (
        move_count == 1
        or (move_count <= 2 and total <= 24)
        or (move_count <= 3 and total <= 20)
        or (move_count <= 4 and total <= 16)
        or total <= 10
    )


def _evaluate(me, opp, moves):
    cross = len(moves)
    my_n = me.bit_count()
    op_n = opp.bit_count()
    mat = my_n - op_n

    my_front = _frontier_count(me, opp)
    op_front = _frontier_count(opp, me)

    score = 20
    score += 55 * mat
    score += 30 * (my_front - op_front)
    score += 5 * cross
    score += 2 * (_weighted_sum(me) - _weighted_sum(opp))

    if cross <= 14:
        am, ao, ac = _active_counts(me, opp)
        active_diff = am - ao
        # Downweight irrelevant dead material.
        score += 35 * (active_diff - mat)
        if ac:
            score += 18 if (ac & 1) else -18

    if cross <= 18:
        best_safe_child = 999
        total_child = 0
        safe = 0
        trap = 0

        for m in moves:
            cme, copp = _apply(me, opp, m)
            cm = _legal_count(cme, copp)
            total_child += cm

            opponent_can_end = False
            if 0 < cm <= 7 and _has_terminal_move(cme, copp):
                opponent_can_end = True

            if opponent_can_end:
                trap += 1
            else:
                safe += 1
                if cm < best_safe_child:
                    best_safe_child = cm

        if safe:
            avg_child = total_child // cross
            score += 80 * (cross - best_safe_child)
            score += 12 * (cross - avg_child)
            score += 30 * safe - 22 * trap
            if best_safe_child <= 2:
                score += 250
        else:
            score -= 100_000

    if score > 400_000:
        return 400_000
    if score < -400_000:
        return -400_000
    return int(score)


def _move_order_score(me, opp, move, tt_move):
    cme, copp = _apply(me, opp, move)
    child_moves = _legal_count(cme, copp)

    if child_moves == 0:
        score = 1_000_000
    else:
        to_sq = _TO[move]
        from_sq = _FROM[move]

        score = -1000 * child_moves

        if child_moves <= 7 and _has_terminal_move(cme, copp):
            score -= 200_000

        # Penalize direct recapture vulnerability of the moved piece.
        retaliation = (_NEI[to_sq] & cme).bit_count()
        support = (_NEI[to_sq] & copp).bit_count()

        score -= 90 * retaliation
        score += 12 * support
        score += _CELL_WEIGHT[to_sq] - (_CELL_WEIGHT[from_sq] // 2)

    if move == tt_move:
        score += 10_000_000

    return score


def _order_moves(me, opp, moves, tt_move=-1):
    scored = []
    for m in moves:
        scored.append((_move_order_score(me, opp, m, tt_move), m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _search(me, opp, depth, alpha, beta):
    global _nodes

    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()

    k = _key(me, opp)
    alpha_orig = alpha
    beta_orig = beta

    entry = _TT.get(k)
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
            elif flag == FLAG_UPPER:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves = _gen_moves(me, opp)
    total = (me | opp).bit_count()

    if not moves:
        val = -MATE - total
        _TT[k] = (EXACT_DEPTH, FLAG_EXACT, val, -1)
        _IMM_CACHE[k] = 0
        return val

    if len(moves) <= 7:
        for m in moves:
            cme, copp = _apply(me, opp, m)
            if _legal_count(cme, copp) == 0:
                val = MATE + total - 1
                _TT[k] = (EXACT_DEPTH, FLAG_EXACT, val, m)
                _IMM_CACHE[k] = 1
                return val
        _IMM_CACHE[k] = 0

    tv = _token_value(me, opp, moves)
    if tv is not None:
        _TT[k] = (EXACT_DEPTH, FLAG_EXACT, tv, moves[0])
        return tv

    fl = _forced_loss_in_two(me, opp, moves, total)
    if fl is not None:
        _TT[k] = (EXACT_DEPTH, FLAG_EXACT, fl, moves[0])
        return fl

    if depth <= 0:
        if _should_extend(len(moves), total):
            depth = 1
        else:
            val = _evaluate(me, opp, moves)
            _TT[k] = (0, FLAG_EXACT, val, -1)
            return val

    ordered = _order_moves(me, opp, moves, tt_move)

    best = -INF
    best_move = ordered[0]
    first = True

    for m in ordered:
        cme, copp = _apply(me, opp, m)

        if first:
            score = -_search(cme, copp, depth - 1, -beta, -alpha)
            first = False
        else:
            # Principal variation search.
            if depth >= 2:
                score = -_search(cme, copp, depth - 1, -alpha - 1, -alpha)
                if alpha < score < beta:
                    score = -_search(cme, copp, depth - 1, -beta, -alpha)
            else:
                score = -_search(cme, copp, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = FLAG_UPPER
    elif best >= beta_orig:
        flag = FLAG_LOWER
    else:
        flag = FLAG_EXACT

    _TT[k] = (depth, flag, best, best_move)
    return best


def policy(you: list[int], opponent: list[int]) -> str:
    global _deadline, _nodes

    me = _board_to_bits(you)
    opp = _board_to_bits(opponent)

    moves = _gen_moves(me, opp)

    # The game engine should not ask for a move in terminal states.
    # If it does, no legal move exists; this is only a last-resort string.
    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return _MOVE_STR[moves[0]]

    if len(_TT) > 300_000:
        _TT.clear()
        _IMM_CACHE.clear()
    elif len(_IMM_CACHE) > 200_000:
        _IMM_CACHE.clear()

    _deadline = time.perf_counter() + TIME_LIMIT
    _nodes = 0

    root_key = _key(me, opp)
    entry = _TT.get(root_key)
    tt_best = entry[3] if entry is not None else -1

    try:
        ordered = _order_moves(me, opp, moves, tt_best)
    except Exception:
        ordered = list(moves)

    best = ordered[0]

    # Never miss an immediate win at the root.
    if len(moves) <= 7:
        for m in ordered:
            cme, copp = _apply(me, opp, m)
            if _legal_count(cme, copp) == 0:
                return _MOVE_STR[m]

    total = (me | opp).bit_count()
    max_depth = total - 1
    if max_depth < 1:
        max_depth = 1
    if max_depth > 30:
        max_depth = 30

    best_val = -INF

    depth = 1
    while depth <= max_depth:
        try:
            if time.perf_counter() > _deadline:
                break

            if best in ordered and ordered[0] != best:
                ordered = [best] + [m for m in ordered if m != best]

            alpha = -INF
            beta = INF
            cur_best = best
            cur_val = -INF
            scores = {}

            for m in ordered:
                if (_nodes & 255) == 0 and time.perf_counter() > _deadline:
                    raise _Timeout()

                cme, copp = _apply(me, opp, m)
                val = -_search(cme, copp, depth - 1, -beta, -alpha)
                scores[m] = val

                if val > cur_val:
                    cur_val = val
                    cur_best = m

                if val > alpha:
                    alpha = val

            best = cur_best
            best_val = cur_val
            _TT[root_key] = (depth, FLAG_EXACT, best_val, best)

            ordered.sort(key=lambda mm: scores.get(mm, -INF), reverse=True)

            if best_val > MATE // 2 or best_val < -MATE // 2:
                break

            depth += 1

        except _Timeout:
            break
        except Exception:
            break

    return _MOVE_STR[best]
