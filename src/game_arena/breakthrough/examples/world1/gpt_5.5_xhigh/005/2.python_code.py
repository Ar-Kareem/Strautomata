
import time

BOARD = 8
SQ_N = 64

INF = 10**9
WIN = 10**7
TIME_LIMIT = 0.88

EXACT, LOWER, UPPER = 0, 1, 2

BIT = [1 << i for i in range(SQ_N)]
ROW = [i >> 3 for i in range(SQ_N)]
COL = [i & 7 for i in range(SQ_N)]

ROW_MASK = []
for r in range(BOARD):
    m = 0
    for c in range(BOARD):
        m |= BIT[(r << 3) | c]
    ROW_MASK.append(m)

DIRECTIONS = (1, -1)  # didx 0: white/up to larger rows, didx 1: black/down to smaller rows

FWD = [[-1] * SQ_N for _ in range(2)]
DIAGS = [[() for _ in range(SQ_N)] for _ in range(2)]
DEF_MASK = [[0] * SQ_N for _ in range(2)]
ENEMY_ATTACK_MASK = [[0] * SQ_N for _ in range(2)]
FRONT_MASK = [[0] * SQ_N for _ in range(2)]
DIRECT_MASK = [[0] * SQ_N for _ in range(2)]
PROGRESS = [[0] * SQ_N for _ in range(2)]

GOAL_ROW = [7, 0]
GOAL_MASK = [ROW_MASK[7], ROW_MASK[0]]
PRE_GOAL_ROW = [6, 1]

SIDE_MASK = [0] * SQ_N
for sq in range(SQ_N):
    r, c = ROW[sq], COL[sq]
    sm = 0
    if c > 0:
        sm |= BIT[sq - 1]
    if c < 7:
        sm |= BIT[sq + 1]
    SIDE_MASK[sq] = sm

for didx, d in enumerate(DIRECTIONS):
    for sq in range(SQ_N):
        r, c = ROW[sq], COL[sq]
        nr = r + d

        if 0 <= nr < BOARD:
            FWD[didx][sq] = (nr << 3) | c
            ds = []
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < BOARD:
                    ds.append((nr << 3) | nc)
            DIAGS[didx][sq] = tuple(ds)

        PROGRESS[didx][sq] = r if d == 1 else 7 - r

        br = r - d
        dm = 0
        if 0 <= br < BOARD:
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < BOARD:
                    dm |= BIT[(br << 3) | nc]
        DEF_MASK[didx][sq] = dm

        ar = r + d
        am = 0
        if 0 <= ar < BOARD:
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < BOARD:
                    am |= BIT[(ar << 3) | nc]
        ENEMY_ATTACK_MASK[didx][sq] = am

        fm = 0
        direct = 0
        rr = r + d
        while 0 <= rr < BOARD:
            direct |= BIT[(rr << 3) | c]
            for cc in range(max(0, c - 1), min(7, c + 1) + 1):
                fm |= BIT[(rr << 3) | cc]
            rr += d
        FRONT_MASK[didx][sq] = fm
        DIRECT_MASK[didx][sq] = direct

PIECE_VALUE = 100
CENTER_BONUS = (3, 5, 8, 11, 11, 8, 5, 3)
ADV_BONUS = (0, 8, 20, 42, 78, 140, 265, 0)
PASS_BONUS = (0, 12, 30, 65, 135, 285, 650, 0)
SEMI_PASS_BONUS = (0, 4, 10, 23, 48, 95, 180, 0)
OPEN_FILE_BONUS = (0, 2, 6, 13, 25, 48, 95, 0)
FASTEST_BONUS = (0, 320, 165, 80, 35, 12, 0, 0, 0)
PASSER_FAST_BONUS = (0, 900, 470, 230, 105, 40, 12, 0, 0)
IMMEDIATE_THREAT_BONUS = 5200
MOBILITY_BONUS = 2

TT = {}
HISTORY = [0] * 4096
KILLERS = [[0, 0] for _ in range(128)]
DEADLINE = 0.0
NODES = 0


class TimeoutSearch(Exception):
    pass


def _didx(d):
    return 0 if d > 0 else 1


def _bits_from_list(pieces):
    b = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            b |= BIT[(r << 3) | c]
    return b


def _decode_move(m):
    fr = m >> 6
    to = m & 63
    return ((ROW[fr], COL[fr]), (ROW[to], COL[to]))


