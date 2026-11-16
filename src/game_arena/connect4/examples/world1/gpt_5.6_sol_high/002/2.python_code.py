
import time as _time


ROWS = 6
COLS = 7
MATE = 100000
INF = 200000

EXACT = 0
LOWER = 1
UPPER = 2

COLUMN_MASKS = tuple(0x3F << (7 * c) for c in range(COLS))
BOTTOM_MASK = sum(1 << (7 * c) for c in range(COLS))
BOARD_MASK = sum(COLUMN_MASKS)

MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)
CENTER_RANK = (1, 3, 5, 7, 6, 4, 2)


def _make_windows():
    windows = []

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            w = 0
            for k in range(4):
                w |= 1 << ((c + k) * 7 + r)
            windows.append(w)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            w = 0
            for k in range(4):
                w |= 1 << (c * 7 + r + k)
            windows.append(w)

    # Rising diagonal
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            w = 0
            for k in range(4):
                w |= 1 << ((c + k) * 7 + r + k)
            windows.append(w)

    # Falling diagonal
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            w = 0
            for k in range(4):
                w |= 1 << ((c + k) * 7 + r - k)
            windows.append(w)

    return tuple(windows)


WINDOWS = _make_windows()
WINDOW_WEIGHTS = (0, 1, 10, 80, 0)


def _possible(mask):
    """Return one bit for the landing cell of every non-full column."""
    return (mask + BOTTOM_MASK) & BOARD_MASK


def _winning_cells(position, mask):
    """Return empty cells which would complete four for position."""
    result = (
        (position << 1)
        & (position << 2)
        & (position << 3)
    )

    for shift in (7, 6, 8):
        pair = (position << shift) & (position << (2 * shift))
        result |= pair & (position << (3 * shift))
        result |= pair & (position >> shift)

        pair = (position >> shift) & (position >> (2 * shift))
        result |= pair & (position << shift)
        result |= pair & (position >> (3 * shift))

    return result & BOARD_MASK & ~mask


