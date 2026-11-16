
from time import perf_counter

# ---------- Constants and precomputation ----------

N = 6
NUM_CELLS = 36
ALL_MASK = (1 << NUM_CELLS) - 1
WIN_SCORE = 10_000_000

CELL_BITS = [1 << i for i in range(NUM_CELLS)]

# All contiguous 5-cell winning masks.
WIN_MASKS = []

# Horizontal
for r in range(6):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= CELL_BITS[r * 6 + c + k]
        WIN_MASKS.append(m)

# Vertical
for c in range(6):
    for r in range(2):
        m = 0
        for k in range(5):
            m |= CELL_BITS[(r + k) * 6 + c]
        WIN_MASKS.append(m)

# Diagonal down-right
for r in range(2):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= CELL_BITS[(r + k) * 6 + c + k]
        WIN_MASKS.append(m)

# Diagonal down-left
for r in range(2):
    for c in range(4, 6):
        m = 0
        for k in range(5):
            m |= CELL_BITS[(r + k) * 6 + c - k]
        WIN_MASKS.append(m)

CELL_WIN_MASKS = [[] for _ in range(NUM_CELLS)]
for wm in WIN_MASKS:
    for i in range(NUM_CELLS):
        if wm & CELL_BITS[i]:
            CELL_WIN_MASKS[i].append(wm)

# Quadrants.
QCELLS = []
QBITS = []
QUAD_MASKS = []
for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if q % 2 == 0 else 3
    cells = []
    mask = 0
    for i in range(3):
        for j in range(3):
            p = (br + i) * 6 + (bc + j)
            cells.append(p)
            mask |= CELL_BITS[p]
    QCELLS.append(cells)
    QBITS.append([CELL_BITS[p] for p in cells])
    QUAD_MASKS.append(mask)

INV_QUAD_MASKS = [ALL_MASK ^ m for m in QUAD_MASKS]

# Rotation tables. ROTATIONS index -> (quad, dir)
ROTATIONS = []
ROT_QUAD = []
ROT_TABLE = []

for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if q % 2 == 0 else 3
    cells = QCELLS[q]

    for d in ("L", "R"):
        ROTATIONS.append((q, d))
        ROT_QUAD.append(q)

        table = [0] * 512
        for idx in range(512):
            out = 0
            for li, old_pos in enumerate(cells):
                if idx & (1 << li):
                    i, j = divmod(li, 3)
                    if d == "R":
                        ni, nj = j, 2 - i
                    else:
                        ni, nj = 2 - j, i
                    new_pos = (br + ni) * 6 + (bc + nj)
                    out |= CELL_BITS[new_pos]
            table[idx] = out
        ROT_TABLE.append(table)

# Positional weights. Quadrant centers are valuable because they do not move.
CELL_WEIGHTS_2D = [
    [3, 4, 5, 5, 4, 3],
    [4, 9, 6, 6, 9, 4],
    [5, 6, 7, 7, 6, 5],
    [5, 6, 7, 7, 6, 5],
    [4, 9, 6, 6, 9, 4],
    [3, 4, 5, 5, 4, 3],
]
CELL_WEIGHTS = []
for r in range(6):
    for c in range(6):
        CELL_WEIGHTS.append(CELL_WEIGHTS_2D[r][c])

ROW_POS_SCORE = [[0] * 64 for _ in range(6)]
for r in range(6):
    for pat in range(64):
        s = 0
        for c in range(6):
            if pat & (1 << c):
                s += CELL_WEIGHTS[r * 6 + c]
        ROW_POS_SCORE[r][pat] = s

LINE_WEIGHTS = (0, 2, 18, 120, 1500, 0)

_WIN_CACHE = {}
_EVAL_CACHE = {}
_THREAT_CACHE = {}


# ---------- Low-level helpers ----------

def _array_to_bits(arr):
    bits = 0
    for r in range(6):
        row = arr[r]
        for c in range(6):
            if int(row[c]):
                bits |= CELL_BITS[r * 6 + c]
    return bits


def _first_legal(me, op):
    empty = ALL_MASK & ~(me | op)
    if empty:
        b = empty & -empty
        cell = b.bit_length() - 1
        return _move_to_str((cell, 0))
    # The API says this should never happen.
    return "1,1,0,L"


