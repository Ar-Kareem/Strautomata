
from typing import List, Tuple

# ---------- Precomputation ----------

FULL_MASK = (1 << 36) - 1
WIN_SCORE = 10**9

# Board index: idx = r * 6 + c, with r,c in 0..5

# Quadrant origins
QUAD_ORIGINS = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

# Rotation maps and masks
ROT_MAP = {}   # (quad, dir) -> list[(old_idx, new_idx)]
QUAD_MASK = {} # quad -> mask

for q, (r0, c0) in QUAD_ORIGINS.items():
    pairs_r = []
    pairs_l = []
    mask = 0
    for i in range(3):
        for j in range(3):
            old_r, old_c = r0 + i, c0 + j
            old_idx = old_r * 6 + old_c
            mask |= 1 << old_idx

            # Clockwise: (i,j) -> (j,2-i)
            nr, nc = r0 + j, c0 + (2 - i)
            pairs_r.append((old_idx, nr * 6 + nc))

            # Counterclockwise: (i,j) -> (2-j,i)
            nr, nc = r0 + (2 - j), c0 + i
            pairs_l.append((old_idx, nr * 6 + nc))
    ROT_MAP[(q, 'R')] = pairs_r
    ROT_MAP[(q, 'L')] = pairs_l
    QUAD_MASK[q] = mask

# All contiguous 5-cell segments on a 6x6 board
SEGMENTS = []

# Rows
for r in range(6):
    for c0 in range(2):
        SEGMENTS.append([r * 6 + (c0 + k) for k in range(5)])

# Cols
for c in range(6):
    for r0 in range(2):
        SEGMENTS.append([(r0 + k) * 6 + c for k in range(5)])

# Diagonal down-right
diag_starts = [(0, 0), (0, 1), (1, 0)]
for r0, c0 in diag_starts:
    cells = []
    r, c = r0, c0
    while r < 6 and c < 6:
        cells.append(r * 6 + c)
        r += 1
        c += 1
    for s in range(len(cells) - 4):
        SEGMENTS.append(cells[s:s+5])

# Diagonal down-left
diag_starts = [(0, 5), (0, 4), (1, 5)]
for r0, c0 in diag_starts:
    cells = []
    r, c = r0, c0
    while r < 6 and c >= 0:
        cells.append(r * 6 + c)
        r += 1
        c -= 1
    for s in range(len(cells) - 4):
        SEGMENTS.append(cells[s:s+5])

SEGMENT_MASKS = []
for seg in SEGMENTS:
    m = 0
    for idx in seg:
        m |= 1 << idx
    SEGMENT_MASKS.append(m)

# Positional weights: prefer center-ish cells
CELL_WEIGHTS = [
    1, 2, 2, 2, 2, 1,
    2, 4, 5, 5, 4, 2,
    2, 5, 6, 6, 5, 2,
    2, 5, 6, 6, 5, 2,
    2, 4, 5, 5, 4, 2,
    1, 2, 2, 2, 2, 1,
]

# Heuristic values by count in an uncontested 5-segment
COUNT_SCORE = [0, 1, 8, 60, 5000, 500000]


# ---------- Bitboard helpers ----------

def popcount(x: int) -> int:
    return x.bit_count()

def arrays_to_masks(you, opponent) -> Tuple[int, int]:
    my_mask = 0
    opp_mask = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            idx = r * 6 + c
            if int(yr[c]) == 1:
                my_mask |= 1 << idx
            elif int(orow[c]) == 1:
                opp_mask |= 1 << idx
    return my_mask, opp_mask

def rotate_mask(mask: int, quad: int, direction: str) -> int:
    base = mask & ~QUAD_MASK[quad]
    moved = 0
    for old_idx, new_idx in ROT_MAP[(quad, direction)]:
        if (mask >> old_idx) & 1:
            moved |= 1 << new_idx
    return base | moved

