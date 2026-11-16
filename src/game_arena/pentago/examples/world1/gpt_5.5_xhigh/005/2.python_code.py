
import time

# Pentago policy: bitboards + tactical checks + alpha-beta search.

BOARD_N = 6
NUM_CELLS = 36
FULL_MASK = (1 << NUM_CELLS) - 1

WIN_SCORE = 1_000_000_000
INF = WIN_SCORE + 1_000_000
EVAL_CAP = 600_000
TIME_LIMIT = 0.88

OPS = tuple(range(8))  # op = quad * 2 + dir, dir: 0=L, 1=R

try:
    _POPCOUNT = int.bit_count
except AttributeError:
    def _POPCOUNT(x):
        return bin(x).count("1")


def _build_win_masks():
    masks = []
    seen = set()
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for dr, dc in directions:
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                er = r + 4 * dr
                ec = c + 4 * dc
                if 0 <= er < BOARD_N and 0 <= ec < BOARD_N:
                    m = 0
                    for k in range(5):
                        rr = r + k * dr
                        cc = c + k * dc
                        m |= 1 << (rr * BOARD_N + cc)
                    if m not in seen:
                        seen.add(m)
                        masks.append(m)
    return tuple(masks)


WIN_MASKS = _build_win_masks()

_Q_CELLS = []
_QMASKS_LIST = []
for q in range(4):
    r0 = 0 if q < 2 else 3
    c0 = 0 if (q % 2) == 0 else 3
    cells = []
    mask = 0
    for i in range(3):
        for j in range(3):
            idx = (r0 + i) * BOARD_N + (c0 + j)
            cells.append(idx)
            mask |= 1 << idx
    _Q_CELLS.append(tuple(cells))
    _QMASKS_LIST.append(mask)

QMASKS = tuple(_QMASKS_LIST)
NQMASKS = tuple(FULL_MASK ^ m for m in QMASKS)
OP_Q = tuple(op >> 1 for op in OPS)


def _build_rot_lookup():
    lookups = []
    for q in range(4):
        cells = _Q_CELLS[q]
        for d in range(2):  # 0=L, 1=R
            table = {}
            for pat in range(512):
                inside = 0
                rotated = 0
                for k, idx in enumerate(cells):
                    if pat & (1 << k):
                        inside |= 1 << idx
                        i = k // 3
                        j = k % 3
                        if d == 0:       # anticlockwise
                            ni, nj = 2 - j, i
                        else:            # clockwise
                            ni, nj = j, 2 - i
                        nidx = cells[ni * 3 + nj]
                        rotated |= 1 << nidx
                table[inside] = rotated
            lookups.append(table)
    return tuple(lookups)


ROT_LOOKUP = _build_rot_lookup()


def _rotate_bits(bb, op, _opq=OP_Q, _q=QMASKS, _nq=NQMASKS, _rot=ROT_LOOKUP):
    q = _opq[op]
    return (bb & _nq[q]) | _rot[op][bb & _q[q]]


INV_OPS = tuple(op ^ 1 for op in OPS)


def _build_prewin():
    by_op = []
    counts = {}
    for op in OPS:
        inv = INV_OPS[op]
        seen = set()
        arr = []
        for w in WIN_MASKS:
            pre = _rotate_bits(w, inv)
            counts[pre] = counts.get(pre, 0) + 1
            if pre not in seen:
                seen.add(pre)
                arr.append(pre)
        by_op.append(tuple(arr))
    return tuple(by_op), counts


PREWIN_BY_OP, _POT_COUNTS = _build_prewin()
POT_ITEMS = tuple(sorted((m, 1 + min(c - 1, 3)) for m, c in _POT_COUNTS.items()))

# Evaluation weights.
LINE_W = (0, 3, 20, 140, 2200, 0)
POT_W = (0, 1, 8, 55, 750, 5000)


def _build_cell_weights():
    w = [0] * NUM_CELLS

    def add_mask(mask, amount):
        x = mask
        while x:
            b = x & -x
            idx = b.bit_length() - 1
            w[idx] += amount
            x -= b

    for m in WIN_MASKS:
        add_mask(m, 5)
    for m, mult in POT_ITEMS:
        add_mask(m, mult)

    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            center_bonus = max(0, 10 - (abs(2 * r - 5) + abs(2 * c - 5)))
            w[idx] += center_bonus
            if r % 3 == 1 and c % 3 == 1:
                w[idx] += 12       # centers of quadrants are stable under rotation
            if r in (2, 3) and c in (2, 3):
                w[idx] += 6        # central-board influence
    return tuple(w)


