
import numpy as np
import time

DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
COLS = "abcdefgh"

# Positional weights: good stable edges/corners, bad X-squares near empty corners.
W_EARLY = np.array([
    [120, -25,  20,   5,   5,  20, -25, 120],
    [-25, -55, -10, -10, -10, -10, -55, -25],
    [ 20, -10,  12,   2,   2,  12, -10,  20],
    [  5, -10,   2,   0,   0,   2, -10,   5],
    [  5, -10,   2,   0,   0,   2, -10,   5],
    [ 20, -10,  12,   2,   2,  12, -10,  20],
    [-25, -55, -10, -10, -10, -10, -55, -25],
    [120, -25,  20,   5,   5,  20, -25, 120],
], dtype=np.int16)

W_LATE = np.array([
    [160, -20,  30,  10,  10,  30, -20, 160],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 30,  -5,  15,   5,   5,  15,  -5,  30],
    [ 10,  -5,   5,   2,   2,   5,  -5,  10],
    [ 10,  -5,   5,   2,   2,   5,  -5,  10],
    [ 30,  -5,  15,   5,   5,  15,  -5,  30],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [160, -20,  30,  10,  10,  30, -20, 160],
], dtype=np.int16)

CORNERS = ((0,0),(0,7),(7,0),(7,7))
X_SQUARES = ((1,1),(1,6),(6,1),(6,6))
C_SQUARES = ((0,1),(1,0),(0,6),(1,7),(6,0),(7,1),(6,7),(7,6))
CORNER_ADJ = {
    (0,0): ((0,1),(1,0),(1,1)),
    (0,7): ((0,6),(1,7),(1,6)),
    (7,0): ((6,0),(7,1),(6,1)),
    (7,7): ((6,7),(7,6),(6,6)),
}

START_TIME = 0.0
TIME_LIMIT = 0.88
NODE_LIMIT_TIME_CHECK = 1024
NODES = 0
TT = {}

