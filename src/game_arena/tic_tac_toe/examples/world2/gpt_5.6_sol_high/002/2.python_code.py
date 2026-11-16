
from functools import lru_cache
from time import perf_counter


# Bit i represents square (i // 4, i % 4).
FULL = (1 << 16) - 1

LINES = (
    0x000F, 0x00F0, 0x0F00, 0xF000,  # rows
    0x1111, 0x2222, 0x4444, 0x8888,  # columns
    0x8421, 0x1248,                  # diagonals
)

CELL_LINES = tuple(
    tuple(line for line in LINES if line & (1 << square))
    for square in range(16)
)

MATE = 1_000_000
INF = 1_100_000

EXACT = 0
LOWER = 1
UPPER = 2

# key -> (searched_depth, value, bound_type, best_move_index)
_TT = {}

_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


@lru_cache(maxsize=65536)
def _has_win(bits: int) -> bool:
    for line in LINES:
        if bits & line == line:
            return True
    return False


@lru_cache(maxsize=65536)
def _completions(bits: int) -> int:
    """Squares which would complete a four-in-a-row for bits.

    Occupied opponent squares are removed by the caller.
    """
    result = 0
    for line in LINES:
        occupied = bits & line
        if occupied.bit_count() == 3:
            result |= line & ~bits
    return result & FULL


def _winning_moves(player: int, opponent: int) -> int:
    return _completions(player) & ~(player | opponent) & FULL


def _evaluate(me: int, opponent: int) -> int:
    # Antisymmetric line-potential evaluation.
    weights = (0, 3, 28, 2400, MATE)
    value = 0

    for line in LINES:
        mine = (me & line).bit_count()
        theirs = (opponent & line).bit_count()

        if theirs == 0:
            value += weights[mine]
        elif mine == 0:
            value -= weights[theirs]

    return value


def _move_order_score(me: int, opponent: int, bit: int) -> int:
    square = bit.bit_length() - 1
    score = len(CELL_LINES[square]) * 4

    for line in CELL_LINES[square]:
        mine = (me & line).bit_count()
        theirs = (opponent & line).bit_count()

        if theirs == 0:
            score += (5, 25, 230, 5000)[mine]
        if mine == 0:
            score += (3, 18, 190, 4500)[theirs]

    remaining = FULL & ~(me | opponent | bit)
    threats = (_completions(me | bit) & remaining).bit_count()

    if threats >= 2:
        score += 100000
    elif threats == 1:
        score += 1200

    return score


def _ordered_moves(
    me: int,
    opponent: int,
    empty: int,
    preferred: int = -1
) -> list[int]:
    moves = []
    remaining = empty

    while remaining:
        bit = remaining & -remaining
        remaining -= bit
        square = bit.bit_length() - 1

        score = _move_order_score(me, opponent, bit)
        if square == preferred:
            score += 1_000_000

        moves.append((score, bit))

    moves.sort(reverse=True)
    return [bit for _, bit in moves]


def _fork_move(me: int, opponent: int, empty: int) -> int:
    """Return a move producing two distinct immediate wins, or zero."""
    for bit in _ordered_moves(me, opponent, empty):
        remaining = empty ^ bit
        threats = _completions(me | bit) & remaining
        if threats.bit_count() >= 2:
            return bit
    return 0


def _store_tt(
    key: tuple[int, int],
    depth: int,
    value: int,
    flag: int,
    best: int
) -> None:
    old = _TT.get(key)

    if (
        old is None
        or depth > old[0]
        or (
            depth == old[0]
            and (flag == EXACT or old[2] != EXACT)
        )
    ):
        _TT[key] = (depth, value, flag, best)


