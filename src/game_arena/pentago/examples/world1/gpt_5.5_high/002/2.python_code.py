
from time import perf_counter

N = 6
FULL_MASK = (1 << 36) - 1
CELL_BITS = tuple(1 << i for i in range(36))
DIR_CHARS = ("L", "R")

WIN_SCORE = 1_000_000_000


def _make_win_masks():
    masks = []
    seen = set()
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= CELL_BITS[(r + k * dr) * 6 + (c + k * dc)]
                    if m not in seen:
                        seen.add(m)
                        masks.append(m)
    return tuple(masks)


WIN_MASKS = _make_win_masks()

# Quadrant cells in row-major local 3x3 order.
_QUAD_CELLS = []
for q in range(4):
    r0 = 0 if q < 2 else 3
    c0 = 0 if (q % 2) == 0 else 3
    cells = []
    for rr in range(3):
        for cc in range(3):
            cells.append((r0 + rr) * 6 + (c0 + cc))
    _QUAD_CELLS.append(tuple(cells))
_QUAD_CELLS = tuple(_QUAD_CELLS)

_QUAD_BITS = tuple(tuple(CELL_BITS[i] for i in cells) for cells in _QUAD_CELLS)
_QUAD_MASKS = tuple(sum(bits) for bits in _QUAD_BITS)
_OUT_MASKS = tuple(FULL_MASK ^ m for m in _QUAD_MASKS)

# Rotation tables. ri = quad * 2 + dir, dir 0=L, 1=R.
_ROT_TABLES = []
_ROTATED_CELL_BITS = []

for q in range(4):
    cells = _QUAD_CELLS[q]
    for d in range(2):
        table = [0] * 512
        for pat in range(512):
            out = 0
            for i, src_cell in enumerate(cells):
                if pat & (1 << i):
                    lr, lc = divmod(i, 3)
                    if d == 0:       # L / anticlockwise
                        nr, nc = 2 - lc, lr
                    else:            # R / clockwise
                        nr, nc = lc, 2 - lr
                    out |= CELL_BITS[cells[nr * 3 + nc]]
            table[pat] = out
        _ROT_TABLES.append(tuple(table))

        moved = [CELL_BITS[i] for i in range(36)]
        for i, src_cell in enumerate(cells):
            lr, lc = divmod(i, 3)
            if d == 0:
                nr, nc = 2 - lc, lr
            else:
                nr, nc = lc, 2 - lr
            moved[src_cell] = CELL_BITS[cells[nr * 3 + nc]]
        _ROTATED_CELL_BITS.append(tuple(moved))

_ROT_TABLES = tuple(_ROT_TABLES)
_ROTATED_CELL_BITS = tuple(_ROTATED_CELL_BITS)

_MOVE_STRINGS = tuple(
    tuple(
        f"{cell // 6 + 1},{cell % 6 + 1},{ri // 2},{DIR_CHARS[ri & 1]}"
        for ri in range(8)
    )
    for cell in range(36)
)

# Positional weights: line participation plus small bonuses for stable quadrant centers
# and central board cells.
_POS_WEIGHTS = [0] * 36
for i, b in enumerate(CELL_BITS):
    _POS_WEIGHTS[i] = sum(1 for m in WIN_MASKS if m & b)

for r, c in ((1, 1), (1, 4), (4, 1), (4, 4)):
    _POS_WEIGHTS[r * 6 + c] += 3

for r in (2, 3):
    for c in (2, 3):
        _POS_WEIGHTS[r * 6 + c] += 4

_POS_WEIGHTS = tuple(_POS_WEIGHTS)

# Open fours are very important because they usually represent a direct next-move win.
_MY_WEIGHTS = (0, 2, 12, 80, 8000, 10000000)
_OPP_WEIGHTS = (0, 3, 15, 100, 9000, 10000000)


def _bits_from_array(board):
    bits = 0
    idx = 0
    for r in range(6):
        for c in range(6):
            try:
                v = board[r][c]
                if v:
                    bits |= CELL_BITS[idx]
            except Exception:
                if board[r, c]:
                    bits |= CELL_BITS[idx]
            idx += 1
    return bits


def _cells_from_mask(mask):
    cells = []
    while mask:
        lsb = mask & -mask
        cells.append(lsb.bit_length() - 1)
        mask ^= lsb
    return cells


def _rotate_bits(bits, ri):
    q = ri >> 1
    qb = _QUAD_BITS[q]
    pat = 0
    for i in range(9):
        if bits & qb[i]:
            pat |= 1 << i
    return (bits & _OUT_MASKS[q]) | _ROT_TABLES[ri][pat]