def inb(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def board_key(me, opp, player_flag=0):
    # bytes key is quick and exact enough for an 8x8 board.
    return (me.tobytes(), opp.tobytes(), player_flag)

def legal_moves(me, opp):
    occupied = me | opp
    moves = []
    for r in range(8):
        for c in range(8):
            if occupied[r, c]:
                continue
            ok = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if not inb(rr, cc) or not opp[rr, cc]:
                    continue
                rr += dr
                cc += dc
                while inb(rr, cc) and opp[rr, cc]:
                    rr += dr
                    cc += dc
                if inb(rr, cc) and me[rr, cc]:
                    ok = True
                    break
            if ok:
                moves.append((r, c))
    return moves

def flips_for_move(me, opp, move):
    r, c = move
    flips = []
    for dr, dc in DIRS:
        line = []
        rr, cc = r + dr, c + dc
        while inb(rr, cc) and opp[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and inb(rr, cc) and me[rr, cc]:
            flips.extend(line)
    return flips

def make_move(me, opp, move):
    nm = me.copy()
    no = opp.copy()
    r, c = move
    nm[r, c] = 1
    fs = flips_for_move(me, opp, move)
    for rr, cc in fs:
        nm[rr, cc] = 1
        no[rr, cc] = 0
    return nm, no, len(fs)

def frontier_count(me, opp):
    empty = ~(me | opp)
    cnt = 0
    for r in range(8):
        for c in range(8):
            if not me[r, c]:
                continue
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inb(rr, cc) and empty[rr, cc]:
                    cnt += 1
                    break
    return cnt

def stable_edge_count(me):
    # Conservative stable proxy: continuous discs from occupied corners along edges.
    s = 0
    if me[0,0]:
        for c in range(8):
            if me[0,c]: s += 1
            else: break
        for r in range(1,8):
            if me[r,0]: s += 1
            else: break
    if me[0,7]:
        for c in range(7,-1,-1):
            if me[0,c]: s += 1
            else: break
        for r in range(1,8):
            if me[r,7]: s += 1
            else: break
    if me[7,0]:
        for c in range(8):
            if me[7,c]: s += 1
            else: break
        for r in range(6,-1,-1):
            if me[r,0]: s += 1
            else: break
    if me[7,7]:
        for c in range(7,-1,-1):
            if me[7,c]: s += 1
            else: break
        for r in range(6,-1,-1):
            if me[r,7]: s += 1
            else: break
    return s

def terminal_score(me, opp):
    return int(np.sum(me) - np.sum(opp)) * 100000

def evaluate(me, opp):
    empties = 64 - int(np.sum(me) + np.sum(opp))
    my_discs = int(np.sum(me))
    op_discs = int(np.sum(opp))

    # If effectively terminal.
    my_moves = legal_moves(me, opp)
    op_moves = legal_moves(opp, me)
    if not my_moves and not op_moves:
        return terminal_score(me, opp)

    phase = (64 - empties) / 64.0
    W = W_EARLY if empties > 18 else W_LATE

    pos = int(np.sum(W * me) - np.sum(W * opp))

    my_mob = len(my_moves)
    op_mob = len(op_moves)
    mobility = 0 if my_mob + op_mob == 0 else 100 * (my_mob - op_mob) / (my_mob + op_mob)

    my_corner = sum(1 for r,c in CORNERS if me[r,c])
    op_corner = sum(1 for r,c in CORNERS if opp[r,c])
    corner_score = 250 * (my_corner - op_corner)

    # Penalize occupying squares adjacent to empty corners; much less bad if corner is ours.
    danger = 0
    for corner, adjs in CORNER_ADJ.items():
        cr, cc = corner
        if not me[cr, cc] and not opp[cr, cc]:
            for ar, ac in adjs:
                if me[ar, ac]:
                    danger -= 45
                elif opp[ar, ac]:
                    danger += 45
        elif me[cr, cc]:
            for ar, ac in adjs:
                if me[ar, ac]:
                    danger += 8
        elif opp[cr, cc]:
            for ar, ac in adjs:
                if opp[ar, ac]:
                    danger -= 8

    my_front = frontier_count(me, opp)
    op_front = frontier_count(opp, me)
    frontier = 0 if my_front + op_front == 0 else -70 * (my_front - op_front) / (my_front + op_front)

    stable = 35 * (stable_edge_count(me) - stable_edge_count(opp))

    parity = 0
    if empties <= 18:
        parity = 35 * (my_discs - op_discs)
        if empties <= 10:
            parity = 120 * (my_discs - op_discs)

    # Mobility dominates early/midgame; disc count matters late.
    if empties > 44:
        return int(pos + 4.0 * mobility + corner_score + danger + 1.5 * frontier + stable)
    elif empties > 18:
        return int(pos + 7.0 * mobility + corner_score + danger + 2.0 * frontier + stable)
    else:
        return int(pos + 4.0 * mobility + corner_score + danger + frontier + stable + parity)

def quick_move_score(me, opp, move):
    r, c = move
    nm, no, nflips = make_move(me, opp, move)
    s = 0
    if (r, c) in CORNERS:
        s += 100000
    # Avoid dangerous adjacent corner moves if the corresponding corner is empty.
    for corner, adjs in CORNER_ADJ.items():
        cr, cc = corner
        if (r, c) in adjs and not me[cr, cc] and not opp[cr, cc]:
            s -= 8000
    s += int(W_EARLY[r, c]) * 30
    s += 100 * len(legal_moves(nm, no)) - 140 * len(legal_moves(no, nm))
    s -= 5 * nflips  # Usually prefer fewer early flips.
    return s

def ordered_moves(me, opp, moves=None):
    if moves is None:
        moves = legal_moves(me, opp)
    return sorted(moves, key=lambda mv: quick_move_score(me, opp, mv), reverse=True)

def time_up():
    return (time.perf_counter() - START_TIME) > TIME_LIMIT

def negamax(me, opp, depth, alpha, beta, passed=False):
    global NODES, TT
    NODES += 1
    if (NODES & (NODE_LIMIT_TIME_CHECK - 1)) == 0 and time_up():
        raise TimeoutError

    empties = 64 - int(np.sum(me) + np.sum(opp))
    key = None
    if depth >= 3:
        key = (me.tobytes(), opp.tobytes(), depth, passed)
        item = TT.get(key)
        if item is not None:
            tt_depth, tt_val, tt_flag = item
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_val
                elif tt_flag == 1:
                    alpha = max(alpha, tt_val)
                else:
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

    moves = legal_moves(me, opp)
    if not moves:
        op_moves = legal_moves(opp, me)
        if not op_moves:
            return terminal_score(me, opp)
        if passed:
            return terminal_score(me, opp)
        return -negamax(opp, me, depth, -beta, -alpha, True)

    if depth <= 0:
        return evaluate(me, opp)

    old_alpha = alpha
    best = -10**12
    for mv in ordered_moves(me, opp, moves):
        nm, no, _ = make_move(me, opp, mv)
        val = -negamax(no, nm, depth - 1, -beta, -alpha, False)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if key is not None:
        flag = 0
        if best <= old_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        TT[key] = (depth, best, flag)

    return best

def exact_endgame(me, opp, alpha, beta, passed=False):
    global NODES
    NODES += 1
    if (NODES & (NODE_LIMIT_TIME_CHECK - 1)) == 0 and time_up():
        raise TimeoutError

    moves = legal_moves(me, opp)
    if not moves:
        if not legal_moves(opp, me):
            return terminal_score(me, opp)
        return -exact_endgame(opp, me, -beta, -alpha, True)

    best = -10**12
    for mv in ordered_moves(me, opp, moves):
        nm, no, _ = make_move(me, opp, mv)
        val = -exact_endgame(no, nm, -beta, -alpha, False)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def move_to_str(mv):
    return COLS[mv[1]] + str(mv[0] + 1)

def choose_fallback(me, opp, moves):
    # Absolute safety fallback: corners first, then avoid empty-corner adjacency, then positional/mobility.
    best = None
    bests = -10**18
    for mv in moves:
        s = quick_move_score(me, opp, mv)
        nm, no, _ = make_move(me, opp, mv)
        # Prefer moves that don't give immediate corner access.
        opp_moves = legal_moves(no, nm)
        for om in opp_moves:
            if om in CORNERS:
                s -= 20000
        if s > bests:
            bests = s
            best = mv
    return best if best is not None else moves[0]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global START_TIME, NODES, TT
    START_TIME = time.perf_counter()
    NODES = 0
    TT = {}

    me = (you.astype(np.uint8) > 0)
    opp = (opponent.astype(np.uint8) > 0)

    moves = legal_moves(me, opp)
    if not moves:
        return "pass"

    fallback = choose_fallback(me, opp, moves)
    best_move = fallback

    empties = 64 - int(np.sum(me) + np.sum(opp))

    # Immediate corner is almost always best and saves time.
    corner_moves = [mv for mv in moves if mv in CORNERS]
    if corner_moves:
        return move_to_str(corner_moves[0])

    # Search depth by phase and branching. Iterative deepening ensures legal return.
    ordered = ordered_moves(me, opp, moves)
    depth_limit = 4
    if empties <= 12:
        depth_limit = empties
    elif empties <= 18:
        depth_limit = 8
    elif empties <= 26:
        depth_limit = 6
    elif len(moves) <= 5:
        depth_limit = 7
    else:
        depth_limit = 5

    try:
        if empties <= 12:
            best_val = -10**18
            alpha = -10**18
            beta = 10**18
            for mv in ordered:
                nm, no, _ = make_move(me, opp, mv)
                val = -exact_endgame(no, nm, -beta, -alpha, False)
                if val > best_val:
                    best_val = val
                    best_move = mv
                if val > alpha:
                    alpha = val
        else:
            # Iterative deepening; keep last completed best move.
            for depth in range(1, depth_limit + 1):
                if time_up():
                    break
                local_best = best_move
                local_val = -10**18
                alpha = -10**12
                beta = 10**12

                # Principal variation move first.
                this_order = ordered[:]
                if best_move in this_order:
                    this_order.remove(best_move)
                    this_order.insert(0, best_move)

                for mv in this_order:
                    nm, no, _ = make_move(me, opp, mv)
                    val = -negamax(no, nm, depth - 1, -beta, -alpha, False)
                    if val > local_val:
                        local_val = val
                        local_best = mv
                    if val > alpha:
                        alpha = val
                best_move = local_best
    except TimeoutError:
        pass
    except Exception:
        # Never risk illegal/no response because of an unexpected issue.
        best_move = fallback

    if best_move not in moves:
        best_move = fallback

    return move_to_str(best_move)
