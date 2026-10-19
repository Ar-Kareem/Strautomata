
WIN_SCORE = 10 ** 9

# ---------- Precompute board geometry ----------

FULL_MASK = (1 << 36) - 1

ROTS = [
    (0, 'L'), (0, 'R'),
    (1, 'L'), (1, 'R'),
    (2, 'L'), (2, 'R'),
    (3, 'L'), (3, 'R'),
]

# Quadrant cells in local row-major order
QCELLS = [
    [0, 1, 2, 6, 7, 8, 12, 13, 14],       # top-left
    [3, 4, 5, 9, 10, 11, 15, 16, 17],     # top-right
    [18, 19, 20, 24, 25, 26, 30, 31, 32], # bottom-left
    [21, 22, 23, 27, 28, 29, 33, 34, 35], # bottom-right
]

QMASKS = []
for cells in QCELLS:
    m = 0
    for g in cells:
        m |= 1 << g
    QMASKS.append(m)

# Rotation maps keyed by masked global subset integer
ROT_MAP = [[None, None] for _ in range(4)]  # [quad][0=L,1=R]

def _build_rot_maps():
    for q in range(4):
        cells = QCELLS[q]
        left_map = {}
        right_map = {}
        for occ in range(512):
            sub = 0
            left_sub = 0
            right_sub = 0
            for old_i, g in enumerate(cells):
                if (occ >> old_i) & 1:
                    sub |= 1 << g
                    r = old_i // 3
                    c = old_i % 3

                    # old(r,c) -> new(2-c, r) for L
                    nl = 2 - c
                    ml = r
                    new_i_l = nl * 3 + ml
                    left_sub |= 1 << cells[new_i_l]

                    # old(r,c) -> new(c, 2-r) for R
                    nr = c
                    mr = 2 - r
                    new_i_r = nr * 3 + mr
                    right_sub |= 1 << cells[new_i_r]

            left_map[sub] = left_sub
            right_map[sub] = right_sub
        ROT_MAP[q][0] = left_map
        ROT_MAP[q][1] = right_map

_build_rot_maps()

# All 5-cell winning masks
WIN_MASKS = []

# Horizontal
for r in range(6):
    for c in range(2):
        m = 0
        for k in range(5):
            idx = r * 6 + (c + k)
            m |= 1 << idx
        WIN_MASKS.append(m)

# Vertical
for r in range(2):
    for c in range(6):
        m = 0
        for k in range(5):
            idx = (r + k) * 6 + c
            m |= 1 << idx
        WIN_MASKS.append(m)

# Diagonal down-right
for r in range(2):
    for c in range(2):
        m = 0
        for k in range(5):
            idx = (r + k) * 6 + (c + k)
            m |= 1 << idx
        WIN_MASKS.append(m)

# Diagonal down-left
for r in range(2):
    for c in range(4, 6):
        m = 0
        for k in range(5):
            idx = (r + k) * 6 + (c - k)
            m |= 1 << idx
        WIN_MASKS.append(m)

WIN_MASKS = tuple(WIN_MASKS)

# Cell importance = how many 5-segments include the cell
CELL_IMPORTANCE = [0] * 36
for idx in range(36):
    bit = 1 << idx
    count = 0
    for wm in WIN_MASKS:
        if wm & bit:
            count += 1
    CELL_IMPORTANCE[idx] = count

