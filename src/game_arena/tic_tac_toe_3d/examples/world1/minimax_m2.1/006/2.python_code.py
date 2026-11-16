
import sys
import math

# ----------------------------------------------------------------------
# Pre‑compute all 49 winning lines (as bit masks)
# Index mapping: i*9 + j*3 + k  (i,j,k in {0,1,2})
# ----------------------------------------------------------------------
FULL_MASK = (1 << 27) - 1

def idx(i, j, k):
    """Convert (i,j,k) to a flat index 0..26."""
    return i * 9 + j * 3 + k

# generate all lines
win_masks = []

# 1) axis‑parallel lines (3 * 9 = 27)
for a in range(3):          # fixed coordinate
    for b in range(3):      # second coordinate
        # line along the third dimension
        m = 0
        for c in range(3):
            m |= 1 << idx(a, b, c)
        win_masks.append(m)
        # line along second dimension
        m = 0
        for c in range(3):
            m |= 1 << idx(a, c, b)
        win_masks.append(m)
        # line along first dimension
        m = 0
        for c in range(3):
            m |= 1 << idx(c, a, b)
        win_masks.append(m)

# 2) face diagonals (6 faces * 2 = 12)
# xy‑planes (z fixed)
for z in range(3):
    m = 0
    for d in range(3):
        m |= 1 << idx(d, d, z)
    win_masks.append(m)
    m = 0
    for d in range(3):
        m |= 1 << idx(d, 2 - d, z)
    win_masks.append(m)
# yz‑planes (x fixed)
for x in range(3):
    m = 0
    for d in range(3):
        m |= 1 << idx(x, d, d)
    win_masks.append(m)
    m = 0
    for d in range(3):
        m |= 1 << idx(x, d, 2 - d)
    win_masks.append(m)
# xz‑planes (y fixed)
for y in range(3):
    m = 0
    for d in range(3):
        m |= 1 << idx(d, y, d)
    win_masks.append(m)
    m = 0
    for d in range(3):
        m |= 1 << idx(d, y, 2 - d)
    win_masks.append(m)

# 3) space diagonals (4)
for d in range(3):
    m = 0
    m |= 1 << idx(d, d, d)
    m |= 1 << idx(2 - d, 2 - d, 2 - d)
    win_masks.append(m)
    m = 0
    m |= 1 << idx(d, d, 2 - d)
    m |= 1 << idx(2 - d, 2 - d, d)
    win_masks.append(m)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def bitcount(x):
    """Number of set bits in x (Python >=3.8)."""
    return x.bit_count()

def mask_from_board(board):
    """Convert the 3‑D list board into two bit‑masks: ours and opponent's."""
    us = 0
    them = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                if v == 1:
                    us |= 1 << idx(i, j, k)
                elif v == -1:
                    them |= 1 << idx(i, j, k)
    return us, them

def emptymask(us, them):
    return FULL_MASK ^ (us | them)

def idx_to_coord(ind):
    i = ind // 9
    j = (ind % 9) // 3
    k = ind % 3
    return (i, j, k)

def generate_moves(mask):
    """Yield indices of set bits in mask (i.e. empty cells)."""
    m = mask
    while m:
        lsb = m & -m
        yield (lsb.bit_length() - 1)
        m ^= lsb

# ----------------------------------------------------------------------
# Static evaluation
# ----------------------------------------------------------------------
def evaluate(us, them):
    """
    Return a scalar score for the position.
    Positive values favour us, negative values favour the opponent.
    """
    score = 0
    for m in win_masks:
        us_bits = bitcount(us & m)
        them_bits = bitcount(them & m)
        # a line already won – should not happen if called correctly,
        # but we give a large penalty / reward anyway
        if us_bits == 3:
            score += 1000
        elif them_bits == 3:
            score -= 1000
        else:
            empty = 3 - us_bits - them_bits
            if us_bits == 2 and empty == 1:
                score += 10
            elif them_bits == 2 and empty == 1:
                score -= 10
            if us_bits == 1:
                score += 1
            if them_bits == 1:
                score -= 1
    return score

# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
INF = 10**9

def minimax(us, them, depth, alpha, beta, is_us_turn):
    """Recursive minimax.  us / them are the current masks."""
    # terminal check
    for m in win_masks:
        if (us & m) == m:
            return 1000 - depth          # we win sooner is better
        if (them & m) == m:
            return -1000 + depth          # opponent wins

    if depth == 0:
        return evaluate(us, them)

    empt = emptymask(us, them)
    moves = list(generate_moves(empt))

    # small optimisation: order moves
    # we do a very cheap static score for each move and sort descending
    # (only useful for the root, but harmless elsewhere)
    if depth >= 2:
        move_scores = []
        for mv in moves:
            if is_us_turn:
                sc = evaluate(us | (1 << mv), them)
            else:
                sc = evaluate(us, them | (1 << mv))
            move_scores.append((sc, mv))
        move_scores.sort(key=lambda x: -x[0])
        moves = [mv for _, mv in move_scores]

    if is_us_turn:
        best = -INF
        for mv in moves:
            new_us = us | (1 << mv)
            val = minimax(new_us, them, depth - 1, alpha, beta, False)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        best = INF
        for mv in moves:
            new_them = them | (1 << mv)
            val = minimax(us, new_them, depth - 1, alpha, beta, True)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(board):
    """
    Given the current board (list of list of list of int),
    return a tuple (i,j,k) with the next move.
    """
    us, them = mask_from_board(board)

    # count pieces – it must be our turn (we play 1)
    if bitcount(us) != bitcount(them):
        # opponent just moved; it's our turn
        pass
    # else: we have the same number – also our turn

    empt = emptymask(us, them)
    if empt == 0:
        # board full – return any coordinate (should not happen)
        return (0, 0, 0)

    # ------------------------------------------------------------------
    # 1) Immediate win ?
    # ------------------------------------------------------------------
    for mv in generate_moves(empt):
        if any(((us | (1 << mv)) & wm) == wm for wm in win_masks):
            return idx_to_coord(mv)

    # ------------------------------------------------------------------
    # 2) Block opponent's immediate win ?
    # ------------------------------------------------------------------
    for mv in generate_moves(empt):
        if any(((them | (1 << mv)) & wm) == wm for wm in win_masks):
            # we must block this one – return immediately
            return idx_to_coord(mv)

    # ------------------------------------------------------------------
    # 3) Full minimax search (depth limited)
    # ------------------------------------------------------------------
    # choose depth based on how many cells are left
    empty_cnt = bitcount(empt)
    depth = 4
    if empty_cnt <= 10:
        depth = 5
    if empty_cnt <= 6:
        depth = 6

    # generate all moves and evaluate
    best_move = None
    best_val = -INF
    alpha = -INF
    beta = INF

    # we will order moves a bit: first centre, then corners, then others
    centre = idx(1, 1, 1)
    moves = list(generate_moves(empt))
    # simple heuristic ordering
    moves.sort(key=lambda m: (m != centre, m))   # centre first

    for mv in moves:
        new_us = us | (1 << mv)
        # quick upper‑bound using static eval (helps ordering)
        val = minimax(new_us, them, depth - 1, alpha, beta, False)
        if val > best_val:
            best_val = val
            best_move = mv
        if best_val > alpha:
            alpha = best_val
        # we could break early if we find a winning move, but we already
        # checked immediate wins; a deeper winning line may exist.
    if best_move is None:
        # fallback – should never happen
        best_move = moves[0]

    return idx_to_coord(best_move)