def _evaluate(me, opponent, mask):
    """Static evaluation from the side-to-move perspective."""
    score = 0

    # Central columns participate in more potential fours.
    score += 6 * (
        (me & COLUMN_MASKS[3]).bit_count()
        - (opponent & COLUMN_MASKS[3]).bit_count()
    )
    score += 2 * (
        (me & (COLUMN_MASKS[2] | COLUMN_MASKS[4])).bit_count()
        - (opponent & (COLUMN_MASKS[2] | COLUMN_MASKS[4])).bit_count()
    )

    for window in WINDOWS:
        mine = me & window
        if mine:
            if not (opponent & window):
                score += WINDOW_WEIGHTS[mine.bit_count()]
        else:
            theirs = opponent & window
            if theirs:
                score -= WINDOW_WEIGHTS[theirs.bit_count()]

    # Unsupported and future three-in-a-row completion squares.
    my_threats = _winning_cells(me, mask)
    opponent_threats = _winning_cells(opponent, mask)
    score += 16 * (
        my_threats.bit_count() - opponent_threats.bit_count()
    )

    return score


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[int]]) -> int:
    start = _time.perf_counter()
    deadline = start + 0.93

    # Use the API definition of legality, ensuring the fallback is legal.
    legal = [
        c for c in MOVE_ORDER
        if any(board[r][c] == 0 for r in range(ROWS))
    ]
    if not legal:
        # A completed board has no legal action and should not be queried.
        return 0

    fallback = legal[0]

    try:
        me = 0
        opponent = 0

        # Bit rows run from bottom (0) to top (5).
        for r in range(ROWS):
            bit_row = ROWS - 1 - r
            for c in range(COLS):
                value = board[r][c]
                bit = 1 << (7 * c + bit_row)
                if value == 1:
                    me |= bit
                elif value == -1:
                    opponent |= bit

        mask = me | opponent
        possible = _possible(mask)

        if not possible:
            return fallback

        # Immediate win.
        immediate = _winning_cells(me, mask) & possible
        if immediate:
            for c in MOVE_ORDER:
                move = possible & COLUMN_MASKS[c]
                if move & immediate and c in legal:
                    return c

        # Mandatory block or unavoidable double threat.
        opponent_wins = _winning_cells(opponent, mask) & possible
        if opponent_wins:
            blocking_columns = []
            for c in MOVE_ORDER:
                move = possible & COLUMN_MASKS[c]
                if move & opponent_wins and c in legal:
                    blocking_columns.append(c)

            if len(blocking_columns) == 1:
                return blocking_columns[0]
            if blocking_columns:
                return blocking_columns[0]

        # Strong and theoretically correct first-move preference.
        stones = mask.bit_count()
        if stones <= 1 and 3 in legal:
            return 3

        transposition = {}
        killers = [[-1, -1] for _ in range(44)]
        nodes = 0

        def save_entry(key, depth, value, flag, best_col):
            old = transposition.get(key)
            if old is not None:
                if depth >= old[0]:
                    transposition[key] = (
                        depth, value, flag, best_col
                    )
            elif len(transposition) < 300000:
                transposition[key] = (
                    depth, value, flag, best_col
                )

        def search(side, other, depth, alpha, beta, ply):
            nonlocal nodes
            nodes += 1

            if (nodes & 255) == 0:
                if _time.perf_counter() >= deadline:
                    raise _SearchTimeout

            state_mask = side | other
            key = side | (other << 49)
            alpha_original = alpha
            beta_original = beta

            entry = transposition.get(key)
            tt_best = -1

            if entry is not None:
                stored_depth, stored_value, flag, tt_best = entry
                if stored_depth >= depth:
                    if flag == EXACT:
                        return stored_value
                    if flag == LOWER and stored_value >= beta:
                        return stored_value
                    if flag == UPPER and stored_value <= alpha:
                        return stored_value

            available = _possible(state_mask)
            if not available:
                save_entry(key, depth, 0, EXACT, -1)
                return 0

            # A win now is always the best possible result.
            winning = _winning_cells(side, state_mask) & available
            if winning:
                win_col = -1
                if tt_best >= 0 and (available & COLUMN_MASKS[tt_best] & winning):
                    win_col = tt_best
                else:
                    for c in MOVE_ORDER:
                        if available & COLUMN_MASKS[c] & winning:
                            win_col = c
                            break

                value = MATE - ply
                save_entry(key, depth, value, EXACT, win_col)
                return value

            # If the opponent has two distinct immediate wins, the game is lost.
            enemy_wins = _winning_cells(other, state_mask) & available
            enemy_win_count = enemy_wins.bit_count()

            if enemy_win_count >= 2:
                best_block = -1
                for c in MOVE_ORDER:
                    if available & COLUMN_MASKS[c] & enemy_wins:
                        best_block = c
                        break

                value = -MATE + ply + 1
                save_entry(key, depth, value, EXACT, best_block)
                return value

            forced_col = -1
            if enemy_win_count == 1:
                threat_bit = enemy_wins
                forced_col = (threat_bit.bit_length() - 1) // 7

            # Quiescence: forced blocks are extended even at the horizon.
            if depth <= 0 and forced_col < 0:
                value = _evaluate(side, other, state_mask)
                save_entry(key, 0, value, EXACT, -1)
                return value

            if forced_col >= 0:
                columns = [forced_col]
            else:
                columns = [
                    c for c in MOVE_ORDER
                    if available & COLUMN_MASKS[c]
                ]

                if len(columns) > 1:
                    killer_one, killer_two = killers[ply]

                    def move_priority(c):
                        move = available & COLUMN_MASKS[c]
                        new_side = side | move
                        new_mask = state_mask | move
                        next_available = _possible(new_mask)

                        priority = CENTER_RANK[c]

                        if c == tt_best:
                            priority += 1000000
                        elif c == killer_one:
                            priority += 500000
                        elif c == killer_two:
                            priority += 250000

                        # Prefer moves creating forcing threats or forks.
                        created = (
                            _winning_cells(new_side, new_mask)
                            & next_available
                        ).bit_count()
                        priority += created * 4000

                        # Search moves allowing an immediate enemy win last.
                        enemy_reply = (
                            _winning_cells(other, new_mask)
                            & next_available
                        )
                        if enemy_reply:
                            priority -= 50000

                        return priority

                    columns.sort(key=move_priority, reverse=True)

            best_value = -INF
            best_col = columns[0]
            first_move = True

            for c in columns:
                move = available & COLUMN_MASKS[c]
                if not move:
                    continue

                next_depth = depth - 1 if depth > 0 else 0

                if first_move:
                    value = -search(
                        other,
                        side | move,
                        next_depth,
                        -beta,
                        -alpha,
                        ply + 1,
                    )
                    first_move = False
                else:
                    # Principal variation search with a null window.
                    value = -search(
                        other,
                        side | move,
                        next_depth,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )
                    if alpha < value < beta:
                        value = -search(
                            other,
                            side | move,
                            next_depth,
                            -beta,
                            -alpha,
                            ply + 1,
                        )

                if value > best_value:
                    best_value = value
                    best_col = c

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    if forced_col < 0:
                        first_killer, second_killer = killers[ply]
                        if c != first_killer:
                            killers[ply][1] = first_killer
                            killers[ply][0] = c
                    break

            if best_value <= alpha_original:
                result_flag = UPPER
            elif best_value >= beta_original:
                result_flag = LOWER
            else:
                result_flag = EXACT

            save_entry(
                key, depth, best_value, result_flag, best_col
            )
            return best_value

        best_move = fallback
        empty_count = ROWS * COLS - stones

        # Iterative deepening preserves the last fully searched answer.
        for depth in range(1, empty_count + 1):
            if _time.perf_counter() >= deadline:
                break

            try:
                score = search(me, opponent, depth, -INF, INF, 0)
            except _SearchTimeout:
                break

            root_key = me | (opponent << 49)
            root_entry = transposition.get(root_key)
            if root_entry is not None:
                candidate = root_entry[3]
                if candidate in legal:
                    best_move = candidate

            # Mate or forced loss has been proven.
            if abs(score) >= MATE - 50:
                break

        if best_move in legal:
            return best_move
        return fallback

    except Exception:
        # Maintain the legal-move guarantee even under unexpected input.
        return fallback
