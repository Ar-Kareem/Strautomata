
import time

# Board constants
FULL_MASK = (1 << 64) - 1
ROW_MASKS = [sum(1 << (r * 8 + c) for c in range(8)) for r in range(8)]
GOAL_MASK = {1: ROW_MASKS[7], -1: ROW_MASKS[0]}

MATE = 1_000_000
INF = 2_000_000

# Squares containing enemy pawns that prevent a pawn from being "passed".
PASSED_MASK = {1: [0] * 64, -1: [0] * 64}
for direction in (1, -1):
    for sq in range(64):
        r, c = divmod(sq, 8)
        mask = 0
        rr = r + direction
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    mask |= 1 << (rr * 8 + cc)
            rr += direction
        PASSED_MASK[direction][sq] = mask

ADVANCE_VALUE = (0, 5, 13, 25, 43, 72, 120, 500)
PASSED_VALUE = (3, 7, 14, 27, 52, 105, 220, 500)
CENTER_VALUE = (0, 3, 6, 9, 9, 6, 3, 0)

_TT = {}
_HISTORY = {}
_KILLERS = []
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _bits(board):
    while board:
        bit = board & -board
        yield bit.bit_length() - 1
        board ^= bit


def _advancement(square, direction):
    row = square >> 3
    return row if direction == 1 else 7 - row


def _is_supported(board, direction, square):
    """Whether a friendly pawn can capture onto square."""
    r, c = divmod(square, 8)
    source_row = r - direction
    if not (0 <= source_row < 8):
        return False
    if c > 0 and board & (1 << (source_row * 8 + c - 1)):
        return True
    if c < 7 and board & (1 << (source_row * 8 + c + 1)):
        return True
    return False


def _is_attacked(board, attacker_direction, square):
    r, c = divmod(square, 8)
    source_row = r - attacker_direction
    if not (0 <= source_row < 8):
        return False
    if c > 0 and board & (1 << (source_row * 8 + c - 1)):
        return True
    if c < 7 and board & (1 << (source_row * 8 + c + 1)):
        return True
    return False


def _generate_moves(player, enemy, direction):
    occupied = player | enemy
    moves = []

    for source in _bits(player):
        r, c = divmod(source, 8)
        nr = r + direction
        if not (0 <= nr < 8):
            continue

        # Straight moves require an empty destination.
        target = nr * 8 + c
        if not (occupied & (1 << target)):
            moves.append((source << 6) | target)

        # Diagonal moves may enter an empty square or capture an enemy,
        # but may never enter a friendly square.
        if c > 0:
            target = nr * 8 + c - 1
            if not (player & (1 << target)):
                moves.append((source << 6) | target)

        if c < 7:
            target = nr * 8 + c + 1
            if not (player & (1 << target)):
                moves.append((source << 6) | target)

    return moves


def _apply_move(player, enemy, move):
    source = move >> 6
    target = move & 63
    source_bit = 1 << source
    target_bit = 1 << target
    new_player = (player ^ source_bit) | target_bit
    new_enemy = enemy & ~target_bit
    return new_player, new_enemy


def _terminal_score(player, enemy, direction, ply):
    if not player:
        return -MATE + ply
    if enemy & GOAL_MASK[-direction]:
        return -MATE + ply
    if player & GOAL_MASK[direction]:
        return MATE - ply
    if not enemy:
        return MATE - ply
    return None