def _gen_moves(p, e, d):
    didx = 0 if d > 0 else 1
    occ = p | e
    moves = []
    bits = BIT
    fwd = FWD[didx]
    diags = DIAGS[didx]

    x = p
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb

        f = fwd[fr]
        if f >= 0 and not (occ & bits[f]):
            moves.append((fr << 6) | f)

        for t in diags[fr]:
            if not (p & bits[t]):
                moves.append((fr << 6) | t)

    return moves


def _make_move(p, e, m):
    fr = m >> 6
    to = m & 63
    fb = BIT[fr]
    tb = BIT[to]
    return (p & ~fb) | tb, e & ~tb


def _move_wins(m, e, didx):
    tb = BIT[m & 63]
    return bool(tb & GOAL_MASK[didx]) or (e & ~tb) == 0


def _piece_has_goal_move_didx(sq, p, e, didx):
    occ = p | e

    f = FWD[didx][sq]
    if f >= 0 and not (occ & BIT[f]):
        return True

    for t in DIAGS[didx][sq]:
        if not (p & BIT[t]):
            return True

    return False


def _has_winning_move(p, e, d):
    didx = 0 if d > 0 else 1
    x = p & ROW_MASK[PRE_GOAL_ROW[didx]]
    if not x:
        return False

    occ = p | e
    bits = BIT
    fwd = FWD[didx]
    diags = DIAGS[didx]

    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb

        f = fwd[sq]
        if f >= 0 and not (occ & bits[f]):
            return True

        for t in diags[sq]:
            if not (p & bits[t]):
                return True

    return False


def _side_value(p, e, didx, occ):
    val = p.bit_count() * PIECE_VALUE

    progress = PROGRESS[didx]
    fwd = FWD[didx]
    diags = DIAGS[didx]
    def_masks = DEF_MASK[didx]
    enemy_attack_masks = ENEMY_ATTACK_MASK[didx]
    front_masks = FRONT_MASK[didx]
    direct_masks = DIRECT_MASK[didx]

    min_dist = 8
    passer_dist = 8
    mobility = 0

    x = p
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb

        prog = progress[sq]
        dist = 7 - prog
        if dist < min_dist:
            min_dist = dist

        val += ADV_BONUS[prog]
        val += CENTER_BONUS[COL[sq]]

        if not (e & front_masks[sq]):
            val += PASS_BONUS[prog]
            if dist < passer_dist:
                passer_dist = dist
        elif not (e & direct_masks[sq]):
            val += SEMI_PASS_BONUS[prog]

        if not (occ & direct_masks[sq]):
            val += OPEN_FILE_BONUS[prog]

        defenders = (p & def_masks[sq]).bit_count()
        attackers = (e & enemy_attack_masks[sq]).bit_count()

        if defenders:
            val += 8 + 9 * defenders
            if prog >= 4:
                val += 5 * defenders
        else:
            val -= 2 + (2 * prog if prog >= 4 else 0)

        if attackers:
            val -= (16 + 5 * prog) * attackers
            if defenders:
                val += 13 * min(defenders, attackers)
            else:
                val -= 14 + 4 * prog

        if p & SIDE_MASK[sq]:
            val += 4

        f = fwd[sq]
        if f >= 0 and not (occ & BIT[f]):
            mobility += 1
        for t in diags[sq]:
            if not (p & BIT[t]):
                mobility += 1

        if prog == 6:
            if _piece_has_goal_move_didx(sq, p, e, didx):
                val += IMMEDIATE_THREAT_BONUS
        elif prog == 5:
            val += 70

    val += MOBILITY_BONUS * mobility

    if min_dist < 8:
        val += FASTEST_BONUS[min_dist]
    if passer_dist < 8:
        val += PASSER_FAST_BONUS[passer_dist]

    return val


def _evaluate(p, e, d):
    didx = 0 if d > 0 else 1
    odidx = 1 - didx

    if e == 0 or (p & GOAL_MASK[didx]):
        return WIN
    if p == 0 or (e & GOAL_MASK[odidx]):
        return -WIN

    occ = p | e
    return _side_value(p, e, didx, occ) - _side_value(e, p, odidx, occ)


