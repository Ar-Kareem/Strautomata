
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]

# Precompute adjacency / move templates
MOVE_TEMPLATES = [[] for _ in range(N)]   # per src: list[(dst, dir_char)]
NEIGHBORS = [[] for _ in range(N)]        # undirected neighbors
IDX_TO_RC = [(i // COLS, i % COLS) for i in range(N)]

for r in range(ROWS):
    for c in range(COLS):
        s = r * COLS + c
        for dch, dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                t = nr * COLS + nc
                MOVE_TEMPLATES[s].append((t, dch))
                NEIGHBORS[s].append(t)

BIT = [1 << i for i in range(N)]

WIN_SCORE = 10**7
TIME_LIMIT = 0.92


def to_bitboard(arr):
    b = 0
    for r in range(ROWS):
        row = arr[r]
        base = r * COLS
        for c in range(COLS):
            if row[c]:
                b |= 1 << (base + c)
    return b


def generate_moves(me, opp):
    moves = []
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        for t, dch in MOVE_TEMPLATES[s]:
            if opp & BIT[t]:
                moves.append((s, t, dch))
        x ^= lsb
    return moves


def count_moves(me, opp):
    cnt = 0
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        for t in NEIGHBORS[s]:
            if opp & BIT[t]:
                cnt += 1
        x ^= lsb
    return cnt


def do_move(me, opp, move):
    s, t, _ = move
    me2 = (me ^ BIT[s]) | BIT[t]
    opp2 = opp ^ BIT[t]
    return opp2, me2  # swapped perspective for negamax


def local_move_score(me, opp, move):
    s, t, _ = move
    score = 0

    # Prefer moves that reduce opponent replies from the landing square area
    opp_adj_to_t = 0
    me_adj_to_t = 0
    for n in NEIGHBORS[t]:
        if opp & BIT[n]:
            opp_adj_to_t += 1
        if me & BIT[n]:
            me_adj_to_t += 1

    # Prefer capturing pieces that were mobile / central
    score += 5 * opp_adj_to_t
    score += 2 * len(NEIGHBORS[t])

    # Prefer not vacating a highly tactical square unless landing is better
    my_adj_to_s = 0
    for n in NEIGHBORS[s]:
        if opp & BIT[n]:
            my_adj_to_s += 1
    score -= 2 * my_adj_to_s

    # Small centrality bonus for destination
    r, c = IDX_TO_RC[t]
    score += 3 - abs(r - 2)
    score += 3 - abs(c - 2.5)

    # If landing square is vulnerable, slight penalty
    score -= me_adj_to_t

    return score


def evaluate(me, opp):
    my_moves = count_moves(me, opp)
    op_moves = count_moves(opp, me)

    my_pieces = me.bit_count()
    op_pieces = opp.bit_count()

    # Favor mobility most, then piece advantage
    score = 100 * (my_moves - op_moves) + 12 * (my_pieces - op_pieces)

    # Tactical contact count
    contact = 0
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        for n in NEIGHBORS[s]:
            if opp & BIT[n]:
                contact += 1
        x ^= lsb
    score += 3 * contact

    return score


def order_moves(me, opp, moves, killer=None):
    if len(moves) <= 1:
        return moves
    scored = []
    for mv in moves:
        sc = local_move_score(me, opp, mv)
        if killer is not None and mv == killer:
            sc += 10000
        scored.append((sc, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def negamax(me, opp, depth, alpha, beta, start, tt, killers):
    if time.time() - start > TIME_LIMIT:
        raise TimeoutError

    key = (me, opp, depth)
    if key in tt:
        return tt[key]

    moves = generate_moves(me, opp)
    if not moves:
        return -WIN_SCORE + (20 - depth)

    if depth == 0:
        val = evaluate(me, opp)
        tt[key] = val
        return val

    killer = killers.get((me, opp))
    moves = order_moves(me, opp, moves, killer)

    best = -10**9
    for mv in moves:
        nme, നോpp = do_move(me, opp, mv)
        val = -negamax(nme, നോpp, depth - 1, -beta, -alpha, start, tt, killers)
        if val > best:
            best = val
            killers[(me, opp)] = mv
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def move_to_string(move):
    s, _, dch = move
    r, c = IDX_TO_RC[s]
    return f"{r},{c},{dch}"


def policy(you, opponent):
    me = to_bitboard(you)
    opp = to_bitboard(opponent)

    legal = generate_moves(me, opp)
    if not legal:
        # Should not happen in valid arena states, but return syntactically valid string.
        return "0,0,U"

    # Immediate fallback to ensure legality no matter what
    fallback = legal[0]

    # Quick tactical checks
    ordered_root = order_moves(me, opp, legal)

    # If any move leaves opponent with no moves, play it immediately
    for mv in ordered_root:
        nme, നോpp = do_move(me, opp, mv)
        if not generate_moves(nme, നോpp):
            return move_to_string(mv)

    start = time.time()
    tt = {}
    killers = {}

    best_move = ordered_root[0]
    best_val = -10**9

    depth = 1
    try:
        while True:
            if time.time() - start > TIME_LIMIT:
                break

            current_best_move = best_move
            current_best_val = -10**9

            root_moves = order_moves(me, opp, legal, best_move)

            alpha = -10**9
            beta = 10**9

            for mv in root_moves:
                if time.time() - start > TIME_LIMIT:
                    raise TimeoutError
                nme, നോpp = do_move(me, opp, mv)
                val = -negamax(nme, നോpp, depth - 1, -beta, -alpha, start, tt, killers)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = mv
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            best_val = current_best_val

            # Proven win/loss region, no need to search deeper aggressively
            if abs(best_val) >= WIN_SCORE - 1000:
                break

            depth += 1

    except TimeoutError:
        pass
    except Exception:
        return move_to_string(fallback)

    return move_to_string(best_move)
