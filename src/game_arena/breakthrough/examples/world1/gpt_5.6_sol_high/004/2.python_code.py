
import time

# Board and search constants
_ALL = (1 << 64) - 1
_ROWS = [0xFF << (8 * r) for r in range(8)]
_MATE = 1_000_000
_MATE_BOUND = 900_000
_INF = 2_000_000

# Side indices: 0 = black, 1 = white
_DIR = (-1, 1)
_GOAL_ROW = (0, 7)
_PENULT_ROW = (1, 6)

# Positional values indexed by progress toward the goal.
_ADVANCE_VALUE = (0, 3, 9, 18, 32, 56, 98, 0)
_PASSED_VALUE = (0, 4, 10, 23, 50, 108, 235, 0)

# Precomputed masks.
_SUPPORT = [[0] * 64 for _ in range(2)]
_ATTACKERS = [[0] * 64 for _ in range(2)]
_PASSED_MASK = [[0] * 64 for _ in range(2)]

for side in (0, 1):
    d = _DIR[side]
    for sq in range(64):
        r, c = divmod(sq, 8)

        # Friendly pieces which could have moved diagonally onto sq.
        origin_r = r - d
        mask = 0
        if 0 <= origin_r < 8:
            if c > 0:
                mask |= 1 << (origin_r * 8 + c - 1)
            if c < 7:
                mask |= 1 << (origin_r * 8 + c + 1)
        _SUPPORT[side][sq] = mask

        # Enemy pieces in the forward three-file corridor.
        passed = 0
        rr = r + d
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    passed |= 1 << (rr * 8 + cc)
            rr += d
        _PASSED_MASK[side][sq] = passed

for side in (0, 1):
    for sq in range(64):
        _ATTACKERS[side][sq] = _SUPPORT[1 - side][sq]

# Persistent search data.
_TT = {}
_HISTORY = [[0] * 4096 for _ in range(2)]
_KILLERS = [[-1, -1] for _ in range(64)]
_generation = 0
_nodes = 0
_deadline = 0.0


class _SearchTimeout(Exception):
    pass


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout


def _encode_move(frm, to):
    return (frm << 6) | to


def _decode_move(move):
    return move >> 6, move & 63


def _generate_moves(white, black, side):
    own = white if side else black
    enemy = black if side else white
    occupied = own | enemy
    d = _DIR[side]

    moves = []
    pieces = own
    while pieces:
        lsb = pieces & -pieces
        frm = lsb.bit_length() - 1
        pieces ^= lsb

        r, c = divmod(frm, 8)
        nr = r + d
        if not (0 <= nr < 8):
            continue

        # Straight moves require an empty destination.
        to = nr * 8 + c
        if not (occupied & (1 << to)):
            moves.append(_encode_move(frm, to))

        # Diagonal moves are legal unless occupied by a friendly piece.
        if c > 0:
            to = nr * 8 + c - 1
            if not (own & (1 << to)):
                moves.append(_encode_move(frm, to))

        if c < 7:
            to = nr * 8 + c + 1
            if not (own & (1 << to)):
                moves.append(_encode_move(frm, to))

    return moves


def _apply_move(white, black, side, move):
    frm, to = _decode_move(move)
    fbit = 1 << frm
    tbit = 1 << to

    if side:
        white = (white ^ fbit) | tbit
        black &= ~tbit
    else:
        black = (black ^ fbit) | tbit
        white &= ~tbit

    return white, black


def _terminal_score(white, black, side):
    if not black or (white & _ROWS[7]):
        return _MATE if side == 1 else -_MATE
    if not white or (black & _ROWS[0]):
        return _MATE if side == 0 else -_MATE
    return None


