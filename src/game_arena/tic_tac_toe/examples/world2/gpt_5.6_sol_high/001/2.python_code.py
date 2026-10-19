
import time

# Winning rows, columns, and diagonals.
_LINES = (
    0x000F, 0x00F0, 0x0F00, 0xF000,
    0x1111, 0x2222, 0x4444, 0x8888,
    0x8421, 0x1248,
)

_FULL = 0xFFFF
_MATE = 100000
_MATE_THRESHOLD = 90000
_INF = 10**9

_EXACT = 0
_LOWER = 1
_UPPER = 2

# Persistent transposition table:
# key -> (depth, normalized_value, bound_flag, best_move_bit)
_TT = {}

# Lines containing each cell.
_CELL_LINES = tuple(
    tuple(line for line in _LINES if line & (1 << cell))
    for cell in range(16)
)

# Small positional preference. Central cells are useful fork intersections.
_POSITION = (
    4, 2, 2, 4,
    2, 6, 6, 2,
    2, 6, 6, 2,
    4, 2, 2, 4,
)

# Static line values.
_EVAL_WEIGHT = (0, 2, 18, 180, _MATE)


class _SearchTimeout(Exception):
    pass


def _winning_cells(player: int, opponent: int) -> int:
    """Return empty cells where player can complete a line immediately."""
    empty = _FULL ^ (player | opponent)
    result = 0
    for line in _LINES:
        if not (line & opponent) and (line & player).bit_count() == 3:
            result |= line & empty
    return result


def _normalize_mate(value: int, ply: int) -> int:
    """Convert root-relative mate scores into transposition-safe scores."""
    if value > _MATE_THRESHOLD:
        return value + ply
    if value < -_MATE_THRESHOLD:
        return value - ply
    return value


