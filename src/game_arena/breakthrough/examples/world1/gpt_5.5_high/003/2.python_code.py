
import time

# Breakthrough 8x8 policy.
# color id: 0 = black, moves toward row 0. 1 = white, moves toward row 7.

WIN = 1_000_000
INF = 10_000_000

EXACT, LOWER, UPPER = 0, 1, 2

BIT = [1 << i for i in range(64)]
ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

ROW_MASK = []
for r in range(8):
    m = 0
    for c in range(8):
        m |= BIT[r * 8 + c]
    ROW_MASK.append(m)

# cid 0 black target is row 0; cid 1 white target is row 7
TARGET_MASK = [ROW_MASK[0], ROW_MASK[7]]
BEFORE_MASK = [ROW_MASK[1], ROW_MASK[6]]
DIR = [-1, 1]

FWD = [[-1] * 64 for _ in range(2)]
DIAGS = [[() for _ in range(64)] for _ in range(2)]
ATTACK_MASK = [[0] * 64 for _ in range(2)]
PROTECTOR_MASK = [[0] * 64 for _ in range(2)]
PROGRESS = [[0] * 64 for _ in range(2)]
DIST = [[0] * 64 for _ in range(2)]

CENTER_BONUS = [0, 2, 5, 7, 7, 5, 2, 0]
ADV_BONUS = [0, 4, 12, 25, 45, 80, 140, 0]
CLOSE_BONUS = [0, 900, 350, 160, 70, 25, 5, 0]
PASSED_BONUS = [0, 1200, 520, 240, 100, 35, 10, 0]
PIECE_VALUE = 115

for cid in (0, 1):
    d = DIR[cid]
    for sq in range(64):
        r, c = ROW[sq], COL[sq]
        p = r if cid == 1 else 7 - r
        PROGRESS[cid][sq] = p
        DIST[cid][sq] = 7 - p

        nr = r + d
        if 0 <= nr < 8:
            FWD[cid][sq] = nr * 8 + c
            ds = []
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    t = nr * 8 + nc
                    ds.append(t)
                    ATTACK_MASK[cid][sq] |= BIT[t]
            DIAGS[cid][sq] = tuple(ds)

for cid in (0, 1):
    for sq in range(64):
        for t in DIAGS[cid][sq]:
            PROTECTOR_MASK[cid][t] |= BIT[sq]

FRONT_NARROW = [[0] * 64 for _ in range(2)]
FRONT_WIDE = [[0] * 64 for _ in range(2)]

for cid in (0, 1):
    d = DIR[cid]
    for sq in range(64):
        r, c = ROW[sq], COL[sq]
        dist = DIST[cid][sq]
        narrow = 0
        wide = 0
        for k in range(1, dist + 1):
            rr = r + d * k
            if not (0 <= rr < 8):
                continue
            for dc in (-1, 0, 1):
                cc = c + dc
                if 0 <= cc < 8:
                    narrow |= BIT[rr * 8 + cc]
            for dc in range(-k, k + 1):
                cc = c + dc
                if 0 <= cc < 8:
                    wide |= BIT[rr * 8 + cc]
        FRONT_NARROW[cid][sq] = narrow
        FRONT_WIDE[cid][sq] = wide

BASE_VAL = [[0] * 64 for _ in range(2)]
for cid in (0, 1):
    for sq in range(64):
        BASE_VAL[cid][sq] = ADV_BONUS[PROGRESS[cid][sq]] + CENTER_BONUS[COL[sq]]

TT = {}
KILLERS = [[None, None] for _ in range(128)]
HISTORY = [[[0 for _ in range(64)] for _ in range(64)] for _ in range(2)]

_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _bits_from_list(pieces):
    b = 0
    for r, c in pieces:
        b |= 1 << (int(r) * 8 + int(c))
    return b


def _move_to_tuple(m):
    fr, to = m
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def _gen_moves(A, B, cid):
    """Legal moves for side A against side B."""
    moves = []
    occ = A | B
    x = A
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb

        f = FWD[cid][fr]
        if f >= 0 and not (occ & BIT[f]):
            moves.append((fr, f))

        for to in DIAGS[cid][fr]:
            if not (A & BIT[to]):
                moves.append((fr, to))

    return moves


def _attack_mask(bits, cid):
    m = 0
    x = bits
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb
        m |= ATTACK_MASK[cid][sq]
    return m


def _has_immediate_win(A, B, cid):
    """True if side A can move a pawn onto its target row now."""
    occ = A | B
    x = A & BEFORE_MASK[cid]
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb

        f = FWD[cid][sq]
        if f >= 0 and not (occ & BIT[f]):
            return True

        for to in DIAGS[cid][sq]:
            if not (A & BIT[to]):
                return True

    return False


