
import time


# Generate every straight winning line in the 3x3x3 cube.
# There are 49 such lines: 27 axial, 18 planar diagonal, and 4 spatial.
def _generate_lines():
    masks = set()

    directions = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if di == 0 and dj == 0 and dk == 0:
                    continue

                # Keep only one of each direction/reverse-direction pair.
                first = di if di != 0 else (dj if dj != 0 else dk)
                if first > 0:
                    directions.append((di, dj, dk))

    for di, dj, dk in directions:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    i2 = i + 2 * di
                    j2 = j + 2 * dj
                    k2 = k + 2 * dk
                    if not (0 <= i2 < 3 and 0 <= j2 < 3 and 0 <= k2 < 3):
                        continue

                    mask = 0
                    for step in range(3):
                        x = i + step * di
                        y = j + step * dj
                        z = k + step * dk
                        index = x * 9 + y * 3 + z
                        mask |= 1 << index
                    masks.add(mask)

    return tuple(sorted(masks))


_LINES = _generate_lines()
_FULL = (1 << 27) - 1
_CENTER = 1 << 13
_WIN_SCORE = 100000
_INF = 1000000

_CELL_LINES = [0] * 27
for _line in _LINES:
    _remaining = _line
    while _remaining:
        _bit = _remaining & -_remaining
        _CELL_LINES[_bit.bit_length() - 1] += 1
        _remaining ^= _bit

_CORNERS = tuple(
    1 << (i * 9 + j * 3 + k)
    for i in (0, 2)
    for j in (0, 2)
    for k in (0, 2)
)


class _SearchTimeout(Exception):
    pass


def _winning_moves(own, opponent):
    """Return all cells that complete an immediate winning line."""
    result = 0
    occupied = own | opponent
    for line in _LINES:
        if line & opponent:
            continue
        own_part = line & own
        if own_part.bit_count() == 2:
            result |= line & ~occupied
    return result


def _threat_targets(own, opponent, empty):
    """
    For each possible move, record the cells that would subsequently be
    immediate winning moves. Two distinct targets constitute a fork.
    """
    targets = [0] * 27

    for line in _LINES:
        if line & opponent:
            continue
        if (line & own).bit_count() != 1:
            continue

        vacant = line & empty
        if vacant.bit_count() != 2:
            continue

        first = vacant & -vacant
        second = vacant ^ first
        targets[first.bit_length() - 1] |= second
        targets[second.bit_length() - 1] |= first

    return targets


def _fork_mask(targets, empty):
    result = 0
    remaining = empty
    while remaining:
        bit = remaining & -remaining
        index = bit.bit_length() - 1
        if targets[index].bit_count() >= 2:
            result |= bit
        remaining ^= bit
    return result


def _coord(bit):
    index = bit.bit_length() - 1
    return index // 9, (index % 9) // 3, index % 3


def _evaluate(own, opponent, own_targets=None):
    """Strategic evaluation from the side-to-move's perspective."""
    occupied = own | opponent
    empty = _FULL & ~occupied

    if own_targets is None:
        own_targets = _threat_targets(own, opponent, empty)
    opponent_targets = _threat_targets(opponent, own, empty)

    # Values for open lines containing zero, one, two, or three marks.
    line_value = (0, 14, 220, 8000)
    score = 4  # Small initiative bonus.

    for line in _LINES:
        own_count = (line & own).bit_count()
        opponent_count = (line & opponent).bit_count()

        if opponent_count == 0:
            score += line_value[own_count]
        if own_count == 0:
            score -= line_value[opponent_count]

    remaining = own
    while remaining:
        bit = remaining & -remaining
        score += 3 * _CELL_LINES[bit.bit_length() - 1]
        remaining ^= bit

    remaining = opponent
    while remaining:
        bit = remaining & -remaining
        score -= 3 * _CELL_LINES[bit.bit_length() - 1]
        remaining ^= bit

    own_pressure = 0
    opponent_pressure = 0
    opponent_forks = 0

    remaining = empty
    while remaining:
        bit = remaining & -remaining
        index = bit.bit_length() - 1

        own_count = own_targets[index].bit_count()
        opponent_count = opponent_targets[index].bit_count()

        own_pressure += own_count * own_count
        opponent_pressure += opponent_count * opponent_count

        if opponent_count >= 2:
            opponent_forks += 1

        remaining ^= bit

    score += 42 * own_pressure
    score -= 42 * opponent_pressure
    score -= 950 * opponent_forks

    if score > 30000:
        return 30000
    if score < -30000:
        return -30000
    return score


def _ordered_moves(empty, own, opponent, own_targets, history, preferred=0):
    opponent_targets = _threat_targets(opponent, own, empty)
    ranked = []

    remaining = empty
    while remaining:
        bit = remaining & -remaining
        index = bit.bit_length() - 1

        own_threats = own_targets[index].bit_count()
        opponent_threats = opponent_targets[index].bit_count()

        value = history[index]
        value += 1250 * own_threats
        value += 700 * opponent_threats
        value += 14 * _CELL_LINES[index]

        if opponent_threats >= 2:
            value += 2600
        if bit == _CENTER:
            value += 500
        if bit == preferred:
            value += 1000000

        ranked.append((value, bit))
        remaining ^= bit

    ranked.sort(reverse=True)
    return [bit for _, bit in ranked]


