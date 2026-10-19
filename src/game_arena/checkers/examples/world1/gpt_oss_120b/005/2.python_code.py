
import itertools

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def dark_square(r, c):
    return (r + c) % 2 == 1

def opponent_color(color):
    return 'w' if color == 'b' else 'b'

def promotion_row(color):
    return 7 if color == 'w' else 0

def piece_value(is_king):
    return 2 if is_king else 1

# ----------------------------------------------------------------------
# Capture‑generation (recursive DFS)
# ----------------------------------------------------------------------
DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def generate_captures(start, my_kings, opp_set, occ_set, is_king):
    """
    Returns a list of tuples (path, captured) where
    - path is a list of positions from start to final landing square
    - captured is a set of opponent squares removed during the sequence
    """
    results = []

    def dfs(pos, occ, captured, path):
        extended = False
        for dr, dc in DIRS:
            mid_r, mid_c = pos[0] + dr, pos[1] + dc
            land_r, land_c = pos[0] + 2 * dr, pos[1] + 2 * dc
            if not (in_bounds(mid_r, mid_c) and in_bounds(land_r, land_c)):
                continue
            if not dark_square(land_r, land_c):
                continue
            mid = (mid_r, mid_c)
            land = (land_r, land_c)
            if mid in opp_set and mid not in captured and land not in occ:
                # perform capture
                new_occ = occ.copy()
                new_occ.remove(pos)          # piece leaves current square
                new_occ.add(land)            # lands on new square
                new_captured = captured | {mid}
                dfs(land, new_occ, new_captured, path + [land])
                extended = True
        if not extended:
            # No further captures – store result
            results.append((path, captured))

    dfs(start, occ_set, frozenset(), [start])
    return results

# ----------------------------------------------------------------------
# Simple (non‑capturing) move generation
# ----------------------------------------------------------------------
def generate_simple_moves(my_men, my_kings, occ_set, color):
    moves = []
    forward = 1 if color == 'w' else -1
    # men
    for r, c in my_men:
        for dr, dc in [(forward, -1), (forward, 1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occ_set:
                moves.append(((r, c), (nr, nc), False))  # False → not a king
    # kings
    for r, c in my_kings:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occ_set:
                moves.append(((r, c), (nr, nc), True))
    return moves

# ----------------------------------------------------------------------
# Opponent capture threat squares (used for safety heuristic)
# ----------------------------------------------------------------------
def opponent_threat_squares(opp_men, opp_kings, my_set, occ_set):
    threat = set()
    # treat opponent pieces as both men and kings for capture direction (men can capture backwards)
    all_opp = opp_men + opp_kings
    for r, c in all_opp:
        for dr, dc in DIRS:
            mid_r, mid_c = r + dr, c + dc
            land_r, land_c = r + 2 * dr, c + 2 * dc
            if not (in_bounds(mid_r, mid_c) and in_bounds(land_r, land_c)):
                continue
            if not dark_square(land_r, land_c):
                continue
            mid = (mid_r, mid_c)
            land = (land_r, land_c)
            if mid in my_set and land not in occ_set:
                threat.add(land)
    return threat

# ----------------------------------------------------------------------
# Evaluation helpers
# ----------------------------------------------------------------------
def eval_capture(path, captured, is_king, color):
    # path[0] is start, path[-1] is final landing
    capture_len = len(captured)
    material = sum(piece_value(pos in opp_kings) for pos in captured)  # king detection relies on outer scope
    promotion = (path[-1][0] == promotion_row(color))
    centrality = -abs(path[-1][1] - 3.5)  # more central → higher (less negative)
    # weighted tuple for easy comparison
    return (capture_len, material, promotion, centrality)

def eval_simple_move(move, my_set, opp_set, occ_set, opp_threats, color):
    (fr, fc), (tr, tc), is_king = move
    # advancement
    adv = tr - fr if color == 'w' else fr - tr
    # centrality
    cent = -abs(tc - 3.5)
    # safety
    safe = -1 if (tr, tc) in opp_threats else 0
    # promotion bonus
    promo = 1 if tr == promotion_row(color) else 0
    return (adv, cent, safe, promo)

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert to sets for fast lookup
    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)
    occ_set = my_set | opp_set

    # --------------------------------------------------------------
    # 1) Look for captures (mandatory)
    # --------------------------------------------------------------
    best_capture = None
    best_score = None
    best_start = None
    best_end = None

    for piece in itertools.chain(my_men, my_kings):
        is_king = piece in my_kings
        caps = generate_captures(piece, my_kings, opp_set, occ_set, is_king)
        for path, captured in caps:
            if len(captured) == 0:
                continue  # not a capture
            score = eval_capture(path, captured, is_king, color)
            if (best_score is None) or (score > best_score):
                best_score = score
                best_capture = (path, captured)
                best_start = path[0]
                best_end = path[-1]

    if best_capture is not None:
        return (best_start, best_end)

    # --------------------------------------------------------------
    # 2) No capture – choose a good simple move
    # --------------------------------------------------------------
    simple_moves = generate_simple_moves(my_men, my_kings, occ_set, color)
    if not simple_moves:
        # No legal moves – return a dummy move (should not happen in normal play)
        return ((0, 0), (0, 0))

    # Compute opponent threat squares once
    opp_threats = opponent_threat_squares(opp_men, opp_kings, my_set, occ_set)

    best_move = None
    best_move_score = None
    for mv in simple_moves:
        score = eval_simple_move(mv, my_set, opp_set, occ_set, opp_threats, color)
        if (best_move_score is None) or (score > best_move_score):
            best_move_score = score
            best_move = mv

    return (best_move[0], best_move[1])