def _has_win(bits):
    for mask in WIN_MASKS:
        if (bits & mask) == mask:
            return True
    return False


def _static_eval(mine, opp):
    score = 0

    for mask in WIN_MASKS:
        mb = mine & mask
        ob = opp & mask

        if mb:
            if not ob:
                score += _MY_WEIGHTS[mb.bit_count()]
        elif ob:
            score -= _OPP_WEIGHTS[ob.bit_count()]

    x = mine
    while x:
        lsb = x & -x
        score += _POS_WEIGHTS[lsb.bit_length() - 1]
        x ^= lsb

    x = opp
    while x:
        lsb = x & -x
        score -= _POS_WEIGHTS[lsb.bit_length() - 1]
        x ^= lsb

    return score


def _min_reply_value(mine, opp, alpha, deadline):
    """
    State after our candidate move.
    Opponent is to move. Return the minimum value they can force,
    from our perspective.
    """
    empty = FULL_MASK ^ (mine | opp)
    if not empty:
        return 0

    cells = _cells_from_mask(empty)
    full_after_reply = len(cells) == 1

    worst = WIN_SCORE
    seen = set()

    for ri in range(8):
        base_opp = _rotate_bits(opp, ri)
        base_mine = _rotate_bits(mine, ri)
        my_win_base = _has_win(base_mine)
        moved_bits = _ROTATED_CELL_BITS[ri]

        for cell in cells:
            opp2 = base_opp | moved_bits[cell]
            mine2 = base_mine

            key = (opp2, mine2)
            if key in seen:
                continue
            seen.add(key)

            opp_win = _has_win(opp2)

            if opp_win:
                if not my_win_base:
                    return -WIN_SCORE
                val = 0
            elif my_win_base:
                val = WIN_SCORE - 1
            elif full_after_reply:
                val = 0
            else:
                val = _static_eval(mine2, opp2)

            if val < worst:
                worst = val
                if worst <= alpha:
                    return worst

        if perf_counter() > deadline:
            return worst if worst != WIN_SCORE else _static_eval(mine, opp)

    return worst if worst != WIN_SCORE else 0


def policy(you, opponent) -> str:
    mine = _bits_from_array(you)
    opp = _bits_from_array(opponent)
    occupied = mine | opp
    empty = FULL_MASK ^ occupied

    # The problem guarantees at least one empty cell, but keep a syntactic fallback.
    if not empty:
        return "1,1,0,L"

    # Strong, stable opening: place in one of the central four cells and rotate
    # an empty quadrant.
    if occupied == 0:
        return "3,3,1,L"

    deadline = perf_counter() + 0.88

    cells = _cells_from_mask(empty)
    fallback = _MOVE_STRINGS[cells[0]][0]
    full_after_move = len(cells) == 1

    candidates = []
    seen = set()

    for ri in range(8):
        base_mine = _rotate_bits(mine, ri)
        base_opp = _rotate_bits(opp, ri)
        opp_win_base = _has_win(base_opp)
        moved_bits = _ROTATED_CELL_BITS[ri]

        for cell in cells:
            mine2 = base_mine | moved_bits[cell]
            opp2 = base_opp

            key = (mine2, opp2)
            if key in seen:
                continue
            seen.add(key)

            move = _MOVE_STRINGS[cell][ri]
            my_win = _has_win(mine2)

            # Immediate sole win: always take it.
            if my_win and not opp_win_base:
                return move

            if opp_win_base and not my_win:
                quick = -WIN_SCORE
                terminal = True
            elif my_win and opp_win_base:
                quick = 0          # simultaneous win is a draw
                terminal = True
            elif full_after_move:
                quick = 0
                terminal = True
            else:
                quick = _static_eval(mine2, opp2)
                terminal = False

            candidates.append((quick, move, mine2, opp2, terminal))

    if not candidates:
        return fallback

    candidates.sort(key=lambda x: x[0], reverse=True)

    best_move = candidates[0][1]
    best_score = -WIN_SCORE - 1
    best_quick = -WIN_SCORE - 1
    alpha = -WIN_SCORE - 1

    for quick, move, mine2, opp2, terminal in candidates:
        if perf_counter() > deadline:
            break

        if terminal:
            val = quick
        else:
            val = _min_reply_value(mine2, opp2, alpha, deadline)

        if val > best_score or (val == best_score and quick > best_quick):
            best_score = val
            best_quick = quick
            best_move = move
            if val > alpha:
                alpha = val

    return best_move