# Search empty cells in a strong order
CELL_ORDER = sorted(range(36), key=lambda i: (-CELL_IMPORTANCE[i], abs((i // 6) - 2.5) + abs((i % 6) - 2.5), i))

MY_W = (0, 2, 16, 140, 12000, 250000)
OP_W = (0, 2, 18, 160, 14000, 250000)

# ---------- Core bitboard helpers ----------

def _boards_to_masks(you, opponent):
    me = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        base = r * 6
        for c in range(6):
            if int(yr[c]) == 1:
                me |= 1 << (base + c)
            elif int(orow[c]) == 1:
                opp |= 1 << (base + c)
    return me, opp

def _rotate(bits, quad, dir_idx):
    sub = bits & QMASKS[quad]
    return (bits & ~QMASKS[quad]) | ROT_MAP[quad][dir_idx][sub]

def _apply_move(me, opp, cell, rot_id):
    quad, dch = ROTS[rot_id]
    dir_idx = 0 if dch == 'L' else 1
    me2 = me | (1 << cell)
    me2 = _rotate(me2, quad, dir_idx)
    opp2 = _rotate(opp, quad, dir_idx)
    return me2, opp2

def _has_win(bits):
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False

def _terminal_after_move(me, opp):
    mw = _has_win(me)
    ow = _has_win(opp)
    if mw and ow:
        return 0
    if mw:
        return WIN_SCORE
    if ow:
        return -WIN_SCORE
    if (me | opp) == FULL_MASK:
        return 0
    return None

def _static_eval(me, opp):
    score = 0

    # Line-based potential
    for m in WIN_MASKS:
        a = (me & m).bit_count()
        b = (opp & m).bit_count()
        if a and b:
            continue
        if a:
            score += MY_W[a]
        elif b:
            score -= OP_W[b]

    # Small cell-importance bonus
    mb = me
    ob = opp
    while mb:
        lsb = mb & -mb
        idx = lsb.bit_length() - 1
        score += 3 * CELL_IMPORTANCE[idx]
        mb ^= lsb
    while ob:
        lsb = ob & -ob
        idx = lsb.bit_length() - 1
        score -= 3 * CELL_IMPORTANCE[idx]
        ob ^= lsb

    return score

def _move_to_str(cell, rot_id):
    r = cell // 6 + 1
    c = cell % 6 + 1
    q, d = ROTS[rot_id]
    return f"{r},{c},{q},{d}"

def _first_legal_move(you, opponent):
    for r in range(6):
        for c in range(6):
            if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                return f"{r+1},{c+1},0,L"
    return "1,1,0,L"

# ---------- Main policy ----------

def policy(you, opponent) -> str:
    try:
        me, opp = _boards_to_masks(you, opponent)
        occupied = me | opp

        # Generate all root moves with quick ordering
        root_moves = []
        best_immediate = None
        best_immediate_score = -10**18

        for cell in CELL_ORDER:
            if (occupied >> cell) & 1:
                continue
            for rot_id in range(8):
                me2, opp2 = _apply_move(me, opp, cell, rot_id)
                term = _terminal_after_move(me2, opp2)

                if term is not None:
                    quick = term
                else:
                    quick = _static_eval(me2, opp2)

                root_moves.append((quick, cell, rot_id, me2, opp2, term))

                if term == WIN_SCORE:
                    return _move_to_str(cell, rot_id)

                if quick > best_immediate_score:
                    best_immediate_score = quick
                    best_immediate = (cell, rot_id)

        if not root_moves:
            return _first_legal_move(you, opponent)

        root_moves.sort(key=lambda x: x[0], reverse=True)

        best_val = -10**18
        best_move = best_immediate if best_immediate is not None else (root_moves[0][1], root_moves[0][2])

        # Exact 2-ply minimax
        for quick, cell, rot_id, me2, opp2, term in root_moves:
            if term is not None:
                val = term
            else:
                occupied2 = me2 | opp2
                worst = 10**18

                # Opponent tries to minimize our value
                stop = False
                for ocell in CELL_ORDER:
                    if (occupied2 >> ocell) & 1:
                        continue
                    for orot in range(8):
                        opp3, me3 = _apply_move(opp2, me2, ocell, orot)
                        term_opp = _terminal_after_move(opp3, me3)

                        if term_opp is not None:
                            val2 = -term_opp
                        else:
                            val2 = _static_eval(me3, opp3)

                        if val2 < worst:
                            worst = val2

                        # Alpha-style cutoff at root
                        if worst <= best_val:
                            stop = True
                            break
                    if stop:
                        break

                val = worst

            if val > best_val:
                best_val = val
                best_move = (cell, rot_id)

                if best_val == WIN_SCORE:
                    break

        return _move_to_str(best_move[0], best_move[1])

    except Exception:
        return _first_legal_move(you, opponent)
