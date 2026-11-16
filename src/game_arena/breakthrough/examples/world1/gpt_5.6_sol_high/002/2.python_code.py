
import time


WIN_SCORE = 1_000_000
INF = 2_000_000

RANK_MASKS = [0xFF << (8 * r) for r in range(8)]
CENTER_VALUE = (0, 2, 4, 6, 6, 4, 2, 0)
ADVANCE_VALUE = (0, 3, 8, 17, 31, 57, 108, 0)
PASSED_VALUE = (0, 0, 2, 5, 13, 31, 74, 0)
FRONT_VALUE = (0, 0, 2, 6, 15, 34, 0, 0)

SUPPORT_MASK = [[0] * 64 for _ in range(2)]
ATTACKER_MASK = [[0] * 64 for _ in range(2)]
CAPTURE_FROM_MASK = [[0] * 64 for _ in range(2)]
PASSED_MASK = [[0] * 64 for _ in range(2)]

for up_index in (0, 1):
    step = 1 if up_index else -1

    for sq in range(64):
        r, c = divmod(sq, 8)

        support = 0
        support_row = r - step
        if 0 <= support_row < 8:
            if c > 0:
                support |= 1 << (support_row * 8 + c - 1)
            if c < 7:
                support |= 1 << (support_row * 8 + c + 1)
        SUPPORT_MASK[up_index][sq] = support

        attackers = 0
        attacker_row = r + step
        if 0 <= attacker_row < 8:
            if c > 0:
                attackers |= 1 << (attacker_row * 8 + c - 1)
            if c < 7:
                attackers |= 1 << (attacker_row * 8 + c + 1)
        ATTACKER_MASK[up_index][sq] = attackers

        origins = 0
        origin_row = r - step
        if 0 <= origin_row < 8:
            if c > 0:
                origins |= 1 << (origin_row * 8 + c - 1)
            if c < 7:
                origins |= 1 << (origin_row * 8 + c + 1)
        CAPTURE_FROM_MASK[up_index][sq] = origins

        passed = 0
        rr = r + step
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    passed |= 1 << (rr * 8 + cc)
            rr += step
        PASSED_MASK[up_index][sq] = passed


_deadline = 0.0
_nodes = 0
_tt = {}
_history = {}
_killers = []


class SearchTimeout(Exception):
    pass


def _progress(row, up):
    return row if up else 7 - row


def _goal_mask(up):
    return RANK_MASKS[7] if up else RANK_MASKS[0]


def _penultimate_mask(up):
    return RANK_MASKS[6] if up else RANK_MASKS[1]


def _generate_moves(own, enemy, up):
    moves = []
    occupied = own | enemy
    step = 1 if up else -1
    pieces = own

    while pieces:
        low = pieces & -pieces
        src = low.bit_length() - 1
        pieces ^= low

        r, c = divmod(src, 8)
        nr = r + step
        if not (0 <= nr < 8):
            continue

        straight = nr * 8 + c
        if not (occupied & (1 << straight)):
            moves.append((src << 6) | straight)

        if c > 0:
            dst = nr * 8 + c - 1
            if not (own & (1 << dst)):
                moves.append((src << 6) | dst)

        if c < 7:
            dst = nr * 8 + c + 1
            if not (own & (1 << dst)):
                moves.append((src << 6) | dst)

    return moves


def _apply_move(own, enemy, move):
    src = move >> 6
    dst = move & 63
    src_bit = 1 << src
    dst_bit = 1 << dst
    new_own = (own & ~src_bit) | dst_bit
    new_enemy = enemy & ~dst_bit
    return new_own, new_enemy


def _immediate_win(own, enemy, up):
    if own & _penultimate_mask(up):
        return True

    if enemy and enemy.bit_count() == 1:
        target = enemy.bit_length() - 1
        if own & CAPTURE_FROM_MASK[int(up)][target]:
            return True

    return False


