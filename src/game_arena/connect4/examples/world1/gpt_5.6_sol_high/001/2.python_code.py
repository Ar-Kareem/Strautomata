
import time


ROWS = 6
COLS = 7
WIN_SCORE = 1_000_000
CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)
CENTER_PRIORITY = (0, 5, 4, 6, 3, 2, 1)

# Bitboard layout uses seven bits per column:
# bits 0..5 are the six cells, while bit 6 is unused.
COLUMN_MASKS = tuple(
    sum(1 << (c * 7 + r) for r in range(6))
    for c in range(7)
)

POSITION_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)


def _make_windows():
    windows = []

    # Horizontal
    for r in range(6):
        for c in range(4):
            mask = 0
            for k in range(4):
                mask |= 1 << ((c + k) * 7 + r)
            windows.append(mask)

    # Vertical
    for c in range(7):
        for r in range(3):
            mask = 0
            for k in range(4):
                mask |= 1 << (c * 7 + r + k)
            windows.append(mask)

    # Diagonal: bottom-left to top-right
    for c in range(4):
        for r in range(3):
            mask = 0
            for k in range(4):
                mask |= 1 << ((c + k) * 7 + r + k)
            windows.append(mask)

    # Diagonal: top-left to bottom-right
    for c in range(4):
        for r in range(3, 6):
            mask = 0
            for k in range(4):
                mask |= 1 << ((c + k) * 7 + r - k)
            windows.append(mask)

    return tuple(windows)


WINDOWS = _make_windows()

_windows_by_cell_lists = [[] for _ in range(49)]
for window in WINDOWS:
    for bit_index in range(49):
        if window & (1 << bit_index):
            _windows_by_cell_lists[bit_index].append(window)
WINDOWS_BY_CELL = tuple(tuple(x) for x in _windows_by_cell_lists)


class _SearchTimeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * 7
_killers = [[-1, -1] for _ in range(50)]
_slots = [[] for _ in range(7)]


def _has_four(bits):
    """Return True if the bitboard contains four connected discs."""
    for direction in (1, 7, 6, 8):
        paired = bits & (bits >> direction)
        if paired & (paired >> (2 * direction)):
            return True
    return False


def _landing_bit(column, used):
    row = _slots[column][used[column]]
    return 1 << (column * 7 + row)


def _evaluate(my_bits, opp_bits):
    """Static evaluation from the side-to-move's perspective."""
    score = 0

    # Reward central control.
    for c in range(7):
        weight = POSITION_WEIGHTS[c]
        score += weight * (
            (my_bits & COLUMN_MASKS[c]).bit_count()
            - (opp_bits & COLUMN_MASKS[c]).bit_count()
        )

    # Reward unblocked potential lines.
    line_values = (0, 2, 13, 70, WIN_SCORE)

    for mask in WINDOWS:
        mine = (my_bits & mask).bit_count()
        theirs = (opp_bits & mask).bit_count()

        if mine and theirs:
            continue
        if mine:
            score += line_values[mine]
        elif theirs:
            score -= line_values[theirs]

    return score


def _move_order_score(column, my_bits, opp_bits, used, tt_move, ply):
    score = CENTER_PRIORITY[column] * 20
    score += min(_history[column], 10_000)

    if column == tt_move:
        score += 1_000_000

    if ply < len(_killers):
        if column == _killers[ply][0]:
            score += 50_000
        elif column == _killers[ply][1]:
            score += 25_000

    bit = _landing_bit(column, used)
    new_my = my_bits | bit
    bit_index = bit.bit_length() - 1

    # Prefer moves that create strong lines or block strong enemy lines.
    for mask in WINDOWS_BY_CELL[bit_index]:
        if not (opp_bits & mask):
            count = (new_my & mask).bit_count()
            score += count * count * 8
            if count == 3:
                score += 90

        if not (my_bits & mask):
            enemy_count = (opp_bits & mask).bit_count()
            score += enemy_count * enemy_count * 6
            if enemy_count == 3:
                score += 80

    return score


