
import time
from heapq import nlargest

FULL_MASK = (1 << 36) - 1
WIN = 1_000_000
INF = 10_000_000
TIME_LIMIT = 0.90

# All length-5 straight segments on a 6x6 board. Any 6-in-a-row contains one of these.
LINE_MASKS = []
LINE_CELLS = []
for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for r in range(6):
        for c in range(6):
            mask = 0
            cells = []
            ok = True
            for k in range(5):
                rr = r + dr * k
                cc = c + dc * k
                if 0 <= rr < 6 and 0 <= cc < 6:
                    i = rr * 6 + cc
                    cells.append(i)
                    mask |= 1 << i
                else:
                    ok = False
                    break
            if ok:
                LINE_MASKS.append(mask)
                LINE_CELLS.append(tuple(cells))
LINE_MASKS = tuple(LINE_MASKS)
LINE_CELLS = tuple(LINE_CELLS)

CELL_BASE = [0] * 36
for cells in LINE_CELLS:
    for i in cells:
        CELL_BASE[i] += 1

# Quadrants: 0=TL, 1=TR, 2=BL, 3=BR. d: 0=L/anticlockwise, 1=R/clockwise.
QUAD_MASK = [0] * 4
ROT = [[None, None] for _ in range(4)]      # ROT[q][d] = tuple of (src, dst)
ROT_INV = [[None, None] for _ in range(4)]  # ROT_INV[q][d][dst] = src, or -1 outside
for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if q in (0, 2) else 3
    qm = 0
    for i in range(3):
        for j in range(3):
            qm |= 1 << ((br + i) * 6 + (bc + j))
    QUAD_MASK[q] = qm
    for d in range(2):
        mapping = []
        inv = [-1] * 36
        for i in range(3):
            for j in range(3):
                src = (br + i) * 6 + (bc + j)
                if d == 1:      # R: old (i,j) -> new (j, 2-i)
                    ni, nj = j, 2 - i
                else:           # L: old (i,j) -> new (2-j, i)
                    ni, nj = 2 - j, i
                dst = (br + ni) * 6 + (bc + nj)
                mapping.append((src, dst))
                inv[dst] = src
        ROT[q][d] = tuple(mapping)
        ROT_INV[q][d] = tuple(inv)

# Static evaluation weights. Indexed by marbles of one color in an otherwise clean length-5 line.
SELF_LINE = (0, 1, 8, 90, 1400, 0)
FOE_LINE = (0, 2, 12, 140, 2200, 0)

# Move-generation weights. Indexed by resulting line count after placing/blocking.
MAKE_VALUE = (0, 1, 8, 100, 1800, 50000)
BLOCK_VALUE = (0, 2, 12, 160, 2600, 60000)
URGENT = 20000

EXACT, LOWER, UPPER = 0, 1, 2
TT = {}


class _Timeout(Exception):
    pass


def has_five(b):
    for m in LINE_MASKS:
        if (b & m) == m:
            return True
    return False


def rotate_bits(b, q, d):
    res = b & ~QUAD_MASK[q]
    for src, dst in ROT[q][d]:
        res |= ((b >> src) & 1) << dst
    return res


def apply_move(my, opp, cell, q, d):
    my |= 1 << cell
    qm = QUAD_MASK[q]
    mapping = ROT[q][d]

    nm = my & ~qm
    for src, dst in mapping:
        nm |= ((my >> src) & 1) << dst

    no = opp & ~qm
    for src, dst in mapping:
        no |= ((opp >> src) & 1) << dst
    return nm, no


def evaluate(side, other):
    # Heuristic value for the player `side` who is to move in this position.
    s = 0
    sw = SELF_LINE
    ow = FOE_LINE
    for m in LINE_MASKS:
        sc = (side & m).bit_count()
        if sc:
            if (other & m) == 0:
                s += sw[sc]
        else:
            oc = (other & m).bit_count()
            if oc:
                s -= ow[oc]
    return s