CELL_WEIGHTS = _build_cell_weights()
CELL_BITS = tuple(1 << i for i in range(NUM_CELLS))
CELL_ORDER = tuple(sorted(range(NUM_CELLS), key=lambda i: (-CELL_WEIGHTS[i], i)))


def _build_chunk_sums():
    chunks = []
    for ch in range(3):
        base = ch * 12
        arr = [0] * 4096
        for pat in range(4096):
            s = 0
            x = pat
            while x:
                b = x & -x
                i = b.bit_length() - 1
                idx = base + i
                if idx < NUM_CELLS:
                    s += CELL_WEIGHTS[idx]
                x -= b
            arr[pat] = s
        chunks.append(tuple(arr))
    return tuple(chunks)


_CS0, _CS1, _CS2 = _build_chunk_sums()


def _pos_sum(bb, _c0=_CS0, _c1=_CS1, _c2=_CS2):
    return _c0[bb & 4095] + _c1[(bb >> 12) & 4095] + _c2[(bb >> 24) & 4095]


def _has_win(bb, _masks=WIN_MASKS):
    for m in _masks:
        if (bb & m) == m:
            return True
    return False


def _apply_move(us, opp, bit, op,
                _opq=OP_Q, _q=QMASKS, _nq=NQMASKS, _rot=ROT_LOOKUP):
    q = _opq[op]
    qm = _q[q]
    nqm = _nq[q]
    table = _rot[op]
    p = us | bit
    p2 = (p & nqm) | table[p & qm]
    o2 = (opp & nqm) | table[opp & qm]
    return p2, o2


def _terminal_after(pbits, obits):
    pw = _has_win(pbits)
    ow = _has_win(obits)
    if pw or ow:
        if pw and not ow:
            return WIN_SCORE
        if ow and not pw:
            return -WIN_SCORE
        return 0
    if (pbits | obits) == FULL_MASK:
        return 0
    return None


def _can_win_own_only(us, opp, _pre=PREWIN_BY_OP):
    empty = FULL_MASK & ~(us | opp)
    if not empty:
        return False

    for op in OPS:
        candidate = False
        for m in _pre[op]:
            if m & opp:
                continue
            missing = m & ~us
            if missing == 0:
                candidate = True
                break
            if (missing & (missing - 1)) == 0 and (missing & empty):
                candidate = True
                break

        if candidate:
            # If opponent also has a line after this same rotation, it is only a draw.
            if not _has_win(_rotate_bits(opp, op)):
                return True
    return False


def _count_winning_moves(us, opp, cap=4, _pre=PREWIN_BY_OP, _pc=_POPCOUNT):
    empty = FULL_MASK & ~(us | opp)
    if not empty:
        return 0

    total = 0
    for op in OPS:
        cells = 0
        for m in _pre[op]:
            if m & opp:
                continue
            missing = m & ~us
            if missing == 0:
                cells = empty
                break
            if (missing & (missing - 1)) == 0 and (missing & empty):
                cells |= missing

        if cells and not _has_win(_rotate_bits(opp, op)):
            total += _pc(cells)
            if total >= cap:
                return total
    return total


def _quick_eval(us, opp, _pc=_POPCOUNT):
    score = _pos_sum(us) - _pos_sum(opp)
    for m in WIN_MASKS:
        u = us & m
        o = opp & m
        if o == 0:
            score += LINE_W[_pc(u)]
        elif u == 0:
            score -= LINE_W[_pc(o)]
    return score


