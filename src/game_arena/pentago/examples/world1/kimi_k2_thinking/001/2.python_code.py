
import sys

# ----------------------------------------------------------------------
# Constants and pre‑computed tables
# ----------------------------------------------------------------------
BOARD_SIZE = 6
NUM_CELLS = BOARD_SIZE * BOARD_SIZE
FULL_MASK = (1 << NUM_CELLS) - 1
INF = 10**9

# ------------------------------------------------------------
# Quadrant definitions (3x3 blocks)
# ------------------------------------------------------------
quad_cells = []
for q in range(4):
    cells = []
    row_start = (q // 2) * 3
    col_start = (q % 2) * 3
    for i in range(3):
        for j in range(3):
            r = row_start + i
            c = col_start + j
            cells.append(r * BOARD_SIZE + c)
    quad_cells.append(cells)

# bit‑mask of each quadrant
quad_mask = [sum(1 << p for p in q) for q in quad_cells]

# ------------------------------------------------------------
# Rotation mappings (9 cells inside a quadrant)
# ------------------------------------------------------------
# left  = 90° anticlockwise, right = 90° clockwise
left_map = [2, 5, 8, 1, 4, 7, 0, 3, 6]
right_map = [6, 3, 0, 7, 4, 1, 8, 5, 2]

# for each quadrant and direction store a list of (old_pos, new_pos)
rot_map = {q: {'L': [], 'R': []} for q in range(4)}
for q in range(4):
    for i in range(9):
        old = quad_cells[q][i]
        new_left = quad_cells[q][left_map[i]]
        new_right = quad_cells[q][right_map[i]]
        rot_map[q]['L'].append((old, new_left))
        rot_map[q]['R'].append((old, new_right))

# ------------------------------------------------------------
# All possible 5‑in‑a‑row lines (horizontal, vertical, both diagonals)
# ------------------------------------------------------------
line_masks = []

# horizontal
for r in range(6):
    for start_c in range(2):
        m = 0
        for c in range(start_c, start_c + 5):
            m |= 1 << (r * 6 + c)
        line_masks.append(m)

# vertical
for c in range(6):
    for start_r in range(2):
        m = 0
        for r in range(start_r, start_r + 5):
            m |= 1 << (r * 6 + c)
        line_masks.append(m)

# diagonal down‑right
for start_r in range(2):
    for start_c in range(2):
        m = 0
        for i in range(5):
            r = start_r + i
            c = start_c + i
            m |= 1 << (r * 6 + c)
        line_masks.append(m)

# diagonal down‑left
for start_r in range(2):
    for start_c in range(4, 6):
        m = 0
        for i in range(5):
            r = start_r + i
            c = start_c - i
            m |= 1 << (r * 6 + c)
        line_masks.append(m)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def rotate_bits(bits, quad, direction):
    """Rotate the chosen quadrant of a 36‑bit board."""
    mask = quad_mask[quad]
    new_bits = bits & ~mask               # keep everything outside the quadrant
    rotated = 0
    for old_pos, new_pos in rot_map[quad][direction]:
        if (bits >> old_pos) & 1:
            rotated |= 1 << new_pos
    new_bits |= rotated
    return new_bits


def apply_move(actor, opponent, pos, quad, direction):
    """Place a marble for `actor` and rotate the quadrant."""
    actor_new = actor | (1 << pos)
    actor_new = rotate_bits(actor_new, quad, direction)
    opponent_new = rotate_bits(opponent, quad, direction)
    return actor_new, opponent_new


def has_win(bits):
    """Check whether the player has at least one line of five."""
    for m in line_masks:
        if (bits & m) == m:
            return True
    return False


def heuristic_bits(bits, opp_bits):
    """Score a player's non‑blocked lines (more marbles = higher value)."""
    score = 0
    for m in line_masks:
        if opp_bits & m:          # blocked by opponent
            continue
        cnt = (bits & m).bit_count()
        if cnt == 5:
            score += 1000000
        elif cnt == 4:
            score += 1000
        elif cnt == 3:
            score += 100
        elif cnt == 2:
            score += 10
        elif cnt == 1:
            score += 1
    return score


def evaluate(you_bits, opp_bits):
    """
    Static evaluation from the point of view of the player whose bits are `you_bits`.
    Returns:
        INF   – we have a winning line and opponent does not,
       -INF   – opponent has a winning line and we do not,
        0     – draw (both win or board full without winner),
        otherwise heuristic difference.
    """
    you_win = has_win(you_bits)
    opp_win = has_win(opp_bits)
    if you_win and opp_win:
        return 0
    if you_win:
        return INF
    if opp_win:
        return -INF
    if (you_bits | opp_bits) == FULL_MASK:   # full board, no winner -> draw
        return 0
    return heuristic_bits(you_bits, opp_bits) - heuristic_bits(opp_bits, you_bits)


def generate_moves(actor_bits, opponent_bits):
    """All legal (pos, quad, dir) for the player whose bits are `actor_bits`."""
    empty = ~(actor_bits | opponent_bits) & FULL_MASK
    moves = []
    while empty:
        low = empty & -empty
        pos = low.bit_length() - 1
        empty ^= low
        for q in range(4):
            for d in ('L', 'R'):
                moves.append((pos, q, d))
    return moves


# ----------------------------------------------------------------------
# Public API – the policy function
# ----------------------------------------------------------------------
def policy(you, opponent):
    """
    Return a move as "row,col,quad,dir".
    The function performs a depth‑2 minimax search with the evaluation described above.
    """
    # ---- convert board arrays to 36‑bit integers -----------------
    you_bits = 0
    opp_bits = 0
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                you_bits |= 1 << (r * 6 + c)
            if opponent[r][c] == 1:
                opp_bits |= 1 << (r * 6 + c)

    # ---- generate all our possible moves -------------------------
    moves = generate_moves(you_bits, opp_bits)

    best_move = None
    best_value = -INF - 1

    # ---- iterate over our moves ---------------------------------
    for pos, q, d in moves:
        # apply our move
        you1, opp1 = apply_move(you_bits, opp_bits, pos, q, d)

        you_win = has_win(you1)
        opp_win = has_win(opp1)

        # immediate win ─ return at once
        if you_win and not opp_win:
            return f"{pos // 6 + 1},{pos % 6 + 1},{q},{d}"
        # immediate loss ─ skip this move
        if opp_win and not you_win:
            continue
        # immediate draw ─ keep it but continue searching
        if you_win and opp_win:
            move_value = 0
        else:
            # no immediate terminal state ─ look at opponent replies
            opp_moves = generate_moves(opp1, you1)
            worst = INF  # opponent will minimise our value
            for opp_pos, opp_q, opp_d in opp_moves:
                # apply opponent move (swap roles)
                opp2, you2 = apply_move(opp1, you1, opp_pos, opp_q, opp_d)
                val = evaluate(you2, opp2)   # from our point of view
                if val < worst:
                    worst = val
                if worst == -INF:            # opponent can force a win, stop early
                    break
            move_value = worst

        # keep the move with the highest worst‑case value
        if move_value > best_value:
            best_value = move_value
            best_move = (pos, q, d)
            # if we found a guaranteed win we could stop here,
            # but we already handled the immediate win case above.

    # ---- no winning move found, return the best we have ----------
    if best_move is None:               # all moves were losing ─ return any legal move
        pos, q, d = moves[0]
        return f"{pos // 6 + 1},{pos % 6 + 1},{q},{d}"

    pos, q, d = best_move
    return f"{pos // 6 + 1},{pos % 6 + 1},{q},{d}"
