
import time

_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)
_SIZE = 6
_INF = 10**9
_WIN = 10**6
_MAX_DEPTH = 4
_ROOT_WIDTH = 80
_TIME_LIMIT = 0.88


class _Timeout(Exception):
    pass


def _coord(index):
    return index // _SIZE, index % _SIZE


def _queen_distance(grid, side):
    """Queen-move distances through empty squares, ignoring amazons only as endpoints."""
    distances = [9999] * 36
    queue = []

    for i, value in enumerate(grid):
        if value == side:
            distances[i] = 0
            queue.append(i)

    head = 0
    while head < len(queue):
        current = queue[head]
        head += 1
        r, c = _coord(current)

        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            next_dist = distances[current] + 1

            while 0 <= nr < _SIZE and 0 <= nc < _SIZE:
                index = nr * _SIZE + nc

                # Arrows and amazons block queen paths.
                if grid[index] != 0:
                    break

                if distances[index] > next_dist:
                    distances[index] = next_dist
                    queue.append(index)

                nr += dr
                nc += dc

    return distances


def _territory_difference(grid, side, opponent):
    own_dist = _queen_distance(grid, side)
    opp_dist = _queen_distance(grid, opponent)

    difference = 0
    for i, value in enumerate(grid):
        if value != 0:
            continue

        if own_dist[i] < opp_dist[i]:
            difference += 1
        elif opp_dist[i] < own_dist[i]:
            difference -= 1

    return difference


def _mobility(grid, side):
    """Number of queen-move landing squares available to `side`."""
    total = 0

    for i, value in enumerate(grid):
        if value != side:
            continue

        r, c = _coord(i)
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < _SIZE and 0 <= nc < _SIZE:
                index = nr * _SIZE + nc
                if grid[index] != 0:
                    break
                total += 1
                nr += dr
                nc += dc

    return total


def _evaluate(board, side):
    grid = board.ravel()
    opponent = 3 - side

    territory = _territory_difference(grid, side, opponent)
    own_mobility = _mobility(grid, side)
    opp_mobility = _mobility(grid, opponent)

    empty_count = sum(1 for v in grid if v == 0)

    # Territory becomes increasingly decisive as arrows close the board.
    if empty_count > 15:
        territory_weight = 10
        mobility_weight = 3
    else:
        territory_weight = 18
        mobility_weight = 2

    return (
        territory_weight * territory
        + mobility_weight * (own_mobility - opp_mobility)
    )


def _quick_move_score(board, opponent, empty_count, from_i, to_i, arrow_i):
    """
    Cheap ordering heuristic. The board is temporarily in the post-amazon-move,
    pre-arrow state.
    """
    grid = board.ravel()
    opponent_positions = [i for i, v in enumerate(grid) if v == opponent]

    ar, ac = _coord(arrow_i)
    tr, tc = _coord(to_i)

    # Closeness to the center is useful while the board is open.
    center_distance = abs(ar - 2.5) + abs(ac - 2.5)
    center_score = 3.0 - center_distance

    if opponent_positions:
        opponent_distance = min(
            abs(ar - _coord(i)[0]) + abs(ac - _coord(i)[1])
            for i in opponent_positions
        )
    else:
        opponent_distance = 6

    if empty_count >= 14:
        # Early game: develop toward controlled central territory.
        phase_score = 5.0 * center_score
    else:
        # Late game: arrows near opponents are often highly restrictive.
        phase_score = max(0.0, 7.0 - opponent_distance) * 7.0

    destination_center = 3.0 - (abs(tr - 2.5) + abs(tc - 2.5))

    return phase_score + destination_center


def _generate_moves(board, side):
    """
    Generate tuples of:
        (ordering_score, from_index, to_index, arrow_index)

    The function temporarily mutates and then restores the board.
    """
    flat = board.ravel()
    opponent = 3 - side
    empty_count = sum(1 for v in flat if v == 0)
    moves = []

    sources = [i for i, v in enumerate(flat) if v == side]

    for from_i in sources:
        r, c = _coord(from_i)

        # Vacate the source while considering amazon destinations.
        flat[from_i] = 0

        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc

            while 0 <= nr < _SIZE and 0 <= nc < _SIZE:
                to_i = nr * _SIZE + nc

                if flat[to_i] == 0:
                    # Occupy the destination before enumerating legal arrows.
                    flat[to_i] = side

                    for adr, adc in _DIRS:
                        ar, ac = nr + adr, nc + adc

                        while 0 <= ar < _SIZE and 0 <= ac < _SIZE:
                            arrow_i = ar * _SIZE + ac

                            if flat[arrow_i] == 0:
                                score = _quick_move_score(
                                    board, opponent, empty_count,
                                    from_i, to_i, arrow_i
                                )
                                moves.append((score, from_i, to_i, arrow_i))
                            else:
                                break

                            ar += adr
                            ac += adc

                    flat[to_i] = 0
                else:
                    break

                nr += dr
                nc += dc

        flat[from_i] = side

    return moves


