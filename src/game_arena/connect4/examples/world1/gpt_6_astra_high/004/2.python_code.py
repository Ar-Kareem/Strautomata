
from __future__ import annotations

from time import perf_counter


_ROWS = 6
_COLS = 7
_ORDER = (3, 2, 4, 1, 5, 0, 6)

_COLUMN_MASKS = tuple(63 << (7 * c) for c in range(7))
_BOTTOM = sum(1 << (7 * c) for c in range(7))
_FULL = sum(_COLUMN_MASKS)

_ODD_ROWS = sum(
    1 << (7 * c + r)
    for c in range(7)
    for r in (0, 2, 4)
)
_EVEN_ROWS = _FULL ^ _ODD_ROWS

_CENTER = _COLUMN_MASKS[3]
_INNER = _COLUMN_MASKS[2] | _COLUMN_MASKS[4]
_OUTER = _COLUMN_MASKS[1] | _COLUMN_MASKS[5]

_WINDOW_STARTS = tuple(
    (
        shift,
        _FULL
        & (_FULL >> shift)
        & (_FULL >> (2 * shift))
        & (_FULL >> (3 * shift)),
    )
    for shift in (1, 6, 7, 8)
)

_WIN = 100000
_INF = 1000000

# Entries: depth, score, bound type, best move bit.
# Bound types: 0 = exact, 1 = lower bound, 2 = upper bound.
_TT = {}


class _SearchTimeout(Exception):
    pass


def _winning_cells(position: int, occupied: int) -> int:
    """Empty cells that complete four for position."""
    result = (position << 1) & (position << 2) & (position << 3)

    for shift in (7, 6, 8):
        pair = (position << shift) & (position << (2 * shift))
        result |= pair & (position << (3 * shift))
        result |= pair & (position >> shift)

        pair = (position >> shift) & (position >> (2 * shift))
        result |= pair & (position << shift)
        result |= pair & (position >> (3 * shift))

    return result & (_FULL ^ occupied)


def _preferred_move(moves: int) -> int:
    for column in _ORDER:
        move = moves & _COLUMN_MASKS[column]
        if move:
            return move
    return 0


def _move_column(move: int) -> int:
    return (move.bit_length() - 1) // 7


def _mirror(bits: int) -> int:
    result = 0
    for column in range(7):
        result |= ((bits >> (7 * column)) & 127) << (7 * (6 - column))
    return result


def _evaluate(
    position: int,
    occupied: int,
    opponent_wins: int,
    stones: int,
) -> int:
    opponent = occupied ^ position
    our_wins = _winning_cells(position, occupied)

    value = 65 * (our_wins.bit_count() - opponent_wins.bit_count())

    our_parity = _EVEN_ROWS if stones & 1 else _ODD_ROWS
    their_parity = _FULL ^ our_parity
    value += 24 * (
        (our_wins & our_parity).bit_count()
        - (opponent_wins & their_parity).bit_count()
    )

    # Adjacent threats in a column are particularly difficult to defend.
    value += 110 * (
        (our_wins & (our_wins >> 1)).bit_count()
        - (opponent_wins & (opponent_wins >> 1)).bit_count()
    )

    value += 5 * (
        (position & _CENTER).bit_count()
        - (opponent & _CENTER).bit_count()
    )
    value += 3 * (
        (position & _INNER).bit_count()
        - (opponent & _INNER).bit_count()
    )
    value += (
        (position & _OUTER).bit_count()
        - (opponent & _OUTER).bit_count()
    )

    # Count open four-cell windows containing at least two friendly discs.
    for shift, starts in _WINDOW_STARTS:
        p1 = position >> shift
        p2 = p1 >> shift
        p3 = p2 >> shift

        o1 = opponent >> shift
        o2 = o1 >> shift
        o3 = o2 >> shift

        our_pairs = (
            (position & p1)
            | (p2 & p3)
            | ((position | p1) & (p2 | p3))
        )
        their_pairs = (
            (opponent & o1)
            | (o2 & o3)
            | ((opponent | o1) & (o2 | o3))
        )

        our_open = our_pairs & starts & ~(opponent | o1 | o2 | o3)
        their_open = their_pairs & starts & ~(position | p1 | p2 | p3)
        value += 7 * (our_open.bit_count() - their_open.bit_count())

    return value