def cell_scores(side, other):
    occ = side | other
    scores = CELL_BASE[:]
    for m, cells in zip(LINE_MASKS, LINE_CELLS):
        sc = (side & m).bit_count()
        if sc:
            if (other & m) == 0 and sc < 5:
                add = MAKE_VALUE[sc + 1]
                for i in cells:
                    if ((occ >> i) & 1) == 0:
                        scores[i] += add
        else:
            oc = (other & m).bit_count()
            if oc and oc < 5:
                add = BLOCK_VALUE[oc + 1]
                for i in cells:
                    if ((occ >> i) & 1) == 0:
                        scores[i] += add
    return scores


def rotation_win_cells(my, opp, scores):
    # Cells from which some placement+rotation makes five immediately.
    res = set()
    occ0 = my | opp
    for q in range(4):
        qm = QUAD_MASK[q]
        for d in range(2):
            rm = rotate_bits(my, q, d)
            ro = rotate_bits(opp, q, d)
            if has_five(ro):
                continue
            if has_five(rm):
                # Adding a marble cannot remove this five; choose the best empty source cell.
                best = -1
                bs = -INF
                for i in range(36):
                    if ((occ0 >> i) & 1) == 0 and scores[i] > bs:
                        bs = scores[i]
                        best = i
                if best >= 0:
                    res.add(best)
                continue
            for m in LINE_MASKS:
                if (ro & m) != 0:
                    continue
                if ((rm & m).bit_count() == 4):
                    f = (m & ~rm).bit_length() - 1
                    if (qm >> f) & 1:
                        src = ROT_INV[q][d][f]
                    else:
                        src = f
                    if src >= 0 and ((occ0 >> src) & 1) == 0:
                        res.add(src)
    return res


def entries_for_position(my, opp, depth, tt_best=None):
    occ = my | opp
    empties = [i for i in range(36) if ((occ >> i) & 1) == 0]
    e = len(empties)
    if e == 0:
        return []

    scores = cell_scores(my, opp)
    if e <= 15:
        cells = sorted(empties, key=scores.__getitem__, reverse=True)
    else:
        breadth = 18 if depth >= 3 else (14 if depth == 2 else 11)
        cells = nlargest(breadth, empties, key=scores.__getitem__)
        present = set(cells)
        for i in empties:
            if scores[i] >= URGENT and i not in present:
                cells.append(i)
                present.add(i)
        for i in rotation_win_cells(my, opp, scores):
            if i not in present:
                cells.append(i)
                present.add(i)
        cells.sort(key=scores.__getitem__, reverse=True)

    entries = []
    seen_states = set()

    def add_entry(cell, q, d):
        my2, opp2 = apply_move(my, opp, cell, q, d)
        state = (my2, opp2)
        if state in seen_states:
            return
        seen_states.add(state)
        yw = has_five(my2)
        ow = has_five(opp2)
        if yw and ow:
            term = 0
        elif yw:
            term = WIN + depth
        elif ow:
            term = -WIN - depth
        elif (my2 | opp2) == FULL_MASK:
            term = 0
        else:
            term = None
        guess = term if term is not None else -evaluate(opp2, my2)
        entries.append((guess, guess, (cell, q, d), my2, opp2, term))

    for cell in cells:
        for q in range(4):
            for d in range(2):
                add_entry(cell, q, d)

    if tt_best is not None and ((occ >> tt_best[0]) & 1) == 0:
        if not any(en[2] == tt_best for en in entries):
            c, q, d = tt_best
            my2, opp2 = apply_move(my, opp, c, q, d)
            yw = has_five(my2)
            ow = has_five(opp2)
            if yw and ow:
                term = 0
            elif yw:
                term = WIN + depth
            elif ow:
                term = -WIN - depth
            elif (my2 | opp2) == FULL_MASK:
                term = 0
            else:
                term = None
            guess = term if term is not None else -evaluate(opp2, my2)
            entries.append((guess, guess, tt_best, my2, opp2, term))
        entries.sort(key=lambda en: (INF if en[2] == tt_best else en[0]), reverse=True)
    else:
        entries.sort(key=lambda en: en[0], reverse=True)
    return entries


