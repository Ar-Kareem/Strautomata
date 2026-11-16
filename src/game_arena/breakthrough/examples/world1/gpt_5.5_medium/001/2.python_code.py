
import time

# Breakthrough policy for an 8x8 board.
# API:
# def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:

INF = 10**9
WIN = 10**7

ROWS = [i // 8 for i in range(64)]
COLS = [i % 8 for i in range(64)]
ROW_MASKS = [sum(1 << (r * 8 + c) for c in range(8)) for r in range(8)]

# Index 0 is dir=-1, index 1 is dir=+1.
PROTECT_MASKS = [[0] * 64 for _ in range(2)]
ATTACK_MASKS = [[0] * 64 for _ in range(2)]
PASS_MASKS = [[0] * 64 for _ in range(2)]

for idx, d in enumerate((-1, 1)):
    for sq in range(64):
        r, c = ROWS[sq], COLS[sq]

        # Friendly protectors of a piece on sq are one row behind it diagonally.
        br = r - d
        m = 0
        if 0 <= br < 8:
            if c > 0:
                m |= 1 << (br * 8 + c - 1)
            if c < 7:
                m |= 1 << (br * 8 + c + 1)
        PROTECT_MASKS[idx][sq] = m

        # Enemy attackers of a piece on sq are one row ahead in our direction,
        # because the enemy moves in the opposite direction.
        ar = r + d
        m = 0
        if 0 <= ar < 8:
            if c > 0:
                m |= 1 << (ar * 8 + c - 1)
            if c < 7:
                m |= 1 << (ar * 8 + c + 1)
        ATTACK_MASKS[idx][sq] = m

        # Passed-pawn mask: enemy pieces in front of us in same/adjacent files.
        m = 0
        rr = r + d
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    m |= 1 << (rr * 8 + cc)
            rr += d
        PASS_MASKS[idx][sq] = m


_DEADLINE = 0.0
_NODES = 0
_TT = {}


def _to_bb(pieces):
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def _goal_row(direction):
    return 7 if direction > 0 else 0


def _progress(row, direction):
    return row if direction > 0 else 7 - row


def _move_to_tuple(move):
    f, t = move
    return ((ROWS[f], COLS[f]), (ROWS[t], COLS[t]))


def _timeout_check():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
        raise TimeoutError


def _has_goal_move(us, them, direction):
    goal = _goal_row(direction)
    occ = us | them
    bb = us
    while bb:
        lsb = bb & -bb
        f = lsb.bit_length() - 1
        bb ^= lsb
        r, c = ROWS[f], COLS[f]
        nr = r + direction
        if nr != goal:
            continue

        # Straight forward, only if empty.
        t = nr * 8 + c
        if not (occ & (1 << t)):
            return True

        # Diagonal forward, if not occupied by own piece.
        if c > 0:
            t = nr * 8 + c - 1
            if not (us & (1 << t)):
                return True
        if c < 7:
            t = nr * 8 + c + 1
            if not (us & (1 << t)):
                return True

    return False


def _side_features(us, them, direction):
    idx = 1 if direction > 0 else 0
    occ = us | them
    score = us.bit_count() * 125
    mobility = 0

    bb = us
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        r, c = ROWS[sq], COLS[sq]
        prog = _progress(r, direction)
        dist = 7 - prog

        # Advancement is very important in Breakthrough.
        score += prog * 18 + prog * prog * 4

        # Slight central preference; edge pawns are less flexible.
        if 2 <= c <= 5:
            score += 7
        elif c == 1 or c == 6:
            score += 3

        protected = bool(us & PROTECT_MASKS[idx][sq])
        attacked = bool(them & ATTACK_MASKS[idx][sq])

        if protected:
            score += 12 + prog
        if attacked and not protected:
            score -= 24 + prog * 5
        elif attacked and protected:
            score += 3

        # Passed pawns are often decisive.
        if not (them & PASS_MASKS[idx][sq]):
            score += 45 + prog * 18 + max(0, 6 - dist) * max(0, 6 - dist) * 8

        # Pawns one step from promotion are urgent threats.
        if prog == 6:
            score += 150
        elif prog == 5:
            score += 55

        # Cheap mobility count while we are already iterating pieces.
        nr = r + direction
        if 0 <= nr < 8:
            t = nr * 8 + c
            if not (occ & (1 << t)):
                mobility += 1
            if c > 0:
                t = nr * 8 + c - 1
                if not (us & (1 << t)):
                    mobility += 1
            if c < 7:
                t = nr * 8 + c + 1
                if not (us & (1 << t)):
                    mobility += 1

    score += mobility * 4
    return score


def _evaluate(curr, enemy, direction):
    goal = _goal_row(direction)
    enemy_goal = _goal_row(-direction)

    if curr & ROW_MASKS[goal]:
        return WIN
    if enemy & ROW_MASKS[enemy_goal]:
        return -WIN
    if enemy == 0:
        return WIN
    if curr == 0:
        return -WIN

    score = _side_features(curr, enemy, direction) - _side_features(enemy, curr, -direction)

    # Immediate promotion threats.
    if _has_goal_move(curr, enemy, direction):
        score += 650
    if _has_goal_move(enemy, curr, -direction):
        score -= 800

    return score


def _move_order_score(curr, enemy, direction, f, t):
    idx = 1 if direction > 0 else 0
    goal = _goal_row(direction)
    score = 0
    tbit = 1 << t

    if ROWS[t] == goal:
        score += 1_000_000

    capture = bool(enemy & tbit)
    if capture:
        # Capturing advanced enemy pieces is especially valuable.
        score += 6000 + _progress(ROWS[t], -direction) * 250
    else:
        score += 50

    prog = _progress(ROWS[t], direction)
    score += prog * 80 + prog * prog * 8

    # Diagonal moves are flexible and can dodge blockers.
    if COLS[f] != COLS[t]:
        score += 20

    # Center preference.
    if 2 <= COLS[t] <= 5:
        score += 18

    new_curr = (curr ^ (1 << f)) | tbit
    protected = bool(new_curr & PROTECT_MASKS[idx][t])
    attacked = bool(enemy & ATTACK_MASKS[idx][t])

    if protected:
        score += 35
    if attacked and not protected:
        score -= 120 + prog * 20

    if not (enemy & PASS_MASKS[idx][t]):
        score += 100 + prog * 35

    return score


def _generate_moves(curr, enemy, direction, tt_move=None):
    occ = curr | enemy
    moves = []
    bb = curr

    while bb:
        lsb = bb & -bb
        f = lsb.bit_length() - 1
        bb ^= lsb

        r, c = ROWS[f], COLS[f]
        nr = r + direction
        if not (0 <= nr < 8):
            continue

        # Straight forward: must be empty.
        t = nr * 8 + c
        if not (occ & (1 << t)):
            s = _move_order_score(curr, enemy, direction, f, t)
            if tt_move == (f, t):
                s += 2_000_000
            moves.append((s, f, t))

        # Diagonal left: may be empty or enemy, but not own.
        if c > 0:
            t = nr * 8 + c - 1
            if not (curr & (1 << t)):
                s = _move_order_score(curr, enemy, direction, f, t)
                if tt_move == (f, t):
                    s += 2_000_000
                moves.append((s, f, t))

        # Diagonal right.
        if c < 7:
            t = nr * 8 + c + 1
            if not (curr & (1 << t)):
                s = _move_order_score(curr, enemy, direction, f, t)
                if tt_move == (f, t):
                    s += 2_000_000
                moves.append((s, f, t))

    moves.sort(reverse=True)
    return [(f, t) for _, f, t in moves]


def _negamax(curr, enemy, direction, depth, alpha, beta, ply):
    _timeout_check()

    goal = _goal_row(direction)
    enemy_goal = _goal_row(-direction)

    if curr & ROW_MASKS[goal]:
        return WIN - ply
    if enemy & ROW_MASKS[enemy_goal]:
        return -WIN + ply
    if enemy == 0:
        return WIN - ply
    if curr == 0:
        return -WIN + ply
    if depth <= 0:
        return _evaluate(curr, enemy, direction)

    alpha_orig = alpha
    key = (curr, enemy, direction, depth)
    entry = _TT.get(key)
    tt_move = None

    if entry is not None:
        stored_depth, val, flag, best_move = entry
        tt_move = best_move
        if stored_depth >= depth:
            if flag == 0:
                return val
            if flag == 1 and val >= beta:
                return val
            if flag == -1 and val <= alpha:
                return val

    moves = _generate_moves(curr, enemy, direction, tt_move)
    if not moves:
        return -WIN + ply

    best_val = -INF
    best_move = moves[0]

    for f, t in moves:
        tbit = 1 << t
        new_curr = (curr ^ (1 << f)) | tbit
        new_enemy = enemy & ~tbit

        if ROWS[t] == goal or new_enemy == 0:
            val = WIN - ply - 1
        else:
            val = -_negamax(new_enemy, new_curr, -direction, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = (f, t)

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = -1   # upper bound
    elif best_val >= beta:
        flag = 1    # lower bound
    else:
        flag = 0    # exact

    _TT[key] = (depth, best_val, flag, best_move)
    return best_val


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DEADLINE, _NODES, _TT

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODES = 0
    _TT = {}

    direction = -1 if color == 'b' else 1
    curr = _to_bb(me)
    enemy = _to_bb(opp)

    moves = _generate_moves(curr, enemy, direction)
    if not moves:
        # In a valid Breakthrough position this should not occur. There is no
        # legal move to return if the side is truly immobilized, but keep a
        # deterministic fallback to avoid crashing.
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Always keep a legal fallback.
    best_move = moves[0]
    goal = _goal_row(direction)

    # If an immediate win exists, play it.
    for f, t in moves:
        tbit = 1 << t
        if ROWS[t] == goal or (enemy & tbit and (enemy & ~tbit) == 0):
            return _move_to_tuple((f, t))

    total_pieces = curr.bit_count() + enemy.bit_count()
    if total_pieces <= 8:
        max_depth = 9
    elif total_pieces <= 14:
        max_depth = 8
    elif total_pieces <= 22:
        max_depth = 7
    else:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _DEADLINE:
                break

            # Put the previous iteration's best move first.
            ordered = moves[:]
            if best_move in ordered:
                ordered.remove(best_move)
                ordered.insert(0, best_move)

            alpha = -INF
            beta = INF
            depth_best = best_move
            depth_best_val = -INF

            for f, t in ordered:
                if time.perf_counter() >= _DEADLINE:
                    raise TimeoutError

                tbit = 1 << t
                new_curr = (curr ^ (1 << f)) | tbit
                new_enemy = enemy & ~tbit

                if ROWS[t] == goal or new_enemy == 0:
                    val = WIN - 1
                else:
                    val = -_negamax(new_enemy, new_curr, -direction, depth - 1, -beta, -alpha, 1)

                if val > depth_best_val:
                    depth_best_val = val
                    depth_best = (f, t)

                if val > alpha:
                    alpha = val

            best_move = depth_best

    except TimeoutError:
        pass

    return _move_to_tuple(best_move)
