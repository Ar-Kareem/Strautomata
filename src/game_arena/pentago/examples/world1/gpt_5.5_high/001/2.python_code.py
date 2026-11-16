
import time

# Pentago policy entry point:
# def policy(you, opponent) -> str

BOARD_N = 6
BOARD_CELLS = 36
BOARD_MASK = (1 << BOARD_CELLS) - 1

WIN_SCORE = 1_000_000
INF = 10**9

# Rotation encoding:
# qdir = quad * 2 + d, where d=0 is L and d=1 is R.
DIR_CHARS = ("L", "R")
CELL_BITS = tuple(1 << i for i in range(36))

# 3x3 quadrant shape inside a 6-wide bitboard, relative to quadrant top-left.
_SHAPE_OFFSETS = (0, 1, 2, 6, 7, 8, 12, 13, 14)
_SHAPE_MASK = 0
for _o in _SHAPE_OFFSETS:
    _SHAPE_MASK |= 1 << _o

# Quadrant top-left bit indices.
_BASES = (0, 3, 18, 21)
_QUAD_MASKS = tuple(_SHAPE_MASK << b for b in _BASES)


def _build_win_masks():
    masks = []
    dirs = ((0, 1), (1, 0), (1, 1), (1, -1))
    for dr, dc in dirs:
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= 1 << ((r + k * dr) * 6 + (c + k * dc))
                    masks.append(m)
    return tuple(masks)


WIN_MASKS = _build_win_masks()

# Positional weights: quadrant centers and generally central cells are useful.
_POS_GRID = (
    (3, 4, 4, 4, 4, 3),
    (4, 7, 6, 6, 7, 4),
    (4, 6, 5, 5, 6, 4),
    (4, 6, 5, 5, 6, 4),
    (4, 7, 6, 6, 7, 4),
    (3, 4, 4, 4, 4, 3),
)
POS_WEIGHTS = tuple(_POS_GRID[r][c] for r in range(6) for c in range(6))

# Weights for unblocked 5-cell windows.
LINE_WEIGHTS = (0, 2, 12, 90, 1200, 200000)

# Precompute rotation of the 15-bit 3x3 shape window.
# ROT_SHAPE[0] = left, ROT_SHAPE[1] = right.
ROT_SHAPE = [[0] * (1 << 15) for _ in range(2)]
for part in range(1 << 15):
    for d in (0, 1):
        res = 0
        for r in range(3):
            for c in range(3):
                old_off = r * 6 + c
                if part & (1 << old_off):
                    if d == 0:       # L / anticlockwise: (r,c) -> (2-c,r)
                        nr, nc = 2 - c, r
                    else:            # R / clockwise: (r,c) -> (c,2-r)
                        nr, nc = c, 2 - r
                    res |= 1 << (nr * 6 + nc)
        ROT_SHAPE[d][part] = res


# Search globals, reset in policy().
DEADLINE = 0.0
TT = {}
WINMOVE_CACHE = {}
NODE_COUNT = 0


class _Timeout(Exception):
    pass


def _has_win(bb):
    for m in WIN_MASKS:
        if (bb & m) == m:
            return True
    return False


def _rotate_bits(bb, qdir):
    q = qdir >> 1
    d = qdir & 1
    base = _BASES[q]
    part = (bb >> base) & _SHAPE_MASK
    return (bb & ~_QUAD_MASKS[q]) | (ROT_SHAPE[d][part] << base)


def _apply_move(me, opp, cell, qdir):
    bit = CELL_BITS[cell]
    return _rotate_bits(me | bit, qdir), _rotate_bits(opp, qdir)


def _terminal_value_after(me_after, opp_after, ply_made):
    """Value from the mover's perspective after the mover's move."""
    mw = _has_win(me_after)
    if mw:
        ow = _has_win(opp_after)
        if ow:
            return 0
        return WIN_SCORE - ply_made
    if _has_win(opp_after):
        return -WIN_SCORE + ply_made
    if (me_after | opp_after) == BOARD_MASK:
        return 0
    return None