def apply_move(my_mask: int, opp_mask: int, row: int, col: int, quad: int, direction: str) -> Tuple[int, int]:
    idx = row * 6 + col
    my_mask |= 1 << idx
    my_mask = rotate_mask(my_mask, quad, direction)
    opp_mask = rotate_mask(opp_mask, quad, direction)
    return my_mask, opp_mask

def has_five(mask: int) -> bool:
    for seg_mask in SEGMENT_MASKS:
        if (mask & seg_mask) == seg_mask:
            return True
    return False

def terminal_value(my_mask: int, opp_mask: int):
    my_win = has_five(my_mask)
    opp_win = has_five(opp_mask)
    if my_win and opp_win:
        return 0
    if my_win:
        return WIN_SCORE
    if opp_win:
        return -WIN_SCORE
    if (my_mask | opp_mask) == FULL_MASK:
        return 0
    return None

def evaluate(my_mask: int, opp_mask: int) -> int:
    t = terminal_value(my_mask, opp_mask)
    if t is not None:
        return t

    score = 0

    # Segment-based potential
    for seg_mask in SEGMENT_MASKS:
        myc = popcount(my_mask & seg_mask)
        oppc = popcount(opp_mask & seg_mask)
        if oppc == 0:
            score += COUNT_SCORE[myc]
        elif myc == 0:
            score -= COUNT_SCORE[oppc]

    # Positional
    mm = my_mask
    while mm:
        lsb = mm & -mm
        idx = lsb.bit_length() - 1
        score += CELL_WEIGHTS[idx]
        mm ^= lsb

    om = opp_mask
    while om:
        lsb = om & -om
        idx = lsb.bit_length() - 1
        score -= CELL_WEIGHTS[idx]
        om ^= lsb

    return score


# ---------- Move generation ----------

def all_legal_moves(my_mask: int, opp_mask: int) -> List[Tuple[int, int, int, str]]:
    occ = my_mask | opp_mask
    moves = []
    for idx in range(36):
        if ((occ >> idx) & 1) == 0:
            r, c = divmod(idx, 6)
            for q in range(4):
                moves.append((r, c, q, 'L'))
                moves.append((r, c, q, 'R'))
    return moves

def ordered_moves(my_mask: int, opp_mask: int, max_moves: int = None) -> List[Tuple[int, int, int, str]]:
    occ = my_mask | opp_mask
    scored = []
    for idx in range(36):
        if ((occ >> idx) & 1) == 0:
            r, c = divmod(idx, 6)
            place_bonus = CELL_WEIGHTS[idx] * 2
            for q in range(4):
                for d in ('L', 'R'):
                    nm, no = apply_move(my_mask, opp_mask, r, c, q, d)
                    t = terminal_value(nm, no)
                    if t == WIN_SCORE:
                        sc = WIN_SCORE
                    elif t == 0:
                        sc = -50  # draw not prioritized unless needed
                    else:
                        sc = evaluate(nm, no) + place_bonus
                    scored.append((sc, (r, c, q, d)))
    scored.sort(key=lambda x: x[0], reverse=True)
    moves = [m for _, m in scored]
    if max_moves is not None and len(moves) > max_moves:
        return moves[:max_moves]
    return moves

def immediate_winning_moves(my_mask: int, opp_mask: int, moves=None) -> List[Tuple[int, int, int, str]]:
    if moves is None:
        moves = all_legal_moves(my_mask, opp_mask)
    wins = []
    for mv in moves:
        nm, no = apply_move(my_mask, opp_mask, *mv)
        my_win = has_five(nm)
        opp_win = has_five(no)
        if my_win and not opp_win:
            wins.append(mv)
    return wins