def _can_capture_last(A, B, cid):
    """True if A can capture B's last remaining piece immediately."""
    if B and (B & (B - 1)) == 0:
        return bool(_attack_mask(A, cid) & B)
    return False


def _side_features(bits, enemy, cid):
    if bits == 0:
        return -WIN // 2, 8

    opp = 1 - cid
    friend_control = _attack_mask(bits, cid)
    enemy_control = _attack_mask(enemy, opp)
    occ = bits | enemy

    score = bits.bit_count() * PIECE_VALUE
    min_dist = 7
    mobility = 0

    x = bits
    while x:
        lsb = x & -x
        sq = lsb.bit_length() - 1
        x ^= lsb

        b = BIT[sq]
        r, c = ROW[sq], COL[sq]
        p = PROGRESS[cid][sq]
        d = DIST[cid][sq]

        if d < min_dist:
            min_dist = d

        score += BASE_VAL[cid][sq]

        # Mobility under this rule set: forward if empty, diagonals if not own.
        f = FWD[cid][sq]
        if f >= 0 and not (occ & BIT[f]):
            mobility += 1
        for to in DIAGS[cid][sq]:
            if not (bits & BIT[to]):
                mobility += 1

        protected = bool(b & friend_control)
        attacked = bool(b & enemy_control)

        if protected:
            score += 10 + 2 * p

        if attacked:
            if protected:
                score -= 7 + p
            else:
                score -= 25 + 4 * p

        # Small bonus for compact pawn groups.
        if c > 0 and (bits & BIT[sq - 1]):
            score += 3
        if c < 7 and (bits & BIT[sq + 1]):
            score += 3

        # Passed/racing pawns are extremely important in Breakthrough.
        ps = PASSED_BONUS[d]
        if ps:
            if (enemy & FRONT_NARROW[cid][sq]) == 0:
                score += ps
            if (enemy & FRONT_WIDE[cid][sq]) == 0:
                score += ps // 2

    score += CLOSE_BONUS[min_dist]
    score += 2 * mobility
    return score, min_dist


def _evaluate(A, B, cid):
    """Evaluation from side-to-move A's perspective."""
    opp = 1 - cid

    if A == 0:
        return -WIN + 10
    if B == 0:
        return WIN - 10
    if A & TARGET_MASK[cid]:
        return WIN - 10
    if B & TARGET_MASK[opp]:
        return -WIN + 10

    if _has_immediate_win(A, B, cid) or _can_capture_last(A, B, cid):
        return WIN - 100

    sa, da = _side_features(A, B, cid)
    sb, db = _side_features(B, A, opp)

    score = sa - sb

    # Race/tempo term. Equal distance favors the player to move.
    score += 55 * (db - da)
    if da <= db:
        score += 30
    else:
        score -= 30

    # If the opponent has a one-move win at the leaf, this is usually urgent.
    if _has_immediate_win(B, A, opp) or _can_capture_last(B, A, opp):
        score -= 350_000

    if score > WIN // 2:
        return WIN // 2
    if score < -WIN // 2:
        return -WIN // 2
    return score


