
import time

WIN_SCORE = 10_000_000
INF = 10**12
FULL = (1 << 16) - 1

POPCOUNT = [0] * (FULL + 1)
for _i in range(1, FULL + 1):
    POPCOUNT[_i] = POPCOUNT[_i >> 1] + (_i & 1)

_LINES = []
for _r in range(4):
    _LINES.append((_r * 4, _r * 4 + 1, _r * 4 + 2, _r * 4 + 3))
for _c in range(4):
    _LINES.append((_c, _c + 4, _c + 8, _c + 12))
_LINES.append((0, 5, 10, 15))
_LINES.append((3, 6, 9, 12))

LINE_MASKS = tuple(sum(1 << i for i in line) for line in _LINES)

_cell_masks = []
for _i in range(16):
    _cell_masks.append(tuple(lm for lm in LINE_MASKS if (lm >> _i) & 1))
CELL_LINE_MASKS = tuple(_cell_masks)

CELL_EVAL = []
for _i in range(16):
    _r, _c = divmod(_i, 4)
    _center_dist = abs(2 * _r - 3) + abs(2 * _c - 3)
    CELL_EVAL.append(len(CELL_LINE_MASKS[_i]) * 8 - _center_dist)
CELL_EVAL = tuple(CELL_EVAL)

BASE_ORDER = tuple(sorted(range(16), key=lambda i: (-CELL_EVAL[i], i)))

# Leaf values for an open line containing k friendly marks and no enemy marks.
LINE_VALUE = (0, 6, 120, 1500, WIN_SCORE)
# Move-ordering values.
CREATE_VALUE = (0, 6, 110, 2200, 0)
BLOCK_VALUE = (0, 5, 170, 0, 0)


def _evaluate(my_mask: int, op_mask: int) -> int:
    score = 0
    for lm in LINE_MASKS:
        a = POPCOUNT[my_mask & lm]
        b = POPCOUNT[op_mask & lm]
        if a:
            if b == 0:
                score += LINE_VALUE[a]
        elif b:
            score -= LINE_VALUE[b]

    m = my_mask
    while m:
        lsb = m & -m
        score += CELL_EVAL[lsb.bit_length() - 1]
        m ^= lsb
    m = op_mask
    while m:
        lsb = m & -m
        score -= CELL_EVAL[lsb.bit_length() - 1]
        m ^= lsb
    return score


def _score_move(side_mask: int, enemy_mask: int, i: int) -> int:
    bit = 1 << i
    new_side = side_mask | bit
    score = CELL_EVAL[i]
    for lm in CELL_LINE_MASKS[i]:
        if enemy_mask & lm:
            # Occupying this cell kills an enemy line; especially valuable
            # when the enemy already had two marks in it.
            if (side_mask & lm) == 0:
                score += BLOCK_VALUE[POPCOUNT[enemy_mask & lm]]
        else:
            # Build friendly lines. Three plus an empty cell is a forcing threat.
            score += CREATE_VALUE[POPCOUNT[new_side & lm]]
    return score


def _ordered_bit(mask: int) -> int:
    for i in BASE_ORDER:
        if (mask >> i) & 1:
            return i
    return -1