def opponent_has_immediate_win_after(my_mask: int, opp_mask: int, candidate_limit: int = 64) -> bool:
    # Opponent to move on board (my_mask, opp_mask) from their perspective.
    # Search for any move producing opponent win without simultaneous my win.
    moves = ordered_moves(opp_mask, my_mask, max_moves=candidate_limit)
    for mv in moves:
        no, nm = apply_move(opp_mask, my_mask, *mv)
        opp_win = has_five(no)
        my_win = has_five(nm)
        if opp_win and not my_win:
            return True
    # Safety fallback if candidate pruning missed something in sparse boards
    if popcount((~(my_mask | opp_mask)) & FULL_MASK) <= 10:
        for mv in all_legal_moves(opp_mask, my_mask):
            no, nm = apply_move(opp_mask, my_mask, *mv)
            opp_win = has_five(no)
            my_win = has_five(nm)
            if opp_win and not my_win:
                return True
    return False


# ---------- Search ----------

TT = {}

def negamax(my_mask: int, opp_mask: int, depth: int, alpha: int, beta: int) -> int:
    key = (my_mask, opp_mask, depth)
    if key in TT:
        return TT[key]

    t = terminal_value(my_mask, opp_mask)
    if t is not None:
        TT[key] = t
        return t
    if depth == 0:
        v = evaluate(my_mask, opp_mask)
        TT[key] = v
        return v

    empties = 36 - popcount(my_mask | opp_mask)
    move_cap = 10 if empties > 12 else 16 if empties > 8 else None
    moves = ordered_moves(my_mask, opp_mask, max_moves=move_cap)

    best = -10**18
    for mv in moves:
        nm, no = apply_move(my_mask, opp_mask, *mv)
        val = -negamax(no, nm, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


# ---------- Main policy ----------

def policy(you, opponent) -> str:
    my_mask, opp_mask = arrays_to_masks(you, opponent)

    # Guaranteed fallback legal move
    fallback = None
    occ = my_mask | opp_mask
    for idx in range(36):
        if ((occ >> idx) & 1) == 0:
            r, c = divmod(idx, 6)
            fallback = (r, c, 0, 'L')
            break

    if fallback is None:
        return "1,1,0,L"  # should never happen per problem statement

    TT.clear()

    empties = 36 - popcount(occ)

    # 1) Immediate winning move anywhere
    all_moves = ordered_moves(my_mask, opp_mask, max_moves=None if empties <= 12 else 64)
    wins = immediate_winning_moves(my_mask, opp_mask, moves=all_moves)
    if wins:
        mv = wins[0]
        return f"{mv[0]+1},{mv[1]+1},{mv[2]},{mv[3]}"

    # 2) Build shortlist
    if empties > 16:
        shortlist = ordered_moves(my_mask, opp_mask, max_moves=12)
    elif empties > 10:
        shortlist = ordered_moves(my_mask, opp_mask, max_moves=18)
    else:
        shortlist = ordered_moves(my_mask, opp_mask, max_moves=None)

    if not shortlist:
        mv = fallback
        return f"{mv[0]+1},{mv[1]+1},{mv[2]},{mv[3]}"

    # 3) Prefer moves that deny opponent an immediate win
    safe_moves = []
    unsafe_moves = []
    for mv in shortlist:
        nm, no = apply_move(my_mask, opp_mask, *mv)
        if opponent_has_immediate_win_after(nm, no):
            unsafe_moves.append(mv)
        else:
            safe_moves.append(mv)

    candidates = safe_moves if safe_moves else shortlist

    # 4) Shallow search
    best_mv = candidates[0]
    best_val = -10**18

    # Use slightly deeper search late game
    depth = 2 if empties > 8 else 3

    for mv in candidates:
        nm, no = apply_move(my_mask, opp_mask, *mv)
        t = terminal_value(nm, no)
        if t is not None:
            val = t
        else:
            val = -negamax(no, nm, depth - 1, -10**18, 10**18)

        # Tiny tie-break using static eval for determinism
        val = (val, evaluate(nm, no))
        if val > best_val if isinstance(best_val, tuple) else True:
            best_val = val
            best_mv = mv

    mv = best_mv
    return f"{mv[0]+1},{mv[1]+1},{mv[2]},{mv[3]}"
