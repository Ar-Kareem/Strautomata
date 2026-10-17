
from time import perf_counter

# Breakthrough policy for an 8x8 board.
# API:
#   policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str)
# returns:
#   ((from_row, from_col), (to_row, to_col))

BOARD_N = 8
N_SQ = 64
WIN = 1_000_000
INF = 10_000_000

BITS = [1 << i for i in range(N_SQ)]
ROWS = [i // 8 for i in range(N_SQ)]
COLS = [i & 7 for i in range(N_SQ)]
ROW_MASKS = [sum(1 << (r * 8 + c) for c in range(8)) for r in range(8)]

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DEADLINE, _NODES, _TT

    start = perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0

    if len(_TT) > 200_000:
        _TT.clear()

    d = 1 if color == "w" else -1

    my_bits = _list_to_bits(me)
    op_bits = _list_to_bits(opp)

    root_moves = _generate_moves(my_bits, op_bits, d)
    if not root_moves:
        # Should not occur in a non-terminal Breakthrough position.
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Safe fallback: best statically ordered legal move.
    best_move = root_moves[0][0]

    # If there is an immediate win, play it instantly.
    for mv, _ in root_moves:
        to = mv[1]
        enemy_after = op_bits & ~BITS[to]
        if ROWS[to] == _goal_row(d) or enemy_after == 0:
            return _move_to_tuple(mv)

    try:
        # Iterative deepening. The timeout exception keeps the last completed depth.
        max_depth = 9
        total_pieces = my_bits.bit_count() + op_bits.bit_count()
        if total_pieces > 22:
            max_depth = 7
        elif total_pieces <= 10:
            max_depth = 11

        last_best = best_move
        for depth in range(1, max_depth + 1):
            score, mv = _search_root(my_bits, op_bits, d, depth, last_best)
            if mv is not None:
                best_move = mv
                last_best = mv
            if score >= WIN // 2:
                break
    except _Timeout:
        pass

    return _move_to_tuple(best_move)


def _list_to_bits(pieces):
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def _move_to_tuple(mv):
    fr, to = mv
    return ((ROWS[fr], COLS[fr]), (ROWS[to], COLS[to]))


def _goal_row(d):
    return 7 if d == 1 else 0


def _goal_mask(d):
    return ROW_MASKS[_goal_row(d)]


def _progress_idx(idx, d):
    r = ROWS[idx]
    return r if d == 1 else 7 - r


def _terminal_value(cur, enemy, d):
    # cur is the side to move, moving in direction d.
    if cur & _goal_mask(d):
        return WIN
    if enemy & _goal_mask(-d):
        return -WIN
    if enemy == 0:
        return WIN
    if cur == 0:
        return -WIN
    return None


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() > _DEADLINE:
        raise _Timeout()


def _generate_moves(cur, enemy, d, tt_move=None):
    occ = cur | enemy
    moves = []

    bb = cur
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        r = ROWS[fr]
        c = COLS[fr]
        nr = r + d
        if nr < 0 or nr > 7:
            continue

        # Straight forward: only into empty square.
        to = fr + d * 8
        tb = BITS[to]
        if not (occ & tb):
            mv = (fr, to)
            moves.append((mv, _move_score(mv, cur, enemy, d, False)))

        # Diagonal left/right: legal into empty or opponent square, not own square.
        if c > 0:
            to = fr + d * 8 - 1
            tb = BITS[to]
            if not (cur & tb):
                mv = (fr, to)
                moves.append((mv, _move_score(mv, cur, enemy, d, bool(enemy & tb))))

        if c < 7:
            to = fr + d * 8 + 1
            tb = BITS[to]
            if not (cur & tb):
                mv = (fr, to)
                moves.append((mv, _move_score(mv, cur, enemy, d, bool(enemy & tb))))

    if tt_move is not None:
        boosted = []
        for mv, sc in moves:
            if mv == tt_move:
                sc += 2_000_000
            boosted.append((mv, sc))
        moves = boosted

    moves.sort(key=lambda x: x[1], reverse=True)
    return moves


def _move_score(mv, cur, enemy, d, is_capture):
    fr, to = mv
    r_to = ROWS[to]
    c_to = COLS[to]
    prog = _progress_idx(to, d)
    dist = 7 - prog

    score = prog * 30

    # Prefer central files slightly.
    score += 10 - abs(2 * c_to - 7)

    if r_to == _goal_row(d):
        score += 1_000_000

    if is_capture:
        # Capturing advanced enemy pieces is especially valuable.
        score += 5000 + _progress_idx(to, -d) * 80
    elif COLS[fr] != c_to:
        score += 35

    if dist == 1:
        score += 1200
    elif dist == 2:
        score += 350

    cur_after = (cur ^ BITS[fr]) | BITS[to]
    enemy_after = enemy & ~BITS[to]

    if _is_passed_square(to, enemy_after, d):
        score += 600 + prog * 60

    if _defended_by_own(to, cur_after, d):
        score += 80
    if _attacked_by_enemy(to, enemy_after, d):
        score -= 120

    return score


def _search_root(cur, enemy, d, depth, preferred):
    moves = _generate_moves(cur, enemy, d, preferred)
    best_score = -INF
    best_move = None
    alpha = -INF
    beta = INF

    for mv, _ in moves:
        _check_time()
        fr, to = mv
        cur_after = (cur ^ BITS[fr]) | BITS[to]
        enemy_after = enemy & ~BITS[to]

        score = -_negamax(enemy_after, cur_after, -d, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

    return best_score, best_move


def _negamax(cur, enemy, d, depth, alpha, beta):
    _check_time()

    term = _terminal_value(cur, enemy, d)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(cur, enemy, d)

    key = (cur, enemy, d, depth)
    entry = _TT.get(key)
    tt_move = None
    if entry is not None:
        ent_depth, ent_val, ent_flag, ent_move = entry
        tt_move = ent_move
        if ent_depth >= depth:
            if ent_flag == 0:
                return ent_val
            if ent_flag == 1 and ent_val >= beta:
                return ent_val
            if ent_flag == -1 and ent_val <= alpha:
                return ent_val

    alpha_orig = alpha
    best = -INF
    best_move = None

    moves = _generate_moves(cur, enemy, d, tt_move)
    if not moves:
        return -WIN

    for mv, _ in moves:
        fr, to = mv
        cur_after = (cur ^ BITS[fr]) | BITS[to]
        enemy_after = enemy & ~BITS[to]

        score = -_negamax(enemy_after, cur_after, -d, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = -1  # upper bound
    elif best >= beta:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    _TT[key] = (depth, best, flag, best_move)
    return best


def _evaluate(cur, enemy, d):
    term = _terminal_value(cur, enemy, d)
    if term is not None:
        return term

    cur_count = cur.bit_count()
    enemy_count = enemy.bit_count()

    score = 0

    # Material.
    score += 130 * (cur_count - enemy_count)

    cur_prog_sum = 0
    enemy_prog_sum = 0
    cur_max_prog = 0
    enemy_max_prog = 0
    cur_min_dist = 7
    enemy_min_dist = 7

    # Current side features.
    bb = cur
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb

        prog = _progress_idx(idx, d)
        dist = 7 - prog
        cur_prog_sum += prog
        cur_max_prog = max(cur_max_prog, prog)
        cur_min_dist = min(cur_min_dist, dist)

        score += prog * prog * 5

        if _is_passed_square(idx, enemy, d):
            score += 120 + prog * 45

        attacked = _attacked_by_enemy(idx, enemy, d)
        defended = _defended_by_own(idx, cur, d)

        if defended:
            score += 14 + prog * 2
        if attacked:
            score -= 32 + prog * 5
            if not defended:
                score -= 18

        # A pawn one step away from promotion is a major threat.
        if dist == 1:
            score += 320
        elif dist == 2:
            score += 95

    # Opponent features, subtracted symmetrically.
    bb = enemy
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb

        prog = _progress_idx(idx, -d)
        dist = 7 - prog
        enemy_prog_sum += prog
        enemy_max_prog = max(enemy_max_prog, prog)
        enemy_min_dist = min(enemy_min_dist, dist)

        score -= prog * prog * 5

        if _is_passed_square(idx, cur, -d):
            score -= 120 + prog * 45

        attacked = _attacked_by_enemy(idx, cur, -d)
        defended = _defended_by_own(idx, enemy, -d)

        if defended:
            score -= 14 + prog * 2
        if attacked:
            score += 32 + prog * 5
            if not defended:
                score += 18

        if dist == 1:
            score -= 340
        elif dist == 2:
            score -= 105

    # Advancement and race.
    score += 18 * (cur_prog_sum - enemy_prog_sum)
    score += 42 * (cur_max_prog - enemy_max_prog)
    score += 65 * (enemy_min_dist - cur_min_dist)

    # Immediate promotion threats at horizon.
    if _has_goal_move(cur, enemy, d):
        score += 55_000
    if _has_goal_move(enemy, cur, -d):
        score -= 58_000

    # Mobility.
    score += 3 * (_mobility(cur, enemy, d) - _mobility(enemy, cur, -d))

    return score


def _mobility(cur, enemy, d):
    occ = cur | enemy
    count = 0
    bb = cur

    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        r = ROWS[fr]
        c = COLS[fr]
        nr = r + d
        if nr < 0 or nr > 7:
            continue

        to = fr + d * 8
        if not (occ & BITS[to]):
            count += 1

        if c > 0:
            to = fr + d * 8 - 1
            if not (cur & BITS[to]):
                count += 1

        if c < 7:
            to = fr + d * 8 + 1
            if not (cur & BITS[to]):
                count += 1

    return count


def _has_goal_move(cur, enemy, d):
    goal = _goal_row(d)
    occ = cur | enemy

    bb = cur
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        r = ROWS[fr]
        c = COLS[fr]
        nr = r + d
        if nr != goal:
            continue

        # Straight to goal if empty.
        to = fr + d * 8
        if not (occ & BITS[to]):
            return True

        # Diagonal to goal if not occupied by own piece.
        if c > 0:
            to = fr + d * 8 - 1
            if not (cur & BITS[to]):
                return True

        if c < 7:
            to = fr + d * 8 + 1
            if not (cur & BITS[to]):
                return True

    return False


def _is_passed_square(idx, enemy, d):
    r = ROWS[idx]
    c = COLS[idx]

    if d == 1:
        row_range = range(r + 1, 8)
    else:
        row_range = range(r - 1, -1, -1)

    c0 = max(0, c - 1)
    c1 = min(7, c + 1)

    for rr in row_range:
        base = rr * 8
        for cc in range(c0, c1 + 1):
            if enemy & BITS[base + cc]:
                return False
    return True


def _attacked_by_enemy(idx, enemy, d):
    # A piece moving in direction d is attacked by enemy pieces
    # one row in front of it, diagonally adjacent.
    r = ROWS[idx]
    c = COLS[idx]
    ar = r + d

    if ar < 0 or ar > 7:
        return False

    base = ar * 8

    if c > 0 and (enemy & BITS[base + c - 1]):
        return True
    if c < 7 and (enemy & BITS[base + c + 1]):
        return True

    return False


def _defended_by_own(idx, cur, d):
    # A piece moving in direction d is defended by own pieces
    # one row behind it, diagonally adjacent.
    r = ROWS[idx]
    c = COLS[idx]
    dr = r - d

    if dr < 0 or dr > 7:
        return False

    base = dr * 8

    if c > 0 and (cur & BITS[base + c - 1]):
        return True
    if c < 7 and (cur & BITS[base + c + 1]):
        return True

    return False
