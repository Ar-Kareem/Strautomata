
# Pentago policy
# Board convention internally:
#   1  = us
#  -1  = opponent
#   0  = empty

WIN_SCORE = 10000000
THREAT_PENALTY = 250000

# ---------------------------------------------------------------------
# Precomputation
# ---------------------------------------------------------------------

LINES = []

# Horizontal length-5 segments
for r in range(6):
    for c in range(2):
        LINES.append(tuple(r * 6 + (c + k) for k in range(5)))

# Vertical length-5 segments
for c in range(6):
    for r in range(2):
        LINES.append(tuple((r + k) * 6 + c for k in range(5)))

# Diagonal down-right length-5 segments
for r in range(2):
    for c in range(2):
        LINES.append(tuple((r + k) * 6 + (c + k) for k in range(5)))

# Diagonal down-left length-5 segments
for r in range(2):
    for c in range(4, 6):
        LINES.append(tuple((r + k) * 6 + (c - k) for k in range(5)))

# Rotation source/destination pairs for each quadrant and direction.
# Applying pairs means: new_board[dest] = old_board[src]
ROT_PAIRS = {}

_quad_bases = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

for q, (br, bc) in _quad_bases.items():
    # Left / anticlockwise
    pairs_l = []
    # Right / clockwise
    pairs_r = []

    for rr in range(3):
        for cc in range(3):
            dest = (br + rr) * 6 + (bc + cc)

            # For anticlockwise:
            # new[rr][cc] = old[cc][2-rr]
            src_l = (br + cc) * 6 + (bc + (2 - rr))
            pairs_l.append((dest, src_l))

            # For clockwise:
            # new[rr][cc] = old[2-cc][rr]
            src_r = (br + (2 - cc)) * 6 + (bc + rr)
            pairs_r.append((dest, src_r))

    ROT_PAIRS[(q, "L")] = pairs_l
    ROT_PAIRS[(q, "R")] = pairs_r

# Positional weights: cells involved in more possible 5-lines are slightly better.
POS_WEIGHT = [0] * 36
for line in LINES:
    for i in line:
        POS_WEIGHT[i] += 1

# Quadrant centers are stable under rotation, so they are useful anchors.
for i in (1 * 6 + 1, 1 * 6 + 4, 4 * 6 + 1, 4 * 6 + 4):
    POS_WEIGHT[i] += 3

CELL_ORDER = sorted(range(36), key=lambda i: POS_WEIGHT[i], reverse=True)

# Heuristic line weights.
OUR_LINE_WEIGHT = [0, 2, 14, 90, 900, WIN_SCORE]
OPP_LINE_WEIGHT = [0, 3, 18, 120, 1100, WIN_SCORE]


# ---------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------

def _apply_move(board, idx, quad, direction, side):
    """Return board after side places at idx and rotates quad direction."""
    b = list(board)
    b[idx] = side
    old = b[:]
    for dest, src in ROT_PAIRS[(quad, direction)]:
        b[dest] = old[src]
    return tuple(b)


def _has_win(board, side):
    target = 5 * side
    for a, b, c, d, e in LINES:
        if board[a] + board[b] + board[c] + board[d] + board[e] == target:
            return True
    return False


def _heuristic(board):
    us_win = _has_win(board, 1)
    op_win = _has_win(board, -1)

    if us_win and op_win:
        return 0
    if us_win:
        return WIN_SCORE
    if op_win:
        return -WIN_SCORE

    score = 0

    for line in LINES:
        p = 0
        n = 0
        for i in line:
            v = board[i]
            if v == 1:
                p += 1
            elif v == -1:
                n += 1

        if p and n:
            continue
        if p:
            score += OUR_LINE_WEIGHT[p]
        elif n:
            score -= OPP_LINE_WEIGHT[n]

    # Mild positional preference.
    for i, v in enumerate(board):
        if v == 1:
            score += POS_WEIGHT[i]
        elif v == -1:
            score -= POS_WEIGHT[i]

    return score


def _ordered_empty_indices(board):
    for i in CELL_ORDER:
        if board[i] == 0:
            yield i