def _immediate_winning_move(white, black, side):
    own = white if side else black
    enemy = black if side else white
    occupied = own | enemy
    d = _DIR[side]
    penult = _ROWS[_PENULT_ROW[side]]

    # Promotion moves.
    pieces = own & penult
    while pieces:
        lsb = pieces & -pieces
        frm = lsb.bit_length() - 1
        pieces ^= lsb

        r, c = divmod(frm, 8)
        nr = r + d

        to = nr * 8 + c
        if not (occupied & (1 << to)):
            return _encode_move(frm, to)

        if c > 0:
            to = nr * 8 + c - 1
            if not (own & (1 << to)):
                return _encode_move(frm, to)

        if c < 7:
            to = nr * 8 + c + 1
            if not (own & (1 << to)):
                return _encode_move(frm, to)

    # Capturing the final enemy piece also wins immediately.
    if enemy and not (enemy & (enemy - 1)):
        target = enemy.bit_length() - 1
        tr, tc = divmod(target, 8)
        origin_r = tr - d

        if 0 <= origin_r < 8:
            if tc > 0:
                frm = origin_r * 8 + tc - 1
                if own & (1 << frm):
                    return _encode_move(frm, target)
            if tc < 7:
                frm = origin_r * 8 + tc + 1
                if own & (1 << frm):
                    return _encode_move(frm, target)

    return -1


def _piece_score(own, enemy, side):
    score = 0
    occupied = own | enemy
    d = _DIR[side]

    pieces = own
    while pieces:
        lsb = pieces & -pieces
        sq = lsb.bit_length() - 1
        pieces ^= lsb

        r, c = divmod(sq, 8)
        progress = r if side else 7 - r

        score += 100 + _ADVANCE_VALUE[progress]

        # Slight central preference without discouraging useful edge pawns.
        if 2 <= c <= 5:
            score += 2

        supporters = (own & _SUPPORT[side][sq]).bit_count()
        attackers = (enemy & _ATTACKERS[side][sq]).bit_count()

        if supporters:
            score += 10 + 3 * progress + 4 * min(supporters, 2)

        if attackers:
            score -= 17 + 4 * progress
            if not supporters:
                score -= 27 + 6 * progress
            elif attackers > supporters:
                score -= 9

        # Count horizontal connections once.
        if c > 0 and (own & (1 << (sq - 1))):
            score += 6

        if not (enemy & _PASSED_MASK[side][sq]):
            score += _PASSED_VALUE[progress]

        nr = r + d
        mobility = 0
        if 0 <= nr < 8:
            to = nr * 8 + c
            if not (occupied & (1 << to)):
                mobility += 1

            if c > 0:
                to = nr * 8 + c - 1
                if not (own & (1 << to)):
                    mobility += 1

            if c < 7:
                to = nr * 8 + c + 1
                if not (own & (1 << to)):
                    mobility += 1

        score += mobility

        # A legal promotion on the following move is a major threat.
        if progress == 6 and mobility:
            score += 500 + 20 * min(mobility, 2)

    return score


def _evaluate(white, black, side):
    value = _piece_score(white, black, 1) - _piece_score(black, white, 0)
    if not side:
        value = -value

    # Tempo matters significantly in pawn races.
    return value + 8


def _back_up(child_score):
    score = -child_score
    if score > _MATE_BOUND:
        score -= 1
    elif score < -_MATE_BOUND:
        score += 1
    return score


def _move_order_score(white, black, side, move, tt_move, ply):
    frm, to = _decode_move(move)
    own = white if side else black
    enemy = black if side else white
    tbit = 1 << to
    fbit = 1 << frm

    score = _HISTORY[side][move]

    if move == tt_move:
        score += 2_000_000

    to_row, to_col = divmod(to, 8)
    progress = to_row if side else 7 - to_row

    if to_row == _GOAL_ROW[side]:
        score += 1_500_000

    if enemy & tbit:
        score += 120_000 + 500 * progress

    if progress == 6:
        score += 12_000
    elif progress >= 4:
        score += 700 * progress

    own_without_from = own & ~fbit
    if own_without_from & _SUPPORT[side][to]:
        score += 420 + 25 * progress

    if enemy & _ATTACKERS[side][to]:
        score -= 260 + 20 * progress

    if not (enemy & _PASSED_MASK[side][to]):
        score += 90 * progress

    if 2 <= to_col <= 5:
        score += 8

    if ply < len(_KILLERS):
        if move == _KILLERS[ply][0]:
            score += 70_000
        elif move == _KILLERS[ply][1]:
            score += 60_000

    return score


