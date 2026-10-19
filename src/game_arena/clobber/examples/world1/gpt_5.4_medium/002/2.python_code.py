
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

INF = 10**9
MATE = 10**6

EXACT = 0
LOWER = 1
UPPER = 2

TIME_BUDGET = 0.94

# Precomputed geometry
ROW_OF = [i // COLS for i in range(N)]
COL_OF = [i % COLS for i in range(N)]

NEIGHBORS = [[] for _ in range(N)]
ADJ_MASK = [0] * N

for i in range(N):
    r = ROW_OF[i]
    c = COL_OF[i]
    if r > 0:
        j = (r - 1) * COLS + c
        NEIGHBORS[i].append((j, 'U'))
        ADJ_MASK[i] |= 1 << j
    if c + 1 < COLS:
        j = r * COLS + (c + 1)
        NEIGHBORS[i].append((j, 'R'))
        ADJ_MASK[i] |= 1 << j
    if r + 1 < ROWS:
        j = (r + 1) * COLS + c
        NEIGHBORS[i].append((j, 'D'))
        ADJ_MASK[i] |= 1 << j
    if c > 0:
        j = r * COLS + (c - 1)
        NEIGHBORS[i].append((j, 'L'))
        ADJ_MASK[i] |= 1 << j

# Mild center preference
ROW_BONUS = [0, 1, 2, 1, 0]
COL_BONUS = [0, 1, 2, 2, 1, 0]
SQUARE_SCORE = [ROW_BONUS[ROW_OF[i]] + COL_BONUS[COL_OF[i]] for i in range(N)]

TT = {}
HISTORY = {}
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def _key(me, opp):
    return me | (opp << 30)


def _check_time(end_time):
    global NODE_COUNTER
    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and time.perf_counter() >= end_time:
        raise SearchTimeout


def _to_bits(board):
    # Accepts nested 5x6 lists/arrays or a flat length-30 structure.
    try:
        if len(board) == N and not hasattr(board[0], "__len__"):
            bits = 0
            for i in range(N):
                if int(board[i]):
                    bits |= 1 << i
            return bits
    except Exception:
        pass

    bits = 0
    idx = 0
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS):
            if int(row[c]):
                bits |= 1 << idx
            idx += 1
    return bits


def _raw_moves(me, opp):
    moves = []
    x = me
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        for j, d in NEIGHBORS[i]:
            if (opp >> j) & 1:
                moves.append((i, j, d))
    return moves


def _legal_count(me, opp):
    cnt = 0
    x = me
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        cnt += (opp & ADJ_MASK[i]).bit_count()
    return cnt


def _square_total(bits):
    total = 0
    x = bits
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        total += SQUARE_SCORE[i]
    return total


def _evaluate(me, opp, my_moves):
    opp_moves = _legal_count(opp, me)
    piece_diff = me.bit_count() - opp.bit_count()
    center_diff = _square_total(me) - _square_total(opp)
    return 48 * (my_moves - opp_moves) + 6 * piece_diff + 2 * center_diff


def _apply_move(me, opp, move):
    i, j, _ = move
    s = 1 << i
    t = 1 << j
    new_me = opp ^ t
    new_opp = (me ^ s) | t
    return new_me, new_opp