def policy(board) -> str:
    side = 1
    deadline = time.perf_counter() + _TIME_LIMIT
    nodes = 0

    def check_time():
        if time.perf_counter() >= deadline:
            raise _Timeout()

    def do_move(move):
        _, from_i, to_i, arrow_i = move
        flat = board.ravel()
        flat[from_i] = 0
        flat[to_i] = side_if_current
        flat[arrow_i] = -1

    def apply_move(move, current_side):
        _, from_i, to_i, arrow_i = move
        flat = board.ravel()
        flat[from_i] = 0
        flat[to_i] = current_side
        flat[arrow_i] = -1

    def undo_move(move, current_side):
        _, from_i, to_i, arrow_i = move
        flat = board.ravel()
        flat[arrow_i] = 0
        flat[to_i] = 0
        flat[from_i] = current_side

    def search(depth, current_side, alpha, beta):
        nonlocal nodes
        nodes += 1

        if (nodes & 15) == 0:
            check_time()

        if depth == 0:
            return _evaluate(board, current_side)

        moves = _generate_moves(board, current_side)
        if not moves:
            return -_WIN + depth

        moves.sort(key=lambda item: item[0], reverse=True)

        # Wider at low remaining depth; narrower deeper in the tree.
        if depth >= 3:
            width = 30
        elif depth == 2:
            width = 24
        else:
            width = 18

        if len(moves) > width:
            moves = moves[:width]

        best = -_INF
        opponent = 3 - current_side

        for move in moves:
            if alpha >= beta:
                break

            if (nodes & 31) == 0:
                check_time()

            apply_move(move, current_side)
            try:
                value = -search(depth - 1, opponent, -beta, -alpha)
            finally:
                undo_move(move, current_side)

            if value > best:
                best = value

            if value > alpha:
                alpha = value

        return best

    root_moves = _generate_moves(board, side)

    if not root_moves:
        # Terminal input should never normally be supplied. There cannot be a
        # legal string when no move exists, but return a well-formed placeholder
        # rather than risk an exception.
        return "0,0:0,1:0,2"

    root_moves.sort(key=lambda item: item[0], reverse=True)
    if len(root_moves) > _ROOT_WIDTH:
        root_moves = root_moves[:_ROOT_WIDTH]

    ordered_moves = root_moves
    best_move = ordered_moves[0]

    try:
        depth = 1
        while depth <= _MAX_DEPTH:
            check_time()

            completed = []
            iteration_best = ordered_moves[0]
            iteration_best_value = -_INF
            alpha = -_INF
            beta = _INF

            for move in ordered_moves:
                check_time()

                apply_move(move, side)
                try:
                    value = -search(depth - 1, 3 - side, -beta, -alpha)
                finally:
                    undo_move(move, side)

                completed.append((value, move[1], move[2], move[3]))

                if value > iteration_best_value:
                    iteration_best_value = value
                    iteration_best = move

                if value > alpha:
                    alpha = value

            # This depth completed fully, so its result is trustworthy.
            ordered_moves = completed
            ordered_moves.sort(key=lambda item: item[0], reverse=True)

            # Convert result tuples back to full move tuples.
            full_by_identity = {
                (m[1], m[2], m[3]): m for m in root_moves
            }
            ordered_moves = [
                full_by_identity[(m[1], m[2], m[3])]
                for m in ordered_moves
            ]
            best_move = iteration_best
            depth += 1

    except _Timeout:
        pass

    _, from_i, to_i, arrow_i = best_move
    fr, fc = _coord(from_i)
    tr, tc = _coord(to_i)
    ar, ac = _coord(arrow_i)

    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
