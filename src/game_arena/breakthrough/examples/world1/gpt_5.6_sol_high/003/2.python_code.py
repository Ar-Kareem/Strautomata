
import time


# Board constants
ROW_0 = (1 << 8) - 1
ROW_1 = ROW_0 << 8
ROW_6 = ROW_0 << 48
ROW_7 = ROW_0 << 56
FULL_BOARD = (1 << 64) - 1

INF = 2_000_000
MATE = 1_000_000

ADVANCE_VALUE = (0, 4, 10, 20, 36, 60, 100, 0)
PASSED_VALUE = (0, 3, 8, 17, 36, 78, 170, 0)
CENTER_VALUE = (0, 3, 6, 9, 9, 6, 3, 0)

# PASS_MASK_UP[sq] contains squares ahead in the same or adjacent files.
PASS_MASK_UP = [0] * 64
PASS_MASK_DOWN = [0] * 64

for _sq in range(64):
    _r, _c = divmod(_sq, 8)

    _up = 0
    for _rr in range(_r + 1, 8):
        for _cc in range(max(0, _c - 1), min(7, _c + 1) + 1):
            _up |= 1 << (_rr * 8 + _cc)
    PASS_MASK_UP[_sq] = _up

    _down = 0
    for _rr in range(0, _r):
        for _cc in range(max(0, _c - 1), min(7, _c + 1) + 1):
            _down |= 1 << (_rr * 8 + _cc)
    PASS_MASK_DOWN[_sq] = _down


class _SearchTimeout(Exception):
    pass


_tt = {}
_history = [0] * 4096
_killers = [[-1, -1] for _ in range(80)]
_deadline = 0.0
_nodes = 0


def _progress(square, direction):
    row = square >> 3
    return row if direction == 1 else 7 - row


def _goal_mask(direction):
    return ROW_7 if direction == 1 else ROW_0


def _passed_mask(square, direction):
    return PASS_MASK_UP[square] if direction == 1 else PASS_MASK_DOWN[square]


def _protected(friends, square, direction):
    """Whether a friendly piece can recapture an attacker on square."""
    row, col = divmod(square, 8)
    source_row = row - direction
    if not (0 <= source_row < 8):
        return False

    if col > 0 and (friends & (1 << (source_row * 8 + col - 1))):
        return True
    if col < 7 and (friends & (1 << (source_row * 8 + col + 1))):
        return True
    return False


def _generate_moves(me, opp, direction):
    occupied = me | opp
    moves = []
    pieces = me
    step = 8 if direction == 1 else -8

    while pieces:
        source_bit = pieces & -pieces
        source = source_bit.bit_length() - 1
        pieces ^= source_bit

        row, col = divmod(source, 8)
        target_row = row + direction
        if not (0 <= target_row < 8):
            continue

        # Straight movement requires an empty destination.
        target = source + step
        target_bit = 1 << target
        if not (occupied & target_bit):
            moves.append((source << 6) | target)

        # Diagonal movement is legal onto empty or opponent-occupied squares.
        if col > 0:
            target = source + step - 1
            if not (me & (1 << target)):
                moves.append((source << 6) | target)

        if col < 7:
            target = source + step + 1
            if not (me & (1 << target)):
                moves.append((source << 6) | target)

    return moves


def _winning_move(me, opp, direction):
    """Return an immediate goal-row move, or -1 if none exists."""
    occupied = me | opp

    if direction == 1:
        candidates = me & ROW_6
        step = 8
    else:
        candidates = me & ROW_1
        step = -8

    while candidates:
        source_bit = candidates & -candidates
        source = source_bit.bit_length() - 1
        candidates ^= source_bit
        col = source & 7

        target = source + step
        if not (occupied & (1 << target)):
            return (source << 6) | target

        if col > 0:
            target = source + step - 1
            if not (me & (1 << target)):
                return (source << 6) | target

        if col < 7:
            target = source + step + 1
            if not (me & (1 << target)):
                return (source << 6) | target

    return -1


def _apply_move(me, opp, move):
    source = move >> 6
    target = move & 63
    source_bit = 1 << source
    target_bit = 1 << target

    new_me = (me ^ source_bit) | target_bit
    new_opp = opp & ~target_bit
    return new_me, new_opp