def _move_order_score(m, p, e, didx, tt_move, ply):
    if m == tt_move:
        return 1_000_000_000

    fr = m >> 6
    to = m & 63
    fb = BIT[fr]
    tb = BIT[to]
    ne = e & ~tb
    prog_to = PROGRESS[didx][to]

    score = HISTORY[m]

    if ply < len(KILLERS):
        if KILLERS[ply][0] == m:
            score += 900_000
        elif KILLERS[ply][1] == m:
            score += 800_000

    if tb & GOAL_MASK[didx]:
        score += 100_000_000

    if tb & e:
        score += 50_000 + 1_000 * PROGRESS[1 - didx][to]

    if prog_to == 6:
        score += 30_000
    elif prog_to == 5:
        score += 8_000
    else:
        score += 600 * prog_to

    score += 100 * CENTER_BONUS[COL[to]]

    newp = (p & ~fb) | tb
    defs = newp & DEF_MASK[didx][to]
    atks = ne & ENEMY_ATTACK_MASK[didx][to]

    if defs:
        score += 1_200 + 200 * defs.bit_count()

    if atks:
        if defs:
            score -= 700
        else:
            score -= 2_500 + 300 * prog_to

    if prog_to == 6 and _piece_has_goal_move_didx(to, newp, ne, didx):
        score += 40_000

    if not (ne & FRONT_MASK[didx][to]):
        score += 2_000 + 300 * prog_to

    return score


def _order_moves(moves, p, e, didx, tt_move, ply):
    moves.sort(key=lambda mv: _move_order_score(mv, p, e, didx, tt_move, ply), reverse=True)


def _record_cutoff(m, depth, ply, is_capture):
    if is_capture:
        return

    h = HISTORY[m] + depth * depth
    HISTORY[m] = h if h < 1_000_000 else 1_000_000

    if ply < len(KILLERS):
        if KILLERS[ply][0] != m:
            KILLERS[ply][1] = KILLERS[ply][0]
            KILLERS[ply][0] = m


def _check_time():
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutSearch()


