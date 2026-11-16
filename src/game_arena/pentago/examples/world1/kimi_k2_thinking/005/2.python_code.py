
import numpy as np

# ----------------------------------------------------------------------
# Pre‑computed data
# ----------------------------------------------------------------------
# All 5‑cell windows that can give a win (horizontal, vertical, both diagonals)
LINE_INDICES = []
# Horizontal (6 rows × 2 possible starts)
for r in range(6):
    for c0 in range(2):
        LINE_INDICES.append([(r, c0 + d) for d in range(5)])
# Vertical (6 columns × 2 possible starts)
for c in range(6):
    for r0 in range(2):
        LINE_INDICES.append([(r0 + d, c) for d in range(5)])
# Diagonal down‑right (2×2 possible starts)
for r0 in range(2):
    for c0 in range(2):
        LINE_INDICES.append([(r0 + d, c0 + d) for d in range(5)])
# Diagonal down‑left (2×2 possible starts)
for r0 in range(2):
    for c0 in range(3, 5):
        LINE_INDICES.append([(r0 + d, c0 - d) for d in range(5)])

# Slices that extract the four 3×3 quadrants
QUAD_SLICES = [
    (slice(0, 3), slice(0, 3)),   # quad 0 – top‑left
    (slice(0, 3), slice(3, 6)),   # quad 1 – top‑right
    (slice(3, 6), slice(0, 3)),   # quad 2 – bottom‑left
    (slice(3, 6), slice(3, 6)),   # quad 3 – bottom‑right
]

WIN_SCORE = 1e9  # sufficiently larger than any normal heuristic value


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def win_status(you, opponent):
    """
    Returns
        'you'      – you have at least one 5‑in‑a‑row, opponent does not,
        'opponent' – opponent has at least one 5‑in‑a‑row, you do not,
        'draw'     – both have a 5‑in‑a‑row,
        None       – nobody has a 5‑in‑a‑row.
    """
    you_win = opp_win = False
    for coords in LINE_INDICES:
        you_cnt = opp_cnt = 0
        for r, c in coords:
            if you[r, c]:
                you_cnt += 1
            elif opponent[r, c]:
                opp_cnt += 1
        if you_cnt == 5:
            you_win = True
        if opp_cnt == 5:
            opp_win = True
    if you_win and opp_win:
        return 'draw'
    if you_win:
        return 'you'
    if opp_win:
        return 'opponent'
    return None


def evaluate(you, opponent):
    """
    Heuristic score from the viewpoint of the player described by `you`.
    Large positive means good for `you`, large negative good for `opponent`.
    """
    status = win_status(you, opponent)
    if status == 'you':
        return WIN_SCORE
    if status == 'opponent':
        return -WIN_SCORE
    if status == 'draw':
        return 0

    you_score = 0.0
    opp_score = 0.0

    # Score open lines for you
    for coords in LINE_INDICES:
        you_cnt = opp_cnt = 0
        for r, c in coords:
            if you[r, c]:
                you_cnt += 1
            elif opponent[r, c]:
                opp_cnt += 1
        if opp_cnt == 0:          # line is open for you
            you_score += [0, 1, 10, 100, 1000][you_cnt]

    # Score open lines for opponent (swap roles)
    for coords in LINE_INDICES:
        you_cnt = opp_cnt = 0
        for r, c in coords:
            if opponent[r, c]:
                opp_cnt += 1
            elif you[r, c]:
                you_cnt += 1
        if you_cnt == 0:          # line is open for opponent
            opp_score += [0, 1, 10, 100, 1000][opp_cnt]

    # tiny centre‑control bonus
    centre = [(2, 2), (2, 3), (3, 2), (3, 3)]
    for r, c in centre:
        if you[r, c]:
            you_score += 0.5
        if opponent[r, c]:
            opp_score += 0.5

    return you_score - opp_score


def legal_moves(you, opponent):
    """Return a list of all legal moves (row, col, quad, dir)."""
    moves = []
    # does a quadrant contain any marble? (used to prune directions)
    quad_nonempty = []
    for q in range(4):
        rsl, csl = QUAD_SLICES[q]
        nonempty = np.any(you[rsl, csl] | opponent[rsl, csl])
        quad_nonempty.append(nonempty)

    for r in range(6):
        for c in range(6):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for q in range(4):
                    if quad_nonempty[q]:
                        moves.append((r + 1, c + 1, q, 'L'))
                        moves.append((r + 1, c + 1, q, 'R'))
                    else:
                        # rotation of an empty quadrant does nothing – store only one direction
                        moves.append((r + 1, c + 1, q, 'L'))
    return moves


def apply_move(you, opponent, move):
    """
    Apply a move described by (row, col, quad, dir) to copies of the boards.
    Returns (new_you, new_opponent).
    """
    row, col, quad, direction = move
    r = row - 1
    c = col - 1
    new_you = you.copy()
    new_opp = opponent.copy()
    # place the marble
    new_you[r, c] = 1

    # rotate the chosen quadrant
    rsl, csl = QUAD_SLICES[quad]
    sub_you = new_you[rsl, csl]
    sub_opp = new_opp[rsl, csl]
    if direction == 'L':          # 90° anticlockwise
        sub_you = np.rot90(sub_you, k=1)
        sub_opp = np.rot90(sub_opp, k=1)
    else:                         # 90° clockwise
        sub_you = np.rot90(sub_you, k=3)
        sub_opp = np.rot90(sub_opp, k=3)
    new_you[rsl, csl] = sub_you
    new_opp[rsl, csl] = sub_opp
    return new_you, new_opp


def format_move(move):
    """Convert a move tuple into the required string representation."""
    row, col, quad, direction = move
    return f"{row},{col},{quad},{direction}"


# ----------------------------------------------------------------------
# Public API – the only function that will be called by the arena
# ----------------------------------------------------------------------
def policy(you, opponent):
    """
    you, opponent : 6×6 arrays (list of lists or numpy arrays) of 0/1.
    Returns a move string "row,col,quad,dir".
    """
    # convert input to numpy arrays (no‑copy if already numpy)
    you = np.asarray(you, dtype=int)
    opponent = np.asarray(opponent, dtype=int)

    # obtain all legal moves for the current player
    moves = legal_moves(you, opponent)

    best_move = None
    best_val = -float('inf')

    for move in moves:
        # Apply our move
        you_new, opp_new = apply_move(you, opponent, move)

        # If we win immediately (and opponent does not) play it straight away
        if win_status(you_new, opp_new) == 'you':
            return format_move(move)

        # Opponent's possible replies
        opp_moves = legal_moves(opp_new, you_new)
        opp_best = -float('inf')
        if not opp_moves:                     # board full -> draw
            opp_best = 0.0
        else:
            for opp_move in opp_moves:
                opp_new2, you_new2 = apply_move(opp_new, you_new, opp_move)
                # If opponent wins after this reply, mark reply as winning
                if win_status(opp_new2, you_new2) == 'opponent':
                    opp_best = float('inf')
                    break
                # Evaluate from opponent's perspective (higher is better for them)
                val = evaluate(opp_new2, you_new2)
                if val > opp_best:
                    opp_best = val

        # Our own heuristic after the move
        our_score = evaluate(you_new, opp_new)

        # Net advantage: our score minus opponent's best reply
        net = our_score - opp_best
        if net > best_val:
            best_val = net
            best_move = move

    # Fallback – should never happen, but guarantees a legal move
    if best_move is None:
        best_move = moves[0]

    return format_move(best_move)
