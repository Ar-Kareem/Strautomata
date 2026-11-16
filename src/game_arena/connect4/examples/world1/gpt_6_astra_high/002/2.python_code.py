
from time import perf_counter


_ROWS = 6
_COLS = 7
_ORDER = (3, 2, 4, 1, 5, 0, 6)
_COLUMN = tuple(63 << (7 * c) for c in range(7))
_BOTTOM = sum(1 << (7 * c) for c in range(7))
_FULL = sum(_COLUMN)
_ODD_ROWS = sum(
    1 << (7 * c + r)
    for c in range(7)
    for r in (0, 2, 4)
)
_EVEN_ROWS = _FULL ^ _ODD_ROWS

_INNER = _COLUMN[2] | _COLUMN[4]
_OUTER = _COLUMN[1] | _COLUMN[5]
_ORDER_BONUS = (0, 16, 32, 48, 40, 24, 8)

# Valid starting cells for four-cell windows in each direction.
_STARTS = []
for _dr, _dc, _shift in ((1, 0, 1), (0, 1, 7),
                         (-1, 1, 6), (1, 1, 8)):
    _starts = 0
    for _c in range(7):
        for _r in range(6):
            if 0 <= _r + 3 * _dr < 6 and 0 <= _c + 3 * _dc < 7:
                _starts |= 1 << (7 * _c + _r)
    _STARTS.append((_shift, _starts))
_STARTS = tuple(_STARTS)

_MATE = 100000
_INF = 1000000

# Entries: (depth, score, bound, best_move_bit).
# Bounds: 0 = exact, 1 = lower bound, 2 = upper bound.
_TT = {}


class _SearchTimeout(Exception):
    pass


def _winning_squares(p, occupied):
    """Empty cells that would complete a four for p."""
    result = (p << 1) & (p << 2) & (p << 3)

    a = (p << 7) & (p << 14)
    result |= a & ((p << 21) | (p >> 7))
    a = (p >> 7) & (p >> 14)
    result |= a & ((p << 7) | (p >> 21))

    a = (p << 6) & (p << 12)
    result |= a & ((p << 18) | (p >> 6))
    a = (p >> 6) & (p >> 12)
    result |= a & ((p << 6) | (p >> 18))

    a = (p << 8) & (p << 16)
    result |= a & ((p << 24) | (p >> 8))
    a = (p >> 8) & (p >> 16)
    result |= a & ((p << 8) | (p >> 24))

    return result & (_FULL ^ occupied)


def _evaluate(p, occupied, opponent_wins, count):
    q = occupied ^ p
    own_wins = _winning_squares(p, occupied)

    score = 60 * (own_wins.bit_count() - opponent_wins.bit_count())

    # The first player generally benefits from odd-height threats;
    # the second player generally benefits from even-height threats.
    favorable = _ODD_ROWS if count % 2 == 0 else _EVEN_ROWS
    other_favorable = _FULL ^ favorable
    score += 18 * (
        (own_wins & favorable).bit_count()
        - (opponent_wins & other_favorable).bit_count()
    )

    # Stacked threats in one column are particularly dangerous.
    score += 75 * (
        (own_wins & (own_wins >> 1)).bit_count()
        - (opponent_wins & (opponent_wins >> 1)).bit_count()
    )

    score += 9 * (
        (p & _COLUMN[3]).bit_count() - (q & _COLUMN[3]).bit_count()
    )
    score += 6 * (
        (p & _INNER).bit_count() - (q & _INNER).bit_count()
    )
    score += 3 * (
        (p & _OUTER).bit_count() - (q & _OUTER).bit_count()
    )

    # Count unobstructed windows containing at least two friendly discs.
    for shift, starts in _STARTS:
        p1 = p >> shift
        p2 = p >> (2 * shift)
        p3 = p >> (3 * shift)
        q1 = q >> shift
        q2 = q >> (2 * shift)
        q3 = q >> (3 * shift)

        p01, p23 = p | p1, p2 | p3
        q01, q23 = q | q1, q2 | q3

        p_twos = (p & p1) | (p2 & p3) | (p01 & p23)
        q_twos = (q & q1) | (q2 & q3) | (q01 & q23)

        score += 10 * (
            (p_twos & starts & ~(q01 | q23)).bit_count()
            - (q_twos & starts & ~(p01 | p23)).bit_count()
        )

    return score