def _move_to_str(move):
    cell, ri = move
    r = cell // 6 + 1
    c = cell % 6 + 1
    q, d = ROTATIONS[ri]
    return f"{r},{c},{q},{d}"


def _rotate_bits(bits, ri):
    q = ROT_QUAD[ri]
    idx = 0
    qbits = QBITS[q]

    for i, b in enumerate(qbits):
        if bits & b:
            idx |= 1 << i

    return (bits & INV_QUAD_MASKS[q]) | ROT_TABLE[ri][idx]


def _apply_move(me, op, cell, ri):
    me2 = me | CELL_BITS[cell]
    return _rotate_bits(me2, ri), _rotate_bits(op, ri)


def _has_win(bits):
    v = _WIN_CACHE.get(bits)
    if v is not None:
        return v

    res = False
    for m in WIN_MASKS:
        if (bits & m) == m:
            res = True
            break

    if len(_WIN_CACHE) < 200000:
        _WIN_CACHE[bits] = res
    return res


def _pos_score(bits):
    return (
        ROW_POS_SCORE[0][bits & 63]
        + ROW_POS_SCORE[1][(bits >> 6) & 63]
        + ROW_POS_SCORE[2][(bits >> 12) & 63]
        + ROW_POS_SCORE[3][(bits >> 18) & 63]
        + ROW_POS_SCORE[4][(bits >> 24) & 63]
        + ROW_POS_SCORE[5][(bits >> 30) & 63]
    )


def _static_eval(me, op):
    """Positive means good for me."""
    key = (me, op)
    v = _EVAL_CACHE.get(key)
    if v is not None:
        return v

    score = 0

    for m in WIN_MASKS:
        mc = (me & m).bit_count()
        oc = (op & m).bit_count()

        if mc and oc:
            continue
        if mc:
            score += LINE_WEIGHTS[mc]
        elif oc:
            # Slight defensive bias.
            score -= (LINE_WEIGHTS[oc] * 11) // 10

    score += 3 * (_pos_score(me) - _pos_score(op))

    if len(_EVAL_CACHE) < 200000:
        _EVAL_CACHE[key] = score
    return score


def _winning_spots_bits(me, empty):
    """Final empty cells where adding one marble gives me a 5-in-row."""
    spots = 0
    e = empty

    while e:
        b = e & -e
        cell = b.bit_length() - 1
        mb = me | b

        for m in CELL_WIN_MASKS[cell]:
            if (mb & m) == m:
                spots |= b
                break

        e ^= b

    return spots


def _clean_win_count(me, op):
    """
    Counts up to 2 clean immediate winning moves for 'me'.

    Exact for Pentago moves because:
      place then rotate == rotate current board then place in rotated empty cell.
    """
    key = (me, op)
    v = _THREAT_CACHE.get(key)
    if v is not None:
        return v

    total = 0

    for ri in range(8):
        rm = _rotate_bits(me, ri)
        ro = _rotate_bits(op, ri)

        # If opponent already wins after this rotation, our win would not be clean.
        if _has_win(ro):
            continue

        # If the rotation alone creates my win, any legal placement works.
        if _has_win(rm):
            total = 2
            break

        empty = ALL_MASK & ~(rm | ro)
        spots = _winning_spots_bits(rm, empty)

        if spots:
            total += spots.bit_count()
            if total >= 2:
                total = 2
                break

    if len(_THREAT_CACHE) < 200000:
        _THREAT_CACHE[key] = total
    return total


# ---------- Search ----------

def _leaf_score(me, op):
    """Position with 'me' to move, evaluated from me's perspective."""
    if _clean_win_count(me, op) > 0:
        return WIN_SCORE - 20

    s = _static_eval(me, op)

    # If the opponent has an immediate threat, prefer positions where we are
    # likely to be able to address it, but do not treat it as already lost.
    if _clean_win_count(op, me) > 0:
        s -= 60000

    return s


