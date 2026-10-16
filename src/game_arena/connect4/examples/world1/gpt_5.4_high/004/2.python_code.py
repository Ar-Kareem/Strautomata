
import time

WIDTH = 7
HEIGHT = 6
STRIDE = HEIGHT + 1  # 7 bits per column including sentinel
MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)

COL_MASKS = [((1 << HEIGHT) - 1) << (c * STRIDE) for c in range(WIDTH)]
BOTTOM_MASKS = [1 << (c * STRIDE) for c in range(WIDTH)]
BOARD_MASK = sum(COL_MASKS)
BOTTOM_MASK_ALL = sum(BOTTOM_MASKS)
CENTER_MASK = COL_MASKS[WIDTH // 2]

EXACT = 0
LOWER = 1
UPPER = 2

INF = 10**18
WIN_SCORE = 10**9


class SearchTimeout(Exception):
    pass


def _build_win_masks():
    masks = []

    # Horizontal
    for r in range(HEIGHT):
        for c in range(WIDTH - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r)
            masks.append(m)

    # Vertical
    for r in range(HEIGHT - 3):
        for c in range(WIDTH):
            m = 0
            for i in range(4):
                m |= 1 << (c * STRIDE + (r + i))
            masks.append(m)

    # Diagonal /
    for r in range(HEIGHT - 3):
        for c in range(WIDTH - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + (r + i))
            masks.append(m)

    # Diagonal \
    for r in range(3, HEIGHT):
        for c in range(WIDTH - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + (r - i))
            masks.append(m)

    return tuple(masks)


WIN_MASKS = _build_win_masks()


def board_to_position_and_mask(board):
    # board rows are 0(top) ... 5(bottom)
    # bitboard rows are 0(bottom) ... 5(top)
    position = 0  # current player's stones (board value 1)
    mask = 0      # all occupied cells
    for r in range(HEIGHT):
        bit_row = HEIGHT - 1 - r
        for c in range(WIDTH):
            v = board[r][c]
            if v:
                bit = 1 << (c * STRIDE + bit_row)
                mask |= bit
                if v == 1:
                    position |= bit
    return position, mask


def possible_moves(mask):
    return (mask + BOTTOM_MASK_ALL) & BOARD_MASK


def has_won(pos):
    # Vertical
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    # Horizontal
    m = pos & (pos >> STRIDE)
    if m & (m >> (2 * STRIDE)):
        return True

    # Diagonal \
    d = STRIDE - 1
    m = pos & (pos >> d)
    if m & (m >> (2 * d)):
        return True

    # Diagonal /
    d = STRIDE + 1
    m = pos & (pos >> d)
    if m & (m >> (2 * d)):
        return True

    return False


def winning_positions(position, mask):
    # Returns empty cells that would complete a connect-4 for `position`.
    r = (position << 1) & (position << 2) & (position << 3)

    # Horizontal
    p = (position << STRIDE) & (position << (2 * STRIDE))
    r |= p & (position << (3 * STRIDE))
    r |= p & (position >> STRIDE)
    p = (position >> STRIDE) & (position >> (2 * STRIDE))
    r |= p & (position << STRIDE)
    r |= p & (position >> (3 * STRIDE))

    # Diagonal \
    d = STRIDE - 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    # Diagonal /
    d = STRIDE + 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    return r & (BOARD_MASK ^ mask)


def possible_non_losing_moves(position, mask, possible=None):
    if possible is None:
        possible = possible_moves(mask)

    opponent = mask ^ position
    opponent_wins = winning_positions(opponent, mask)

    # Forced blocks against opponent immediate wins.
    forced = possible & opponent_wins
    if forced:
        # More than one forced block => loss no matter what.
        if forced & (forced - 1):
            return 0
        possible = forced

    # Avoid moves that drop under an opponent winning square.
    return possible & ~(opponent_wins >> 1)


def ordered_columns(move_mask, preferred=None):
    if preferred is not None and (move_mask & COL_MASKS[preferred]):
        yield preferred
    for c in MOVE_ORDER:
        if c != preferred and (move_mask & COL_MASKS[c]):
            yield c


def first_column_from_mask(move_mask):
    for c in MOVE_ORDER:
        if move_mask & COL_MASKS[c]:
            return c
    return 0


def evaluate(position, mask, possible=None):
    if possible is None:
        possible = possible_moves(mask)

    opponent = mask ^ position
    empty = BOARD_MASK ^ mask

    score = 0

    # Center control
    score += 6 * ((position & CENTER_MASK).bit_count() - (opponent & CENTER_MASK).bit_count())

    my_threats = 0
    opp_threats = 0

    for wm in WIN_MASKS:
        pc = (position & wm).bit_count()
        oc = (opponent & wm).bit_count()

        if pc and oc:
            continue

        if pc:
            if pc == 3:
                if wm & empty & possible:
                    my_threats += 1
                    score += 70
                else:
                    score += 25
            elif pc == 2:
                score += 10
            elif pc == 1:
                score += 2
        elif oc:
            if oc == 3:
                if wm & empty & possible:
                    opp_threats += 1
                    score -= 75
                else:
                    score -= 28
            elif oc == 2:
                score -= 11
            elif oc == 1:
                score -= 2

    score += 30 * my_threats
    score -= 35 * opp_threats

    if my_threats >= 2:
        score += 60
    if opp_threats >= 2:
        score -= 70

    # Latent winning structure
    score += 4 * winning_positions(position, mask).bit_count()
    score -= 5 * winning_positions(opponent, mask).bit_count()

    return score


def policy(board):
    position, mask = board_to_position_and_mask(board)
    possible = possible_moves(mask)

    # No legal move should not normally happen, but keep a total fallback.
    if possible == 0:
        return 0

    # Immediate win.
    winning_now = winning_positions(position, mask) & possible
    if winning_now:
        return first_column_from_mask(winning_now)

    # Only consider non-losing moves when possible.
    non_losing = possible_non_losing_moves(position, mask, possible)
    if non_losing == 0:
        # All moves lose immediately; still return a legal move.
        return first_column_from_mask(possible)

    if (non_losing & (non_losing - 1)) == 0:
        return first_column_from_mask(non_losing)

    deadline = time.perf_counter() + 0.92
    node_counter = 0
    tt = {}

    def search(position, mask, depth, alpha, beta):
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 511) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

        opponent = mask ^ position

        # If the previous move already won for the opponent, this is losing.
        if has_won(opponent):
            return -WIN_SCORE - depth

        possible = possible_moves(mask)
        if possible == 0:
            return 0

        # Current side can win immediately.
        if winning_positions(position, mask) & possible:
            return WIN_SCORE + depth

        if depth == 0:
            return evaluate(position, mask, possible)

        non_losing = possible_non_losing_moves(position, mask, possible)
        if non_losing == 0:
            return -WIN_SCORE - depth

        key = (position, mask)
        orig_alpha = alpha
        orig_beta = beta
        preferred = None

        entry = tt.get(key)
        if entry is not None:
            stored_depth, flag, value, stored_move = entry
            preferred = stored_move
            if stored_depth >= depth:
                if flag == EXACT:
                    return value
                if flag == LOWER:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        best_value = -INF
        best_move = preferred

        # After we move, the side to move becomes the current opponent.
        child_position = opponent

        for c in ordered_columns(non_losing, preferred):
            move = non_losing & COL_MASKS[c]
            value = -search(child_position, mask | move, depth - 1, -beta, -alpha)

            if value > best_value:
                best_value = value
                best_move = c

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        flag = EXACT
        if best_value <= orig_alpha:
            flag = UPPER
        elif best_value >= orig_beta:
            flag = LOWER

        tt[key] = (depth, flag, best_value, best_move)
        return best_value

    best_move = first_column_from_mask(non_losing)
    root_child_position = mask ^ position
    empties = 42 - mask.bit_count()

    for depth in range(1, empties + 1):
        try:
            alpha = -INF
            beta = INF
            current_best_move = best_move
            current_best_score = -INF

            for c in ordered_columns(non_losing, best_move):
                move = non_losing & COL_MASKS[c]
                score = -search(root_child_position, mask | move, depth - 1, -beta, -alpha)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = c

                if score > alpha:
                    alpha = score

                if current_best_score >= WIN_SCORE // 2:
                    break

            best_move = current_best_move

            if abs(current_best_score) >= WIN_SCORE // 2:
                break

        except SearchTimeout:
            break

    return best_move
