
from time import perf_counter


# Winning rows, columns, and diagonals for a 4x4 board.
WIN_MASKS = []

for r in range(4):
    WIN_MASKS.append(0b1111 << (4 * r))

for c in range(4):
    mask = 0
    for r in range(4):
        mask |= 1 << (4 * r + c)
    WIN_MASKS.append(mask)

WIN_MASKS.append(sum(1 << (5 * i) for i in range(4)))
WIN_MASKS.append(sum(1 << (3 + 3 * i) for i in range(4)))

WIN_MASKS = tuple(WIN_MASKS)
FULL_MASK = (1 << 16) - 1

CELL_LINES = []
for index in range(16):
    bit = 1 << index
    CELL_LINES.append(tuple(mask for mask in WIN_MASKS if mask & bit))
CELL_LINES = tuple(CELL_LINES)

# Preferred order among otherwise similar moves.
BASE_ORDER = (
    5, 6, 9, 10,       # central diagonal cells
    0, 3, 12, 15,      # corners
    1, 2, 4, 7, 8, 11, 13, 14
)
BASE_RANK = [0] * 16
for rank, index in enumerate(BASE_ORDER):
    BASE_RANK[index] = rank

MATE = 1_000_000
INF = 10_000_000


class _SearchTimeout(Exception):
    pass


def _has_win(bits: int) -> bool:
    for mask in WIN_MASKS:
        if bits & mask == mask:
            return True
    return False


def _winning_moves(player: int, opponent: int) -> int:
    """Return a bit mask of moves that win immediately for player."""
    result = 0
    for mask in WIN_MASKS:
        if not (mask & opponent) and (mask & player).bit_count() == 3:
            result |= mask & ~(player | opponent)
    return result


def _find_fork(player: int, opponent: int) -> int:
    """
    Return one move that creates at least two distinct immediate winning
    threats, or zero if no such move exists.
    """
    empty = FULL_MASK ^ (player | opponent)

    while empty:
        bit = empty & -empty
        empty ^= bit
        index = bit.bit_length() - 1
        threats = 0

        for mask in CELL_LINES[index]:
            if not (mask & opponent) and (mask & player).bit_count() == 2:
                threats += 1
                if threats >= 2:
                    return bit

    return 0


def _count_forks(player: int, opponent: int) -> int:
    empty = FULL_MASK ^ (player | opponent)
    count = 0

    while empty:
        bit = empty & -empty
        empty ^= bit
        index = bit.bit_length() - 1
        threats = 0

        for mask in CELL_LINES[index]:
            if not (mask & opponent) and (mask & player).bit_count() == 2:
                threats += 1
                if threats >= 2:
                    count += 1
                    break

    return count


def _evaluate(me: int, opponent: int, turn: int) -> int:
    """Static evaluation from the policy player's perspective."""
    weights = (0, 3, 22, 180, 0)
    score = 0

    for mask in WIN_MASKS:
        mine = (me & mask).bit_count()
        theirs = (opponent & mask).bit_count()

        if theirs == 0:
            score += weights[mine]
        elif mine == 0:
            score -= weights[theirs]

    # Potential forks are especially important in 4x4 play.
    score += 300 * (
        _count_forks(me, opponent) - _count_forks(opponent, me)
    )

    # Small tempo preference.
    score += 4 if turn == 1 else -4
    return score


def _move_order_score(bit: int, player: int, opponent: int) -> int:
    index = bit.bit_length() - 1
    score = 20 * (16 - BASE_RANK[index])
    created_threats = 0

    for mask in CELL_LINES[index]:
        if not (mask & opponent):
            count = (mask & player).bit_count() + 1
            if count == 3:
                created_threats += 1
            score += (0, 4, 28, 190, 10000)[count]

        if not (mask & player):
            opponent_count = (mask & opponent).bit_count()
            score += (0, 5, 34, 240, 0)[opponent_count]

    if created_threats >= 2:
        score += 50_000
    elif created_threats == 1:
        score += 5_000

    return score


def _ordered_moves(player: int, opponent: int) -> list[int]:
    empty = FULL_MASK ^ (player | opponent)
    moves = []

    while empty:
        bit = empty & -empty
        empty ^= bit
        moves.append(bit)

    moves.sort(
        key=lambda move: _move_order_score(move, player, opponent),
        reverse=True,
    )
    return moves


def _to_action(bit: int) -> tuple[int, int]:
    index = bit.bit_length() - 1
    return index // 4, index % 4