def _side_features(friends, enemies, direction):
    occupied = friends | enemies
    score = 0
    pieces = friends

    while pieces:
        piece_bit = pieces & -pieces
        square = piece_bit.bit_length() - 1
        pieces ^= piece_bit

        row, col = divmod(square, 8)
        progress = row if direction == 1 else 7 - row

        score += 100
        score += ADVANCE_VALUE[progress]
        score += CENTER_VALUE[col] * (1 + progress // 4)

        is_protected = _protected(friends, square, direction)
        if is_protected:
            score += 11 + 2 * progress

        # Connected pieces are generally harder to isolate.
        if col > 0 and (friends & (1 << (square - 1))):
            score += 3
        if col < 7 and (friends & (1 << (square + 1))):
            score += 3

        # Passed pieces are especially dangerous in Breakthrough.
        if not (enemies & _passed_mask(square, direction)):
            score += PASSED_VALUE[progress]

        # An enemy that protects this square can capture this piece next turn.
        attacked = _protected(enemies, square, -direction)
        if attacked:
            danger = 11 + 4 * progress
            score -= danger if is_protected else 3 * danger

        target_row = row + direction
        mobility = 0
        if 0 <= target_row < 8:
            straight = square + 8 * direction
            if not (occupied & (1 << straight)):
                mobility += 1

            if col > 0:
                diagonal = straight - 1
                if not (friends & (1 << diagonal)):
                    mobility += 1

            if col < 7:
                diagonal = straight + 1
                if not (friends & (1 << diagonal)):
                    mobility += 1

        score += 2 * mobility

        # A piece one move from the goal is a forcing tactical threat.
        if progress == 6 and mobility:
            score += 360

    return score


def _evaluate(me, opp, direction):
    # A small tempo bonus helps distinguish otherwise symmetric races.
    return (
        _side_features(me, opp, direction)
        - _side_features(opp, me, -direction)
        + 7
    )


def _move_score(me, opp, direction, move, tt_move, ply):
    if move == tt_move:
        return 20_000_000

    source = move >> 6
    target = move & 63
    target_bit = 1 << target
    capture = bool(opp & target_bit)
    progress = _progress(target, direction)

    score = _history[move]
    score += progress * 700
    score += CENTER_VALUE[target & 7] * 20

    if progress == 7:
        score += 10_000_000

    if capture:
        victim_progress = _progress(target, -direction)
        score += 120_000 + victim_progress * 4_000
        if opp.bit_count() == 1:
            score += 9_000_000
    elif ply < len(_killers):
        if move == _killers[ply][0]:
            score += 18_000
        elif move == _killers[ply][1]:
            score += 12_000

    new_me, new_opp = _apply_move(me, opp, move)

    if _protected(new_me, target, direction):
        score += 2_800

    if _protected(new_opp, target, -direction):
        if _protected(new_me, target, direction):
            score -= 700
        else:
            score -= 2_800

    if not (new_opp & _passed_mask(target, direction)):
        score += 700 + progress * 450

    if progress == 6:
        score += 35_000

    return score


def _ordered_moves(me, opp, direction, moves, tt_move, ply):
    moves.sort(
        key=lambda mv: _move_score(me, opp, direction, mv, tt_move, ply),
        reverse=True,
    )
    return moves


def _check_time():
    if time.perf_counter() >= _deadline:
        raise _SearchTimeout


def _search(me, opp, direction, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0:
        _check_time()

    my_goal = _goal_mask(direction)
    opp_goal = _goal_mask(-direction)

    if not opp or (me & my_goal):
        return MATE - ply
    if not me or (opp & opp_goal):
        return -MATE + ply

    immediate = _winning_move(me, opp, direction)
    if immediate != -1:
        return MATE - ply - 1

    key = (me, opp, direction)
    entry = _tt.get(key)
    tt_move = -1

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1 and stored_value >= beta:
                return stored_value
            if flag == 2 and stored_value <= alpha:
                return stored_value

    if depth <= 0:
        return _evaluate(me, opp, direction)

    alpha_original = alpha
    beta_original = beta

    moves = _generate_moves(me, opp, direction)
    if not moves:
        return -MATE + ply

    _ordered_moves(me, opp, direction, moves, tt_move, ply)

    best_value = -INF
    best_move = moves[0]
    first = True

    for index, move in enumerate(moves):
        new_me, new_opp = _apply_move(me, opp, move)
        child_depth = depth - 1
        target = move & 63
        quiet = not bool(opp & (1 << target))

        if first:
            value = -_search(
                new_opp, new_me, -direction,
                child_depth, -beta, -alpha, ply + 1
            )
            first = False
        else:
            # Reduce late, non-tactical moves, but verify any promising result.
            can_reduce = (
                depth >= 4
                and index >= 8
                and quiet
                and _progress(target, direction) < 5
            )

            if can_reduce:
                value = -_search(
                    new_opp, new_me, -direction,
                    child_depth - 1, -alpha - 1, -alpha, ply + 1
                )
                if value > alpha:
                    value = -_search(
                        new_opp, new_me, -direction,
                        child_depth, -alpha - 1, -alpha, ply + 1
                    )
            else:
                value = -_search(
                    new_opp, new_me, -direction,
                    child_depth, -alpha - 1, -alpha, ply + 1
                )

            if alpha < value < beta:
                value = -_search(
                    new_opp, new_me, -direction,
                    child_depth, -beta, -alpha, ply + 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if quiet:
                _history[move] += depth * depth
                if ply < len(_killers) and move != _killers[ply][0]:
                    _killers[ply][1] = _killers[ply][0]
                    _killers[ply][0] = move
            break

    if best_value <= alpha_original:
        flag = 2  # Upper bound
    elif best_value >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _tt[key] = (depth, best_value, flag, best_move)
    return best_value


def _search_root(me, opp, direction, moves, depth, previous_best):
    _check_time()

    ordered = list(moves)
    _ordered_moves(me, opp, direction, ordered, previous_best, 0)

    alpha = -INF
    best_value = -INF
    best_move = ordered[0]

    for move in ordered:
        _check_time()
        new_me, new_opp = _apply_move(me, opp, move)

        value = -_search(
            new_opp, new_me, -direction,
            depth - 1, -INF, -alpha, 1
        )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_value, best_move


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _tt, _history, _killers, _deadline, _nodes

    direction = -1 if color.lower() == "b" else 1

    my_bits = 0
    for row, col in me:
        my_bits |= 1 << (row * 8 + col)

    opp_bits = 0
    for row, col in opp:
        opp_bits |= 1 << (row * 8 + col)

    _tt = {}
    _history = [0] * 4096
    _killers = [[-1, -1] for _ in range(80)]
    _nodes = 0
    _deadline = time.perf_counter() + 0.90

    legal_moves = _generate_moves(my_bits, opp_bits, direction)

    # A policy is only called in a playable state. This branch is defensive.
    if not legal_moves:
        return ((0, 0), (0, 0))

    # Take an immediate goal-row win without spending search time.
    immediate = _winning_move(my_bits, opp_bits, direction)
    if immediate != -1:
        source = immediate >> 6
        target = immediate & 63
        return (divmod(source, 8), divmod(target, 8))

    # Capturing the final opposing piece also wins immediately.
    if opp_bits.bit_count() == 1:
        for move in legal_moves:
            target = move & 63
            if opp_bits & (1 << target):
                source = move >> 6
                return (divmod(source, 8), divmod(target, 8))

    # Establish a strategically ordered legal fallback before timed search.
    fallback_moves = list(legal_moves)
    _ordered_moves(my_bits, opp_bits, direction, fallback_moves, -1, 0)
    best_move = fallback_moves[0]
    previous_best = best_move

    # Iterative deepening means only fully completed depths replace the move.
    for depth in range(1, 21):
        try:
            value, candidate = _search_root(
                my_bits, opp_bits, direction,
                legal_moves, depth, previous_best
            )
        except _SearchTimeout:
            break

        best_move = candidate
        previous_best = candidate

        # A proven forced result needs no deeper search.
        if abs(value) >= MATE - 100:
            break

    source = best_move >> 6
    target = best_move & 63
    return (divmod(source, 8), divmod(target, 8))