def _ordered_moves(white, black, side, moves, tt_move=-1, ply=0):
    moves.sort(
        key=lambda mv: _move_order_score(
            white, black, side, mv, tt_move, ply
        ),
        reverse=True,
    )
    return moves


def _is_reducible(white, black, side, move):
    _, to = _decode_move(move)
    enemy = black if side else white

    if enemy & (1 << to):
        return False

    to_row = to >> 3
    progress = to_row if side else 7 - to_row
    return progress < 5


def _qsearch(white, black, side, alpha, beta, qdepth, ply, checked=False):
    _check_time()

    terminal = _terminal_score(white, black, side)
    if terminal is not None:
        return terminal

    if not checked and _immediate_winning_move(white, black, side) >= 0:
        return _MATE - 1

    stand_pat = _evaluate(white, black, side)
    if stand_pat >= beta:
        return stand_pat
    if stand_pat > alpha:
        alpha = stand_pat

    if qdepth <= 0:
        return stand_pat

    enemy = black if side else white
    all_moves = _generate_moves(white, black, side)
    tactical = []

    for move in all_moves:
        _, to = _decode_move(move)
        to_row = to >> 3
        progress = to_row if side else 7 - to_row

        if (enemy & (1 << to)) or progress >= 6:
            tactical.append(move)

    if not tactical:
        return stand_pat

    _ordered_moves(white, black, side, tactical, -1, ply)

    for move in tactical:
        nw, nb = _apply_move(white, black, side, move)
        child = _qsearch(nw, nb, 1 - side, -beta, -alpha, qdepth - 1, ply + 1)
        score = _back_up(child)

        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def _record_cutoff(side, move, depth, ply, is_quiet):
    if not is_quiet:
        return

    bonus = depth * depth + 2 * depth
    new_value = _HISTORY[side][move] + bonus
    _HISTORY[side][move] = min(new_value, 200_000)

    if ply < len(_KILLERS) and move != _KILLERS[ply][0]:
        _KILLERS[ply][1] = _KILLERS[ply][0]
        _KILLERS[ply][0] = move


def _search(white, black, side, depth, alpha, beta, ply):
    global _TT

    _check_time()

    terminal = _terminal_score(white, black, side)
    if terminal is not None:
        return terminal

    immediate = _immediate_winning_move(white, black, side)
    if immediate >= 0:
        return _MATE - 1

    if depth <= 0:
        return _qsearch(white, black, side, alpha, beta, 1, ply, checked=True)

    key = (white, black, side)
    entry = _TT.get(key)
    tt_move = -1
    alpha_original = alpha
    beta_original = beta

    if entry is not None:
        entry_depth, entry_score, flag, tt_move, _ = entry
        if entry_depth >= depth:
            if flag == 0:
                return entry_score
            if flag == 1:
                if entry_score > alpha:
                    alpha = entry_score
            else:
                if entry_score < beta:
                    beta = entry_score
            if alpha >= beta:
                return entry_score

    moves = _generate_moves(white, black, side)
    if not moves:
        return -_MATE

    _ordered_moves(white, black, side, moves, tt_move, ply)

    best_score = -_INF
    best_move = moves[0]
    enemy = black if side else white

    for index, move in enumerate(moves):
        nw, nb = _apply_move(white, black, side, move)
        normal_depth = depth - 1

        reducible = (
            depth >= 3
            and index >= 5
            and move != tt_move
            and _is_reducible(white, black, side, move)
        )

        if index == 0:
            child = _search(
                nw, nb, 1 - side, normal_depth, -beta, -alpha, ply + 1
            )
            score = _back_up(child)
        elif reducible:
            reduction = 2 if depth >= 6 and index >= 12 else 1
            reduced_depth = max(0, normal_depth - reduction)

            child = _search(
                nw, nb, 1 - side, reduced_depth, -alpha - 1, -alpha, ply + 1
            )
            score = _back_up(child)

            if score > alpha:
                child = _search(
                    nw, nb, 1 - side, normal_depth, -alpha - 1, -alpha, ply + 1
                )
                score = _back_up(child)

                if score > alpha and score < beta:
                    child = _search(
                        nw, nb, 1 - side, normal_depth, -beta, -alpha, ply + 1
                    )
                    score = _back_up(child)
        else:
            child = _search(
                nw, nb, 1 - side, normal_depth, -alpha - 1, -alpha, ply + 1
            )
            score = _back_up(child)

            if score > alpha and score < beta:
                child = _search(
                    nw, nb, 1 - side, normal_depth, -beta, -alpha, ply + 1
                )
                score = _back_up(child)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            is_quiet = not (enemy & (1 << (move & 63)))
            _record_cutoff(side, move, depth, ply, is_quiet)
            break

    if best_score <= alpha_original:
        flag = 2  # Upper bound
    elif best_score >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    old = _TT.get(key)
    if old is None or depth >= old[0] or old[4] != _generation:
        _TT[key] = (depth, best_score, flag, best_move, _generation)

    return best_score