def _has_winning_move(board, side):
    """True if side has a legal move that wins without also giving a draw."""
    other = -side

    for idx in _ordered_empty_indices(board):
        for q in range(4):
            for d in ("L", "R"):
                nb = _apply_move(board, idx, q, d, side)
                if _has_win(nb, side) and not _has_win(nb, other):
                    return True

    return False


def _opponent_min_value(board, alpha):
    """
    Opponent to move. Return the minimum resulting heuristic value
    assuming opponent chooses the most damaging reply.
    """
    worst = WIN_SCORE
    seen = set()

    for idx in _ordered_empty_indices(board):
        for q in range(4):
            for d in ("L", "R"):
                nb = _apply_move(board, idx, q, d, -1)
                if nb in seen:
                    continue
                seen.add(nb)

                us_win = _has_win(nb, 1)
                op_win = _has_win(nb, -1)

                if op_win and not us_win:
                    val = -WIN_SCORE
                elif us_win and not op_win:
                    val = WIN_SCORE
                elif us_win and op_win:
                    val = 0
                else:
                    val = _heuristic(nb)

                if val < worst:
                    worst = val
                    if worst <= alpha:
                        return worst

    if worst == WIN_SCORE:
        return 0
    return worst


def _format_move(move):
    idx, q, d = move
    r = idx // 6 + 1
    c = idx % 6 + 1
    return f"{r},{c},{q},{d}"


def _fallback_move(board):
    for i, v in enumerate(board):
        if v == 0:
            return f"{i // 6 + 1},{i % 6 + 1},0,R"
    return "1,1,0,R"


# ---------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------

def policy(you, opponent) -> str:
    board_list = []
    stones = 0

    for r in range(6):
        for c in range(6):
            if int(you[r][c]):
                board_list.append(1)
                stones += 1
            elif int(opponent[r][c]):
                board_list.append(-1)
                stones += 1
            else:
                board_list.append(0)

    board = tuple(board_list)

    # Strong and fast opening: quadrant center, rotation irrelevant.
    if stones == 0:
        return "2,2,0,R"

    safe_moves = []
    best_any_score = -10**18
    best_any_move = None
    draw_move = None

    seen = set()

    # First pass:
    # 1. Take immediate wins.
    # 2. Reject self-losing rotations.
    # 3. Prefer moves that do not allow an opponent immediate win.
    for idx in _ordered_empty_indices(board):
        for q in range(4):
            for d in ("L", "R"):
                nb = _apply_move(board, idx, q, d, 1)
                if nb in seen:
                    continue
                seen.add(nb)

                move = (idx, q, d)

                us_win = _has_win(nb, 1)
                op_win = _has_win(nb, -1)

                # Winning move, not merely a draw.
                if us_win and not op_win:
                    return _format_move(move)

                # Both winning is a draw.
                if us_win and op_win:
                    if draw_move is None:
                        draw_move = move
                    score = 0

                # Rotating into opponent-only five-in-a-row loses.
                elif op_win:
                    score = -WIN_SCORE + _heuristic(nb) // 100

                else:
                    h = _heuristic(nb)

                    # Avoid any move allowing an immediate opponent win.
                    if _has_winning_move(nb, -1):
                        score = h - THREAT_PENALTY
                    else:
                        score = h
                        safe_moves.append((score, move, nb))

                if score > best_any_score:
                    best_any_score = score
                    best_any_move = move

    # If there are safe moves, do a limited opponent-response search.
    if safe_moves:
        safe_moves.sort(key=lambda x: x[0], reverse=True)

        # Search more deeply later in the game when branching is lower.
        if stones < 10:
            max_candidates = 8
        elif stones < 20:
            max_candidates = 12
        else:
            max_candidates = 20

        best_val = -10**18
        best_move = safe_moves[0][1]

        for base_score, move, nb in safe_moves[:max_candidates]:
            # The opponent will minimize our resulting heuristic.
            val = _opponent_min_value(nb, best_val - base_score // 8)
            combined = val + base_score // 8

            if combined > best_val:
                best_val = combined
                best_move = move

        return _format_move(best_move)

    # If no safe move exists, take a draw if one is immediately available.
    if draw_move is not None:
        return _format_move(draw_move)

    # Otherwise play the least-bad legal move found.
    if best_any_move is not None:
        return _format_move(best_any_move)

    # Absolute safety fallback.
    return _fallback_move(board)