def _order_moves(A, B, cid, moves, hash_move, ply):
    opp = 1 - cid
    enemy_attacks = _attack_mask(B, opp)
    scored = []

    k1 = k2 = None
    if ply < len(KILLERS):
        k1, k2 = KILLERS[ply]

    for m in moves:
        fr, to = m
        fb = BIT[fr]
        tb = BIT[to]

        sc = HISTORY[cid][fr][to]

        if hash_move is not None and m == hash_move:
            sc += 30_000_000
        if m == k1:
            sc += 50_000
        elif m == k2:
            sc += 25_000

        if tb & TARGET_MASK[cid]:
            sc += 10_000_000

        if B & tb:
            sc += 200_000 + PROGRESS[opp][to] * 500
            if (B & ~tb) == 0:
                sc += 9_000_000

        d = DIST[cid][to]
        if d == 1:
            sc += 70_000
        elif d == 2:
            sc += 12_000
        elif d == 3:
            sc += 2_000

        sc += PROGRESS[cid][to] * 100 + CENTER_BONUS[COL[to]] * 20

        if (B & FRONT_NARROW[cid][to]) == 0:
            sc += PASSED_BONUS[d] // 5

        # Prefer not to move onto an undefended attacked square.
        if tb & enemy_attacks:
            protected = PROTECTOR_MASK[cid][to] & (A ^ fb)
            if protected:
                sc -= 1_000
            else:
                sc -= 8_000 + PROGRESS[cid][to] * 500
        else:
            if fb & enemy_attacks:
                sc += 1_000

        scored.append((sc, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _remember_killer(ply, m):
    if ply >= len(KILLERS):
        return
    if KILLERS[ply][0] != m:
        KILLERS[ply][1] = KILLERS[ply][0]
        KILLERS[ply][0] = m


def _search(A, B, cid, depth, alpha, beta, ply):
    _check_time()

    opp = 1 - cid

    if A == 0:
        return -WIN + ply
    if B == 0:
        return WIN - ply
    if A & TARGET_MASK[cid]:
        return WIN - ply
    if B & TARGET_MASK[opp]:
        return -WIN + ply

    # Exact tactical wins available immediately.
    if _has_immediate_win(A, B, cid) or _can_capture_last(A, B, cid):
        return WIN - ply

    if depth <= 0:
        return _evaluate(A, B, cid)

    key = (A, B, cid)
    entry = TT.get(key)
    hash_move = None
    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        edepth, evalv, flag, emove = entry
        hash_move = emove
        if edepth >= depth:
            if flag == EXACT:
                return evalv
            if flag == LOWER:
                alpha = max(alpha, evalv)
            elif flag == UPPER:
                beta = min(beta, evalv)
            if alpha >= beta:
                return evalv

    moves = _gen_moves(A, B, cid)
    if not moves:
        return -WIN + ply

    ordered = _order_moves(A, B, cid, moves, hash_move, ply)

    best_val = -INF
    best_move = ordered[0]

    for m in ordered:
        fr, to = m
        fb = BIT[fr]
        tb = BIT[to]

        A2 = (A ^ fb) | tb
        B2 = B & ~tb

        if (tb & TARGET_MASK[cid]) or B2 == 0:
            val = WIN - ply
        else:
            val = -_search(B2, A2, opp, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            if not (B & tb):
                _remember_killer(ply, m)
                nh = HISTORY[cid][fr][to] + depth * depth
                HISTORY[cid][fr][to] = nh if nh < 1_000_000 else 1_000_000
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best_val, flag, best_move)
    return best_val


def _root_search(A, B, cid, depth, preferred):
    moves = _gen_moves(A, B, cid)
    if not moves:
        return preferred, -INF

    ordered = _order_moves(A, B, cid, moves, preferred, 0)

    best_move = ordered[0]
    best_val = -INF
    alpha = -INF
    beta = INF
    opp = 1 - cid

    for m in ordered:
        _check_time()

        fr, to = m
        fb = BIT[fr]
        tb = BIT[to]

        A2 = (A ^ fb) | tb
        B2 = B & ~tb

        if (tb & TARGET_MASK[cid]) or B2 == 0:
            val = WIN
        else:
            val = -_search(B2, A2, opp, depth - 1, -beta, -alpha, 1)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    return best_move, best_val


def _choose_heuristic(A, B, cid, moves):
    """Fast safe fallback, always choosing from legal generated moves."""
    opp = 1 - cid
    best = moves[0]
    best_score = -INF

    for m in moves:
        fr, to = m
        fb = BIT[fr]
        tb = BIT[to]

        A2 = (A ^ fb) | tb
        B2 = B & ~tb

        if (tb & TARGET_MASK[cid]) or B2 == 0:
            return m

        val = -_evaluate(B2, A2, opp)

        if _has_immediate_win(B2, A2, opp) or _can_capture_last(B2, A2, opp):
            val -= 200_000

        # Tie-breaking nudges.
        if B & tb:
            val += 2_000
        val += PROGRESS[cid][to] * 20 + CENTER_BONUS[COL[to]] * 5

        if val > best_score:
            best_score = val
            best = m

    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DEADLINE, _NODES

    cid = 1 if color == "w" else 0
    A = _bits_from_list(me)
    B = _bits_from_list(opp)

    moves = _gen_moves(A, B, cid)

    # Terminal states should not be passed to the policy, but keep a fallback.
    if not moves:
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Never miss an immediate legal win.
    for m in moves:
        to_bit = BIT[m[1]]
        if (to_bit & TARGET_MASK[cid]) or ((B & to_bit) and ((B & ~to_bit) == 0)):
            return _move_to_tuple(m)

    fallback = _choose_heuristic(A, B, cid, moves)
    best = fallback

    # Conservative deadline to stay under a 1 second hard limit.
    _DEADLINE = time.perf_counter() + 0.90
    _NODES = 0

    # Prevent unbounded memory growth across many arena calls.
    if len(TT) > 300_000:
        TT.clear()

    total_pieces = (A | B).bit_count()
    if total_pieces <= 6:
        max_depth = 14
    elif total_pieces <= 12:
        max_depth = 12
    elif total_pieces <= 20:
        max_depth = 10
    else:
        max_depth = 8

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE - 0.01:
                break

            candidate, value = _root_search(A, B, cid, depth, best)
            best = candidate

            if value >= WIN - 1000:
                break

    except _Timeout:
        pass

    return _move_to_tuple(best)
