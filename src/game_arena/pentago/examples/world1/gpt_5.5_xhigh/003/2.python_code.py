
import time

# -------- Constants --------

_CELLS = 36
_FULL_MASK = (1 << 36) - 1
_BITS = tuple(1 << i for i in range(36))

_WIN_SCORE = 10_000_000
_INF = 1_000_000_000
_TIME_LIMIT = 0.88

_ROT_RANGE = tuple(range(8))
_STATE_SHIFT = 36
_DEPTH_SHIFT = 72

_LINE_WEIGHTS = (0, 2, 12, 85, 950, 50_000)
_FOUR_SQUARE_BONUS = 160
_THREE_SQUARE_BONUS = 10

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


# -------- Precomputation --------

def _build_win_masks():
    masks = []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        idx = (r + k * dr) * 6 + (c + k * dc)
                        m |= _BITS[idx]
                    masks.append(m)
    return tuple(masks)


_WIN_MASKS = _build_win_masks()


def _build_win_by_cell():
    by_cell = [[] for _ in range(36)]
    for mask in _WIN_MASKS:
        x = mask
        while x:
            lsb = x & -x
            idx = lsb.bit_length() - 1
            by_cell[idx].append(mask)
            x -= lsb
    return tuple(tuple(v) for v in by_cell)


_WIN_BY_CELL = _build_win_by_cell()