def _piece_features(pieces, enemy, up):
    score = 100 * pieces.bit_count()
    mobility = 0
    max_progress = 0
    occupied = pieces | enemy
    step = 1 if up else -1
    up_index = int(up)

    remaining = pieces
    while remaining:
        low = remaining & -remaining
        sq = low.bit_length() - 1
        remaining ^= low

        r, c = divmod(sq, 8)
        progress = _progress(r, up)
        if progress > max_progress:
            max_progress = progress

        score += ADVANCE_VALUE[progress]
        score += CENTER_VALUE[c]

        supporters = (pieces & SUPPORT_MASK[up_index][sq]).bit_count()
        attackers = (enemy & ATTACKER_MASK[up_index][sq]).bit_count()

        score += supporters * 9
        if attackers:
            score -= attackers * 4
            if supporters == 0:
                score -= 13
            elif attackers > supporters:
                score -= 5 * (attackers - supporters)

        if not (enemy & PASSED_MASK[up_index][sq]):
            score += PASSED_VALUE[progress]

        nr = r + step
        if 0 <= nr < 8:
            straight = nr * 8 + c
            if not (occupied & (1 << straight)):
                mobility += 1

            if c > 0:
                dst = nr * 8 + c - 1
                if not (pieces & (1 << dst)):
                    mobility += 1

            if c < 7:
                dst = nr * 8 + c + 1
                if not (pieces & (1 << dst)):
                    mobility += 1

    score += FRONT_VALUE[max_progress]
    score += mobility
    return score


def _evaluate(own, enemy, up):
    own_score = _piece_features(own, enemy, up)
    enemy_score = _piece_features(enemy, own, not up)
    return own_score - enemy_score + 3


def _move_order_score(move, own, enemy, up, tt_move, ply):
    if move == tt_move:
        return 20_000_000

    src = move >> 6
    dst = move & 63
    dst_bit = 1 << dst
    dst_row, dst_col = divmod(dst, 8)
    progress = _progress(dst_row, up)
    capture = bool(enemy & dst_bit)

    score = _history.get((int(up), move), 0)
    score += progress * 900
    score += CENTER_VALUE[dst_col] * 25

    if progress == 7:
        score += 10_000_000

    if capture:
        score += 450_000
        enemy_progress = _progress(dst_row, not up)
        score += enemy_progress * 700
        if enemy.bit_count() == 1:
            score += 9_000_000
    elif ply < len(_killers):
        killer_a, killer_b = _killers[ply]
        if move == killer_a:
            score += 180_000
        elif move == killer_b:
            score += 130_000

    if progress == 6:
        score += 220_000

    own_after, enemy_after = _apply_move(own, enemy, move)
    supporters = (
        own_after & SUPPORT_MASK[int(up)][dst]
    ).bit_count()
    attackers = (
        enemy_after & ATTACKER_MASK[int(up)][dst]
    ).bit_count()

    score += supporters * 2400
    if attackers and not supporters:
        score -= 3200
    elif attackers > supporters:
        score -= 1000 * (attackers - supporters)

    return score


def _ordered_moves(own, enemy, up, tt_move, ply):
    moves = _generate_moves(own, enemy, up)
    moves.sort(
        key=lambda mv: _move_order_score(
            mv, own, enemy, up, tt_move, ply
        ),
        reverse=True,
    )
    return moves


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise SearchTimeout


def _record_killer(move, up, ply, enemy):
    if enemy & (1 << (move & 63)):
        return

    if ply >= len(_killers):
        return

    first, second = _killers[ply]
    if move != first:
        _killers[ply] = [move, first]

    key = (int(up), move)
    value = _history.get(key, 0) + 1
    if value > 200_000:
        value = 200_000
    _history[key] = value