def _evaluate(us, opp, _pc=_POPCOUNT):
    score = _pos_sum(us) - _pos_sum(opp)

    for m in WIN_MASKS:
        u = us & m
        o = opp & m
        if o == 0:
            score += LINE_W[_pc(u)]
        elif u == 0:
            score -= LINE_W[_pc(o)]

    hot_us = 0
    hot_opp = 0
    for m, mult in POT_ITEMS:
        u = us & m
        o = opp & m
        if o == 0:
            c = _pc(u)
            score += mult * POT_W[c]
            if c >= 4:
                hot_us += mult * (c - 3)
        elif u == 0:
            c = _pc(o)
            score -= mult * POT_W[c]
            if c >= 4:
                hot_opp += mult * (c - 3)

    # At a leaf, an exact own immediate win is effectively decisive.
    if hot_us and _can_win_own_only(us, opp):
        return EVAL_CAP

    if hot_us:
        score += 60_000 + 9_000 * min(hot_us, 16)
    if hot_opp:
        score -= 120_000 + 9_000 * min(hot_opp, 16)
        if hot_us:
            score += 30_000  # side to move has tempo in mutual-threat positions

    if score > EVAL_CAP:
        return EVAL_CAP
    if score < -EVAL_CAP:
        return -EVAL_CAP
    return score


def _generate_children_sorted(us, opp):
    empty = FULL_MASK & ~(us | opp)
    if not empty:
        return 0, None

    seen = set()
    children = []
    for idx in CELL_ORDER:
        bit = CELL_BITS[idx]
        if not (empty & bit):
            continue
        for op in OPS:
            p2, o2 = _apply_move(us, opp, bit, op)
            key = (p2, o2)
            if key in seen:
                continue
            seen.add(key)

            term = _terminal_after(p2, o2)
            if term == WIN_SCORE:
                return WIN_SCORE, None

            if term is None:
                order = _quick_eval(p2, o2) + CELL_WEIGHTS[idx]
                children.append((order, None, o2, p2))
            else:
                children.append((term, term, 0, 0))

    if not children:
        return 0, None
    children.sort(key=lambda x: x[0], reverse=True)
    return None, children


def _make_root_candidates(us, opp):
    empty = FULL_MASK & ~(us | opp)
    states = {}

    for idx in CELL_ORDER:
        bit = CELL_BITS[idx]
        if not (empty & bit):
            continue
        for op in OPS:
            p2, o2 = _apply_move(us, opp, bit, op)
            term = _terminal_after(p2, o2)

            # Exact immediate win: take it.
            if term == WIN_SCORE:
                return [], (idx, op)

            key = (p2, o2)
            if key not in states:
                states[key] = (idx, bit, op, p2, o2, term)

    candidates = []
    for idx, bit, op, p2, o2, term in states.values():
        unsafe = False
        threats = 0

        if term is None:
            base = -_evaluate(o2, p2)
            unsafe = _can_win_own_only(o2, p2)
            if unsafe:
                heuristic = -WIN_SCORE // 4 + base
            else:
                threats = _count_winning_moves(p2, o2, 4)
                if threats:
                    base += 70_000 + 35_000 * min(threats, 4)
                heuristic = base
        else:
            heuristic = term

        candidates.append((heuristic, idx, bit, op, p2, o2, term, unsafe, threats))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates, None


class _SearchTimeout(Exception):
    pass