def _root_search(white, black, side, depth):
    key = (white, black, side)
    entry = _TT.get(key)
    tt_move = entry[3] if entry is not None else -1

    moves = _generate_moves(white, black, side)
    _ordered_moves(white, black, side, moves, tt_move, 0)

    alpha = -_INF
    beta = _INF
    best_score = -_INF
    best_move = moves[0]

    for index, move in enumerate(moves):
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        nw, nb = _apply_move(white, black, side, move)
        normal_depth = depth - 1

        reducible = (
            depth >= 4
            and index >= 6
            and move != tt_move
            and _is_reducible(white, black, side, move)
        )

        if index == 0:
            child = _search(
                nw, nb, 1 - side, normal_depth, -beta, -alpha, 1
            )
            score = _back_up(child)
        elif reducible:
            reduction = 2 if depth >= 7 and index >= 14 else 1
            reduced_depth = max(0, normal_depth - reduction)

            child = _search(
                nw, nb, 1 - side, reduced_depth, -alpha - 1, -alpha, 1
            )
            score = _back_up(child)

            if score > alpha:
                child = _search(
                    nw, nb, 1 - side, normal_depth, -alpha - 1, -alpha, 1
                )
                score = _back_up(child)

                if score > alpha:
                    child = _search(
                        nw, nb, 1 - side, normal_depth, -beta, -alpha, 1
                    )
                    score = _back_up(child)
        else:
            child = _search(
                nw, nb, 1 - side, normal_depth, -alpha - 1, -alpha, 1
            )
            score = _back_up(child)

            if score > alpha:
                child = _search(
                    nw, nb, 1 - side, normal_depth, -beta, -alpha, 1
                )
                score = _back_up(child)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    _TT[key] = (depth, best_score, 0, best_move, _generation)
    return best_score, best_move


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _generation, _nodes, _deadline, _TT

    my_bits = 0
    for r, c in me:
        my_bits |= 1 << (r * 8 + c)

    opp_bits = 0
    for r, c in opp:
        opp_bits |= 1 << (r * 8 + c)

    if color == "w":
        white, black, side = my_bits, opp_bits, 1
    else:
        white, black, side = opp_bits, my_bits, 0

    legal_moves = _generate_moves(white, black, side)

    # Active arena positions should always contain a legal move.
    if not legal_moves:
        return ((0, 0), (0, 0))

    immediate = _immediate_winning_move(white, black, side)
    if immediate >= 0:
        frm, to = _decode_move(immediate)
        return (divmod(frm, 8), divmod(to, 8))

    _generation += 1
    _nodes = 0
    _deadline = time.perf_counter() + 0.90

    if len(_TT) > 250_000:
        _TT.clear()

    root_entry = _TT.get((white, black, side))
    root_tt_move = root_entry[3] if root_entry is not None else -1
    _ordered_moves(white, black, side, legal_moves, root_tt_move, 0)

    # This remains legal even if the first search iteration times out.
    best_move = legal_moves[0]

    try:
        for depth in range(1, 21):
            score, move = _root_search(white, black, side, depth)
            best_move = move

            if score > _MATE_BOUND:
                break

            if time.perf_counter() >= _deadline:
                break
    except _SearchTimeout:
        pass

    frm, to = _decode_move(best_move)
    return (divmod(frm, 8), divmod(to, 8))