def policy(board: list[list[int]]) -> tuple[int, int]:
    my_mask = 0
    op_mask = 0
    for r in range(4):
        row = board[r]
        base = r * 4
        for c in range(4):
            v = int(row[c])
            if v == 1:
                my_mask |= 1 << (base + c)
            elif v == -1:
                op_mask |= 1 << (base + c)

    occupied = my_mask | op_mask
    empty_mask = FULL & ~occupied
    if empty_mask == 0:
        return (0, 0)

    # Immediate tactical decision for the root.
    win_mask = 0
    threat_mask = 0
    for lm in LINE_MASKS:
        mine = my_mask & lm
        theirs = op_mask & lm
        if theirs == 0 and POPCOUNT[mine] == 3:
            win_mask |= lm & ~my_mask
        if mine == 0 and POPCOUNT[theirs] == 3:
            threat_mask |= lm & ~op_mask

    if win_mask:
        i = _ordered_bit(win_mask)
        return (i // 4, i % 4)
    if threat_mask:
        # If there are several distinct enemy winning cells the position is lost;
        # still return a legal block. If several lines share one empty cell, this
        # single move blocks them all.
        i = _ordered_bit(threat_mask)
        return (i // 4, i % 4)

    # Guaranteed-legal fallback before spending search time.
    best_move = _ordered_bit(empty_mask)
    best_static = -INF
    for i in BASE_ORDER:
        if (empty_mask >> i) & 1:
            v = _evaluate(my_mask | (1 << i), op_mask)
            if v > best_static:
                best_static = v
                best_move = i

    deadline = time.monotonic() + 0.95
    tt = {}
    nodes = 0
    root_move = None

    EXACT = 0
    LOWER = 1
    UPPER = 2

    def search(my_mask: int, op_mask: int, side: int, depth: int,
               alpha: int, beta: int, ply: int) -> int:
        nonlocal nodes, root_move

        nodes += 1
        if (nodes & 1023) == 0 and time.monotonic() > deadline:
            raise TimeoutError

        orig_alpha = alpha
        orig_beta = beta
        key = (my_mask, op_mask, side)
        ent = tt.get(key)
        tt_move = -1
        if ent is not None:
            ent_depth, ent_value, ent_flag, ent_move = ent
            if ent_depth >= depth:
                if ent_flag == EXACT:
                    return ent_value
                if ent_flag == LOWER:
                    if ent_value > alpha:
                        alpha = ent_value
                else:
                    if ent_value < beta:
                        beta = ent_value
                if alpha >= beta:
                    return ent_value
            tt_move = ent_move

        if side == 1:
            side_mask = my_mask
            enemy_mask = op_mask
        else:
            side_mask = op_mask
            enemy_mask = my_mask

        threats = 0
        for lm in LINE_MASKS:
            sm = side_mask & lm
            em = enemy_mask & lm
            sc = POPCOUNT[sm]
            ec = POPCOUNT[em]

            if sc == 4:
                return (WIN_SCORE - ply) if side == 1 else (-WIN_SCORE + ply)
            if ec == 4:
                return (-WIN_SCORE + ply) if side == 1 else (WIN_SCORE - ply)

            # Side to move wins immediately.
            if ec == 0 and sc == 3:
                return (WIN_SCORE - ply) if side == 1 else (-WIN_SCORE + ply)

            # Enemy cells that would win on the next move.
            if sc == 0 and ec == 3:
                threats |= lm & ~enemy_mask

        forced = False
        if threats:
            if threats & (threats - 1):
                # Two different one-move wins cannot both be stopped.
                return (-WIN_SCORE + ply) if side == 1 else (WIN_SCORE - ply)
            only = threats.bit_length() - 1
            moves = (only,)
            forced = True
        else:
            if depth <= 0:
                return _evaluate(my_mask, op_mask)
            rest = [i for i in BASE_ORDER if (empty := FULL & ~(my_mask | op_mask)) and ((empty >> i) & 1)]
            if tt_move >= 0 and ((empty >> tt_move) & 1):
                rest.remove(tt_move)
                first = (tt_move,)
            else:
                first = ()
            rest.sort(key=lambda i: _score_move(side_mask, enemy_mask, i), reverse=True)
            moves = first + tuple(rest)

        if side == 1:
            best = -INF
            best_i = -1
            for i in moves:
                bit = 1 << i
                value = search(
                    my_mask | bit,
                    op_mask,
                    -1,
                    depth if forced else depth - 1,
                    alpha,
                    beta,
                    ply + 1,
                )
                if value > best:
                    best = value
                    best_i = i
                    if ply == 0:
                        root_move = i
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
        else:
            best = INF
            best_i = -1
            for i in moves:
                bit = 1 << i
                value = search(
                    my_mask,
                    op_mask | bit,
                    1,
                    depth if forced else depth - 1,
                    alpha,
                    beta,
                    ply + 1,
                )
                if value < best:
                    best = value
                    best_i = i
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break

        if best <= orig_alpha:
            flag = UPPER
        elif best >= orig_beta:
            flag = LOWER
        else:
            flag = EXACT
        tt[key] = (depth, best, flag, best_i)
        return best

    try:
        for depth in range(1, POPCOUNT[empty_mask] + 1):
            root_move = None
            value = search(my_mask, op_mask, 1, depth, -INF, INF, 0)
            if root_move is not None and ((occupied >> root_move) & 1) == 0:
                best_move = root_move
            if value > WIN_SCORE // 2 or value < -WIN_SCORE // 2:
                break
    except TimeoutError:
        pass

    return (best_move // 4, best_move % 4)