def policy(board: list[list[int]]) -> int:
    deadline = perf_counter() + 0.88

    legal = [
        column
        for column in _ORDER
        if any(board[row][column] == 0 for row in range(6))
    ]
    if not legal:
        # A completed board has no legal action; normal games do not call here.
        return 0

    fallback_column = legal[0]
    position = 0
    occupied = 0
    malformed = False

    for column in range(7):
        column_occupancy = 0
        for height in range(6):
            cell = board[5 - height][column]
            if cell != 0:
                bit = 1 << (7 * column + height)
                occupied |= bit
                column_occupancy |= 1 << height
                if cell == 1:
                    position |= bit

        # Preserve legality even if handed a board with gravity violations.
        if column_occupancy & (column_occupancy + 1):
            malformed = True

    if malformed:
        return fallback_column

    root_count = occupied.bit_count()
    if root_count == 0:
        return 3

    possible = (occupied + _BOTTOM) & _FULL
    immediate_wins = _winning_cells(position, occupied) & possible
    if immediate_wins:
        return _move_column(_preferred_move(immediate_wins))

    opponent_wins = _winning_cells(occupied ^ position, occupied)
    forced = possible & opponent_wins

    if forced and (forced & (forced - 1)):
        # Multiple immediate threats cannot all be blocked.
        return _move_column(_preferred_move(forced))

    safe = forced if forced else possible
    safe &= ~(opponent_wins >> 1)

    if not safe:
        return _move_column(_preferred_move(forced or possible))

    best_move = _preferred_move(safe)
    if not (safe & (safe - 1)):
        return _move_column(best_move)

    empty_count = 42 - root_count
    if empty_count <= 2:
        return _move_column(best_move)

    root_moves = safe
    if _mirror(position) == position and _mirror(occupied) == occupied:
        # Search one representative of each mirrored root move.
        root_moves &= (1 << 28) - 1
        if not (root_moves & (root_moves - 1)):
            return _move_column(root_moves)

    if len(_TT) > 170000:
        _TT.clear()

    table = _TT
    root_key = position + occupied
    old_root = table.get(root_key)
    if old_root is not None and old_root[3] & safe:
        best_move = old_root[3]

    history = [0] * 98
    killers = [[0, 0] for _ in range(43)]
    nodes = 0

    def search(
        player: int,
        mask: int,
        depth: int,
        alpha: int,
        beta: int,
        stones: int,
        enemy_wins=None,
    ) -> int:
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        key = player + mask
        original_alpha = alpha
        entry = table.get(key)
        tt_move = 0

        if entry is not None:
            stored_depth, stored_score, bound, tt_move = entry
            if stored_depth >= depth:
                if bound == 0:
                    return stored_score
                if bound == 1:
                    if stored_score > alpha:
                        alpha = stored_score
                elif stored_score < beta:
                    beta = stored_score
                if alpha >= beta:
                    return stored_score

        empties = 42 - stones
        playable = (mask + _BOTTOM) & _FULL
        if not playable:
            return 0

        enemy = mask ^ player
        if enemy_wins is None:
            enemy_wins = _winning_cells(enemy, mask)

        must_block = playable & enemy_wins
        if must_block and (must_block & (must_block - 1)):
            score = -_WIN - (empties - 2)
            table[key] = (99, score, 0, 0)
            return score

        moves = must_block if must_block else playable
        moves &= ~(enemy_wins >> 1)

        if not moves:
            score = -_WIN - (empties - 2)
            table[key] = (99, score, 0, 0)
            return score

        if stones == root_count:
            moves &= root_moves

        if empties <= 2:
            table[key] = (99, 0, 0, moves & -moves)
            return 0

        single_move = not (moves & (moves - 1))

        if depth <= 0 and not single_move:
            return _evaluate(player, mask, enemy_wins, stones)

        next_depth = depth - 1 if depth > 0 else 0

        if single_move:
            # Continue forced lines beyond the nominal search horizon.
            move = moves
            score = -search(
                enemy, mask | move, next_depth,
                -beta, -alpha, stones + 1,
            )
            flag = (
                1 if score >= beta
                else 2 if score <= original_alpha
                else 0
            )
            table[key] = (depth, score, flag, move)
            return score

        first_killer, second_killer = killers[stones]
        history_offset = (stones & 1) * 49
        ordered = []

        for rank, column in enumerate(_ORDER):
            move = moves & _COLUMN_MASKS[column]
            if not move:
                continue

            index = history_offset + move.bit_length() - 1
            priority = history[index] + 8 * (6 - rank)
            child_threats = None
            forcing = False

            if depth >= 3:
                child_mask = mask | move
                child_threats = _winning_cells(player | move, child_mask)
                checks = child_threats & ((child_mask + _BOTTOM) & _FULL)

                if checks & (checks - 1):
                    # A safe move creating two immediate threats wins in three.
                    score = _WIN + empties - 3
                    table[key] = (99, score, 0, move)
                    return score

                forcing = bool(checks)
                priority += 1024 * child_threats.bit_count()
                if forcing:
                    priority += 100000

            if move == first_killer:
                priority += 20000
            elif move == second_killer:
                priority += 10000

            if move == tt_move:
                priority += 1000000000

            ordered.append(
                (priority, move, child_threats, forcing, index)
            )

        ordered.sort(key=lambda item: item[0], reverse=True)

        best_score = -_INF
        local_best = ordered[0][1]
        principal_node = beta - alpha > 1

        for move_number, item in enumerate(ordered):
            _, move, child_threats, forcing, history_index = item
            child_mask = mask | move

            if move_number == 0 or depth < 3:
                score = -search(
                    enemy, child_mask, next_depth,
                    -beta, -alpha, stones + 1, child_threats,
                )
            else:
                reduction = int(
                    depth >= 5
                    and move_number >= 3
                    and empties > 16
                    and stones != root_count
                    and not principal_node
                    and not forcing
                    and move != first_killer
                    and move != second_killer
                )

                score = -search(
                    enemy, child_mask, next_depth - reduction,
                    -alpha - 1, -alpha, stones + 1, child_threats,
                )

                if reduction and score > alpha:
                    score = -search(
                        enemy, child_mask, next_depth,
                        -alpha - 1, -alpha, stones + 1, child_threats,
                    )

                if alpha < score < beta:
                    score = -search(
                        enemy, child_mask, next_depth,
                        -beta, -alpha, stones + 1, child_threats,
                    )

            if score > best_score:
                best_score = score
                local_best = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if move != first_killer:
                    killers[stones][1] = first_killer
                    killers[stones][0] = move

                history[history_index] = min(
                    60000, history[history_index] + depth * depth
                )
                break

        flag = (
            1 if best_score >= beta
            else 2 if best_score <= original_alpha
            else 0
        )
        table[key] = (depth, best_score, flag, local_best)
        return best_score

    previous_score = 0

    try:
        for depth in range(2, empty_count + 1):
            if perf_counter() >= deadline:
                break

            if depth >= 4:
                low = previous_score - 96
                high = previous_score + 96
            else:
                low, high = -_INF, _INF

            score = search(
                position, occupied, depth,
                low, high, root_count, opponent_wins,
            )

            if score <= low or score >= high:
                score = search(
                    position, occupied, depth,
                    -_INF, _INF, root_count, opponent_wins,
                )

            completed = table.get(root_key)
            if completed is not None and completed[3] & safe:
                best_move = completed[3]

            previous_score = score
            if abs(score) >= _WIN:
                break

    except _SearchTimeout:
        pass

    column = _move_column(best_move)
    return column if column in legal else fallback_column