def policy(board: list[list[int]]) -> tuple[int, int]:
    me = 0
    opponent = 0
    legal_bits = []

    for row in range(4):
        for col in range(4):
            index = 4 * row + col
            value = board[row][col]

            if value == 1:
                me |= 1 << index
            elif value == -1:
                opponent |= 1 << index
            elif value == 0:
                legal_bits.append(1 << index)

    # Normal game states always have at least one empty cell.
    if not legal_bits:
        return 0, 0

    # Establish a legal fallback before doing any search.
    fallback = min(
        legal_bits,
        key=lambda bit: BASE_RANK[bit.bit_length() - 1],
    )

    # If called after a terminal state, still return an empty cell.
    if _has_win(me) or _has_win(opponent):
        return _to_action(fallback)

    my_wins = _winning_moves(me, opponent)
    if my_wins:
        return _to_action(my_wins & -my_wins)

    opponent_wins = _winning_moves(opponent, me)
    opponent_win_count = opponent_wins.bit_count()

    # A single immediate threat must be blocked.
    if opponent_win_count == 1:
        return _to_action(opponent_wins)

    # Multiple immediate threats cannot all be stopped. Block one to retain
    # the best chance against a fallible opponent.
    if opponent_win_count >= 2:
        possible_blocks = []
        bits = opponent_wins
        while bits:
            bit = bits & -bits
            bits ^= bit
            possible_blocks.append(bit)

        best_block = max(
            possible_blocks,
            key=lambda bit: _move_order_score(bit, me, opponent),
        )
        return _to_action(best_block)

    # An immediate fork is a forced win.
    my_fork = _find_fork(me, opponent)
    if my_fork:
        return _to_action(my_fork)

    occupied_count = (me | opponent).bit_count()

    # Symmetric opening: avoid spending the time budget on an empty board.
    if occupied_count == 0:
        return 1, 1

    deadline = perf_counter() + 0.94
    nodes = 0

    # key -> (searched depth, value, bound flag)
    # flag: 0 exact, -1 upper bound, 1 lower bound
    transposition = {}

    def check_time() -> None:
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

    def search(
        mine: int,
        theirs: int,
        turn: int,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
    ) -> int:
        check_time()

        if _has_win(mine):
            return MATE - ply
        if _has_win(theirs):
            return -MATE + ply

        occupied = mine | theirs
        if occupied == FULL_MASK:
            return 0

        key = (mine, theirs, turn)
        original_alpha = alpha
        original_beta = beta

        cached = transposition.get(key)
        if cached is not None:
            cached_depth, cached_value, flag = cached
            if cached_depth >= depth:
                if flag == 0:
                    return cached_value
                if flag == 1:
                    alpha = max(alpha, cached_value)
                else:
                    beta = min(beta, cached_value)

                if alpha >= beta:
                    return cached_value

        if turn == 1:
            player = mine
            other = theirs
        else:
            player = theirs
            other = mine

        current_wins = _winning_moves(player, other)
        if current_wins:
            value = (
                MATE - (ply + 1)
                if turn == 1
                else -MATE + (ply + 1)
            )
            transposition[key] = (depth, value, 0)
            return value

        enemy_wins = _winning_moves(other, player)
        enemy_win_count = enemy_wins.bit_count()

        if enemy_win_count >= 2:
            # Current player can block only one; the other side wins next turn.
            value = (
                -MATE + (ply + 2)
                if turn == 1
                else MATE - (ply + 2)
            )
            transposition[key] = (depth, value, 0)
            return value

        forced_move = enemy_wins if enemy_win_count == 1 else 0

        # A fork is a forced win, but only when there is no immediate threat
        # that must first be answered.
        if not forced_move:
            fork = _find_fork(player, other)
            if fork:
                value = (
                    MATE - (ply + 3)
                    if turn == 1
                    else -MATE + (ply + 3)
                )
                transposition[key] = (depth, value, 0)
                return value

        # Continue forced blocking sequences even beyond the nominal horizon.
        if depth <= 0 and not forced_move:
            value = _evaluate(mine, theirs, turn)
            transposition[key] = (depth, value, 0)
            return value

        if forced_move:
            moves = [forced_move]
        else:
            moves = _ordered_moves(player, other)

        if turn == 1:
            value = -INF

            for bit in moves:
                child = search(
                    mine | bit,
                    theirs,
                    -1,
                    depth - 1,
                    alpha,
                    beta,
                    ply + 1,
                )

                if child > value:
                    value = child
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        else:
            value = INF

            for bit in moves:
                child = search(
                    mine,
                    theirs | bit,
                    1,
                    depth - 1,
                    alpha,
                    beta,
                    ply + 1,
                )

                if child < value:
                    value = child
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

        if value <= original_alpha:
            flag = -1
        elif value >= original_beta:
            flag = 1
        else:
            flag = 0

        transposition[key] = (depth, value, flag)
        return value

    root_moves = _ordered_moves(me, opponent)
    best_move = root_moves[0]
    best_score = -INF
    empty_count = len(root_moves)

    try:
        for depth in range(1, empty_count + 1):
            if perf_counter() >= deadline:
                break

            # Search the previous iteration's principal move first.
            ordered = _ordered_moves(me, opponent)
            if best_move in ordered:
                ordered.remove(best_move)
                ordered.insert(0, best_move)

            iteration_best_move = ordered[0]
            iteration_best_score = -INF
            alpha = -INF

            for bit in ordered:
                if perf_counter() >= deadline:
                    raise _SearchTimeout

                value = search(
                    me | bit,
                    opponent,
                    -1,
                    depth - 1,
                    alpha,
                    INF,
                    1,
                )

                if value > iteration_best_score:
                    iteration_best_score = value
                    iteration_best_move = bit

                if value > alpha:
                    alpha = value

            # Only commit results from a fully completed depth.
            best_move = iteration_best_move
            best_score = iteration_best_score

            # Mate scores are exact tactical proofs.
            if abs(best_score) > MATE - 100:
                break

    except _SearchTimeout:
        pass

    return _to_action(best_move)