def _best_bit(mask, own, opponent):
    """Choose a strong deterministic move from a supplied legal mask."""
    occupied = own | opponent
    empty = _FULL & ~occupied
    own_targets = _threat_targets(own, opponent, empty)
    opponent_targets = _threat_targets(opponent, own, empty)

    best_bit = mask & -mask
    best_value = -_INF

    remaining = mask
    while remaining:
        bit = remaining & -remaining
        index = bit.bit_length() - 1

        value = 20 * _CELL_LINES[index]
        value += 1100 * own_targets[index].bit_count()
        value += 750 * opponent_targets[index].bit_count()

        if bit == _CENTER:
            value += 1000

        if value > best_value:
            best_value = value
            best_bit = bit

        remaining ^= bit

    return best_bit


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    own = 0
    opponent = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                value = board[i][j][k]
                bit = 1 << (i * 9 + j * 3 + k)
                if value == 1:
                    own |= bit
                elif value == -1:
                    opponent |= bit

    occupied = own | opponent
    empty = _FULL & ~occupied

    # A full board has no legal move. Valid arena calls should never reach this.
    if not empty:
        return 0, 0, 0

    # Establish a legal fallback before doing any expensive work.
    fallback = empty & -empty

    # Always win immediately when possible.
    immediate_win = _winning_moves(own, opponent)
    if immediate_win:
        return _coord(_best_bit(immediate_win, own, opponent))

    # Immediate opposing wins must be blocked.
    opponent_wins = _winning_moves(opponent, own)
    if opponent_wins:
        return _coord(_best_bit(opponent_wins, own, opponent))

    move_count = occupied.bit_count()

    # Strong and symmetry-preserving opening choices.
    if move_count == 0 and (empty & _CENTER):
        return 1, 1, 1

    if move_count == 1:
        if empty & _CENTER:
            return 1, 1, 1

        available_corners = empty
        corner_mask = 0
        for corner in _CORNERS:
            corner_mask |= corner
        available_corners &= corner_mask

        if available_corners:
            return _coord(_best_bit(available_corners, own, opponent))

    own_targets = _threat_targets(own, opponent, empty)
    own_forks = _fork_mask(own_targets, empty)

    # With no immediate opposing win, a two-target fork is a forced win.
    if own_forks:
        return _coord(_best_bit(own_forks, own, opponent))

    history = [0] * 27
    initial_order = _ordered_moves(
        empty, own, opponent, own_targets, history
    )
    if initial_order:
        fallback = initial_order[0]

    deadline = time.perf_counter() + 0.88
    nodes = 0

    # Entry format: depth, value, flag, best_move
    # flag: -1 = upper bound, 0 = exact, 1 = lower bound
    transposition = {}

    def search(current, other, depth, alpha, beta, ply):
        nonlocal nodes

        nodes += 1
        if (nodes & 127) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        occupied_here = current | other
        empty_here = _FULL & ~occupied_here

        if not empty_here:
            return 0

        key = (current, other)
        alpha_original = alpha
        beta_original = beta

        entry = transposition.get(key)
        preferred = 0

        if entry is not None:
            stored_depth, stored_value, flag, preferred = entry
            if stored_depth >= depth:
                if flag == 0:
                    return stored_value
                if flag == 1:
                    if stored_value > alpha:
                        alpha = stored_value
                else:
                    if stored_value < beta:
                        beta = stored_value
                if alpha >= beta:
                    return stored_value

        current_wins = _winning_moves(current, other)
        if current_wins:
            return _WIN_SCORE - (ply + 1)

        other_wins = _winning_moves(other, current)

        # Distinct immediate winning cells cannot all be blocked.
        if other_wins.bit_count() >= 2:
            return -_WIN_SCORE + (ply + 2)

        forced = other_wins

        if not forced:
            current_targets = _threat_targets(
                current, other, empty_here
            )
            current_forks = _fork_mask(current_targets, empty_here)

            if current_forks:
                return _WIN_SCORE - (ply + 3)

            if depth <= 0:
                return _evaluate(current, other, current_targets)

            moves = _ordered_moves(
                empty_here,
                current,
                other,
                current_targets,
                history,
                preferred,
            )
            next_depth = depth - 1
        else:
            # Forced defensive moves do not consume strategic search depth.
            moves = [forced]
            next_depth = depth

        best_value = -_INF
        best_move = moves[0]

        for move in moves:
            value = -search(
                other,
                current | move,
                next_depth,
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
                index = move.bit_length() - 1
                bonus_depth = depth if depth > 0 else 1
                history[index] += bonus_depth * bonus_depth
                break

        if best_value <= alpha_original:
            result_flag = -1
        elif best_value >= beta_original:
            result_flag = 1
        else:
            result_flag = 0

        old_entry = transposition.get(key)
        if old_entry is None or old_entry[0] <= depth:
            transposition[key] = (
                depth,
                best_value,
                result_flag,
                best_move,
            )

        return best_value

    root_moves = initial_order
    best_move = fallback
    best_score = -_INF
    empty_count = empty.bit_count()

    maximum_depth = empty_count if empty_count <= 9 else 9

    for depth in range(1, maximum_depth + 1):
        if time.perf_counter() >= deadline:
            break

        ordered_root = list(root_moves)
        if best_move in ordered_root:
            ordered_root.remove(best_move)
            ordered_root.insert(0, best_move)

        iteration_best = None
        iteration_score = -_INF
        iteration_values = []
        alpha = -_INF

        try:
            for move in ordered_root:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                value = -search(
                    opponent,
                    own | move,
                    depth - 1,
                    -_INF,
                    -alpha,
                    1,
                )

                iteration_values.append((value, move))

                if value > iteration_score:
                    iteration_score = value
                    iteration_best = move

                if value > alpha:
                    alpha = value

        except _SearchTimeout:
            break

        if iteration_best is not None:
            best_move = iteration_best
            best_score = iteration_score
            iteration_values.sort(reverse=True)
            root_moves = [move for _, move in iteration_values]

        # A completed forced-mate result needs no further deepening.
        if abs(best_score) >= _WIN_SCORE - 40:
            break

    # best_move was selected exclusively from the current empty-cell mask.
    return _coord(best_move)
