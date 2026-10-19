
import numpy as np
import time

# ----------------------------------------------------------------------
# 1. Constants
# ----------------------------------------------------------------------
# 8 directions: N, NE, E, SE, S, SW, W, NW
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

# Static weights for each square (row‑major, a1 = index 0)
WEIGHTS = [
    # rank 1 (row 0)
    100, -10, 10, 5, 5, 10, -10, 100,
    # rank 2
    -10, -20, -1, -1, -1, -1, -20, -10,
    # rank 3
    10, -1, 1, 1, 1, 1, -1, 10,
    # rank 4
    5, -1, 1, 0, 0, 1, -1, 5,
    # rank 5
    5, -1, 1, 0, 0, 1, -1, 5,
    # rank 6
    10, -1, 1, 1, 1, 1, -1, 10,
    # rank 7
    -10, -20, -1, -1, -1, -1, -20, -10,
    # rank 8
    100, -10, 10, 5, 5, 10, -10, 100,
]

# indices of the four corners
CORNER_INDICES = [0, 7, 56, 63]

# ----------------------------------------------------------------------
# 2. Bitboard utilities
# ----------------------------------------------------------------------
def board_to_bitboard(arr):
    """Convert 8×8 numpy array to a 64‑bit bitboard."""
    bb = 0
    for r in range(8):
        row = arr[r]
        for c in range(8):
            if row[c]:
                bb |= 1 << (r * 8 + c)
    return bb

def move_index_to_str(idx):
    """Bit index (0..63) → algebraic notation, e.g. 0 → 'a1'."""
    col = idx % 8
    row = idx // 8
    return chr(ord('a') + col) + str(row + 1)

def is_legal_move(idx, player_bb, opp_bb):
    """Return True iff placing a disc at idx flips at least one opponent disc."""
    r = idx // 8
    c = idx % 8
    mask = 1 << idx
    # already occupied – should never happen because we only call it on empty squares
    if (player_bb & mask) or (opp_bb & mask):
        return False
    for dr, dc in DIRECTIONS:
        nr = r + dr
        nc = c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        nidx = nr * 8 + nc
        if not (opp_bb & (1 << nidx)):
            continue
        # there is at least one opponent disc adjacent – now walk the line
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            nidx = nr * 8 + nc
            if player_bb & (1 << nidx):
                return True          # a player disc ends the line
            elif opp_bb & (1 << nidx):
                continue               # keep scanning opponent discs
            else:
                break                  # empty square – line is invalid
    return False

def generate_moves(player_bb, opp_bb):
    """List of all legal move indices for player."""
    moves = []
    empty = ~(player_bb | opp_bb) & 0xFFFFFFFFFFFFFFFF
    e = empty
    while e:
        lsb = e & -e
        idx = (lsb.bit_length() - 1)
        if is_legal_move(idx, player_bb, opp_bb):
            moves.append(idx)
        e ^= lsb
    return moves

def apply_move(idx, player_bb, opp_bb):
    """Return new (player_bb, opp_bb) after playing idx (which must be legal)."""
    new_player = player_bb | (1 << idx)
    new_opp = opp_bb
    r = idx // 8
    c = idx % 8
    flips = 0
    for dr, dc in DIRECTIONS:
        direction_flips = 0
        nr = r + dr
        nc = c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        nidx = nr * 8 + nc
        if not (opp_bb & (1 << nidx)):
            continue
        # first opponent disc adjacent
        direction_flips = 1 << nidx
        # walk the line
        while True:
            nr += dr
            nc += dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                direction_flips = 0
                break
            nidx = nr * 8 + nc
            if player_bb & (1 << nidx):
                break               # valid line – direction_flips are flipped
            elif opp_bb & (1 << nidx):
                direction_flips |= 1 << nidx
                continue
            else:
                direction_flips = 0
                break
        flips |= direction_flips
    new_player |= flips
    new_opp &= ~flips
    return new_player, new_opp