def _search(me: int, opponent: int, depth: int, alpha: int, beta: int) -> int:
    global _nodes

    _nodes += 1
    if (_nodes & 511) == 0 and perf_counter() >= _deadline:
        raise _Timeout

    # Robust handling of terminal positions.
    if _has_win(opponent):
        return -MATE
    if _has_win(me):
        return MATE

    occupied = me | opponent
    empty = FULL & ~occupied

    if not empty:
        return 0

    requested_depth = max(depth, 0)
    key = (me, opponent)
    entry = _TT.get(key)
    preferred = -1

    alpha_original = alpha
    beta_original = beta

    if entry is not None:
        stored_depth, stored_value, flag, preferred = entry

        if stored_depth >= requested_depth:
            if flag == EXACT:
                return stored_value
            if flag == LOWER:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)

            if alpha >= beta:
                return stored_value

    # Win immediately whenever possible.
    my_wins = _winning_moves(me, opponent)
    if my_wins:
        bit = my_wins & -my_wins
        best = bit.bit_length() - 1
        _store_tt(key, 16, MATE, EXACT, best)
        return MATE

    opponent_wins = _winning_moves(opponent, me)

    # Two distinct winning squares cannot both be blocked.
    if opponent_wins.bit_count() >= 2:
        _store_tt(key, 16, -MATE, EXACT, -1)
        return -MATE

    # A single enemy threat makes the blocking move compulsory.
    if opponent_wins:
        candidates = [opponent_wins & -opponent_wins]
    else:
        if depth <= 0:
            fork = _fork_move(me, opponent, empty)
            if fork:
                best = fork.bit_length() - 1
                _store_tt(key, 16, MATE, EXACT, best)
                return MATE

            value = _evaluate(me, opponent)
            _store_tt(key, 0, value, EXACT, -1)
            return value

        candidates = _ordered_moves(me, opponent, empty, preferred)

    best_value = -INF
    best_move = -1

    for bit in candidates:
        child_value = -_search(
            opponent,
            me | bit,
            depth - 1,
            -beta,
            -alpha
        )

        if child_value > best_value:
            best_value = child_value
            best_move = bit.bit_length() - 1

        if child_value > alpha:
            alpha = child_value

        if alpha >= beta:
            break

    if best_value <= alpha_original:
        result_flag = UPPER
    elif best_value >= beta_original:
        result_flag = LOWER
    else:
        result_flag = EXACT

    _store_tt(
        key,
        requested_depth,
        best_value,
        result_flag,
        best_move
    )
    return best_value


def _root_search(
    me: int,
    opponent: int,
    depth: int,
    preferred: int
) -> tuple[int, int]:
    empty = FULL & ~(me | opponent)
    candidates = _ordered_moves(me, opponent, empty, preferred)

    best_move = candidates[0].bit_length() - 1
    best_value = -INF
    alpha = -INF

    for bit in candidates:
        if perf_counter() >= _deadline:
            raise _Timeout

        value = -_search(
            opponent,
            me | bit,
            depth - 1,
            -INF,
            -alpha
        )

        if value > best_value:
            best_value = value
            best_move = bit.bit_length() - 1

        if value > alpha:
            alpha = value

        if best_value == MATE:
            break

    return best_value, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _deadline, _nodes

    me = 0
    opponent = 0
    empty_cells = []

    for row in range(4):
        for col in range(4):
            value = board[row][col]
            square = row * 4 + col
            bit = 1 << square

            if value == 1:
                me |= bit
            elif value == -1:
                opponent |= bit
            else:
                empty_cells.append(square)

    # A legal move cannot exist on a full board. In normal arena use,
    # policy is only called on nonterminal positions.
    if not empty_cells:
        return (0, 0)

    # This fallback remains legal even if search times out.
    fallback = empty_cells[0]
    empty = FULL & ~(me | opponent)

    try:
        # If handed a terminal position with empty cells, remain legal.
        if _has_win(me) or _has_win(opponent):
            return divmod(fallback, 4)

        # Immediate tactical decisions require no search.
        winning = _winning_moves(me, opponent)
        if winning:
            square = (winning & -winning).bit_length() - 1
            return divmod(square, 4)

        enemy_winning = _winning_moves(opponent, me)
        if enemy_winning:
            square = (enemy_winning & -enemy_winning).bit_length() - 1
            return divmod(square, 4)

        # Strong symmetric opening with three incident winning lines.
        if len(empty_cells) == 16:
            return (1, 1)

        fork = _fork_move(me, opponent, empty)
        if fork:
            return divmod(fork.bit_length() - 1, 4)

        # Limit long-lived cache growth while preserving it across turns.
        if len(_TT) > 600000:
            _TT.clear()

        _nodes = 0
        _deadline = perf_counter() + 0.90

        ordered = _ordered_moves(me, opponent, empty)
        best_move = ordered[0].bit_length() - 1
        preferred = best_move
        remaining_moves = len(empty_cells)

        # Only results from fully completed iterations replace best_move.
        for depth in range(1, remaining_moves + 1):
            value, candidate = _root_search(
                me,
                opponent,
                depth,
                preferred
            )

            best_move = candidate
            preferred = candidate

            if value == MATE:
                break

        if empty & (1 << best_move):
            return divmod(best_move, 4)

    except _Timeout:
        if empty & (1 << best_move):
            return divmod(best_move, 4)
    except Exception:
        # Preserve legality even if the environment supplies unusual
        # integer subclasses or another unexpected condition occurs.
        pass

    return divmod(fallback, 4)