def _opponent_min_value(my, opp, alpha, deadline):
    """
    Board after our candidate move. Opponent is to move.
    Return value from our perspective assuming opponent minimizes it.
    """
    # Exact immediate-loss check.
    if _clean_win_count(opp, my) > 0:
        return -WIN_SCORE + 2

    empty = ALL_MASK & ~(my | opp)
    if not empty:
        return 0

    minv = WIN_SCORE * 2
    checked = 0
    e = empty

    while e:
        b = e & -e
        cell = b.bit_length() - 1

        for ri in range(8):
            opp2, my2 = _apply_move(opp, my, cell, ri)

            ow = _has_win(opp2)
            mw = _has_win(my2)

            if ow or mw:
                if ow and not mw:
                    return -WIN_SCORE + 2
                elif mw and not ow:
                    val = WIN_SCORE - 2
                else:
                    val = 0
            else:
                val = _leaf_score(my2, opp2)

            if val < minv:
                minv = val
                if minv <= alpha:
                    return minv

            checked += 1
            if (checked & 31) == 0 and perf_counter() > deadline:
                return minv if minv != WIN_SCORE * 2 else _static_eval(my, opp)

        e ^= b

    return minv if minv != WIN_SCORE * 2 else 0


def _choose_move(me, op):
    start = perf_counter()
    deadline = start + 0.88

    empty = ALL_MASK & ~(me | op)
    empty_count = empty.bit_count()

    draw_move = None
    scored = []

    e = empty
    while e:
        b = e & -e
        cell = b.bit_length() - 1

        for ri in range(8):
            move = (cell, ri)
            nm, no = _apply_move(me, op, cell, ri)

            mw = _has_win(nm)
            ow = _has_win(no)

            # Take any clean immediate win.
            if mw and not ow:
                return _move_to_str(move)

            # Terminal draw: good fallback, but keep searching for a win.
            if mw and ow:
                if draw_move is None:
                    draw_move = move
                continue

            # Terminal losing move.
            if ow and not mw:
                scored.append((-WIN_SCORE, move, nm, no, -WIN_SCORE, True, 0))
                continue

            opp_threat = _clean_win_count(no, nm)
            my_threat = _clean_win_count(nm, no)

            s = _static_eval(nm, no)
            s += my_threat * 70000
            s -= opp_threat * 300000

            unsafe = opp_threat > 0
            if unsafe:
                s -= 1_000_000

            scored.append((s, move, nm, no, None, unsafe, my_threat))

        e ^= b

    if not scored:
        if draw_move is not None:
            return _move_to_str(draw_move)
        return _first_legal(me, op)

    scored.sort(key=lambda x: x[0], reverse=True)

    # Start from a draw if we have one; otherwise from the best heuristic move.
    if draw_move is not None:
        best_move = draw_move
        best_val = 0
        best_order = 0
    else:
        best_move = scored[0][1]
        best_val = -WIN_SCORE * 2
        best_order = scored[0][0]

    safe = [x for x in scored if not x[5]]

    if safe:
        current_opp_threat = _clean_win_count(op, me) > 0

        if current_opp_threat:
            max_roots = len(safe)
        elif empty_count >= 32:
            max_roots = 64
        elif empty_count >= 26:
            max_roots = 96
        elif empty_count >= 18:
            max_roots = 150
        else:
            max_roots = len(safe)

        selected = safe[:max_roots]

        # Also include tactical threat-creating moves even if their static
        # ordering is slightly lower.
        chosen = {x[1] for x in selected}
        for x in safe[max_roots:]:
            if x[6] > 0 and x[1] not in chosen and len(selected) < max_roots + 40:
                selected.append(x)
                chosen.add(x[1])
    else:
        # If every move allows an immediate win, still return the least bad one.
        selected = scored[:min(48, len(scored))]

    for item in selected:
        if perf_counter() > deadline:
            break

        order_score, move, nm, no, terminal_val, _unsafe, _my_threat = item

        if terminal_val is not None:
            val = terminal_val
        else:
            val = _opponent_min_value(nm, no, best_val, deadline)

        if val > best_val or (val == best_val and order_score > best_order):
            best_val = val
            best_order = order_score
            best_move = move

    return _move_to_str(best_move)


# ---------- Required API ----------

def policy(you, opponent) -> str:
    me = 0
    op = 0

    try:
        me = _array_to_bits(you)
        op = _array_to_bits(opponent)
        return _choose_move(me, op)
    except Exception:
        # Absolute safety fallback: always return some legal placement if possible.
        return _first_legal(me, op)