def evaluate(player_bb, opp_bb):
    """Static evaluation from the point of view of player_bb."""
    # weighted board difference
    score = 0
    p = player_bb
    while p:
        lsb = p & -p
        idx = (lsb.bit_length() - 1)
        score += WEIGHTS[idx]
        p ^= lsb
    o = opp_bb
    while o:
        lsb = o & -o
        idx = (lsb.bit_length() - 1)
        score -= WEIGHTS[idx]
        o ^= lsb
    # extra corner bonus
    for ci in CORNER_INDICES:
        if player_bb & (1 << ci):
            score += 5000
        elif opp_bb & (1 << ci):
            score -= 5000
    return score

# ----------------------------------------------------------------------
# 3. Alpha‑beta (negamax) search
# ----------------------------------------------------------------------
def negamax(player_bb, opp_bb, depth, alpha, beta):
    """Negamax search – returns value for the player to move."""
    if depth == 0:
        return evaluate(player_bb, opp_bb)

    moves = generate_moves(player_bb, opp_bb)
    if not moves:
        # player has no move – check opponent
        opp_moves = generate_moves(opp_bb, player_bb)
        if not opp_moves:
            # terminal position
            pc = player_bb.bit_count()
            oc = opp_bb.bit_count()
            return (pc - oc) * 1000
        # pass – opponent moves again
        return -negamax(opp_bb, player_bb, depth, -beta, -alpha)

    # order moves by number of opponent discs flipped (descending)
    move_list = []
    for mv in moves:
        nxt_pl, nxt_op = apply_move(mv, player_bb, opp_bb)
        flips = nxt_pl ^ (player_bb | (1 << mv))
        capture = flips.bit_count()
        move_list.append((mv, nxt_pl, nxt_op, capture))
    move_list.sort(key=lambda x: x[3], reverse=True)

    best = -float('inf')
    for mv, nxt_pl, nxt_op, _ in move_list:
        val = -negamax(nxt_op, nxt_pl, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best

def search_root(player_bb, opp_bb, depth):
    """Find the best move for the player at the root (returns move index)."""
    moves = generate_moves(player_bb, opp_bb)
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    best_move = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # order by capture count (as in negamax)
    move_list = []
    for mv in moves:
        nxt_pl, nxt_op = apply_move(mv, player_bb, opp_bb)
        flips = nxt_pl ^ (player_bb | (1 << mv))
        capture = flips.bit_count()
        move_list.append((mv, nxt_pl, nxt_op, capture))
    move_list.sort(key=lambda x: x[3], reverse=True)

    for mv, nxt_pl, nxt_op, _ in move_list:
        val = -negamax(nxt_op, nxt_pl, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best_move

def choose_best_by_heuristic(player_bb, opp_bb, moves):
    """Greedy 1‑ply choice using the static evaluation."""
    best = -float('inf')
    best_move = moves[0]
    for mv in moves:
        nxt_pl, nxt_op = apply_move(mv, player_bb, opp_bb)
        val = evaluate(nxt_pl, nxt_op)
        if val > best:
            best = val
            best_move = mv
    return best_move

# ----------------------------------------------------------------------
# 4. Public API
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal move for the player ``you`` in algebraic notation,
    e.g. ``"c5"``, or ``"pass"`` if no move exists.
    """
    player_bb = board_to_bitboard(you)
    opp_bb    = board_to_bitboard(opponent)

    moves = generate_moves(player_bb, opp_bb)
    if not moves:
        return "pass"
    if len(moves) == 1:
        return move_index_to_str(moves[0])

    start = time.time()
    best_move = None
    # iterative deepening until time runs out
    for depth in range(1, 10):
        move = search_root(player_bb, opp_bb, depth)
        if move is not None:
            best_move = move
        if time.time() - start > 0.9:
            break

    if best_move is None:
        # fallback to greedy if search never finished a depth
        best_move = choose_best_by_heuristic(player_bb, opp_bb, moves)

    return move_index_to_str(best_move)