def _choose_move(us, opp):
    occupied = us | opp
    empty = FULL_MASK & ~occupied
    if not empty:
        return 0, 0

    # Strong, safe opening: quadrant center, which is rotation-invariant.
    if occupied == 0:
        return 7, 0  # row 2, col 2, quadrant 0, left

    first_bit = empty & -empty
    fallback = (first_bit.bit_length() - 1, 0)

    perf = time.perf_counter
    start = perf()
    deadline = start + TIME_LIMIT

    candidates, winning_move = _make_root_candidates(us, opp)
    if winning_move is not None:
        return winning_move
    if not candidates:
        return fallback

    best_move = (candidates[0][1], candidates[0][3])
    preferred = best_move

    tt = {}
    nodes = 0

    def check_time(force=False):
        nonlocal nodes
        nodes += 1
        if force or (nodes & 255) == 0:
            if perf() > deadline:
                raise _SearchTimeout

    def store_tt(key, depth, value):
        old = tt.get(key)
        if old is None or old[0] <= depth:
            tt[key] = (depth, value)

    def negamax(side, other, depth, alpha, beta):
        check_time(False)

        if depth <= 0:
            return _evaluate(side, other)

        key = (side, other)
        ent = tt.get(key)
        if ent is not None and ent[0] >= depth:
            return ent[1]

        empty_here = FULL_MASK & ~(side | other)
        if not empty_here:
            return 0

        # Fast exact one-ply search; avoids sorting overhead at the frontier.
        if depth == 1:
            best = -INF
            cut = False
            seen = set()
            scanned = 0

            for idx in CELL_ORDER:
                bit = CELL_BITS[idx]
                if not (empty_here & bit):
                    continue
                for op in OPS:
                    p2, o2 = _apply_move(side, other, bit, op)
                    child_key = (p2, o2)
                    if child_key in seen:
                        continue
                    seen.add(child_key)

                    term = _terminal_after(p2, o2)
                    if term == WIN_SCORE:
                        store_tt(key, depth, WIN_SCORE)
                        return WIN_SCORE

                    if term is None:
                        val = -_evaluate(o2, p2)
                    else:
                        val = term

                    if val > best:
                        best = val
                    if val > alpha:
                        alpha = val
                    if alpha >= beta:
                        cut = True
                        break

                    scanned += 1
                    if (scanned & 63) == 0 and perf() > deadline:
                        raise _SearchTimeout
                if cut:
                    break

            if best == -INF:
                best = 0
            if not cut:
                store_tt(key, depth, best)
            return best

        immediate, children = _generate_children_sorted(side, other)
        if immediate is not None:
            store_tt(key, depth, immediate)
            return immediate

        best = -INF
        cut = False
        for _, term, next_side, next_other in children:
            if term is None:
                val = -negamax(next_side, next_other, depth - 1, -beta, -alpha)
            else:
                val = term

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                cut = True
                break

        if best == -INF:
            best = 0
        if not cut:
            store_tt(key, depth, best)
        return best

    def root_search(depth, pref):
        if pref is not None:
            pi, po = pref
            ordered = sorted(
                candidates,
                key=lambda c: ((c[1] == pi and c[3] == po), c[0]),
                reverse=True
            )
        else:
            ordered = candidates

        alpha = -INF
        best_val = -INF
        best_heur = -INF
        best_mv = best_move

        for cand in ordered:
            check_time(True)
            heuristic, idx, bit, op, p2, o2, term, unsafe, threats = cand

            if term is None:
                val = -negamax(o2, p2, depth - 1, -INF, -alpha)
                # Root-level exact check: never choose a move that permits an
                # immediate opponent win if any alternative exists.
                if unsafe and val > -WIN_SCORE // 4:
                    val = -WIN_SCORE // 4
            else:
                val = term

            if val > best_val or (val == best_val and heuristic > best_heur):
                best_val = val
                best_heur = heuristic
                best_mv = (idx, op)

            if val > alpha:
                alpha = val

        return best_val, best_mv

    branch = len(candidates)
    empties = _POPCOUNT(empty)

    if branch > 190:
        max_depth = 2
    elif branch > 115:
        max_depth = 3
    elif branch > 70:
        max_depth = 4
    else:
        max_depth = 5

    if empties >= 28:
        max_depth = min(max_depth, 3)
    if empties >= 22 and branch > 70:
        max_depth = min(max_depth, 3)
    if empties <= 8:
        max_depth = max(max_depth, 6)

    for depth in range(1, max_depth + 1):
        if perf() > deadline:
            break
        try:
            score, mv = root_search(depth, preferred)
            best_move = mv
            preferred = mv
            if score >= WIN_SCORE // 2:
                break
        except _SearchTimeout:
            break

    return best_move


def _arrays_to_bits(you, opponent):
    us = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            bit = 1 << (r * 6 + c)
            if int(yr[c]) != 0:
                us |= bit
            elif int(orow[c]) != 0:
                opp |= bit
    return us, opp


def _format_move(idx, op):
    row = idx // 6 + 1
    col = idx % 6 + 1
    quad = op >> 1
    direction = "L" if (op & 1) == 0 else "R"
    return f"{row},{col},{quad},{direction}"


def _first_legal_from_bits(us, opp):
    empty = FULL_MASK & ~(us | opp)
    if empty:
        bit = empty & -empty
        idx = bit.bit_length() - 1
        return _format_move(idx, 0)
    return "1,1,0,L"


def _fallback_from_arrays(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    return "1,1,0,L"


def policy(you, opponent) -> str:
    try:
        us, opp = _arrays_to_bits(you, opponent)
        idx, op = _choose_move(us, opp)
        if 0 <= idx < 36 and 0 <= op < 8 and (CELL_BITS[idx] & (us | opp)) == 0:
            return _format_move(idx, op)
        return _first_legal_from_bits(us, opp)
    except Exception:
        return _fallback_from_arrays(you, opponent)