def _side_features(player, enemy, direction):
    score = 0
    count = player.bit_count()
    score += 108 * count

    for square in _bits(player):
        r, c = divmod(square, 8)
        advancement = r if direction == 1 else 7 - r

        score += ADVANCE_VALUE[advancement]
        score += CENTER_VALUE[c]

        supported = _is_supported(player, direction, square)
        attacked = _is_attacked(enemy, -direction, square)

        if supported:
            score += 13 + advancement * 2

        if attacked:
            if supported:
                score -= 9 + advancement * 2
            else:
                score -= 28 + advancement * 5

        # Horizontal and diagonal cohesion.
        if c > 0 and player & (1 << (r * 8 + c - 1)):
            score += 4
        if c < 7 and player & (1 << (r * 8 + c + 1)):
            score += 4

        # Passed pawns become increasingly dangerous near promotion.
        if not (enemy & PASSED_MASK[direction][square]):
            bonus = PASSED_VALUE[advancement]
            if supported:
                bonus += bonus // 3
            score += bonus

        nr = r + direction
        mobility = 0
        if 0 <= nr < 8:
            straight = nr * 8 + c
            if not ((player | enemy) & (1 << straight)):
                mobility += 1

            if c > 0:
                diagonal = nr * 8 + c - 1
                if not (player & (1 << diagonal)):
                    mobility += 1
                    if enemy & (1 << diagonal):
                        victim_adv = _advancement(diagonal, -direction)
                        score += 13 + victim_adv * 3

            if c < 7:
                diagonal = nr * 8 + c + 1
                if not (player & (1 << diagonal)):
                    mobility += 1
                    if enemy & (1 << diagonal):
                        victim_adv = _advancement(diagonal, -direction)
                        score += 13 + victim_adv * 3

        score += mobility * 2

        if mobility == 0:
            score -= 12 + advancement * 2
        elif advancement == 6:
            score += 245
        elif advancement == 5:
            score += 35

    return score


def _evaluate(player, enemy, direction):
    # A small tempo bonus is useful in a pure racing game.
    return (
        _side_features(player, enemy, direction)
        - _side_features(enemy, player, -direction)
        + 7
    )


def _move_order_score(move, player, enemy, direction, ply, tt_move):
    source = move >> 6
    target = move & 63
    target_bit = 1 << target
    tr, tc = divmod(target, 8)
    score = _HISTORY.get((direction, move), 0)

    if move == tt_move:
        score += 10_000_000

    if ply < len(_KILLERS):
        if move == _KILLERS[ply][0]:
            score += 75_000
        elif move == _KILLERS[ply][1]:
            score += 60_000

    if target_bit & GOAL_MASK[direction]:
        score += 5_000_000

    is_capture = bool(enemy & target_bit)
    if is_capture:
        victim_adv = _advancement(target, -direction)
        score += 22_000 + victim_adv * 300

    advance = tr if direction == 1 else 7 - tr
    score += advance * 90
    score += CENTER_VALUE[tc] * 8

    new_player, new_enemy = _apply_move(player, enemy, move)

    if _is_supported(new_player, direction, target):
        score += 650 + advance * 20

    if not (new_enemy & PASSED_MASK[direction][target]):
        score += 250 + PASSED_VALUE[advance] * 6

    attacked = _is_attacked(new_enemy, -direction, target)
    defended = _is_supported(new_player, direction, target)
    if attacked and not defended:
        score -= 900 + advance * 80
    elif attacked:
        score -= 120

    if advance == 6:
        score += 5_000
    elif advance == 5:
        score += 700

    return score