def _search(my_bits, opp_bits, used, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    depth_key = depth if depth > 0 else 0
    key = my_bits | (opp_bits << 49)

    alpha_in = alpha
    beta_in = beta
    tt_move = -1

    entry = _tt.get(key)
    if entry is not None:
        entry_depth, entry_score, entry_flag, tt_move = entry

        if entry_depth >= depth_key:
            if entry_flag == 0:  # Exact
                return entry_score
            if entry_flag == 1:  # Lower bound
                if entry_score > alpha:
                    alpha = entry_score
            else:                # Upper bound
                if entry_score < beta:
                    beta = entry_score

            if alpha >= beta:
                return entry_score

    legal = [
        c for c in CENTER_ORDER
        if used[c] < len(_slots[c])
    ]

    if not legal:
        _tt[key] = (depth_key, 0, 0, -1)
        return 0

    # Winning immediately is always best.
    for c in legal:
        bit = _landing_bit(c, used)
        if _has_four(my_bits | bit):
            return WIN_SCORE - (ply + 1)

    # Find opponent's currently playable winning cells.
    opponent_threats = []
    for c in legal:
        bit = _landing_bit(c, used)
        if _has_four(opp_bits | bit):
            opponent_threats.append(c)

    # Two distinct immediate threats cannot both be blocked.
    if len(opponent_threats) >= 2:
        return -WIN_SCORE + ply + 2

    if opponent_threats:
        candidates = opponent_threats
    else:
        candidates = legal

    # Reject moves that make the next cell in the same column an immediate
    # opponent win. Other columns' playable cells are unchanged.
    safe_moves = []
    for c in candidates:
        next_index = used[c] + 1
        if next_index < len(_slots[c]):
            next_row = _slots[c][next_index]
            next_bit = 1 << (c * 7 + next_row)
            if _has_four(opp_bits | next_bit):
                continue
        safe_moves.append(c)

    if not safe_moves:
        return -WIN_SCORE + ply + 2

    # At the horizon, continue only forced tactical blocking sequences.
    if depth <= 0 and not opponent_threats:
        value = _evaluate(my_bits, opp_bits)
        _tt[key] = (0, value, 0, -1)
        return value

    safe_moves.sort(
        key=lambda c: _move_order_score(
            c, my_bits, opp_bits, used, tt_move, ply
        ),
        reverse=True,
    )

    best_score = -WIN_SCORE
    best_move = safe_moves[0]
    next_depth = depth - 1 if depth > 0 else 0

    for c in safe_moves:
        bit = _landing_bit(c, used)
        used[c] += 1

        score = -_search(
            opp_bits,
            my_bits | bit,
            used,
            next_depth,
            -beta,
            -alpha,
            ply + 1,
        )

        used[c] -= 1

        if score > best_score:
            best_score = score
            best_move = c

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if depth > 0:
                _history[c] = min(10_000, _history[c] + depth * depth)

                if ply < len(_killers) and _killers[ply][0] != c:
                    _killers[ply][1] = _killers[ply][0]
                    _killers[ply][0] = c
            break

    if best_score <= alpha_in:
        flag = 2  # Upper bound
    elif best_score >= beta_in:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _tt[key] = (depth_key, best_score, flag, best_move)
    return best_score


def policy(board: list[list[int]]) -> int:
    global _deadline, _nodes, _tt, _history, _killers, _slots

    # Build bitboards. Rows in the bitboard are indexed from the bottom.
    my_bits = 0
    opp_bits = 0
    slots = [[] for _ in range(7)]

    for c in range(7):
        for bit_row in range(6):
            board_row = 5 - bit_row
            value = board[board_row][c]
            bit = 1 << (c * 7 + bit_row)

            if value == 1:
                my_bits |= bit
            elif value == -1:
                opp_bits |= bit
            else:
                slots[c].append(bit_row)

    _slots = slots
    used = [0] * 7

    legal = [c for c in CENTER_ORDER if slots[c]]

    # A full board should not be passed to the policy. This fallback keeps the
    # API total for malformed inputs.
    if not legal:
        return 0

    fallback = legal[0]

    # Immediate win.
    winning_moves = []
    for c in legal:
        if _has_four(my_bits | _landing_bit(c, used)):
            winning_moves.append(c)

    if winning_moves:
        return winning_moves[0]

    # Immediate defensive action.
    opponent_wins = []
    for c in legal:
        if _has_four(opp_bits | _landing_bit(c, used)):
            opponent_wins.append(c)

    if len(opponent_wins) == 1:
        return opponent_wins[0]

    if len(opponent_wins) >= 2:
        # The position is lost tactically, but blocking one threat remains a
        # legal move and usually prolongs the game.
        return opponent_wins[0]

    # Strong and unambiguous opening move.
    if my_bits == 0 and opp_bits == 0 and 3 in legal:
        return 3

    _deadline = time.perf_counter() + 0.93
    _nodes = 0
    _tt = {}
    _history = [0] * 7
    _killers = [[-1, -1] for _ in range(50)]

    best_move = fallback
    remaining = sum(len(x) for x in slots)

    # Iterative deepening ensures a completed legal result is always retained.
    for depth in range(1, remaining + 1):
        try:
            score = _search(
                my_bits,
                opp_bits,
                used,
                depth,
                -WIN_SCORE,
                WIN_SCORE,
                0,
            )

            root_entry = _tt.get(my_bits | (opp_bits << 49))
            if root_entry is not None:
                candidate = root_entry[3]
                if candidate in legal:
                    best_move = candidate

            # A mate score means the result is proven.
            if abs(score) > 900_000:
                break

            if time.perf_counter() >= _deadline:
                break

        except _SearchTimeout:
            break

    if best_move not in legal:
        best_move = fallback

    return int(best_move)