def _evaluate(me, opp):
    """Static board evaluation from me's perspective."""
    score = 0

    for m in WIN_MASKS:
        mc = (me & m).bit_count()
        oc = (opp & m).bit_count()
        if oc == 0:
            score += LINE_WEIGHTS[mc]
        elif mc == 0:
            score -= LINE_WEIGHTS[oc]

    x = me
    while x:
        lsb = x & -x
        score += POS_WEIGHTS[lsb.bit_length() - 1]
        x -= lsb

    x = opp
    while x:
        lsb = x & -x
        score -= POS_WEIGHTS[lsb.bit_length() - 1]
        x -= lsb

    return score


def _move_to_str(cell, qdir):
    return f"{cell // 6 + 1},{cell % 6 + 1},{qdir // 2},{DIR_CHARS[qdir & 1]}"


def _first_empty_cell(occ):
    empty = (~occ) & BOARD_MASK
    lsb = empty & -empty
    return lsb.bit_length() - 1


def _winning_move_count(side, other, limit=1):
    """Number of distinct immediate winning moves for side, capped at limit."""
    key = (side, other, limit)
    cached = WINMOVE_CACHE.get(key)
    if cached is not None:
        return cached

    occ = side | other
    empty = (~occ) & BOARD_MASK
    count = 0
    seen = set()

    while empty:
        lsb = empty & -empty
        empty -= lsb
        placed = side | lsb
        for qdir in range(8):
            ns = _rotate_bits(placed, qdir)
            no = _rotate_bits(other, qdir)
            k = (ns, no)
            if k in seen:
                continue
            seen.add(k)
            if _has_win(ns) and not _has_win(no):
                count += 1
                if count >= limit:
                    WINMOVE_CACHE[key] = count
                    return count

    WINMOVE_CACHE[key] = count
    return count


def _node_limit(depth):
    # Limits are for ordered candidate search at internal nodes.
    if depth >= 3:
        return 28
    if depth == 2:
        return 42
    if depth == 1:
        return 84
    return None


def _ordered_moves(me, opp, depth, ply_done):
    occ = me | opp
    empty = (~occ) & BOARD_MASK
    moves = []
    seen = set()

    while empty:
        lsb = empty & -empty
        empty -= lsb
        cell = lsb.bit_length() - 1
        placed = me | lsb

        for qdir in range(8):
            ns = _rotate_bits(placed, qdir)
            no = _rotate_bits(opp, qdir)
            k = (ns, no)
            if k in seen:
                continue
            seen.add(k)

            term = _terminal_value_after(ns, no, ply_done + 1)
            if term is None:
                score = _evaluate(ns, no)
            else:
                score = term

            moves.append((score, cell, qdir, ns, no, term))

    moves.sort(key=lambda x: x[0], reverse=True)
    lim = _node_limit(depth)
    if lim is not None and len(moves) > lim:
        moves = moves[:lim]
    return moves


def _negamax(me, opp, depth, alpha, beta, ply_done):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 127) == 0 and time.perf_counter() > DEADLINE:
        raise _Timeout()

    if depth <= 0:
        return _evaluate(me, opp)

    if (me | opp) == BOARD_MASK:
        return 0

    key = (me, opp, depth, ply_done)
    cached = TT.get(key)
    if cached is not None:
        return cached

    best = -INF
    cutoff = False

    moves = _ordered_moves(me, opp, depth, ply_done)
    if not moves:
        return 0

    for _, cell, qdir, ns, no, term in moves:
        if term is not None:
            val = term
        else:
            val = -_negamax(no, ns, depth - 1, -beta, -alpha, ply_done + 1)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            cutoff = True
            break

    if not cutoff:
        TT[key] = best
    return best


def _arrays_to_bits(you, opponent):
    me = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            bit = 1 << (r * 6 + c)
            if int(yr[c]):
                me |= bit
            elif int(orow[c]):
                opp |= bit
    return me, opp