def policy(board: list[list[int]]) -> int:
    started = perf_counter()
    deadline = started + 0.88

    legal_columns = [
        c for c in _ORDER
        if any(board[r][c] == 0 for r in range(6))
    ]
    if not legal_columns:
        # No legal action exists on a completely full board.
        return 0

    fallback = legal_columns[0]
    if len(legal_columns) == 1:
        return int(fallback)

    position = 0
    occupied = 0
    for c in range(7):
        for r in range(6):
            value = board[r][c]
            if value:
                bit = 1 << (7 * c + 5 - r)
                occupied |= bit
                if value == 1:
                    position |= bit

    count = occupied.bit_count()
    if count == 0:
        _TT.clear()
        return 3

    if len(_TT) > 160000:
        _TT.clear()

    possible = (occupied + _BOTTOM) & _FULL

    immediate = _winning_squares(position, occupied) & possible
    if immediate:
        for c in legal_columns:
            if immediate & _COLUMN[c]:
                return int(c)

    opponent_wins = _winning_squares(occupied ^ position, occupied)
    forced = possible & opponent_wins
    if forced:
        # With one threat this is compulsory. With multiple threats,
        # blocking one is the best practical attempt in a lost position.
        for c in legal_columns:
            if forced & _COLUMN[c]:
                return int(c)

    safe = possible & ~(opponent_wins >> 1)
    if not safe:
        return int(fallback)

    safe_columns = [c for c in legal_columns if safe & _COLUMN[c]]
    if not safe_columns:
        return int(fallback)
    fallback = safe_columns[0]
    if len(safe_columns) == 1:
        return int(fallback)

    root_key = position + occupied
    root_allowed = safe

    # Symmetric alternatives have identical game-theoretic values.
    if all(row == row[::-1] for row in board):
        root_allowed &= (
            _COLUMN[0] | _COLUMN[1] | _COLUMN[2] | _COLUMN[3]
        )

    table = _TT
    history = [[0] * 7 for _ in range(2)]
    killers = [[-1, -1] for _ in range(43)]
    nodes = 0

    def ordered_moves(p, mask, moves, depth, hash_move, ply):
        # Yield the transposition move before spending time sorting others.
        if hash_move and hash_move & moves:
            c = (hash_move.bit_length() - 1) // 7
            yield hash_move, c, None, True
            moves ^= hash_move

        if not moves:
            return

        hist = history[ply & 1]
        killer1, killer2 = killers[ply]
        ranked = []

        for c in _ORDER:
            move = moves & _COLUMN[c]
            if not move:
                continue

            priority = _ORDER_BONUS[c] + (hist[c] >> 4)
            if c == killer1:
                priority += 256
            elif c == killer2:
                priority += 128

            child_opponent_wins = None
            tactical = False
            if depth >= 3:
                next_mask = mask | move
                child_opponent_wins = _winning_squares(
                    p | move, next_mask
                )
                next_possible = (next_mask + _BOTTOM) & _FULL
                threats = (
                    child_opponent_wins & next_possible
                ).bit_count()
                tactical = threats != 0
                priority += (
                    80 * child_opponent_wins.bit_count()
                    + 160 * threats
                )

            ranked.append(
                (priority, move, c, child_opponent_wins, tactical)
            )

        ranked.sort(reverse=True)
        for _, move, c, wins, tactical in ranked:
            yield move, c, wins, tactical

    def search(p, mask, depth, alpha, beta, ply, opp_wins=None):
        nonlocal nodes
        nodes += 1
        if nodes & 255 == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        if ply >= 42:
            return 0

        key = p + mask
        entry = table.get(key)
        hash_move = 0

        if entry is not None:
            saved_depth, value, bound, hash_move = entry
            if saved_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1 and value >= beta:
                    return value
                if bound == 2 and value <= alpha:
                    return value

        original_alpha = alpha

        # Invariant: the current player has no immediate win.
        # Root checks establish it; searching only non-losing moves
        # preserves it for every child.
        if opp_wins is None:
            opp_wins = _winning_squares(mask ^ p, mask)

        moves = (mask + _BOTTOM) & _FULL
        forced_moves = moves & opp_wins

        if forced_moves:
            if forced_moves & (forced_moves - 1):
                return -_MATE - (42 - ply)
            moves = forced_moves

        # Do not provide support immediately below an enemy winning cell.
        moves &= ~(opp_wins >> 1)
        if not moves:
            return -_MATE - (42 - ply)

        if ply >= 40:
            return 0

        if key == root_key:
            moves &= root_allowed

        single_move = not (moves & (moves - 1))
        if depth <= 0 and not single_move:
            return _evaluate(p, mask, opp_wins, ply)

        next_player = mask ^ p
        next_depth = max(0, depth - 1)

        if single_move:
            # At the horizon, continue compulsory moves until quiet.
            best_move = moves
            best_value = -search(
                next_player, mask | moves, next_depth,
                -beta, -alpha, ply + 1
            )
        else:
            best_value = -_INF
            best_move = 0
            narrow_window = beta - alpha == 1

            for index, (move, c, child_wins, tactical) in enumerate(
                ordered_moves(p, mask, moves, depth, hash_move, ply)
            ):
                next_mask = mask | move

                if index == 0:
                    value = -search(
                        next_player, next_mask, next_depth,
                        -beta, -alpha, ply + 1, child_wins
                    )
                else:
                    reduction = 0
                    if (
                        depth >= 5
                        and index >= 3
                        and narrow_window
                        and not tactical
                    ):
                        reduction = 1
                        if depth >= 9 and index >= 5:
                            reduction = 2

                    value = -search(
                        next_player, next_mask,
                        max(0, next_depth - reduction),
                        -alpha - 1, -alpha, ply + 1, child_wins
                    )

                    if reduction and value > alpha:
                        value = -search(
                            next_player, next_mask, next_depth,
                            -alpha - 1, -alpha, ply + 1, child_wins
                        )

                    if alpha < value < beta:
                        value = -search(
                            next_player, next_mask, next_depth,
                            -beta, -alpha, ply + 1, child_wins
                        )

                if value > best_value:
                    best_value = value
                    best_move = move

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    hist = history[ply & 1]
                    hist[c] = min(8192, hist[c] + depth * depth)
                    if killers[ply][0] != c:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = c
                    break

        if best_value <= original_alpha:
            bound = 2
        elif best_value >= beta:
            bound = 1
        else:
            bound = 0

        table[key] = (depth, best_value, bound, best_move)
        return best_value

    best_column = fallback
    previous_value = 0

    for depth in range(1, 43 - count):
        if perf_counter() >= deadline:
            break

        try:
            if depth >= 4:
                low = previous_value - 70
                high = previous_value + 70
                value = search(
                    position, occupied, depth,
                    low, high, count, opponent_wins
                )
                if value <= low or value >= high:
                    value = search(
                        position, occupied, depth,
                        -_INF, _INF, count, opponent_wins
                    )
            else:
                value = search(
                    position, occupied, depth,
                    -_INF, _INF, count, opponent_wins
                )

            entry = table.get(root_key)
            if entry is not None:
                move = entry[3]
                if move and move & safe:
                    candidate = (move.bit_length() - 1) // 7
                    if candidate in legal_columns:
                        best_column = candidate

            previous_value = value
            if abs(value) >= _MATE:
                break

        except _SearchTimeout:
            break

    if best_column not in legal_columns:
        best_column = fallback
    return int(best_column)