def _sort_moves(me, opp, moves, tt_move=None, depth=0, root=False):
    scored = []
    for mv in moves:
        i, j, _ = mv
        bonus = 0
        if tt_move is not None and mv == tt_move:
            bonus += 10**8

        t = 1 << j
        danger = ((opp ^ t) & ADJ_MASK[j]).bit_count()
        hist = HISTORY.get((i, j), 0)

        score = bonus + hist + (SQUARE_SCORE[j] - SQUARE_SCORE[i]) - 6 * danger

        # More detailed ordering near the root / in important nodes
        if root or depth >= 6:
            nme, nopp = _apply_move(me, opp, mv)
            opp_mob = _legal_count(nme, nopp)
            score -= 15 * opp_mob
            if opp_mob == 0:
                score += 200000

        scored.append((score, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def _negamax(me, opp, depth, alpha, beta, ply, end_time):
    _check_time(end_time)

    alpha_orig = alpha
    beta_orig = beta
    key = _key(me, opp)

    tt_move = None
    entry = TT.get(key)
    if entry is not None:
        edepth, eval_score, flag, best_mv = entry
        tt_move = best_mv
        if edepth >= depth:
            if flag == EXACT:
                return eval_score
            elif flag == LOWER:
                if eval_score > alpha:
                    alpha = eval_score
            else:
                if eval_score < beta:
                    beta = eval_score
            if alpha >= beta:
                return eval_score

    moves = _raw_moves(me, opp)
    if not moves:
        return -MATE + ply

    if depth <= 0:
        return _evaluate(me, opp, len(moves))

    moves = _sort_moves(me, opp, moves, tt_move=tt_move, depth=depth, root=False)

    best = -INF
    best_move = moves[0]

    first = True
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)

        if first:
            score = -_negamax(nme, nopp, depth - 1, -beta, -alpha, ply + 1, end_time)
            first = False
        else:
            score = -_negamax(nme, nopp, depth - 1, -alpha - 1, -alpha, ply + 1, end_time)
            if alpha < score < beta:
                score = -_negamax(nme, nopp, depth - 1, -beta, -alpha, ply + 1, end_time)

        if score > best:
            best = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            i, j, _ = mv
            HISTORY[(i, j)] = HISTORY.get((i, j), 0) + depth * depth
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best, flag, best_move)
    return best


def _search_root(me, opp, depth, end_time, fallback_move):
    key = _key(me, opp)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else None

    moves = _raw_moves(me, opp)
    if not moves:
        return -MATE, fallback_move

    moves = _sort_moves(me, opp, moves, tt_move=tt_move, depth=depth, root=True)

    best = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    first = True
    for mv in moves:
        _check_time(end_time)
        nme, nopp = _apply_move(me, opp, mv)

        if first:
            score = -_negamax(nme, nopp, depth - 1, -beta, -alpha, 1, end_time)
            first = False
        else:
            score = -_negamax(nme, nopp, depth - 1, -alpha - 1, -alpha, 1, end_time)
            if alpha < score < beta:
                score = -_negamax(nme, nopp, depth - 1, -beta, -alpha, 1, end_time)

        if score > best:
            best = score
            best_move = mv

        if score > alpha:
            alpha = score

    TT[key] = (depth, best, EXACT, best_move)
    return best, best_move


def _format_move(move):
    i, _, d = move
    return f"{ROW_OF[i]},{COL_OF[i]},{d}"


def policy(you, opponent):
    global NODE_COUNTER

    # Keep tables bounded if many games are played in one process.
    if len(TT) > 800000:
        TT.clear()
    if len(HISTORY) > 50000:
        HISTORY.clear()

    NODE_COUNTER = 0
    end_time = time.perf_counter() + TIME_BUDGET

    me = _to_bits(you)
    opp = _to_bits(opponent)

    legal = _raw_moves(me, opp)
    if not legal:
        # No legal move exists. This should normally not be queried,
        # but return a syntactically valid string anyway.
        return "0,0,U"

    if len(legal) == 1:
        return _format_move(legal[0])

    # Strong heuristic fallback, also checks immediate wins.
    ordered = _sort_moves(me, opp, legal, tt_move=None, depth=8, root=True)
    fallback_move = ordered[0]

    for mv in ordered:
        nme, nopp = _apply_move(me, opp, mv)
        if _legal_count(nme, nopp) == 0:
            return _format_move(mv)

    best_move = fallback_move
    total_pieces = (me | opp).bit_count()
    max_depth = total_pieces  # Full game cannot exceed this many plies.

    try:
        for depth in range(1, max_depth + 1):
            score, mv = _search_root(me, opp, depth, end_time, best_move)
            best_move = mv

            # Proven short win/loss found inside current horizon.
            if abs(score) >= MATE // 2:
                break
    except SearchTimeout:
        pass

    return _format_move(best_move)