def _search(own, enemy, up, depth, alpha, beta, ply):
    _check_time()

    own_goal = _goal_mask(up)
    enemy_goal = _goal_mask(not up)

    if not enemy or (own & own_goal):
        return WIN_SCORE - ply
    if not own or (enemy & enemy_goal):
        return -WIN_SCORE + ply

    if _immediate_win(own, enemy, up):
        return WIN_SCORE - ply - 1

    if depth <= 0:
        return _evaluate(own, enemy, up)

    alpha_original = alpha
    beta_original = beta
    key = (own, enemy, int(up))
    entry = _tt.get(key)
    tt_move = -1

    if entry is not None:
        entry_depth, entry_value, entry_flag, tt_move = entry
        if entry_depth >= depth:
            if entry_flag == 0:
                return entry_value
            if entry_flag == 1:
                if entry_value > alpha:
                    alpha = entry_value
            else:
                if entry_value < beta:
                    beta = entry_value
            if alpha >= beta:
                return entry_value

    moves = _ordered_moves(own, enemy, up, tt_move, ply)
    if not moves:
        return -WIN_SCORE + ply

    best_value = -INF
    best_move = moves[0]

    for index, move in enumerate(moves):
        dst = move & 63
        capture = bool(enemy & (1 << dst))
        dst_progress = _progress(dst >> 3, up)
        new_own, new_enemy = _apply_move(own, enemy, move)

        if index == 0:
            value = -_search(
                new_enemy,
                new_own,
                not up,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
        else:
            reduced = (
                depth >= 3
                and index >= 6
                and not capture
                and dst_progress < 6
            )

            if reduced:
                value = -_search(
                    new_enemy,
                    new_own,
                    not up,
                    depth - 2,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )
                if value > alpha:
                    value = -_search(
                        new_enemy,
                        new_own,
                        not up,
                        depth - 1,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )
            else:
                value = -_search(
                    new_enemy,
                    new_own,
                    not up,
                    depth - 1,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )

            if alpha < value < beta:
                value = -_search(
                    new_enemy,
                    new_own,
                    not up,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if not capture:
                _record_killer(move, up, ply, enemy)
                history_key = (int(up), move)
                bonus = depth * depth * 8
                _history[history_key] = min(
                    200_000,
                    _history.get(history_key, 0) + bonus,
                )
            break

    if best_value <= alpha_original:
        flag = 2
    elif best_value >= beta_original:
        flag = 1
    else:
        flag = 0

    if len(_tt) < 250_000 or key in _tt:
        old = _tt.get(key)
        if old is None or depth >= old[0]:
            _tt[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(own, enemy, depth, preferred):
    moves = _ordered_moves(own, enemy, True, preferred, 0)
    if not moves:
        raise SearchTimeout

    alpha = -INF
    beta = INF
    best_move = moves[0]
    best_value = -INF

    for index, move in enumerate(moves):
        if time.perf_counter() >= _deadline:
            raise SearchTimeout

        new_own, new_enemy = _apply_move(own, enemy, move)

        if index == 0:
            value = -_search(
                new_enemy,
                new_own,
                False,
                depth - 1,
                -beta,
                -alpha,
                1,
            )
        else:
            value = -_search(
                new_enemy,
                new_own,
                False,
                depth - 1,
                -alpha - 1,
                -alpha,
                1,
            )
            if alpha < value < beta:
                value = -_search(
                    new_enemy,
                    new_own,
                    False,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_move, best_value


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes, _tt, _history, _killers

    start = time.perf_counter()
    _deadline = start + 0.90
    _nodes = 0
    _tt = {}
    _history = {}
    _killers = [[-1, -1] for _ in range(128)]

    flip = color == "b"

    own = 0
    for row, col in me:
        internal_row = 7 - row if flip else row
        own |= 1 << (internal_row * 8 + col)

    enemy = 0
    for row, col in opp:
        internal_row = 7 - row if flip else row
        enemy |= 1 << (internal_row * 8 + col)

    legal_moves = _generate_moves(own, enemy, True)
    if not legal_moves:
        # A valid nonterminal Breakthrough position always has a move.
        # This branch is only a defensive fallback for malformed input.
        src_row, src_col = me[0]
        direction = -1 if color == "b" else 1
        return ((src_row, src_col), (src_row + direction, src_col))

    ordered = _ordered_moves(own, enemy, True, -1, 0)
    best_move = ordered[0]

    enemy_count = enemy.bit_count()
    for move in ordered:
        dst = move & 63
        dst_row = dst >> 3
        if dst_row == 7:
            best_move = move
            break
        if enemy_count == 1 and (enemy & (1 << dst)):
            best_move = move
            break
    else:
        preferred = best_move

        for depth in range(1, 33):
            if time.perf_counter() >= _deadline:
                break
            try:
                completed_move, _ = _root_search(
                    own, enemy, depth, preferred
                )
                best_move = completed_move
                preferred = completed_move
            except SearchTimeout:
                break

    src = best_move >> 6
    dst = best_move & 63
    src_row, src_col = divmod(src, 8)
    dst_row, dst_col = divmod(dst, 8)

    if flip:
        src_row = 7 - src_row
        dst_row = 7 - dst_row

    return ((src_row, src_col), (dst_row, dst_col))
