
import time

_INF = 10**9
_WIN = 10**7

# Direction order:
# 0 = down-left, 1 = down-right, 2 = up-left, 3 = up-right
_DIR_DELTAS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_DOWN_DIRS = (0, 1)
_UP_DIRS = (2, 3)
_ALL_DIRS = (0, 1, 2, 3)

_ROWS = [i // 8 for i in range(64)]
_COLS = [i % 8 for i in range(64)]
_BITS = [1 << i for i in range(64)]

_STEP = [[-1] * 4 for _ in range(64)]
_JUMP_MID = [[-1] * 4 for _ in range(64)]
_JUMP_LAND = [[-1] * 4 for _ in range(64)]

for i in range(64):
    r, c = _ROWS[i], _COLS[i]
    for d, (dr, dc) in enumerate(_DIR_DELTAS):
        r1, c1 = r + dr, c + dc
        r2, c2 = r + 2 * dr, c + 2 * dc
        if 0 <= r1 < 8 and 0 <= c1 < 8:
            _STEP[i][d] = r1 * 8 + c1
        if 0 <= r2 < 8 and 0 <= c2 < 8:
            _JUMP_MID[i][d] = r1 * 8 + c1
            _JUMP_LAND[i][d] = r2 * 8 + c2

_ADV_BLACK = tuple(7 - _ROWS[i] for i in range(64))
_ADV_WHITE = tuple(_ROWS[i] for i in range(64))

_CENTER_MAN = []
_CENTER_KING = []
_EDGE_BONUS = []
for i in range(64):
    r, c = _ROWS[i], _COLS[i]
    if 2 <= r <= 5 and 2 <= c <= 5:
        _CENTER_MAN.append(6)
        _CENTER_KING.append(8)
    elif 1 <= r <= 6 and 1 <= c <= 6:
        _CENTER_MAN.append(2)
        _CENTER_KING.append(3)
    else:
        _CENTER_MAN.append(0)
        _CENTER_KING.append(0)
    _EDGE_BONUS.append(3 if c == 0 or c == 7 else 0)

# Globals configured per call.
_MY_MEN_DIRS = _DOWN_DIRS
_OPP_MEN_DIRS = _UP_DIRS
_MY_KING_ROW = 0
_OPP_KING_ROW = 7
_MY_HOME_ROW = 7
_OPP_HOME_ROW = 0
_MY_ADV = _ADV_BLACK
_OPP_ADV = _ADV_WHITE

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _make_mask(squares):
    mask = 0
    for r, c in squares:
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= 1 << (r * 8 + c)
    return mask


def _gen_captures(state, side):
    mm, mk, om, ok = state
    occ = mm | mk | om | ok

    if side == 1:
        men = mm
        kings = mk
        enemy = om | ok
        man_dirs = _MY_MEN_DIRS
    else:
        men = om
        kings = ok
        enemy = mm | mk
        man_dirs = _OPP_MEN_DIRS

    captures = []

    b = men
    while b:
        lsb = b & -b
        fr = lsb.bit_length() - 1
        b ^= lsb

        for d in man_dirs:
            land = _JUMP_LAND[fr][d]
            if land != -1:
                mid = _JUMP_MID[fr][d]
                if (enemy & _BITS[mid]) and not (occ & _BITS[land]):
                    captures.append((fr, land, mid))

    b = kings
    while b:
        lsb = b & -b
        fr = lsb.bit_length() - 1
        b ^= lsb

        for d in _ALL_DIRS:
            land = _JUMP_LAND[fr][d]
            if land != -1:
                mid = _JUMP_MID[fr][d]
                if (enemy & _BITS[mid]) and not (occ & _BITS[land]):
                    captures.append((fr, land, mid))

    return captures


def _gen_quiets(state, side):
    mm, mk, om, ok = state
    occ = mm | mk | om | ok

    if side == 1:
        men = mm
        kings = mk
        man_dirs = _MY_MEN_DIRS
    else:
        men = om
        kings = ok
        man_dirs = _OPP_MEN_DIRS

    moves = []

    b = men
    while b:
        lsb = b & -b
        fr = lsb.bit_length() - 1
        b ^= lsb

        for d in man_dirs:
            to = _STEP[fr][d]
            if to != -1 and not (occ & _BITS[to]):
                moves.append((fr, to, -1))

    b = kings
    while b:
        lsb = b & -b
        fr = lsb.bit_length() - 1
        b ^= lsb

        for d in _ALL_DIRS:
            to = _STEP[fr][d]
            if to != -1 and not (occ & _BITS[to]):
                moves.append((fr, to, -1))

    return moves


def _gen_legal(state, side):
    captures = _gen_captures(state, side)
    if captures:
        return captures
    return _gen_quiets(state, side)


def _apply_move(state, move, side):
    mm, mk, om, ok = state
    fr, to, cap = move
    fb = _BITS[fr]
    tb = _BITS[to]

    if side == 1:
        if mm & fb:
            mm &= ~fb
            if _ROWS[to] == _MY_KING_ROW:
                mk |= tb
            else:
                mm |= tb
        else:
            mk &= ~fb
            mk |= tb

        if cap != -1:
            cb = _BITS[cap]
            if om & cb:
                om &= ~cb
            else:
                ok &= ~cb

    else:
        if om & fb:
            om &= ~fb
            if _ROWS[to] == _OPP_KING_ROW:
                ok |= tb
            else:
                om |= tb
        else:
            ok &= ~fb
            ok |= tb

        if cap != -1:
            cb = _BITS[cap]
            if mm & cb:
                mm &= ~cb
            else:
                mk &= ~cb

    return (mm, mk, om, ok)


def _evaluate(state):
    mm, mk, om, ok = state

    my_piece_count = (mm | mk).bit_count()
    opp_piece_count = (om | ok).bit_count()

    if my_piece_count == 0:
        return -_WIN // 2
    if opp_piece_count == 0:
        return _WIN // 2

    my_men_n = mm.bit_count()
    my_king_n = mk.bit_count()
    opp_men_n = om.bit_count()
    opp_king_n = ok.bit_count()

    total = my_piece_count + opp_piece_count
    king_value = 176 + max(0, 12 - total) * 3

    score = 0

    b = mm
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        adv = _MY_ADV[i]
        val = 100 + adv * 7 + _CENTER_MAN[i] + _EDGE_BONUS[i]
        if adv >= 6:
            val += 22
        elif adv >= 5:
            val += 9
        if opp_king_n == 0 and _ROWS[i] == _MY_HOME_ROW:
            val += 6
        score += val

    b = om
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        adv = _OPP_ADV[i]
        val = 100 + adv * 7 + _CENTER_MAN[i] + _EDGE_BONUS[i]
        if adv >= 6:
            val += 22
        elif adv >= 5:
            val += 9
        if my_king_n == 0 and _ROWS[i] == _OPP_HOME_ROW:
            val += 6
        score -= val

    b = mk
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        score += king_value + _CENTER_KING[i] + _EDGE_BONUS[i]

    b = ok
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        score -= king_value + _CENTER_KING[i] + _EDGE_BONUS[i]

    material_diff = 100 * (my_men_n - opp_men_n) + king_value * (my_king_n - opp_king_n)

    # When ahead, simplification is good; when behind, keeping material on board is better.
    simplification = min(60, max(0, 24 - total) * 3)
    if material_diff > 120:
        score += simplification
    elif material_diff < -120:
        score -= simplification

    return score


def _victim_value(state, move, side):
    cap = move[2]
    if cap == -1:
        return 0
    cb = _BITS[cap]
    mm, mk, om, ok = state
    if side == 1:
        return 190 if (ok & cb) else 100
    return 190 if (mk & cb) else 100


def _move_score(state, move, side, ttmove=None):
    if ttmove is not None and move == ttmove:
        return 1_000_000

    mm, mk, om, ok = state
    fr, to, cap = move
    fb = _BITS[fr]

    if side == 1:
        mover_king = bool(mk & fb)
        crown = _MY_KING_ROW
        adv_table = _MY_ADV
    else:
        mover_king = bool(ok & fb)
        crown = _OPP_KING_ROW
        adv_table = _OPP_ADV

    score = 0

    if cap != -1:
        attacker = 175 if mover_king else 100
        victim = _victim_value(state, move, side)
        score += 10_000 + victim * 8 - attacker
    else:
        score += _CENTER_MAN[to] * 3 + _EDGE_BONUS[to]

    if not mover_king:
        score += (adv_table[to] - adv_table[fr]) * 12
        if _ROWS[to] == crown:
            score += 5_000 if cap != -1 else 1_200
    else:
        score += _CENTER_KING[to] * 2

    return score


def _ordered_moves(state, moves, side, ttmove=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: _move_score(state, m, side, ttmove), reverse=True)


# Transposition table flags.
_EXACT = 0
_LOWER = 1
_UPPER = 2


def _negamax(state, depth, alpha, beta, side, qleft, ply):
    _check_time()

    alpha_orig = alpha
    beta_orig = beta

    key = (state, side)
    entry = _TT.get(key)
    ttmove = None
    if entry is not None:
        ent_depth, ent_qleft, ent_flag, ent_value, ent_move = entry
        ttmove = ent_move
        if ent_depth >= depth and ent_qleft >= qleft:
            if ent_flag == _EXACT:
                return ent_value
            if ent_flag == _LOWER:
                alpha = max(alpha, ent_value)
            elif ent_flag == _UPPER:
                beta = min(beta, ent_value)
            if alpha >= beta:
                return ent_value

    moves = _gen_legal(state, side)
    if not moves:
        return -_WIN + ply

    capture_phase = moves[0][2] != -1
    if depth <= 0 and not (capture_phase and qleft > 0):
        return _evaluate(state) * side

    if depth > 0:
        next_depth = depth - 1
        next_qleft = qleft
    else:
        next_depth = 0
        next_qleft = qleft - 1

    best_value = -_INF
    best_move = moves[0]

    for move in _ordered_moves(state, moves, side, ttmove):
        child = _apply_move(state, move, side)
        value = -_negamax(child, next_depth, -beta, -alpha, -side, next_qleft, ply + 1)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= alpha_orig:
        flag = _UPPER
    elif best_value >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (depth, qleft, flag, best_value, best_move)
    return best_value


def _root_heuristic_choice(state, moves):
    best = moves[0]
    best_score = -_INF

    for move in moves:
        child = _apply_move(state, move, 1)
        score = _evaluate(child) + _move_score(state, move, 1) // 12

        # Immediate win by blocking all opponent moves.
        if not _gen_legal(child, -1):
            score += _WIN // 4

        if score > best_score:
            best_score = score
            best = move

    return best


def _move_to_coords(move):
    fr, to, _ = move
    return ((_ROWS[fr], _COLS[fr]), (_ROWS[to], _COLS[to]))


def _emergency_fallback(my_men, my_kings, opp_men, opp_kings, color):
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)

    man_dirs = ((-1, -1), (-1, 1)) if color == "b" else ((1, -1), (1, 1))
    king_dirs = ((-1, -1), (-1, 1), (1, -1), (1, 1))

    for r, c in my_men:
        for dr, dc in man_dirs:
            to = (r + dr, c + dc)
            if 0 <= to[0] < 8 and 0 <= to[1] < 8 and to not in occupied:
                return ((r, c), to)

    for r, c in my_kings:
        for dr, dc in king_dirs:
            to = (r + dr, c + dc)
            if 0 <= to[0] < 8 and 0 <= to[1] < 8 and to not in occupied:
                return ((r, c), to)

    pieces = list(my_men) + list(my_kings)
    if pieces:
        return (tuple(pieces[0]), tuple(pieces[0]))
    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _MY_MEN_DIRS, _OPP_MEN_DIRS
    global _MY_KING_ROW, _OPP_KING_ROW, _MY_HOME_ROW, _OPP_HOME_ROW
    global _MY_ADV, _OPP_ADV
    global _TT, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0
    _TT = {}

    if color == "b":
        _MY_MEN_DIRS = _DOWN_DIRS
        _OPP_MEN_DIRS = _UP_DIRS
        _MY_KING_ROW = 0
        _OPP_KING_ROW = 7
        _MY_HOME_ROW = 7
        _OPP_HOME_ROW = 0
        _MY_ADV = _ADV_BLACK
        _OPP_ADV = _ADV_WHITE
    else:
        _MY_MEN_DIRS = _UP_DIRS
        _OPP_MEN_DIRS = _DOWN_DIRS
        _MY_KING_ROW = 7
        _OPP_KING_ROW = 0
        _MY_HOME_ROW = 0
        _OPP_HOME_ROW = 7
        _MY_ADV = _ADV_WHITE
        _OPP_ADV = _ADV_BLACK

    state = (
        _make_mask(my_men),
        _make_mask(my_kings),
        _make_mask(opp_men),
        _make_mask(opp_kings),
    )

    root_moves = _gen_legal(state, 1)
    if not root_moves:
        return _emergency_fallback(my_men, my_kings, opp_men, opp_kings, color)

    if len(root_moves) == 1:
        return _move_to_coords(root_moves[0])

    root_moves = _ordered_moves(state, root_moves, 1)
    best_move = _root_heuristic_choice(state, root_moves)

    total_pieces = (state[0] | state[1] | state[2] | state[3]).bit_count()
    if total_pieces <= 6:
        max_depth = 12
    elif total_pieces <= 10:
        max_depth = 10
    elif total_pieces <= 16:
        max_depth = 8
    else:
        max_depth = 7

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break

            alpha = -_INF
            beta = _INF
            current_best = best_move
            current_best_value = -_INF

            ordered = _ordered_moves(state, root_moves, 1, best_move)

            for move in ordered:
                child = _apply_move(state, move, 1)
                value = -_negamax(child, depth - 1, -beta, -alpha, -1, 4, 1)

                if value > current_best_value:
                    current_best_value = value
                    current_best = move

                if value > alpha:
                    alpha = value

            best_move = current_best

            # No need to spend more time if a forced win is already found.
            if current_best_value > _WIN // 2:
                break

    except _SearchTimeout:
        pass

    return _move_to_coords(best_move)
