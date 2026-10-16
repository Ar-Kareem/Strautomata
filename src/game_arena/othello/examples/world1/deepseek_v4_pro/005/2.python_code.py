
import numpy as np
import time

# ------------------------------------------------------------------------------
# Precomputed direction rays for each of the 64 squares
# ------------------------------------------------------------------------------
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

dir_sq = [[[] for _ in range(8)] for _ in range(64)]
for r in range(8):
    for c in range(8):
        sq = r * 8 + c
        for d, (dr, dc) in enumerate(DIRS):
            lst = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                lst.append(nr * 8 + nc)
                nr += dr
                nc += dc
            dir_sq[sq][d] = tuple(lst)

# ------------------------------------------------------------------------------
# Static square weights (standard Othello heuristic)
# ------------------------------------------------------------------------------
WEIGHTS = np.array([
    100, -20, 10,  5,  5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10,  -2, -1, -1, -1, -1,  -2,  10,
     5,  -2, -1,  0,  0, -1,  -2,   5,
     5,  -2, -1,  0,  0, -1,  -2,   5,
    10,  -2, -1, -1, -1, -1,  -2,  10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10,  5,  5, 10, -20, 100
], dtype=np.int32)

# ------------------------------------------------------------------------------
# Bitboard helpers
# ------------------------------------------------------------------------------
def get_moves(own, opp):
    """Return list of legal move squares for the player with bitboard own."""
    empty = ~(own | opp) & 0xFFFFFFFFFFFFFFFF
    moves = []
    e = empty
    while e:
        sq = (e & -e).bit_length() - 1
        e &= e - 1
        for ray in dir_sq[sq]:
            if not ray:
                continue
            first = ray[0]
            if not (opp >> first) & 1:
                continue
            for nxt in ray[1:]:
                cell_state = (own | opp) >> nxt & 1
                if cell_state == 0:      # empty square
                    break
                if (own >> nxt) & 1:     # own disc found → legal
                    moves.append(sq)
                    break
    return moves


def make_move(own, opp, sq):
    """Return (new_own, new_opp) after placing own disc at sq."""
    new_own = own | (1 << sq)
    new_opp = opp
    for ray in dir_sq[sq]:
        if not ray:
            continue
        first = ray[0]
        if not (opp >> first) & 1:
            continue
        flip = []
        for nxt in ray[1:]:
            if ((own | opp) >> nxt) & 1 == 0:
                break
            if (own >> nxt) & 1:
                for f in flip:
                    new_own |= (1 << f)
                    new_opp &= ~(1 << f)
                break
            else:
                flip.append(nxt)
    return new_own, new_opp


def evaluate(own, opp):
    """Heuristic evaluation of the board from own's perspective."""
    my_cnt = own.bit_count()
    op_cnt = opp.bit_count()
    empty = 64 - my_cnt - op_cnt
    piece_diff = my_cnt - op_cnt
    if empty == 0:
        if piece_diff > 0: return 1000
        if piece_diff < 0: return -1000
        return 0

    # Static square value
    my_val = 0
    o = own
    while o:
        sq = (o & -o).bit_length() - 1
        my_val += WEIGHTS[sq]
        o &= o - 1
    op_val = 0
    p = opp
    while p:
        sq = (p & -p).bit_length() - 1
        op_val += WEIGHTS[sq]
        p &= p - 1
    static_diff = my_val - op_val

    # Mobility
    my_moves = len(get_moves(own, opp))
    op_moves = len(get_moves(opp, own))
    mob_diff = my_moves - op_moves

    # Phase‑dependent weights
    if empty > 40:        # opening
        w_static, w_mob = 1, 10
    elif empty > 20:      # midgame
        w_static, w_mob = 2, 5
    else:                 # endgame
        w_static, w_mob = 10, 1

    return static_diff * w_static + mob_diff * w_mob + piece_diff * w_static * 0.5


def evaluate_terminal(own, opp):
    """Terminal evaluation – only disc count matters."""
    diff = own.bit_count() - opp.bit_count()
    if diff > 0: return 1000
    if diff < 0: return -1000
    return 0


# ------------------------------------------------------------------------------
# Alpha‑beta with iterative deepening trigger
# ------------------------------------------------------------------------------
def alpha_beta(own, opp, depth, alpha, beta, maximizing, start_time, time_limit):
    if time.time() - start_time > time_limit:
        return None, None
    if depth == 0:
        return evaluate(own, opp), None

    if maximizing:
        moves = get_moves(own, opp)
        if not moves:
            if not get_moves(opp, own):
                return evaluate_terminal(own, opp), None
            # pass
            return alpha_beta(own, opp, depth - 1, alpha, beta, False,
                              start_time, time_limit)
        best_move = None
        moves.sort(key=lambda sq: WEIGHTS[sq], reverse=True)
        for sq in moves:
            if time.time() - start_time > time_limit:
                return None, None
            new_own, new_opp = make_move(own, opp, sq)
            val, _ = alpha_beta(new_own, new_opp, depth - 1, alpha, beta, False,
                                start_time, time_limit)
            if val is None:
                return None, None
            if val > alpha:
                alpha = val
                best_move = sq
            if alpha >= beta:
                break
        return alpha, best_move
    else:
        moves = get_moves(opp, own)
        if not moves:
            if not get_moves(own, opp):
                return evaluate_terminal(own, opp), None
            return alpha_beta(own, opp, depth - 1, alpha, beta, True,
                              start_time, time_limit)
        best_move = None
        moves.sort(key=lambda sq: WEIGHTS[sq], reverse=True)
        for sq in moves:
            if time.time() - start_time > time_limit:
                return None, None
            new_opp, new_own = make_move(opp, own, sq)
            val, _ = alpha_beta(new_own, new_opp, depth - 1, alpha, beta, True,
                                start_time, time_limit)
            if val is None:
                return None, None
            if val < beta:
                beta = val
                best_move = sq
            if alpha >= beta:
                break
        return beta, best_move


# ------------------------------------------------------------------------------
# Required API
# ------------------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert to bitboards
    own_bb = 0
    opp_bb = 0
    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            if you[r, c]:
                own_bb |= (1 << sq)
            if opponent[r, c]:
                opp_bb |= (1 << sq)

    my_moves = get_moves(own_bb, opp_bb)
    if not my_moves:
        return "pass"

    start = time.time()
    time_limit = 0.9
    best_move = my_moves[0]          # fallback
    depth = 1
    while True:
        if time.time() - start > time_limit:
            break
        val, move = alpha_beta(own_bb, opp_bb, depth,
                               -float('inf'), float('inf'), True,
                               start, time_limit)
        if move is not None:
            best_move = move
        else:
            break       # timeout propagated
        depth += 1
        if depth > 64:
            break

    # Convert square index to algebraic notation (a1 = r0,c0)
    c = best_move % 8
    r = best_move // 8
    return chr(ord('a') + c) + str(r + 1)