_CELL_QUAD = tuple((r // 3) * 2 + (c // 3) for r in range(6) for c in range(6))
_OPENING_CELLS = (7, 28, 10, 25)  # quadrant centers: (2,2), (5,5), (2,5), (5,2)


def _build_cell_values():
    vals = []
    quad_centers = set(_OPENING_CELLS)
    global_centers = {14, 15, 20, 21}

    for i in range(36):
        r, c = divmod(i, 6)
        v = 3 * len(_WIN_BY_CELL[i])
        if i in quad_centers:
            v += 18
        if i in global_centers:
            v += 5
        if (r in (0, 5)) and (c in (0, 5)):
            v -= 2
        vals.append(v)

    order = tuple(sorted(range(36), key=lambda x: vals[x], reverse=True))
    return tuple(vals), order


_CELL_VALUES, _CELL_ORDER = _build_cell_values()


def _build_pos_tables():
    tables = []
    for chunk in range(3):
        offset = 12 * chunk
        table = [0] * 4096
        for pat in range(4096):
            s = 0
            x = pat
            while x:
                lsb = x & -x
                j = lsb.bit_length() - 1
                s += _CELL_VALUES[offset + j]
                x -= lsb
            table[pat] = s
        tables.append(tuple(table))
    return tuple(tables)


_POS_TABLES = _build_pos_tables()


def _build_rotations():
    masks = []
    not_masks = []
    tables = []
    rot_cell = []
    rot_bit = []

    for q in range(4):
        base_r = 0 if q < 2 else 3
        base_c = 0 if (q % 2) == 0 else 3

        cells = []
        qmask = 0
        for lr in range(3):
            for lc in range(3):
                idx = (base_r + lr) * 6 + (base_c + lc)
                cells.append(idx)
                qmask |= _BITS[idx]

        for dch in ("L", "R"):
            mapping = list(range(36))

            for lr in range(3):
                for lc in range(3):
                    old_idx = (base_r + lr) * 6 + (base_c + lc)
                    if dch == "R":
                        nr, nc = lc, 2 - lr
                    else:
                        nr, nc = 2 - lc, lr
                    new_idx = (base_r + nr) * 6 + (base_c + nc)
                    mapping[old_idx] = new_idx

            table = {}
            for pat in range(512):
                old_bits = 0
                new_bits = 0
                for p, old_idx in enumerate(cells):
                    if pat & (1 << p):
                        old_bits |= _BITS[old_idx]
                        new_bits |= _BITS[mapping[old_idx]]
                table[old_bits] = new_bits

            masks.append(qmask)
            not_masks.append(_FULL_MASK ^ qmask)
            tables.append(table)
            rot_cell.append(tuple(mapping))
            rot_bit.append(tuple(_BITS[mapping[i]] for i in range(36)))

    return tuple(masks), tuple(not_masks), tuple(tables), tuple(rot_cell), tuple(rot_bit)


_ROT_MASKS, _ROT_NOT_MASKS, _ROT_TABLES, _ROT_CELL, _ROT_BIT = _build_rotations()

_MOVE_STR = tuple(
    tuple(
        f"{cell // 6 + 1},{cell % 6 + 1},{rot // 2},{'L' if rot % 2 == 0 else 'R'}"
        for rot in range(8)
    )
    for cell in range(36)
)


# -------- Basic bitboard utilities --------

def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & 31) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _to_bits(board):
    bb = 0
    for r in range(6):
        row = board[r]
        base = 6 * r
        for c in range(6):
            if int(row[c]):
                bb |= _BITS[base + c]
    return bb


def _rotate_bb(bb, rot):
    return (bb & _ROT_NOT_MASKS[rot]) | _ROT_TABLES[rot][bb & _ROT_MASKS[rot]]


def _has_win(bb):
    for m in _WIN_MASKS:
        if (bb & m) == m:
            return True
    return False


def _wins_with_cell(bb, cell):
    for m in _WIN_BY_CELL[cell]:
        if (bb & m) == m:
            return True
    return False


def _pos_sum(bb):
    return (
        _POS_TABLES[0][bb & 0xFFF]
        + _POS_TABLES[1][(bb >> 12) & 0xFFF]
        + _POS_TABLES[2][(bb >> 24) & 0xFFF]
    )


def _term_value(term, depth):
    if term > 0:
        return _WIN_SCORE + depth
    if term < 0:
        return -_WIN_SCORE - depth
    return 0


def _move_of(child):
    return _MOVE_STR[child[1]][child[2]]


def _fallback_from_bits(me, opp):
    occ = me | opp
    for cell in _CELL_ORDER:
        if not (occ & _BITS[cell]):
            q = _CELL_QUAD[cell]
            return _MOVE_STR[cell][q * 2]
    return "1,1,0,L"


def _fallback_arrays(you, opponent):
    try:
        return _fallback_from_bits(_to_bits(you), _to_bits(opponent))
    except Exception:
        try:
            for r in range(6):
                for c in range(6):
                    if not int(you[r][c]) and not int(opponent[r][c]):
                        return f"{r + 1},{c + 1},0,L"
        except Exception:
            pass
    return "1,1,0,L"


# -------- Evaluation --------

def _evaluate(me, opp):
    score = _pos_sum(me) - _pos_sum(opp)

    my4 = opp4 = 0
    my3 = opp3 = 0
    lw = _LINE_WEIGHTS

    for mask in _WIN_MASKS:
        ob = opp & mask
        if ob == 0:
            c = (me & mask).bit_count()
            if c:
                score += lw[c]
                if c == 4:
                    my4 += 1
                elif c == 3:
                    my3 += 1
        else:
            mb = me & mask
            if mb == 0:
                c = ob.bit_count()
                if c:
                    score -= lw[c]
                    if c == 4:
                        opp4 += 1
                    elif c == 3:
                        opp3 += 1

    score += _FOUR_SQUARE_BONUS * (my4 * my4 - opp4 * opp4)
    score += _THREE_SQUARE_BONUS * (my3 * my3 - opp3 * opp3)
    return score


# -------- Move generation and search --------

def _node_rotation_info(me, opp):
    me_rots = [0] * 8
    opp_rots = [0] * 8
    me_wins = [False] * 8
    opp_wins = [False] * 8

    for rot in _ROT_RANGE:
        mr = _rotate_bb(me, rot)
        orr = _rotate_bb(opp, rot)
        me_rots[rot] = mr
        opp_rots[rot] = orr
        me_wins[rot] = _has_win(mr)
        opp_wins[rot] = _has_win(orr)

    return me_rots, opp_rots, me_wins, opp_wins


def _generate_children(me, opp, ordered=True, stop_on_win=False):
    occ = me | opp
    if occ == _FULL_MASK:
        return []

    me_rots, opp_rots, me_wins, opp_wins = _node_rotation_info(me, opp)

    children = []
    seen = set()

    for cell in _CELL_ORDER:
        bit = _BITS[cell]
        if occ & bit:
            continue

        full_after = (occ | bit) == _FULL_MASK

        for rot in _ROT_RANGE:
            final_cell = _ROT_CELL[rot][cell]
            m2 = me_rots[rot] | _ROT_BIT[rot][cell]
            o2 = opp_rots[rot]

            key = m2 | (o2 << _STATE_SHIFT)
            if key in seen:
                continue
            seen.add(key)

            mw = me_wins[rot] or _wins_with_cell(m2, final_cell)
            ow = opp_wins[rot]

            if mw:
                if ow:
                    term = 0
                    order = 0
                else:
                    if stop_on_win:
                        return [(_WIN_SCORE, cell, rot, m2, o2, 1)]
                    term = 1
                    order = _WIN_SCORE
            elif ow:
                term = -1
                order = -_WIN_SCORE
            elif full_after:
                term = 0
                order = 0
            else:
                term = None
                order = _evaluate(m2, o2) if ordered else 0

            children.append((order, cell, rot, m2, o2, term))

    if ordered:
        children.sort(key=lambda ch: ch[0], reverse=True)
    return children


def _search_depth1(me, opp, alpha, beta):
    _tick()

    occ = me | opp
    if occ == _FULL_MASK:
        return 0

    me_rots, opp_rots, me_wins, opp_wins = _node_rotation_info(me, opp)

    best = -_INF
    seen = set()

    for cell in _CELL_ORDER:
        bit = _BITS[cell]
        if occ & bit:
            continue

        full_after = (occ | bit) == _FULL_MASK

        for rot in _ROT_RANGE:
            final_cell = _ROT_CELL[rot][cell]
            m2 = me_rots[rot] | _ROT_BIT[rot][cell]
            o2 = opp_rots[rot]

            key = m2 | (o2 << _STATE_SHIFT)
            if key in seen:
                continue
            seen.add(key)

            mw = me_wins[rot] or _wins_with_cell(m2, final_cell)
            ow = opp_wins[rot]

            if mw:
                if not ow:
                    return _WIN_SCORE + 1
                val = 0
            elif ow:
                val = -_WIN_SCORE - 1
            elif full_after:
                val = 0
            else:
                val = _evaluate(m2, o2)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    return best

    return best if best != -_INF else 0


def _negamax(me, opp, depth, alpha, beta):
    _tick()

    if depth <= 0:
        return _evaluate(me, opp)
    if depth == 1:
        return _search_depth1(me, opp, alpha, beta)

    key = me | (opp << _STATE_SHIFT) | (depth << _DEPTH_SHIFT)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    children = _generate_children(me, opp, ordered=True, stop_on_win=True)
    if not children:
        return 0

    best = -_INF
    exact = True

    for ch in children:
        term = ch[5]
        if term is not None:
            val = _term_value(term, depth)
        else:
            val = -_negamax(ch[4], ch[3], depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
            if alpha >= beta:
                exact = False
                break

    if exact:
        _TT[key] = best
    return best


def _root_search(children, depth, limit=None):
    _tick()

    if not children:
        return None, 0, children

    n = len(children) if limit is None else min(limit, len(children))
    alpha = -_INF
    beta = _INF

    best_child = children[0]
    best_val = -_INF
    scored = []

    for i in range(n):
        _tick()
        ch = children[i]
        term = ch[5]

        if term is not None:
            val = _term_value(term, depth)
        elif depth <= 1:
            val = ch[0]
        else:
            val = -_negamax(ch[4], ch[3], depth - 1, -beta, -alpha)

        scored.append((val, ch))

        if val > best_val or (val == best_val and ch[0] > best_child[0]):
            best_val = val
            best_child = ch

        if val > alpha:
            alpha = val

    scored.sort(key=lambda item: (item[0], item[1][0]), reverse=True)
    ordered = [ch for _, ch in scored]
    if n < len(children):
        ordered.extend(children[n:])

    return _move_of(best_child), best_val, ordered


# -------- Public API --------

def _policy_impl(you, opponent):
    global _DEADLINE, _NODES, _TT

    me = _to_bits(you)
    opp = _to_bits(opponent)
    occ = me | opp
    total = occ.bit_count()
    empty_count = _CELLS - total

    fallback = _fallback_from_bits(me, opp)

    # Strong and fast opening: take an unoccupied quadrant center.
    if total <= 1 and me.bit_count() == 0:
        for cell in _OPENING_CELLS:
            if not (occ & _BITS[cell]):
                return _MOVE_STR[cell][_CELL_QUAD[cell] * 2]

    _DEADLINE = time.perf_counter() + _TIME_LIMIT
    _NODES = 0
    _TT = {}

    root_children = _generate_children(me, opp, ordered=True, stop_on_win=True)
    if not root_children:
        return fallback

    # Immediate non-drawing win.
    if root_children[0][5] == 1:
        return _move_of(root_children[0])

    best_move = _move_of(root_children[0])

    try:
        # Static 1-ply ordering.
        bm1, _, root_children = _root_search(root_children, 1)
        if bm1:
            best_move = bm1

        if len(root_children) <= 1:
            return best_move

        # Exact very-late endgame when feasible.
        if empty_count <= 4:
            _TT = {}
            bm_end, _, root_children = _root_search(root_children, empty_count)
            if bm_end:
                best_move = bm_end
            return best_move

        # Full 2-ply tactical safety search.
        _TT = {}
        bm2, val2, root_children = _root_search(root_children, 2)
        if bm2:
            best_move = bm2

        # If 2-ply proves a forced immediate win/loss, deeper search cannot alter it.
        if val2 >= _WIN_SCORE // 2 or val2 <= -_WIN_SCORE // 2:
            return best_move

        # Selective 3-ply search with the remaining time.
        if time.perf_counter() < _DEADLINE - 0.06:
            if empty_count <= 10:
                limit = len(root_children)
            elif empty_count <= 14:
                limit = min(len(root_children), 18)
            elif empty_count <= 22:
                limit = min(len(root_children), 8)
            elif empty_count <= 30:
                limit = min(len(root_children), 5)
            else:
                limit = min(len(root_children), 4)

            bm3, val3, root_children = _root_search(root_children, 3, limit=limit)
            if bm3 and (limit == len(root_children) or val3 > -_WIN_SCORE // 2):
                best_move = bm3

    except _Timeout:
        pass

    return best_move


def policy(you, opponent) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        return _fallback_arrays(you, opponent)
