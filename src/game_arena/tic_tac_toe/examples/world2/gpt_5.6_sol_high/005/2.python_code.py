
"""Strong time-bounded policy for 4x4 Tic Tac Toe."""

from time import perf_counter


# Four rows, four columns, and two diagonals.
WIN_LINES = []

for r in range(4):
    mask = 0
    for c in range(4):
        mask |= 1 << (4 * r + c)
    WIN_LINES.append(mask)

for c in range(4):
    mask = 0
    for r in range(4):
        mask |= 1 << (4 * r + c)
    WIN_LINES.append(mask)

WIN_LINES.append(sum(1 << (4 * i + i) for i in range(4)))
WIN_LINES.append(sum(1 << (4 * i + (3 - i)) for i in range(4)))
WIN_LINES = tuple(WIN_LINES)

FULL_MASK = (1 << 16) - 1
INNER_MASK = (1 << 5) | (1 << 6) | (1 << 9) | (1 << 10)

MATE = 10000
INF = 20000

# Preferred order for otherwise equivalent moves.
_PREFERENCE_ORDER = (
    5, 6, 9, 10,
    0, 3, 12, 15,
    1, 2, 4, 7, 8, 11, 13, 14,
)
PREFERENCE = [0] * 16
for rank, square in enumerate(_PREFERENCE_ORDER):
    PREFERENCE[square] = 16 - rank
PREFERENCE = tuple(PREFERENCE)

# Lines containing each square.
CELL_LINES = []
for square in range(16):
    bit = 1 << square
    CELL_LINES.append(tuple(line for line in WIN_LINES if line & bit))
CELL_LINES = tuple(CELL_LINES)


# Build the eight square symmetries.
_symmetry_maps = [[0] * 16 for _ in range(8)]

for r in range(4):
    for c in range(4):
        source = 4 * r + c

        positions = []
        rr, cc = r, c
        for _ in range(4):
            positions.append((rr, cc))
            rr, cc = cc, 3 - rr

        rr, cc = r, 3 - c
        for _ in range(4):
            positions.append((rr, cc))
            rr, cc = cc, 3 - rr

        for t, (rr, cc) in enumerate(positions):
            _symmetry_maps[t][source] = 1 << (4 * rr + cc)

# Byte lookup tables make symmetry transforms inexpensive.
_TRANSFORM_LOW = []
_TRANSFORM_HIGH = []

for t in range(8):
    low = [0] * 256
    high = [0] * 256

    for value in range(256):
        transformed_low = 0
        transformed_high = 0

        for i in range(8):
            if value & (1 << i):
                transformed_low |= _symmetry_maps[t][i]
                transformed_high |= _symmetry_maps[t][i + 8]

        low[value] = transformed_low
        high[value] = transformed_high

    _TRANSFORM_LOW.append(tuple(low))
    _TRANSFORM_HIGH.append(tuple(high))

_TRANSFORM_LOW = tuple(_TRANSFORM_LOW)
_TRANSFORM_HIGH = tuple(_TRANSFORM_HIGH)


# Search state, reset on every policy call.
_deadline = 0.0
_nodes = 0
_tt = {}


class _SearchTimeout(Exception):
    pass


def _canonical_key(me: int, opponent: int) -> int:
    """Return a symmetry-normalized key for the two bitboards."""
    me_low = me & 255
    me_high = me >> 8
    op_low = opponent & 255
    op_high = opponent >> 8

    best = (1 << 33) - 1

    for t in range(8):
        transformed_me = (
            _TRANSFORM_LOW[t][me_low] |
            _TRANSFORM_HIGH[t][me_high]
        )
        transformed_op = (
            _TRANSFORM_LOW[t][op_low] |
            _TRANSFORM_HIGH[t][op_high]
        )
        key = (transformed_me << 16) | transformed_op
        if key < best:
            best = key

    return best


def _threats(me: int, opponent: int):
    """
    Return:
      me_already_won, opponent_already_won,
      my_immediate_winning_cells, opponent_immediate_winning_cells
    """
    me_won = False
    opponent_won = False
    my_wins = 0
    opponent_wins = 0

    for line in WIN_LINES:
        my_part = line & me
        op_part = line & opponent

        if not op_part:
            count = my_part.bit_count()
            if count == 4:
                me_won = True
            elif count == 3:
                my_wins |= line & ~me

        if not my_part:
            count = op_part.bit_count()
            if count == 4:
                opponent_won = True
            elif count == 3:
                opponent_wins |= line & ~opponent

    return me_won, opponent_won, my_wins, opponent_wins


def _evaluate(me: int, opponent: int) -> int:
    """Static evaluation from the side-to-move's perspective."""
    # Open lines containing two stones are the main positional asset.
    line_values = (0, 3, 24, 300, 0)
    score = 0

    for line in WIN_LINES:
        my_part = line & me
        op_part = line & opponent

        if not op_part:
            score += line_values[my_part.bit_count()]
        if not my_part:
            score -= line_values[op_part.bit_count()]

    # A small preference for the four interior squares.
    score += 2 * (
        (me & INNER_MASK).bit_count()
        - (opponent & INNER_MASK).bit_count()
    )

    return score