def _denormalize_mate(value: int, ply: int) -> int:
    if value > _MATE_THRESHOLD:
        return value - ply
    if value < -_MATE_THRESHOLD:
        return value + ply
    return value


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.88

    player = 0
    opponent = 0
    for row in range(4):
        for col in range(4):
            value = board[row][col]
            bit = 1 << (row * 4 + col)
            if value == 1:
                player |= bit
            elif value == -1:
                opponent |= bit

    empty = _FULL ^ (player | opponent)

    # A full board should not be submitted to a move policy. This keeps the
    # function total for malformed calls.
    if not empty:
        return (0, 0)

    # Always establish a legal fallback before doing any search.
    preferred = (5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)
    fallback_bit = 0
    for index in preferred:
        bit = 1 << index
        if empty & bit:
            fallback_bit = bit
            break

    # Never search past an immediate win.
    immediate_win = _winning_cells(player, opponent)
    if immediate_win:
        bit = immediate_win & -immediate_win
        index = bit.bit_length() - 1
        return (index // 4, index % 4)

    # The fallback must block an immediate loss when possible.
    immediate_loss = _winning_cells(opponent, player)
    if immediate_loss:
        fallback_bit = immediate_loss & -immediate_loss

    best_bit = fallback_bit
    remaining = empty.bit_count()

    # Prevent unbounded memory growth across many arena games.
    if len(_TT) > 280000:
        _TT.clear()

    nodes = 0

    def check_time() -> None:
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

    def store(key: int, depth: int, value: int, flag: int,
              move: int, ply: int) -> None:
        old = _TT.get(key)
        if old is None or depth >= old[0] or (
            flag == _EXACT and old[2] != _EXACT
        ):
            _TT[key] = (
                depth,
                _normalize_mate(value, ply),
                flag,
                move,
            )

    def evaluate(p: int, o: int) -> int:
        score = 1  # Small side-to-move bonus.

        for line in _LINES:
            pc = (p & line).bit_count()
            oc = (o & line).bit_count()

            if oc == 0:
                score += _EVAL_WEIGHT[pc]
            if pc == 0:
                score -= _EVAL_WEIGHT[oc]

        occupied = p | o
        bits = occupied
        while bits:
            bit = bits & -bits
            index = bit.bit_length() - 1
            if p & bit:
                score += _POSITION[index]
            else:
                score -= _POSITION[index]
            bits ^= bit

        return score

    def ordered_moves(p: int, o: int, legal: int, tt_move: int):
        scored = []
        bits = legal

        while bits:
            bit = bits & -bits
            bits ^= bit
            index = bit.bit_length() - 1
            score = _POSITION[index]

            if bit == tt_move:
                score += 1000000

            # Prefer moves that create threats, build open lines, or disrupt
            # the opponent's strongest open lines.
            for line in _CELL_LINES[index]:
                pc = (p & line).bit_count()
                oc = (o & line).bit_count()

                if oc == 0:
                    if pc == 0:
                        score += 3
                    elif pc == 1:
                        score += 25
                    elif pc == 2:
                        score += 500
                    else:
                        score += 10000

                if pc == 0:
                    if oc == 1:
                        score += 20
                    elif oc == 2:
                        score += 430
                    elif oc == 3:
                        score += 9000

            scored.append((score, bit))

        scored.sort(reverse=True)
        return [bit for _, bit in scored]

    def search(p: int, o: int, depth: int,
               alpha: int, beta: int, ply: int) -> int:
        check_time()

        legal = _FULL ^ (p | o)
        if not legal:
            return 0

        key = p | (o << 16)
        alpha_original = alpha
        beta_original = beta
        tt_move = 0

        entry = _TT.get(key)
        if entry is not None:
            entry_depth, stored_value, flag, tt_move = entry
            if entry_depth >= depth:
                value = _denormalize_mate(stored_value, ply)
                if flag == _EXACT:
                    return value
                if flag == _LOWER:
                    if value > alpha:
                        alpha = value
                else:
                    if value < beta:
                        beta = value
                if alpha >= beta:
                    return value

        # Tactical terminal: current player wins in one move.
        own_wins = _winning_cells(p, o)
        if own_wins:
            if tt_move & own_wins:
                move = tt_move
            else:
                move = own_wins & -own_wins
            value = _MATE - ply - 1
            store(key, 99, value, _EXACT, move, ply)
            return value

        opponent_wins = _winning_cells(o, p)

        # Two distinct immediate winning cells cannot both be blocked.
        if opponent_wins.bit_count() >= 2:
            move = opponent_wins & -opponent_wins
            value = -_MATE + ply + 2
            store(key, 99, value, _EXACT, move, ply)
            return value

        # Extend forced blocking sequences beyond the nominal horizon.
        forced = opponent_wins
        if depth <= 0 and not forced:
            value = evaluate(p, o)
            store(key, 0, value, _EXACT, 0, ply)
            return value

        if forced:
            moves = [forced]
        else:
            moves = ordered_moves(p, o, legal, tt_move)

        best_value = -_INF
        best_move = moves[0]
        next_depth = depth - 1 if depth > 0 else 0

        for move in moves:
            child_value = -search(
                o,
                p | move,
                next_depth,
                -beta,
                -alpha,
                ply + 1,
            )

            if child_value > best_value:
                best_value = child_value
                best_move = move

            if child_value > alpha:
                alpha = child_value

            if alpha >= beta:
                break

        if best_value <= alpha_original:
            bound = _UPPER
        elif best_value >= beta_original:
            bound = _LOWER
        else:
            bound = _EXACT

        store(key, depth, best_value, bound, best_move, ply)
        return best_value

    # Iterative deepening ensures that a completed result is always available.
    try:
        for depth in range(1, remaining + 1):
            value = search(player, opponent, depth, -_INF, _INF, 0)

            root_entry = _TT.get(player | (opponent << 16))
            if root_entry is not None:
                candidate = root_entry[3]
                if candidate and (candidate & empty):
                    best_bit = candidate

            # A mate score is a proven result, not a heuristic estimate.
            if abs(value) > _MATE_THRESHOLD:
                break

            # Searching all remaining cells gives an exact result.
            if depth >= remaining:
                break

    except _SearchTimeout:
        pass

    # Final legality guard.
    if not (best_bit & empty):
        best_bit = empty & -empty

    index = best_bit.bit_length() - 1
    return (index // 4, index % 4)
