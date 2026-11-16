
import time

# Breakthrough policy for an 8x8 board.
# API:
#   policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str)
# returns:
#   ((from_row, from_col), (to_row, to_col))

BOARD_N = 8
ALL = (1 << 64) - 1
WIN = 1_000_000
INF = 10_000_000

BITS = [1 << i for i in range(64)]
ROW_OF = [i // 8 for i in range(64)]
COL_OF = [i & 7 for i in range(64)]

ROW_MASKS = []
for r in range(8):
    m = 0
    for c in range(8):
        m |= 1 << (r * 8 + c)
    ROW_MASKS.append(m)

FILE_A = 0
FILE_H = 0
for r in range(8):
    FILE_A |= 1 << (r * 8)
    FILE_H |= 1 << (r * 8 + 7)

CENTER_BONUS = [0, 2, 5, 7, 7, 5, 2, 0]
ADV_BONUS = [0, 6, 16, 34, 65, 120, 230, 0]
PASSED_BONUS = [0, 4, 12, 35, 90, 220, 550, 0]

# Precomputed passed-pawn masks.
# A pawn is considered passed if no enemy pawn is ahead of it in same/adjacent files.
PASSED_MASK_UP = [0] * 64
PASSED_MASK_DOWN = [0] * 64
for i in range(64):
    r, c = ROW_OF[i], COL_OF[i]

    m = 0
    for rr in range(r + 1, 8):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
    PASSED_MASK_UP[i] = m

    m = 0
    for rr in range(r - 1, -1, -1):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
    PASSED_MASK_DOWN[i] = m


class SearchTimeout(Exception):
    pass


DEADLINE = 0.0
NODE_COUNT = 0
TT = {}


def _bit_index(bit: int) -> int:
    return bit.bit_length() - 1


def _progress(idx: int, direction: int) -> int:
    r = ROW_OF[idx]
    return r if direction == 1 else 7 - r


def _goal_mask(direction: int) -> int:
    return ROW_MASKS[7] if direction == 1 else ROW_MASKS[0]


def _reached_goal(bb: int, direction: int) -> bool:
    return bool(bb & _goal_mask(direction))


def _attack_mask(bb: int, direction: int) -> int:
    # Diagonal forward attack/move squares.
    if direction == 1:
        return (((bb & ~FILE_A) << 7) | ((bb & ~FILE_H) << 9)) & ALL
    else:
        return (((bb & ~FILE_A) >> 9) | ((bb & ~FILE_H) >> 7)) & ALL


def _to_bitboard(pieces) -> int:
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def _generate_moves(cur: int, enemy: int, direction: int):
    """Return legal moves as list of (from_bit, to_bit)."""
    moves = []
    own = cur
    occ = cur | enemy
    d8 = direction * 8

    bb = cur
    while bb:
        f = bb & -bb
        bb ^= f
        i = _bit_index(f)
        r = ROW_OF[i]
        c = COL_OF[i]
        nr = r + direction
        if not (0 <= nr < 8):
            continue

        # Straight forward: only if empty.
        ti = i + d8
        t = BITS[ti]
        if not (occ & t):
            moves.append((f, t))

        # Diagonal left: legal if not occupied by own piece; may capture or move empty.
        if c > 0:
            ti = i + d8 - 1
            t = BITS[ti]
            if not (own & t):
                moves.append((f, t))

        # Diagonal right.
        if c < 7:
            ti = i + d8 + 1
            t = BITS[ti]
            if not (own & t):
                moves.append((f, t))

    return moves


def _has_winning_move(cur: int, enemy: int, direction: int) -> int:
    """Count legal moves that immediately reach the goal row."""
    goal_row = 7 if direction == 1 else 0
    pre_row = goal_row - direction
    if not (0 <= pre_row < 8):
        return 0

    row_pieces = cur & ROW_MASKS[pre_row]
    if not row_pieces:
        return 0

    count = 0
    own = cur
    occ = cur | enemy
    d8 = direction * 8

    bb = row_pieces
    while bb:
        f = bb & -bb
        bb ^= f
        i = _bit_index(f)
        c = COL_OF[i]

        # Straight to goal row: must be empty.
        t = BITS[i + d8]
        if not (occ & t):
            count += 1

        # Diagonal to goal row: may be empty or enemy, but not own.
        if c > 0:
            t = BITS[i + d8 - 1]
            if not (own & t):
                count += 1
        if c < 7:
            t = BITS[i + d8 + 1]
            if not (own & t):
                count += 1

    return count


def _evaluate(cur: int, enemy: int, direction: int) -> int:
    """Static evaluation from the side-to-move's perspective."""
    if cur == 0:
        return -WIN
    if enemy == 0:
        return WIN
    if _reached_goal(cur, direction):
        return WIN
    if _reached_goal(enemy, -direction):
        return -WIN

    cur_win_moves = _has_winning_move(cur, enemy, direction)
    if cur_win_moves:
        return WIN // 2 + 1000 * cur_win_moves

    enemy_win_moves = _has_winning_move(enemy, cur, -direction)

    cur_count = cur.bit_count()
    enemy_count = enemy.bit_count()
    score = 130 * (cur_count - enemy_count)

    cur_attacks = _attack_mask(cur, direction)
    enemy_attacks = _attack_mask(enemy, -direction)

    cur_defended = cur & cur_attacks
    enemy_defended = enemy & enemy_attacks

    cur_vulnerable = cur & enemy_attacks
    enemy_vulnerable = enemy & cur_attacks

    # Captures available / threatened.
    score += 18 * ((cur_attacks & enemy).bit_count() - (enemy_attacks & cur).bit_count())

    # Defended formations are good.
    score += 8 * (cur_defended.bit_count() - enemy_defended.bit_count())

    # Undefended attacked pieces are bad.
    score -= 40 * (cur_vulnerable & ~cur_defended).bit_count()
    score -= 14 * (cur_vulnerable & cur_defended).bit_count()
    score += 40 * (enemy_vulnerable & ~enemy_defended).bit_count()
    score += 14 * (enemy_vulnerable & enemy_defended).bit_count()

    max_cur_prog = 0
    max_enemy_prog = 0

    passed_masks_cur = PASSED_MASK_UP if direction == 1 else PASSED_MASK_DOWN
    passed_masks_enemy = PASSED_MASK_DOWN if direction == 1 else PASSED_MASK_UP

    bb = cur
    while bb:
        b = bb & -bb
        bb ^= b
        i = _bit_index(b)
        p = _progress(i, direction)
        max_cur_prog = max(max_cur_prog, p)
        score += ADV_BONUS[p]
        score += CENTER_BONUS[COL_OF[i]]
        if not (enemy & passed_masks_cur[i]):
            score += PASSED_BONUS[p]

    bb = enemy
    enemy_dir = -direction
    while bb:
        b = bb & -bb
        bb ^= b
        i = _bit_index(b)
        p = _progress(i, enemy_dir)
        max_enemy_prog = max(max_enemy_prog, p)
        score -= ADV_BONUS[p]
        score -= CENTER_BONUS[COL_OF[i]]
        if not (cur & passed_masks_enemy[i]):
            score -= PASSED_BONUS[p]

    # Race pressure: the most advanced pawn often decides Breakthrough.
    score += 35 * (max_cur_prog - max_enemy_prog)
    score += 8 * (max_cur_prog * max_cur_prog - max_enemy_prog * max_enemy_prog)

    # Opponent has an immediate promotion threat; very dangerous.
    if enemy_win_moves:
        score -= 25_000 * enemy_win_moves

    return score


def _move_order_score(move, cur: int, enemy: int, direction: int) -> int:
    f, t = move
    ti = _bit_index(t)
    score = 0

    # Promotion moves first.
    if t & _goal_mask(direction):
        score += 1_000_000

    # Captures are usually important.
    if enemy & t:
        enemy_prog = _progress(ti, -direction)
        score += 5000 + 80 * enemy_prog

    p = _progress(ti, direction)
    score += 30 * p
    score += CENTER_BONUS[COL_OF[ti]]

    new_cur = (cur ^ f) | t
    enemy_attacks = _attack_mask(enemy, -direction)
    new_defense = _attack_mask(new_cur, direction)

    # Prefer not to walk into an undefended capture unless tactically justified.
    if t & enemy_attacks:
        if t & new_defense:
            score -= 20
        else:
            score -= 100

    passed_masks = PASSED_MASK_UP if direction == 1 else PASSED_MASK_DOWN
    if not (enemy & passed_masks[ti]):
        score += 70 * p

    return score


def _ordered_moves(cur: int, enemy: int, direction: int):
    moves = _generate_moves(cur, enemy, direction)
    moves.sort(key=lambda m: _move_order_score(m, cur, enemy, direction), reverse=True)
    return moves


def _negamax(cur: int, enemy: int, direction: int, depth: int, alpha: int, beta: int) -> int:
    global NODE_COUNT, DEADLINE, TT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()

    # Terminal checks.
    if cur == 0:
        return -WIN
    if enemy == 0:
        return WIN
    if _reached_goal(cur, direction):
        return WIN
    if _reached_goal(enemy, -direction):
        return -WIN

    if depth <= 0:
        return _evaluate(cur, enemy, direction)

    key = (cur, enemy, direction, depth)
    entry = TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == 0:      # exact
            return val
        if flag == 1 and val >= beta:   # lower bound
            return val
        if flag == 2 and val <= alpha:  # upper bound
            return val

    original_alpha = alpha
    original_beta = beta

    moves = _ordered_moves(cur, enemy, direction)
    if not moves:
        return -WIN

    best = -INF

    for f, t in moves:
        new_cur = (cur ^ f) | t
        new_enemy = enemy & ~t

        val = -_negamax(new_enemy, new_cur, -direction, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= original_alpha:
        flag = 2  # upper
    elif best >= original_beta:
        flag = 1  # lower
    else:
        flag = 0  # exact
    TT[key] = (best, flag)

    return best


def _move_to_tuple(move):
    f, t = move
    fi = _bit_index(f)
    ti = _bit_index(t)
    return ((ROW_OF[fi], COL_OF[fi]), (ROW_OF[ti], COL_OF[ti]))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODE_COUNT, TT

    start = time.perf_counter()
    DEADLINE = start + 0.90
    NODE_COUNT = 0
    TT = {}

    direction = -1 if color == "b" else 1
    cur = _to_bitboard(me)
    enemy = _to_bitboard(opp)

    legal = _ordered_moves(cur, enemy, direction)

    # A legal fallback is mandatory.
    if not legal:
        # This should not occur in normal Breakthrough positions.
        # Return a harmless-shaped fallback if the arena ever supplies a terminal/no-move state.
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    best_move = legal[0]

    # Immediate win: take it without spending time.
    for mv in legal:
        if mv[1] & _goal_mask(direction):
            return _move_to_tuple(mv)

    total_pieces = cur.bit_count() + enemy.bit_count()
    if total_pieces >= 28:
        max_depth = 4
    elif total_pieces >= 22:
        max_depth = 5
    elif total_pieces >= 14:
        max_depth = 6
    else:
        max_depth = 8

    # Iterative deepening. Only commit a result after a full depth completes.
    previous_best = best_move

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > DEADLINE:
            break

        try:
            # Put previous best first to improve alpha-beta pruning.
            root_moves = legal[:]
            if previous_best in root_moves:
                root_moves.remove(previous_best)
                root_moves.insert(0, previous_best)

            alpha = -INF
            beta = INF
            depth_best = previous_best
            depth_best_score = -INF

            for f, t in root_moves:
                if time.perf_counter() > DEADLINE:
                    raise SearchTimeout()

                new_cur = (cur ^ f) | t
                new_enemy = enemy & ~t

                val = -_negamax(new_enemy, new_cur, -direction, depth - 1, -beta, -alpha)

                if val > depth_best_score:
                    depth_best_score = val
                    depth_best = (f, t)

                if val > alpha:
                    alpha = val

            best_move = depth_best
            previous_best = depth_best

            # If a forced/immediate win has been found, no need to risk the clock.
            if depth_best_score > WIN - 1000:
                break

        except SearchTimeout:
            break

    return _move_to_tuple(best_move)