def negamax(my, opp, depth, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise _Timeout()
    if depth <= 0:
        return evaluate(my, opp)

    alpha_orig, beta_orig = alpha, beta
    key = (my, opp)
    entry = TT.get(key)
    tt_best = None
    if entry is not None:
        ed, ev, flag, eb = entry
        if ed >= depth:
            if flag == EXACT:
                return ev
            if flag == LOWER and ev > alpha:
                alpha = ev
            elif flag == UPPER and ev < beta:
                beta = ev
            if alpha >= beta:
                return ev
        tt_best = eb

    entries = entries_for_position(my, opp, depth, tt_best)
    if not entries:
        return 0

    best_val = -INF
    best_action = entries[0][2]
    first = True

    for _, guess, action, my2, opp2, term in entries:
        if term is not None:
            val = term
        elif depth == 1:
            val = guess
        else:
            if first:
                val = -negamax(opp2, my2, depth - 1, -beta, -alpha, deadline)
            else:
                val = -negamax(opp2, my2, depth - 1, -alpha - 1, -alpha, deadline)
                if alpha < val < beta:
                    val = -negamax(opp2, my2, depth - 1, -beta, -alpha, deadline)

        if val > best_val:
            best_val = val
            best_action = action
        if val > alpha:
            alpha = val
        first = False
        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, best_val, flag, best_action)
        if len(TT) > 300000:
            TT.clear()
    return best_val


def root_search(entries, depth, deadline):
    alpha = -INF
    beta = INF
    best_val = -INF
    best_action = entries[0][2]
    new_entries = []

    for idx, en in enumerate(entries):
        if time.perf_counter() > deadline:
            raise _Timeout()
        _, guess, action, my2, opp2, term = en
        if term is not None:
            val = term
        elif depth == 1:
            val = guess
        else:
            if idx == 0:
                val = -negamax(opp2, my2, depth - 1, -beta, -alpha, deadline)
            else:
                val = -negamax(opp2, my2, depth - 1, -alpha - 1, -alpha, deadline)
                if alpha < val < beta:
                    val = -negamax(opp2, my2, depth - 1, -beta, -alpha, deadline)

        new_entries.append((val, guess, action, my2, opp2, term))
        if val > best_val:
            best_val = val
            best_action = action
        if val > alpha:
            alpha = val

    new_entries.sort(key=lambda en: en[0], reverse=True)
    return new_entries, best_action


def fmt(cell, q, d):
    return f"{cell // 6 + 1},{cell % 6 + 1},{q},{'R' if d else 'L'}"


def policy(you, opponent) -> str:
    start = time.perf_counter()
    deadline = start + TIME_LIMIT

    y = 0
    o = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                y |= 1 << (r * 6 + c)
            if opponent[r][c]:
                o |= 1 << (r * 6 + c)

    occ = y | o
    entries = []
    losing = []
    seen_states = set()

    # Full legal scan: immediate win is returned; self-loss rotations are excluded unless unavoidable.
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        for q in range(4):
            for d in range(2):
                y2, o2 = apply_move(y, o, cell, q, d)
                yw = has_five(y2)
                ow = has_five(o2)
                if yw and not ow:
                    return fmt(cell, q, d)
                state = (y2, o2)
                if state in seen_states:
                    continue
                seen_states.add(state)
                if yw and ow:
                    entries.append((0, 0, (cell, q, d), y2, o2, 0))
                elif ow:
                    losing.append((cell, q, d))
                else:
                    if (y2 | o2) == FULL_MASK:
                        entries.append((0, 0, (cell, q, d), y2, o2, 0))
                    else:
                        val = -evaluate(o2, y2)
                        entries.append((val, val, (cell, q, d), y2, o2, None))

    if not entries:
        if losing:
            return fmt(*losing[0])
        # Defensive fallback; should not happen because at least one empty cell is guaranteed.
        for cell in range(36):
            if ((occ >> cell) & 1) == 0:
                return fmt(cell, 0, 0)

    entries.sort(key=lambda en: en[0], reverse=True)
    best_action = entries[0][2]

    # Iterative deepening. Completed deeper iterations replace the move; timed-out ones are discarded.
    for depth in range(2, 13):
        try:
            entries, best_action = root_search(entries, depth, deadline)
        except _Timeout:
            break

    return fmt(*best_action)
