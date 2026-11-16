
import time

_FULL = (1 << 64) - 1
_ROWS = [0xFF << (8 * r) for r in range(8)]
_FILE_A = 0x0101010101010101
_FILE_H = _FILE_A << 7
_NOT_A = _FULL ^ _FILE_A
_NOT_H = _FULL ^ _FILE_H
_BITS = [1 << s for s in range(64)]

# Direction index: 0 moves down; 1 moves up.
_GOAL = [_ROWS[0], _ROWS[7]]
_PENULT = [_ROWS[1], _ROWS[6]]
_PREPENULT = [_ROWS[2], _ROWS[5]]
_CRITICAL = [
    _ROWS[0] | _ROWS[1] | _ROWS[2],
    _ROWS[5] | _ROWS[6] | _ROWS[7],
]
_ADVANCED_W = _ROWS[3] | _ROWS[4] | _ROWS[5] | _ROWS[6]
_ADVANCED_B = _ROWS[1] | _ROWS[2] | _ROWS[3] | _ROWS[4]

_ATTACK = [[0] * 64 for _ in range(2)]
_DANGER = [[0] * 64 for _ in range(2)]
_AHEAD = [[0] * 64 for _ in range(2)]
_ORDER = [[0] * 64 for _ in range(2)]
_ORDER_ADV = [0, 16, 34, 65, 120, 230, 600, 10000]
_PASS_BONUS = [0, 0, 15, 40, 90, 180, 350, 0]

for direction in range(2):
    step = 1 if direction else -1
    for square in range(64):
        row, col = divmod(square, 8)
        nr = row + step
        if 0 <= nr < 8:
            for nc in (col - 1, col + 1):
                if 0 <= nc < 8:
                    _ATTACK[direction][square] |= 1 << (nr * 8 + nc)

        # Conservative interception cone for a pawn running straight.
        for rr in range(8):
            distance = (rr - row) * step
            if distance > 0:
                _AHEAD[direction][square] |= 1 << (rr * 8 + col)
                radius = (distance + 1) // 2
                for cc in range(max(0, col - radius),
                                min(7, col + radius) + 1):
                    _DANGER[direction][square] |= 1 << (rr * 8 + cc)

        advance = row if direction else 7 - row
        center = min(col, 7 - col)
        _ORDER[direction][square] = _ORDER_ADV[advance] + center * 3

_CENTER = sum(1 << (r * 8 + c)
              for r in range(8) for c in range(2, 6))

_MATE = 1_000_000
_MATE_BOUND = _MATE - 1000
_INF = 2_000_000


class _SearchTimeout(Exception):
    pass


def _attacks(pieces, up):
    if up:
        return (((pieces & _NOT_A) << 7) |
                ((pieces & _NOT_H) << 9)) & _FULL
    return ((pieces & _NOT_A) >> 9) | ((pieces & _NOT_H) >> 7)


def _moves(a, b, up, captures_only=False):
    if captures_only:
        allowed = b
        straight = 0
    else:
        allowed = _FULL ^ a
        empty = _FULL ^ (a | b)
        straight = ((a << 8) & empty) if up else ((a >> 8) & empty)

    if up:
        left = ((a & _NOT_A) << 7) & allowed
        right = ((a & _NOT_H) << 9) & allowed
        groups = ((straight, 8), (left, 7), (right, 9))
    else:
        left = ((a & _NOT_A) >> 9) & allowed
        right = ((a & _NOT_H) >> 7) & allowed
        groups = ((straight, -8), (left, -9), (right, -7))

    result = []
    for destinations, delta in groups:
        while destinations:
            bit = destinations & -destinations
            destinations ^= bit
            target = bit.bit_length() - 1
            result.append(((target - delta) << 6) | target)
    return result


def _safe_goal_threat(a, b, up):
    """Return a move creating an uncapturable promotion threat, or -1."""
    pawns = a & _PREPENULT[up]
    if not pawns:
        return -1

    safe = _FULL ^ (a | _attacks(b, not up))
    empty = _FULL ^ (a | b)

    if up:
        groups = (
            ((pawns << 8) & empty & safe, 8),
            (((pawns & _NOT_A) << 7) & safe, 7),
            (((pawns & _NOT_H) << 9) & safe, 9),
        )
    else:
        groups = (
            ((pawns >> 8) & empty & safe, -8),
            (((pawns & _NOT_A) >> 9) & safe, -9),
            (((pawns & _NOT_H) >> 7) & safe, -7),
        )

    for destinations, delta in groups:
        if destinations:
            target = (destinations & -destinations).bit_length() - 1
            return ((target - delta) << 6) | target
    return -1