def _ordered_bits(
    empty_mask: int,
    me: int,
    opponent: int,
    principal_bit: int = 0,
):
    """Order legal moves to improve alpha-beta pruning."""
    attack_values = (3, 18, 260, 9000)
    defense_values = (2, 15, 220, 8500)
    scored = []

    remaining = empty_mask
    while remaining:
        bit = remaining & -remaining
        remaining ^= bit
        square = bit.bit_length() - 1

        score = PREFERENCE[square]

        if bit == principal_bit:
            score += 20000

        for line in CELL_LINES[square]:
            if not (line & opponent):
                count = (line & me).bit_count()
                score += attack_values[count]

            if not (line & me):
                count = (line & opponent).bit_count()
                score += defense_values[count]

        scored.append((score, bit))

    scored.sort(reverse=True)
    return [bit for _, bit in scored]


def _negamax(
    me: int,
    opponent: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
) -> int:
    """Negamax with alpha-beta pruning and forcing-line extensions."""
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and perf_counter() >= _deadline:
        raise _SearchTimeout

    me_won, opponent_won, my_wins, opponent_wins = _threats(
        me, opponent
    )

    # In valid searches, only opponent_won can normally occur here.
    if opponent_won:
        return -MATE + ply
    if me_won:
        return MATE - ply

    occupied = me | opponent
    empty = FULL_MASK ^ occupied

    if my_wins:
        return MATE - (ply + 1)

    if not empty:
        return 0

    # Two distinct immediate threats cannot both be stopped.
    if opponent_wins.bit_count() >= 2:
        return -MATE + min(16, ply + 2)

    # Extend forced defensive sequences through the normal horizon.
    forced_move = opponent_wins if opponent_wins else 0
    if depth <= 0 and not forced_move:
        return _evaluate(me, opponent)

    use_tt = depth >= 0
    key = 0
    original_alpha = alpha
    original_beta = beta

    if use_tt:
        key = _canonical_key(me, opponent)
        entry = _tt.get(key)

        if entry is not None:
            stored_depth, stored_value, flag = entry
            if stored_depth >= depth:
                if flag == 0:          # Exact value
                    return stored_value
                if flag > 0:           # Lower bound
                    if stored_value > alpha:
                        alpha = stored_value
                else:                  # Upper bound
                    if stored_value < beta:
                        beta = stored_value

                if alpha >= beta:
                    return stored_value

    if forced_move:
        moves = (forced_move,)
    else:
        moves = _ordered_bits(empty, me, opponent)

    best = -INF

    for bit in moves:
        value = -_negamax(
            opponent,
            me | bit,
            depth - 1,
            -beta,
            -alpha,
            ply + 1,
        )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    if use_tt:
        if best <= original_alpha:
            flag = -1                 # Upper bound
        elif best >= original_beta:
            flag = 1                  # Lower bound
        else:
            flag = 0                  # Exact
        _tt[key] = (depth, best, flag)

    return best


def _bit_to_move(bit: int) -> tuple[int, int]:
    square = bit.bit_length() - 1
    return divmod(square, 4)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move for a 4x4 board.

    The caller's stones are represented by 1 and the opponent's by -1.
    """
    global _deadline, _nodes, _tt

    me = 0
    opponent = 0

    for r in range(4):
        for c in range(4):
            value = board[r][c]
            bit = 1 << (4 * r + c)
            if value == 1:
                me |= bit
            elif value == -1:
                opponent |= bit

    empty = FULL_MASK ^ (me | opponent)

    # A full board has no legal action; normal game drivers never call
    # policy in this state.
    if not empty:
        return (0, 0)

    initial_order = _ordered_bits(empty, me, opponent)
    best_bit = initial_order[0]  # Legal timeout-safe fallback.

    _, opponent_won, my_wins, opponent_wins = _threats(me, opponent)

    # Always take an immediate win.
    if my_wins:
        winning_bit = _ordered_bits(my_wins, me, opponent)[0]
        return _bit_to_move(winning_bit)

    # If the position is already terminal but still contains empties,
    # preserve the API guarantee by returning an empty cell.
    if opponent_won:
        return _bit_to_move(best_bit)

    # A single threat has exactly one rational response.
    if opponent_wins.bit_count() == 1:
        return _bit_to_move(opponent_wins)

    # Against multiple immediate threats, loss is forced, but returning
    # one blocking cell is still legal and delays the finish.
    if opponent_wins.bit_count() > 1:
        blocking_bit = _ordered_bits(opponent_wins, me, opponent)[0]
        return _bit_to_move(blocking_bit)

    if empty.bit_count() == 1:
        return _bit_to_move(empty)

    _nodes = 0
    _tt = {}
    _deadline = perf_counter() + 0.90

    remaining_moves = empty.bit_count()
    root_order = _ordered_bits(empty, me, opponent, best_bit)

    # Each fully completed iteration replaces the previous choice.
    for depth in range(1, remaining_moves + 1):
        iteration_best_bit = root_order[0]
        iteration_best_score = -INF
        alpha = -INF
        completed = False

        try:
            for bit in root_order:
                if perf_counter() >= _deadline:
                    raise _SearchTimeout

                score = -_negamax(
                    opponent,
                    me | bit,
                    depth - 1,
                    -INF,
                    -alpha,
                    1,
                )

                if score > iteration_best_score:
                    iteration_best_score = score
                    iteration_best_bit = bit

                if score > alpha:
                    alpha = score

                # Mate-range values are produced only by concrete,
                # tactically verified winning sequences.
                if score >= MATE - 32:
                    return _bit_to_move(iteration_best_bit)

            completed = True

        except _SearchTimeout:
            break

        if completed:
            best_bit = iteration_best_bit
            root_order = _ordered_bits(empty, me, opponent, best_bit)

            # At full depth this is an exact game-theoretic result.
            if depth == remaining_moves:
                break

    return _bit_to_move(best_bit)