def _threat_evasion_value(p, e, d, alpha, beta, ply):
    didx = 0 if d > 0 else 1
    moves = _gen_moves(p, e, d)
    if not moves:
        return -WIN + ply

    _order_moves(moves, p, e, didx, 0, ply)

    best = -INF
    for m in moves:
        np, ne = _make_move(p, e, m)

        if _move_wins(m, e, didx):
            score = WIN - ply - 1
        elif _has_winning_move(ne, np, -d):
            score = -WIN + ply + 2
        else:
            score = _evaluate(np, ne, d)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _negamax(p, e, d, depth, alpha, beta, ply):
    _check_time()

    didx = 0 if d > 0 else 1
    odidx = 1 - didx

    if p == 0:
        return -WIN + ply
    if e == 0:
        return WIN - ply
    if p & GOAL_MASK[didx]:
        return WIN - ply
    if e & GOAL_MASK[odidx]:
        return -WIN + ply

    if _has_winning_move(p, e, d):
        return WIN - ply - 1

    if depth <= 0:
        if _has_winning_move(e, p, -d):
            return _threat_evasion_value(p, e, d, alpha, beta, ply)
        return _evaluate(p, e, d)

    alpha_orig = alpha
    beta_orig = beta

    key = (p, e, didx)
    tt_move = 0
    ent = TT.get(key)
    if ent is not None:
        ent_depth, ent_val, ent_flag, ent_best = ent
        tt_move = ent_best
        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_val
            if ent_flag == LOWER:
                if ent_val > alpha:
                    alpha = ent_val
            elif ent_flag == UPPER:
                if ent_val < beta:
                    beta = ent_val
            if alpha >= beta:
                return ent_val

    moves = _gen_moves(p, e, d)
    if not moves:
        return -WIN + ply

    _order_moves(moves, p, e, didx, tt_move, ply)

    best = -INF
    best_move = moves[0]
    first = True
    child_depth = depth - 1
    reduced_skipped = False
    cutoff = False

    for i, m in enumerate(moves):
        fr = m >> 6
        to = m & 63
        tb = BIT[to]
        fb = BIT[fr]

        np = (p & ~fb) | tb
        ne = e & ~tb

        if (tb & GOAL_MASK[didx]) or ne == 0:
            score = WIN - ply - 1
        else:
            if first:
                score = -_negamax(ne, np, -d, child_depth, -beta, -alpha, ply + 1)
            else:
                reduction = 0
                if depth >= 3 and i >= 5 and not (tb & e) and PROGRESS[didx][to] < 5:
                    reduction = 1

                rd = child_depth - reduction
                score = -_negamax(ne, np, -d, rd, -alpha - 1, -alpha, ply + 1)

                if reduction and score <= alpha:
                    reduced_skipped = True
                else:
                    if reduction and score > alpha:
                        score = -_negamax(ne, np, -d, child_depth, -alpha - 1, -alpha, ply + 1)

                    if score > alpha and score < beta:
                        score = -_negamax(ne, np, -d, child_depth, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            cutoff = True
            _record_cutoff(m, depth, ply, bool(tb & e))
            break

        first = False

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    if cutoff or not reduced_skipped:
        TT[key] = (depth, best, flag, best_move)

    return best


def _root_search(p, e, d, depth, prev_best):
    didx = 0 if d > 0 else 1
    moves = _gen_moves(p, e, d)
    if not moves:
        return -WIN, None

    tt_move = prev_best
    ent = TT.get((p, e, didx))
    if ent is not None and ent[3]:
        tt_move = ent[3]

    _order_moves(moves, p, e, didx, tt_move, 0)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = moves[0]
    first = True

    for m in moves:
        if time.perf_counter() > DEADLINE:
            raise TimeoutSearch()

        np, ne = _make_move(p, e, m)

        if _move_wins(m, e, didx):
            score = WIN - 1
        else:
            if first:
                score = -_negamax(ne, np, -d, depth - 1, -beta, -alpha, 1)
            else:
                score = -_negamax(ne, np, -d, depth - 1, -alpha - 1, -alpha, 1)
                if score > alpha and score < beta:
                    score = -_negamax(ne, np, -d, depth - 1, -beta, -alpha, 1)

        if score > best:
            best = score
            best_move = m

        if score > alpha:
            alpha = score

        first = False

    TT[(p, e, didx)] = (depth, best, EXACT, best_move)
    return best, best_move


def _choose_fallback(p, e, d, moves):
    didx = 0 if d > 0 else 1

    safe = []
    for m in moves:
        np, ne = _make_move(p, e, m)
        if _move_wins(m, e, didx):
            return m
        if not _has_winning_move(ne, np, -d):
            safe.append(m)

    candidates = safe if safe else moves
    best_move = candidates[0]
    best_val = -INF

    for m in candidates:
        np, ne = _make_move(p, e, m)
        val = _evaluate(np, ne, d)
        val += _move_order_score(m, p, e, didx, 0, 0) // 50

        if val > best_val:
            best_val = val
            best_move = m

    return best_move


def _safe_legal_from_lists(me, opp, color):
    d = 1 if color == "w" else -1
    goal = 7 if d == 1 else 0

    me_set = set(me)
    opp_set = set(opp)
    occ = me_set | opp_set

    wins = []
    captures = []
    quiet = []

    for r, c in me:
        nr = r + d
        if not (0 <= nr < 8):
            continue

        to = (nr, c)
        if to not in occ:
            mv = ((r, c), to)
            if nr == goal:
                wins.append(mv)
            else:
                quiet.append(mv)

        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < 8:
                to = (nr, nc)
                if to not in me_set:
                    mv = ((r, c), to)
                    if nr == goal:
                        wins.append(mv)
                    elif to in opp_set:
                        captures.append(mv)
                    else:
                        quiet.append(mv)

    if wins:
        return wins[0]
    if captures:
        return captures[0]
    if quiet:
        quiet.sort(
            key=lambda mv: (
                mv[1][0] if d == 1 else 7 - mv[1][0],
                -abs(3.5 - mv[1][1]),
            ),
            reverse=True,
        )
        return quiet[0]

    if me:
        return (me[0], me[0])
    return ((0, 0), (0, 0))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global TT, HISTORY, KILLERS, DEADLINE, NODES

    try:
        start = time.perf_counter()
        DEADLINE = start + TIME_LIMIT

        d = 1 if color == "w" else -1
        p = _bits_from_list(me)
        e = _bits_from_list(opp)

        moves = _gen_moves(p, e, d)
        if not moves:
            return _safe_legal_from_lists(me, opp, color)

        if len(moves) == 1:
            return _decode_move(moves[0])

        didx = 0 if d > 0 else 1

        for m in moves:
            if _move_wins(m, e, didx):
                return _decode_move(m)

        TT = {}
        HISTORY = [0] * 4096
        KILLERS = [[0, 0] for _ in range(128)]
        NODES = 0

        fallback = _choose_fallback(p, e, d, moves)
        best_move = fallback
        prev_best = fallback
        best_score = -INF

        total_pieces = (p | e).bit_count()
        if total_pieces <= 6:
            max_depth = 40
        elif total_pieces <= 12:
            max_depth = 28
        elif total_pieces <= 20:
            max_depth = 18
        else:
            max_depth = 12

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > DEADLINE - 0.015:
                break

            try:
                score, mv = _root_search(p, e, d, depth, prev_best)
                if mv is not None:
                    best_move = mv
                    prev_best = mv
                    best_score = score

                if best_score >= WIN - 1000:
                    break

            except TimeoutSearch:
                break

        if best_move not in moves:
            best_move = fallback if fallback in moves else moves[0]

        return _decode_move(best_move)

    except Exception:
        return _safe_legal_from_lists(me, opp, color)