def _tactics(a, b, up, ply):
    """Return (solved score, forced moves), with None for unknown."""
    if not a or (b & _GOAL[not up]):
        return -_MATE + ply, None
    if not b or (a & _GOAL[up]):
        return _MATE - ply, None

    # In a nonterminal position a penultimate-rank pawn can promote
    # diagonally, irrespective of enemy occupation of the goal rank.
    if a & _PENULT[up]:
        return _MATE - ply - 1, None

    if not (b & (b - 1)) and (_attacks(a, up) & b):
        return _MATE - ply - 1, None

    urgent = b & _PENULT[not up]
    if urgent:
        if urgent & (urgent - 1):
            return -_MATE + ply + 2, None

        target = urgent.bit_length() - 1
        sources = a & _ATTACK[not up][target]
        if not sources:
            return -_MATE + ply + 2, None

        forced = []
        while sources:
            bit = sources & -sources
            sources ^= bit
            source = bit.bit_length() - 1
            forced.append((source << 6) | target)
        return None, forced

    if _safe_goal_threat(a, b, up) >= 0:
        return _MATE - ply - 3, None
    return None, None


def _evaluate(a, b, up):
    if up:
        w, black = a, b
    else:
        w, black = b, a

    wa = _attacks(w, True)
    ba = _attacks(black, False)

    score = 110 * (w.bit_count() - black.bit_count())

    for row, weight in ((1, 4), (2, 10), (3, 21),
                        (4, 43), (5, 80), (6, 170)):
        score += weight * (
            (w & _ROWS[row]).bit_count()
            - (black & _ROWS[7 - row]).bit_count()
        )

    # Supported formations and exposure to capture.
    wh = w & ba & ~wa
    bh = black & wa & ~ba
    score += 24 * (bh.bit_count() - wh.bit_count())
    score += 18 * (
        (bh & (_ROWS[1] | _ROWS[2] | _ROWS[3])).bit_count()
        - (wh & (_ROWS[4] | _ROWS[5] | _ROWS[6])).bit_count()
    )
    score += 7 * (
        (w & wa).bit_count() - (black & ba).bit_count()
    )
    score += 4 * (
        (w & (w << 1) & _NOT_A).bit_count()
        - (black & (black << 1) & _NOT_A).bit_count()
    )
    score += 2 * (
        (w & _CENTER).bit_count() - (black & _CENTER).bit_count()
    )

    # Home-rank guards are valued by the distinct squares they cover.
    score += 6 * (
        (wa & _ROWS[1]).bit_count() - (ba & _ROWS[6]).bit_count()
    )
    score += 2 * (
        (wa & _ROWS[2]).bit_count() - (ba & _ROWS[5]).bit_count()
    )

    empty = _FULL ^ (w | black)
    wm = ((wa & ~w) | ((w << 8) & empty)) & ~ba & _FULL
    bm = ((ba & ~black) | ((black >> 8) & empty)) & ~wa
    score += 2 * (wm.bit_count() - bm.bit_count())
    score += 7 * (
        (wm & _ROWS[5]).bit_count() - (bm & _ROWS[2]).bit_count()
    )
    score += 3 * (
        (wm & _ROWS[4]).bit_count() - (bm & _ROWS[3]).bit_count()
    )

    white_run = 8
    black_run = 8

    candidates = w & _ADVANCED_W
    while candidates:
        bit = candidates & -candidates
        candidates ^= bit
        square = bit.bit_length() - 1
        row = square >> 3
        if not (black & _DANGER[1][square]):
            if not (w & _AHEAD[1][square]):
                score += _PASS_BONUS[row]
                white_run = min(white_run, 7 - row)

    candidates = black & _ADVANCED_B
    while candidates:
        bit = candidates & -candidates
        candidates ^= bit
        square = bit.bit_length() - 1
        row = square >> 3
        if not (w & _DANGER[0][square]):
            if not (black & _AHEAD[0][square]):
                score -= _PASS_BONUS[7 - row]
                black_run = min(black_run, row)

    # A safe runner that beats even the opponent's theoretical fastest
    # promotion is a proven win, not merely a positional advantage.
    black_fastest = ((black & -black).bit_length() - 1) >> 3
    white_fastest = 7 - ((w.bit_length() - 1) >> 3)

    if white_run <= black_fastest - (0 if up else 1):
        value = 20000 - 40 * white_run
        return value if up else -value
    if black_run <= white_fastest - (1 if up else 0):
        value = 20000 - 40 * black_run
        return -value if up else value

    return (score if up else -score) + 7


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()
    deadline = start + 0.90

    # Reflect ranks for black, so the root player always moves upward.
    flip = 56 if color == "b" else 0
    a = 0
    b = 0
    for row, col in me:
        a |= 1 << (((row << 3) | col) ^ flip)
    for row, col in opp:
        b |= 1 << (((row << 3) | col) ^ flip)

    def decode(move):
        source = (move >> 6) ^ flip
        target = (move & 63) ^ flip
        return ((source >> 3, source & 7),
                (target >> 3, target & 7))

    root_moves = _moves(a, b, True)

    # The arena calls the policy on nonterminal positions.
    # Every returned action is selected from this legal move list.
    best_move = root_moves[0]

    for move in root_moves:
        target_bit = _BITS[move & 63]
        if target_bit & _GOAL[1] or not (b & ~target_bit):
            return decode(move)

    urgent = b & _PENULT[0]
    if urgent:
        if not (urgent & (urgent - 1)):
            defenses = [m for m in root_moves
                        if _BITS[m & 63] & urgent]
            if defenses:
                root_moves = defenses
    else:
        threat = _safe_goal_threat(a, b, True)
        if threat >= 0:
            return decode(threat)

        # Execute a proven, uninterrupted straight-line race.
        opponent_distance = ((b & -b).bit_length() - 1) >> 3
        runners = a & _ADVANCED_W
        runner_move = -1
        runner_distance = 8
        while runners:
            bit = runners & -runners
            runners ^= bit
            square = bit.bit_length() - 1
            distance = 7 - (square >> 3)
            if (distance <= opponent_distance
                    and distance < runner_distance
                    and not (b & _DANGER[1][square])
                    and not (a & _AHEAD[1][square])):
                runner_move = (square << 6) | (square + 8)
                runner_distance = distance
        if runner_move >= 0:
            return decode(runner_move)

    tt = {}
    history = [[0] * 4096 for _ in range(2)]
    killers = [[-1, -1] for _ in range(128)]
    nodes = 0

    def ordered(moves, own, enemy, up, tt_move, ply):
        enemy_attacks = _attacks(enemy, not up)
        hist = history[up]
        first_killer, second_killer = killers[min(ply, 127)]
        position_order = _ORDER[up]
        reverse_attacks = _ATTACK[not up]
        penult = _PENULT[up]

        def key(move):
            if move == tt_move:
                return 100_000_000

            source = move >> 6
            target = move & 63
            source_bit = _BITS[source]
            target_bit = _BITS[target]
            value = hist[move] + position_order[target]
            value -= position_order[source] // 3

            if enemy & target_bit:
                value += 6500
            if penult & target_bit:
                value += 7000

            if not (enemy_attacks & target_bit):
                value += 900
            elif not (reverse_attacks[target] & (own ^ source_bit)):
                value -= 2200
            else:
                value -= 200

            if enemy_attacks & source_bit:
                value += 450
            if move == first_killer:
                value += 3200
            elif move == second_killer:
                value += 2600
            return value

        moves.sort(key=key, reverse=True)
        return moves

    def quiescence(own, enemy, up, alpha, beta, ply, remaining):
        nonlocal nodes
        nodes += 1
        if not (nodes & 63) and time.perf_counter() >= deadline:
            raise _SearchTimeout

        solved, forced = _tactics(own, enemy, up, ply)
        if solved is not None:
            return solved

        if forced is None:
            stand = _evaluate(own, enemy, up)
            if stand >= beta:
                return stand
            if remaining <= 0:
                return stand
            if stand > alpha:
                alpha = stand
            best = stand

            if own & _PREPENULT[up]:
                moves = [
                    m for m in _moves(own, enemy, up)
                    if _BITS[m & 63] & (enemy | _PENULT[up])
                ]
            else:
                moves = _moves(own, enemy, up, True)
        else:
            best = -_INF
            moves = forced

        if not moves:
            return best

        ordered(moves, own, enemy, up, -1, ply)
        for move in moves:
            source_bit = _BITS[move >> 6]
            target_bit = _BITS[move & 63]
            new_own = (own ^ source_bit) | target_bit
            new_enemy = enemy & ~target_bit

            value = -quiescence(
                new_enemy, new_own, not up,
                -beta, -alpha, ply + 1, remaining - 1
            )
            if value > best:
                best = value
            if value > alpha:
                alpha = value
                if alpha >= beta:
                    break
        return best

    def search(own, enemy, up, depth, alpha, beta, ply):
        nonlocal nodes
        if depth <= 0:
            return quiescence(own, enemy, up, alpha, beta, ply, 3)

        nodes += 1
        if not (nodes & 63) and time.perf_counter() >= deadline:
            raise _SearchTimeout

        solved, forced = _tactics(own, enemy, up, ply)
        if solved is not None:
            return solved

        key = (own, enemy, up)
        entry = tt.get(key)
        tt_move = -1
        if entry is not None:
            saved_depth, flag, value, tt_move = entry
            if value > _MATE_BOUND:
                value -= ply
            elif value < -_MATE_BOUND:
                value += ply

            if saved_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        original_alpha = alpha
        principal = beta - alpha > 1
        moves = forced if forced is not None else _moves(own, enemy, up)
        if not moves:
            return -_MATE + ply

        ordered(moves, own, enemy, up, tt_move, ply)

        # A unique forced defensive capture need not consume search depth.
        next_depth = depth if forced is not None and len(moves) == 1 else depth - 1
        best = -_INF
        best_local = moves[0]
        quiet_tried = []

        for index, move in enumerate(moves):
            source_bit = _BITS[move >> 6]
            target_bit = _BITS[move & 63]
            capture = bool(enemy & target_bit)
            new_own = (own ^ source_bit) | target_bit
            new_enemy = enemy & ~target_bit

            if index == 0:
                value = -search(
                    new_enemy, new_own, not up, next_depth,
                    -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (depth >= 3 and index >= 4 and not capture
                        and forced is None
                        and not (target_bit & _CRITICAL[up])
                        and move not in killers[min(ply, 127)]):
                    reduction = 1
                    if depth >= 6 and index >= 10:
                        reduction += 1
                    if not principal and depth >= 4 and index >= 18:
                        reduction += 1
                    reduction = min(reduction, max(0, next_depth - 1))

                value = -search(
                    new_enemy, new_own, not up, next_depth - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -search(
                        new_enemy, new_own, not up, next_depth,
                        -alpha - 1, -alpha, ply + 1
                    )
                if alpha < value < beta:
                    value = -search(
                        new_enemy, new_own, not up, next_depth,
                        -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_local = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capture:
                    slot = killers[min(ply, 127)]
                    if slot[0] != move:
                        slot[1] = slot[0]
                        slot[0] = move

                    bonus = min(1500, 32 * depth * depth)
                    hist = history[up]
                    hist[move] += bonus - hist[move] * bonus // 8192
                    for previous in quiet_tried:
                        hist[previous] -= (
                            bonus // 3
                            + hist[previous] * (bonus // 3) // 8192
                        )
                break

            if not capture:
                quiet_tried.append(move)

        flag = 2 if best <= original_alpha else (1 if best >= beta else 0)
        saved_value = best
        if best > _MATE_BOUND:
            saved_value += ply
        elif best < -_MATE_BOUND:
            saved_value -= ply
        tt[key] = (depth, flag, saved_value, best_local)
        return best

    ordered(root_moves, a, b, True, -1, 0)
    best_move = root_moves[0]
    root_scores = {move: -i for i, move in enumerate(root_moves)}
    previous_score = 0

    try:
        for depth in range(1, 25):
            if time.perf_counter() >= deadline:
                break

            window = 90
            if depth >= 4 and abs(previous_score) < 15000:
                low = previous_score - window
                high = previous_score + window
            else:
                low, high = -_INF, _INF

            hint = best_move

            while True:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                root_order = sorted(
                    root_moves,
                    key=lambda m: (m == hint, root_scores.get(m, -_INF)),
                    reverse=True,
                )
                alpha = low
                value_best = -_INF
                candidate = root_order[0]
                iteration_scores = {}

                for index, move in enumerate(root_order):
                    if time.perf_counter() >= deadline:
                        raise _SearchTimeout

                    source_bit = _BITS[move >> 6]
                    target_bit = _BITS[move & 63]
                    new_a = (a ^ source_bit) | target_bit
                    new_b = b & ~target_bit

                    if index == 0:
                        value = -search(
                            new_b, new_a, False, depth - 1,
                            -high, -alpha, 1
                        )
                    else:
                        value = -search(
                            new_b, new_a, False, depth - 1,
                            -alpha - 1, -alpha, 1
                        )
                        if alpha < value < high:
                            value = -search(
                                new_b, new_a, False, depth - 1,
                                -high, -alpha, 1
                            )

                    iteration_scores[move] = value
                    if value > value_best:
                        value_best = value
                        candidate = move
                    if value > alpha:
                        alpha = value
                    if alpha >= high:
                        break

                root_scores.update(iteration_scores)
                hint = candidate

                if value_best <= low and low > -_INF:
                    low = (-_INF if value_best < -_MATE_BOUND
                           else max(-_INF, value_best - window))
                    window *= 2
                    continue
                if value_best >= high and high < _INF:
                    high = (_INF if value_best > _MATE_BOUND
                            else min(_INF, value_best + window))
                    window *= 2
                    continue

                best_move = candidate
                previous_score = value_best
                break

            if abs(previous_score) > _MATE_BOUND:
                break

    except _SearchTimeout:
        pass

    return decode(best_move)