def _fallback_from_arrays(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    # Should never be reached because policy is not called on a full board.
    return "1,1,0,L"


def _choose_move(me, opp):
    global DEADLINE, TT, WINMOVE_CACHE, NODE_COUNT

    DEADLINE = time.perf_counter() + 0.88
    TT = {}
    WINMOVE_CACHE = {}
    NODE_COUNT = 0

    occ = me | opp
    default_cell = _first_empty_cell(occ)
    default_move = (default_cell, 0)

    # Opening book: quadrant center is stable under its own quadrant rotation.
    if occ == 0:
        return "2,2,0,L"

    root = []
    seen = set()
    empty = (~occ) & BOARD_MASK

    # Generate all unique resulting root states.
    while empty:
        lsb = empty & -empty
        empty -= lsb
        cell = lsb.bit_length() - 1
        placed = me | lsb

        for qdir in range(8):
            ns = _rotate_bits(placed, qdir)
            no = _rotate_bits(opp, qdir)
            k = (ns, no)
            if k in seen:
                continue
            seen.add(k)

            term = _terminal_value_after(ns, no, 1)
            if term is not None and term > WIN_SCORE // 2:
                return _move_to_str(cell, qdir)

            score = term if term is not None else _evaluate(ns, no)
            root.append((score, cell, qdir, ns, no, term))

    if not root:
        return _move_to_str(*default_move)

    annotated = []
    safe = []
    nonloss = []

    # Prefer moves that do not allow an immediate opponent win.
    for score, cell, qdir, ns, no, term in root:
        if term is not None:
            item = (score, cell, qdir, ns, no, term)
            annotated.append(item)
            if term >= 0:
                nonloss.append(item)
                safe.append(item)
            continue

        # no is the opponent after our move; opponent moves next.
        danger = _winning_move_count(no, ns, 1) > 0
        my_threats = _winning_move_count(ns, no, 2)

        score += 22000 * my_threats
        if danger:
            score -= 300000

        item = (score, cell, qdir, ns, no, term)
        annotated.append(item)
        nonloss.append(item)
        if not danger:
            safe.append(item)

    pool = safe if safe else (nonloss if nonloss else annotated)
    if not pool:
        return _move_to_str(*default_move)

    pool.sort(key=lambda x: x[0], reverse=True)
    order = pool
    best = order[0]
    best_val = best[0]

    # Iterative deepening from the root. The move is always legal even if timeout.
    plans = (
        (1, len(order)),
        (2, min(48, len(order))),
        (3, min(22, len(order))),
    )

    for depth, root_limit in plans:
        if time.perf_counter() > DEADLINE:
            break

        subset = order[:root_limit]
        results = []

        try:
            for _, cell, qdir, ns, no, term in subset:
                if time.perf_counter() > DEADLINE:
                    raise _Timeout()

                if term is not None:
                    val = term
                else:
                    # Opponent to move; negate opponent-perspective search value.
                    val = -_negamax(no, ns, depth, -INF, INF, 1)

                results.append((val, cell, qdir, ns, no, term))

        except _Timeout:
            if results:
                results.sort(key=lambda x: x[0], reverse=True)
                if results[0][0] > best_val:
                    best = results[0]
                    best_val = results[0][0]
            break

        if results:
            results.sort(key=lambda x: x[0], reverse=True)
            best = results[0]
            best_val = best[0]

            searched = {(x[1], x[2]) for x in results}
            rest = [x for x in order if (x[1], x[2]) not in searched]
            order = results + rest

            # If a forced win is found, no need to search deeper.
            if best_val > WIN_SCORE // 2:
                break

    return _move_to_str(best[1], best[2])


def policy(you, opponent) -> str:
    try:
        me, opp = _arrays_to_bits(you, opponent)
        return _choose_move(me, opp)
    except Exception:
        # Absolute safety: always return a legal-looking move on an empty cell.
        return _fallback_from_arrays(you, opponent)
