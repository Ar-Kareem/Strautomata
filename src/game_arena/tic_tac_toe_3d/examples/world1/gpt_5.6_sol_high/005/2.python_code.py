
from itertools import product
from time import perf_counter


BOARD_SIZE = 27
FULL_MASK = (1 << BOARD_SIZE) - 1
WIN_SCORE = 1_000_000
INF = 2_000_000


def _cell_index(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _coordinates(index: int) -> tuple[int, int, int]:
    i, remainder = divmod(index, 9)
    j, k = divmod(remainder, 3)
    return i, j, k


def _generate_winning_lines() -> tuple[int, ...]:
    lines = set()

    for direction in product((-1, 0, 1), repeat=3):
        if direction == (0, 0, 0):
            continue

        # Keep one orientation from each pair of opposite directions.
        first_nonzero = next(value for value in direction if value != 0)
        if first_nonzero != 1:
            continue

        di, dj, dk = direction

        for i, j, k in product(range(3), repeat=3):
            cells = []
            valid = True

            for step in range(3):
                x = i + step * di
                y = j + step * dj
                z = k + step * dk

                if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                    valid = False
                    break

                cells.append(_cell_index(x, y, z))

            if not valid:
                continue

            # The preceding point must be outside the board, ensuring that
            # this is the beginning of the complete length-three line.
            pi = i - di
            pj = j - dj
            pk = k - dk
            if 0 <= pi < 3 and 0 <= pj < 3 and 0 <= pk < 3:
                continue

            mask = 0
            for index in cells:
                mask |= 1 << index
            lines.add(mask)

    return tuple(sorted(lines))


WIN_LINES = _generate_winning_lines()

_lines_by_cell_lists = [[] for _ in range(BOARD_SIZE)]
for line in WIN_LINES:
    for index in range(BOARD_SIZE):
        if line & (1 << index):
            _lines_by_cell_lists[index].append(line)

LINES_BY_CELL = tuple(tuple(lines) for lines in _lines_by_cell_lists)
POSITION_VALUE = tuple(len(lines) for lines in LINES_BY_CELL)


def _has_win(bits: int) -> bool:
    for line in WIN_LINES:
        if bits & line == line:
            return True
    return False


def _winning_move_bits(player: int, opponent: int) -> int:
    """Return all empty cells at which player wins immediately."""
    result = 0
    occupied = player | opponent

    for line in WIN_LINES:
        if line & opponent:
            continue
        owned = line & player
        if owned.bit_count() == 2:
            result |= line & ~occupied

    return result & FULL_MASK


def _fork_move_bits(player: int, opponent: int, empty: int) -> int:
    """
    Return moves that create at least two distinct immediate winning cells.
    Such a move is a forced win when the opponent has no immediate threat.
    """
    forks = 0
    remaining_moves = empty

    while remaining_moves:
        move_bit = remaining_moves & -remaining_moves
        remaining_moves ^= move_bit
        index = move_bit.bit_length() - 1

        future_wins = 0
        for line in LINES_BY_CELL[index]:
            if line & opponent:
                continue

            # One existing mark plus this move creates a two-in-line threat.
            if (line & player).bit_count() == 1:
                future_wins |= line & empty & ~move_bit
                if future_wins.bit_count() >= 2:
                    forks |= move_bit
                    break

    return forks


def _move_order_score(index: int, player: int, opponent: int) -> int:
    move_bit = 1 << index
    occupied = player | opponent
    empty = FULL_MASK & ~occupied
    score = POSITION_VALUE[index] * 40
    created_threats = 0

    for line in LINES_BY_CELL[index]:
        player_count = (line & player).bit_count()
        opponent_count = (line & opponent).bit_count()

        if opponent_count == 0:
            if player_count == 2:
                score += 100_000
            elif player_count == 1:
                score += 1_800
                created_threats |= line & empty & ~move_bit
            else:
                score += 25

        if player_count == 0:
            if opponent_count == 2:
                score += 80_000
            elif opponent_count == 1:
                score += 450

    threat_count = created_threats.bit_count()
    if threat_count >= 2:
        score += 30_000 + threat_count * 2_000
    elif threat_count == 1:
        score += 2_500

    return score


def _ordered_indices(
    move_mask: int,
    player: int,
    opponent: int,
    preferred: int = -1,
) -> list[int]:
    indices = []
    remaining = move_mask

    while remaining:
        bit = remaining & -remaining
        remaining ^= bit
        indices.append(bit.bit_length() - 1)

    indices.sort(
        key=lambda index: (
            1 if index == preferred else 0,
            _move_order_score(index, player, opponent),
            POSITION_VALUE[index],
            -index,
        ),
        reverse=True,
    )
    return indices


def _evaluate(player: int, opponent: int, empty: int) -> int:
    """Static score from the perspective of the side to move."""
    score = 0
    line_weights = (0, 9, 150, WIN_SCORE)

    for line in WIN_LINES:
        player_count = (line & player).bit_count()
        opponent_count = (line & opponent).bit_count()

        if player_count and opponent_count:
            continue
        if player_count:
            score += line_weights[player_count]
        elif opponent_count:
            score -= line_weights[opponent_count] + 1

    # Reward occupation of cells belonging to many winning lines.
    player_bits = player
    while player_bits:
        bit = player_bits & -player_bits
        player_bits ^= bit
        index = bit.bit_length() - 1
        score += POSITION_VALUE[index] * 4

    opponent_bits = opponent
    while opponent_bits:
        bit = opponent_bits & -opponent_bits
        opponent_bits ^= bit
        index = bit.bit_length() - 1
        score -= POSITION_VALUE[index] * 4

    # Estimate future intersection strength at each empty cell.
    remaining = empty
    while remaining:
        move_bit = remaining & -remaining
        remaining ^= move_bit
        index = move_bit.bit_length() - 1

        player_builds = 0
        opponent_builds = 0

        for line in LINES_BY_CELL[index]:
            if not (line & opponent) and (line & player).bit_count() == 1:
                player_builds += 1
            if not (line & player) and (line & opponent).bit_count() == 1:
                opponent_builds += 1

        score += 18 * player_builds * player_builds
        score -= 21 * opponent_builds * opponent_builds

        if opponent_builds >= 2:
            score -= 900 * (opponent_builds - 1)

    # Keep heuristic values well below proven tactical scores.
    return max(-100_000, min(100_000, score))


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    player = 0
    opponent = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                value = board[i][j][k]
                bit = 1 << _cell_index(i, j, k)
                if value == 1:
                    player |= bit
                elif value == -1:
                    opponent |= bit

    empty = FULL_MASK & ~(player | opponent)

    # A completed game should not request another move, but retain a
    # deterministic return value if it does.
    if not empty:
        return 0, 0, 0

    fallback_moves = _ordered_indices(empty, player, opponent)
    fallback_index = fallback_moves[0]

    # Win immediately whenever possible.
    immediate_wins = _winning_move_bits(player, opponent)
    if immediate_wins:
        best = _ordered_indices(immediate_wins, player, opponent)[0]
        return _coordinates(best)

    # An opponent immediate win has to be blocked.
    opponent_wins = _winning_move_bits(opponent, player)
    if opponent_wins:
        blocks = _ordered_indices(opponent_wins, player, opponent)
        return _coordinates(blocks[0])

    # Create a guaranteed double threat.
    forks = _fork_move_bits(player, opponent, empty)
    if forks:
        best = _ordered_indices(forks, player, opponent)[0]
        return _coordinates(best)

    occupied_count = BOARD_SIZE - empty.bit_count()
    center_index = _cell_index(1, 1, 1)
    center_bit = 1 << center_index

    # Strong, symmetry-preserving opening policy.
    if occupied_count <= 1:
        if empty & center_bit:
            return 1, 1, 1
        return _coordinates(fallback_index)

    deadline = perf_counter() + 0.92
    transposition = {}
    node_count = 0

    # TT flags.
    EXACT = 0
    LOWER = 1
    UPPER = 2

    class SearchTimeout(Exception):
        pass

    def negamax(
        side: int,
        other: int,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> int:
        nonlocal node_count

        node_count += 1
        if (node_count & 127) == 0 and perf_counter() >= deadline:
            raise SearchTimeout

        if _has_win(other):
            return -WIN_SCORE + ply

        local_empty = FULL_MASK & ~(side | other)
        if not local_empty:
            return 0

        side_wins = _winning_move_bits(side, other)
        if side_wins:
            return WIN_SCORE - ply - 1

        other_wins = _winning_move_bits(other, side)
        threat_count = other_wins.bit_count()

        if threat_count >= 2:
            return -WIN_SCORE + ply + 2

        forced_move = other_wins if threat_count == 1 else 0

        if not forced_move:
            side_forks = _fork_move_bits(side, other, local_empty)
            if side_forks:
                return WIN_SCORE - ply - 3

        if depth <= 0 and not forced_move:
            return _evaluate(side, other, local_empty)

        key = (side, other)
        original_alpha = alpha
        preferred = -1

        entry = transposition.get(key)
        if entry is not None:
            stored_depth, flag, value, stored_best = entry
            preferred = stored_best

            if stored_depth >= depth:
                if flag == EXACT:
                    return value
                if flag == LOWER:
                    alpha = max(alpha, value)
                elif flag == UPPER:
                    beta = min(beta, value)

                if alpha >= beta:
                    return value

        move_mask = forced_move if forced_move else local_empty
        moves = _ordered_indices(move_mask, side, other, preferred)

        best_value = -INF
        best_move = moves[0]
        child_depth = max(0, depth - 1)

        for index in moves:
            move_bit = 1 << index
            value = -negamax(
                other,
                side | move_bit,
                child_depth,
                -beta,
                -alpha,
                ply + 1,
            )

            if value > best_value:
                best_value = value
                best_move = index

            if value > alpha:
                alpha = value

            if alpha >= beta:
                break

        if best_value <= original_alpha:
            result_flag = UPPER
        elif best_value >= beta:
            result_flag = LOWER
        else:
            result_flag = EXACT

        old_entry = transposition.get(key)
        if old_entry is None or depth >= old_entry[0]:
            transposition[key] = (depth, result_flag, best_value, best_move)

        return best_value

    root_moves = fallback_moves
    best_index = fallback_index
    best_completed_score = -INF
    maximum_depth = empty.bit_count()

    # Iterative deepening guarantees that the last fully completed result is
    # used if the time limit is reached during a deeper search.
    for depth in range(1, maximum_depth + 1):
        iteration_best = root_moves[0]
        iteration_score = -INF
        alpha = -INF

        ordered_root = [best_index]
        ordered_root.extend(index for index in root_moves if index != best_index)

        try:
            for index in ordered_root:
                if perf_counter() >= deadline:
                    raise SearchTimeout

                move_bit = 1 << index
                value = -negamax(
                    opponent,
                    player | move_bit,
                    depth - 1,
                    -INF,
                    -alpha,
                    1,
                )

                if value > iteration_score:
                    iteration_score = value
                    iteration_best = index

                if value > alpha:
                    alpha = value

        except SearchTimeout:
            break

        best_index = iteration_best
        best_completed_score = iteration_score
        root_moves = [best_index] + [
            index for index in root_moves if index != best_index
        ]

        # This is a proven tactical win, so deeper searching is unnecessary.
        if best_completed_score >= WIN_SCORE - 100:
            break

    return _coordinates(best_index)