def _ordered_moves(moves, player, enemy, direction, ply, tt_move=-1):
    moves.sort(
        key=lambda m: _move_order_score(
            m, player, enemy, direction, ply, tt_move
        ),
        reverse=True,
    )
    return moves


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _quiescence(player, enemy, direction, alpha, beta, ply, qdepth):
    _check_time()

    terminal = _terminal_score(player, enemy, direction, ply)
    if terminal is not None:
        return terminal

    all_moves = _generate_moves(player, enemy, direction)

    if not all_moves:
        return -MATE + ply

    # Promotion is an immediate win and must never be hidden by the horizon.
    goal = GOAL_MASK[direction]
    for move in all_moves:
        if (1 << (move & 63)) & goal:
            return MATE - ply

    stand_pat = _evaluate(player, enemy, direction)
    if qdepth <= 0:
        return stand_pat

    if stand_pat >= beta:
        return stand_pat
    if stand_pat > alpha:
        alpha = stand_pat

    tactical = [
        move for move in all_moves
        if enemy & (1 << (move & 63))
    ]

    if not tactical:
        return stand_pat

    _ordered_moves(tactical, player, enemy, direction, ply)

    best = stand_pat
    for move in tactical:
        target = move & 63
        new_player, new_enemy = _apply_move(player, enemy, move)

        if not new_enemy:
            score = MATE - ply
        else:
            score = -_quiescence(
                new_enemy,
                new_player,
                -direction,
                -beta,
                -alpha,
                ply + 1,
                qdepth - 1,
            )

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _search(player, enemy, direction, depth, alpha, beta, ply):
    _check_time()

    terminal = _terminal_score(player, enemy, direction, ply)
    if terminal is not None:
        return terminal

    if depth <= 0:
        return _quiescence(
            player, enemy, direction, alpha, beta, ply, 3
        )

    key = (player, enemy, direction)
    alpha_original = alpha
    beta_original = beta
    tt_move = -1

    entry = _TT.get(key)
    if entry is not None:
        stored_depth, stored_value, flag, stored_move = entry
        tt_move = stored_move
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    moves = _generate_moves(player, enemy, direction)
    if not moves:
        return -MATE + ply

    _ordered_moves(moves, player, enemy, direction, ply, tt_move)

    best_value = -INF
    best_move = moves[0]

    for index, move in enumerate(moves):
        target = move & 63
        target_bit = 1 << target
        is_capture = bool(enemy & target_bit)
        new_player, new_enemy = _apply_move(player, enemy, move)

        if (target_bit & GOAL_MASK[direction]) or not new_enemy:
            score = MATE - ply
        elif index == 0:
            score = -_search(
                new_enemy,
                new_player,
                -direction,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
        else:
            target_advance = _advancement(target, direction)
            reduced = (
                depth >= 4
                and index >= 7
                and not is_capture
                and target_advance < 6
                and move != tt_move
            )

            if reduced:
                score = -_search(
                    new_enemy,
                    new_player,
                    -direction,
                    depth - 2,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )
                if score > alpha:
                    score = -_search(
                        new_enemy,
                        new_player,
                        -direction,
                        depth - 1,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )
            else:
                score = -_search(
                    new_enemy,
                    new_player,
                    -direction,
                    depth - 1,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )

            if alpha < score < beta:
                score = -_search(
                    new_enemy,
                    new_player,
                    -direction,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

        if score > best_value:
            best_value = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not is_capture:
                if ply < len(_KILLERS):
                    if _KILLERS[ply][0] != move:
                        _KILLERS[ply][1] = _KILLERS[ply][0]
                        _KILLERS[ply][0] = move
                key_hist = (direction, move)
                _HISTORY[key_hist] = (
                    _HISTORY.get(key_hist, 0) + depth * depth
                )
            break

    if best_value <= alpha_original:
        flag = -1  # Upper bound
    elif best_value >= beta_original:
        flag = 1   # Lower bound
    else:
        flag = 0   # Exact value

    old_entry = _TT.get(key)
    if old_entry is None or depth >= old_entry[0]:
        _TT[key] = (depth, best_value, flag, best_move)

    return best_value


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _TT, _HISTORY, _KILLERS, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODES = 0
    _TT = {}
    _HISTORY = {}
    _KILLERS = [[-1, -1] for _ in range(128)]

    direction = 1 if color == "w" else -1

    player = 0
    enemy = 0
    for r, c in me:
        player |= 1 << (r * 8 + c)
    for r, c in opp:
        enemy |= 1 << (r * 8 + c)

    legal_moves = _generate_moves(player, enemy, direction)

    # Active game states always have a legal move.
    if not legal_moves:
        return ((0, 0), (0, 0))

    # First establish a tactically sensible legal fallback.
    ordered_fallback = legal_moves[:]
    _ordered_moves(ordered_fallback, player, enemy, direction, 0)
    best_move = ordered_fallback[0]

    # Immediate wins need no search.
    for move in legal_moves:
        target = move & 63
        if ((1 << target) & GOAL_MASK[direction]) or (
            enemy & (1 << target) and enemy.bit_count() == 1
        ):
            source = move >> 6
            return (
                (source >> 3, source & 7),
                (target >> 3, target & 7),
            )

    root_key = (player, enemy, direction)

    # Iterative deepening preserves the last fully completed result.
    for depth in range(1, 25):
        if time.perf_counter() >= _DEADLINE:
            break
        try:
            value = _search(
                player, enemy, direction, depth, -INF, INF, 0
            )
            entry = _TT.get(root_key)
            if entry is not None and entry[3] in legal_moves:
                best_move = entry[3]

            if value >= MATE - 1000:
                break
        except _SearchTimeout:
            break

    # Defensive legality verification.
    if best_move not in legal_moves:
        best_move = legal_moves[0]

    source = best_move >> 6
    target = best_move & 63
    return (
        (source >> 3, source & 7),
        (target >> 3, target & 7),
    )
