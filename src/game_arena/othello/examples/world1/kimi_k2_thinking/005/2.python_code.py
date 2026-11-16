
import numpy as np
import time

# ----------------------------------------------------------------------
# 1. Board‑feature weights (corners, edges, danger squares)
# ----------------------------------------------------------------------
WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

# ----------------------------------------------------------------------
# 2. Helpers
# ----------------------------------------------------------------------
DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def algebraic(r,c):
    """(r,c) -> 'a4' style string."""
    return chr(ord('a')+c) + str(r+1)

def parse_move(mv):
    """'a4' -> (r,c)."""
    c = ord(mv[0]) - ord('a')
    r = int(mv[1]) - 1
    return r,c

def flips_in_direction(you, opp, r, c, dr, dc):
    """Return a list of opponent discs that would be flipped in direction (dr,dc)."""
    flips = []
    r += dr
    c += dc
    while 0 <= r < 8 and 0 <= c < 8:
        if opp[r,c] == 1:
            flips.append((r,c))
            r += dr
            c += dc
        elif you[r,c] == 1:
            return flips
        else:                     # empty cell
            break
    return []

def is_legal_move(you, opp, r, c):
    """True iff placing a disc at (r,c) for 'you' flips at least one opponent disc."""
    if you[r,c] == 1 or opp[r,c] == 1:
        return False
    for dr, dc in DIRECTIONS:
        if flips_in_direction(you, opp, r, c, dr, dc):
            return True
    return False

def get_legal_moves(you, opp):
    """All legal move strings for the player 'you'."""
    moves = []
    empty = (you == 0) & (opp == 0)
    rs, cs = np.where(empty)
    for r,c in zip(rs, cs):
        if is_legal_move(you, opp, r, c):
            moves.append(algebraic(r,c))
    return moves

def make_move(you, opp, mv):
    """Apply move mv (string) for 'you' and return (new_you,new_opponent)."""
    if mv == "pass":
        return you.copy(), opp.copy()
    r,c = parse_move(mv)
    ny = you.copy()
    no = opp.copy()
    ny[r,c] = 1
    for dr,dc in DIRECTIONS:
        flips = flips_in_direction(you, opp, r, c, dr, dc)
        for rr,cc in flips:
            ny[rr,cc] = 1
            no[rr,cc] = 0
    return ny, no

def evaluate(you, opp):
    """Heuristic score from the perspective of the root player ('you')."""
    wscore = np.sum(you * WEIGHTS) - np.sum(opp * WEIGHTS)
    piece_diff = np.sum(you) - np.sum(opp)
    return wscore + piece_diff * 10

# ----------------------------------------------------------------------
# 3. Minimax with α‑β pruning, pass handling and transposition table
# ----------------------------------------------------------------------
transposition_table = {}

def minimax(state, depth, alpha, beta, player):
    """
    state : (you, opponent) – always from the root player's point of view.
    player : 0 → root player (maximising), 1 → opponent (minimising).
    Returns (score, best_move).
    """
    you, opp = state
    key = (you.tobytes(), opp.tobytes(), player, depth)
    if key in transposition_table:
        return transposition_table[key]

    if depth == 0:
        scr = evaluate(you, opp)
        transposition_table[key] = (scr, None)
        return scr, None

    # generate moves for the player whose turn it is
    if player == 0:
        moves = get_legal_moves(you, opp)
        opp_moves = get_legal_moves(opp, you)
    else:
        moves = get_legal_moves(opp, you)   # view opponent as the moving player
        opp_moves = get_legal_moves(you, opp)

    # no legal moves -> pass or game over
    if not moves:
        if not opp_moves:                # both pass -> game ends
            scr = np.sum(you) - np.sum(opp)
            transposition_table[key] = (scr, None)
            return scr, None
        # turn passes, same depth
        scr, _ = minimax(state, depth, alpha, beta, 1 - player)
        transposition_table[key] = (scr, None)
        return scr, None

    best_move = None
    if player == 0:                     # maximising
        best_score = -np.inf
        for mv in moves:
            if mv == "pass":
                nstate = state
            else:
                ny, no = make_move(you, opp, mv)
                nstate = (ny, no)
            scr, _ = minimax(nstate, depth - 1, alpha, beta, 1)
            if scr > best_score:
                best_score = scr
                best_move = mv
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        transposition_table[key] = (best_score, best_move)
        return best_score, best_move
    else:                               # minimising
        best_score = np.inf
        for mv in moves:
            if mv == "pass":
                nstate = state
            else:
                # apply move from opponent's perspective (swap roles)
                no, ny = make_move(opp, you, mv)
                nstate = (ny, no)
            scr, _ = minimax(nstate, depth - 1, alpha, beta, 0)
            if scr < best_score:
                best_score = scr
                best_move = mv
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        transposition_table[key] = (best_score, best_move)
        return best_score, best_move

# ----------------------------------------------------------------------
# 4. Policy API
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move for the current player.
    """
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    if len(moves) == 1:
        return moves[0]

    empties = 64 - np.sum(you | opponent)
    if empties > 50:
        max_depth = 4
    elif empties > 30:
        max_depth = 6
    else:
        max_depth = 8

    best_move = moves[0]                     # safe fallback
    start = time.time()
    global transposition_table
    transposition_table = {}                 # fresh cache per call

    for depth in range(1, max_depth + 1):
        _, move = minimax((you, opponent), depth, -np.inf, np.inf, 0)
        if move is not None:
            best_move = move
        if time.time() - start > 0.9:        # keep a safety margin
            break
    return best_move
