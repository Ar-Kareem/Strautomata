
import time

HEIGHT = 6
WIDTH = 7

SHIFT_H = HEIGHT + 1   # horizontal shift in bitboard representation
SHIFT_D1 = HEIGHT      # diagonal /
SHIFT_D2 = HEIGHT + 2  # diagonal \

MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)

BOTTOM_MASKS = tuple(1 << (c * SHIFT_H) for c in range(WIDTH))
TOP_MASKS = tuple(1 << (c * SHIFT_H + HEIGHT - 1) for c in range(WIDTH))
COLUMN_MASKS = tuple((((1 << HEIGHT) - 1) << (c * SHIFT_H)) for c in range(WIDTH))

BOARD_MASK_ALL = 0
for m in COLUMN_MASKS:
    BOARD_MASK_ALL |= m

BOTTOM_MASK_ALL = 0
for m in BOTTOM_MASKS:
    BOTTOM_MASK_ALL |= m

CENTER_MASK = COLUMN_MASKS[3]
NEAR_CENTER_MASK = COLUMN_MASKS[2] | COLUMN_MASKS[4]

BIT_AT = tuple(
    tuple(1 << (c * SHIFT_H + (HEIGHT - 1 - r)) for c in range(WIDTH))
    for r in range(HEIGHT)
)


def _build_window_masks():
    masks = []

    # Horizontal
    for r in range(HEIGHT):
        for c in range(WIDTH - 3):
            m = 0
            for k in range(4):
                m |= BIT_AT[r][c + k]
            masks.append(m)

    # Vertical
    for r in range(HEIGHT - 3):
        for c in range(WIDTH):
            m = 0
            for k in range(4):
                m |= BIT_AT[r + k][c]
            masks.append(m)

    # Diagonal down-right
    for r in range(HEIGHT - 3):
        for c in range(WIDTH - 3):
            m = 0
            for k in range(4):
                m |= BIT_AT[r + k][c + k]
            masks.append(m)

    # Diagonal up-right
    for r in range(3, HEIGHT):
        for c in range(WIDTH - 3):
            m = 0
            for k in range(4):
                m |= BIT_AT[r - k][c + k]
            masks.append(m)

    return tuple(masks)


WINDOW_MASKS = _build_window_masks()

LINE_SCORES = (0, 1, 8, 40, 0)
PLAYABLE_THREE_BONUS = 120
WIN_SCORE = 1_000_000

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
MAX_TT_SIZE = 350_000

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def possible(mask: int) -> int:
    return (mask + BOTTOM_MASK_ALL) & BOARD_MASK_ALL


def winning_position(position: int, mask: int) -> int:
    r = (position << 1) & (position << 2) & (position << 3)

    p = (position << SHIFT_H) & (position << (2 * SHIFT_H))
    r |= p & (position << (3 * SHIFT_H))
    r |= p & (position >> SHIFT_H)
    p = (position >> SHIFT_H) & (position >> (2 * SHIFT_H))
    r |= p & (position << SHIFT_H)
    r |= p & (position >> (3 * SHIFT_H))

    p = (position << SHIFT_D1) & (position << (2 * SHIFT_D1))
    r |= p & (position << (3 * SHIFT_D1))
    r |= p & (position >> SHIFT_D1)
    p = (position >> SHIFT_D1) & (position >> (2 * SHIFT_D1))
    r |= p & (position << SHIFT_D1)
    r |= p & (position >> (3 * SHIFT_D1))

    p = (position << SHIFT_D2) & (position << (2 * SHIFT_D2))
    r |= p & (position << (3 * SHIFT_D2))
    r |= p & (position >> SHIFT_D2)
    p = (position >> SHIFT_D2) & (position >> (2 * SHIFT_D2))
    r |= p & (position << SHIFT_D2)
    r |= p & (position >> (3 * SHIFT_D2))

    return r & (BOARD_MASK_ALL ^ mask)


def can_win_next_mask(position: int, mask: int) -> int:
    return winning_position(position, mask) & possible(mask)


def possible_non_losing_moves(position: int, mask: int) -> int:
    pm = possible(mask)
    opponent = position ^ mask
    opponent_winning = winning_position(opponent, mask)

    forced_moves = pm & opponent_winning
    if forced_moves:
        if forced_moves & (forced_moves - 1):
            return 0
        pm = forced_moves

    return pm & ~(opponent_winning >> 1)


def choose_col_from_mask(mask_bits: int) -> int:
    for col in MOVE_ORDER:
        if mask_bits & COLUMN_MASKS[col]:
            return col
    for col in range(WIDTH):
        if mask_bits & COLUMN_MASKS[col]:
            return col
    return 0


def board_to_bitboards(board) -> tuple[int, int]:
    position = 0
    mask = 0
    for r in range(HEIGHT):
        row = board[r]
        for c in range(WIDTH):
            v = row[c]
            if v:
                bit = BIT_AT[r][c]
                mask |= bit
                if v == 1:
                    position |= bit
    return position, mask


def evaluate(position: int, mask: int) -> int:
    opponent = position ^ mask
    playable = possible(mask)

    score = 0
    score += 6 * (position & CENTER_MASK).bit_count()
    score -= 6 * (opponent & CENTER_MASK).bit_count()
    score += 3 * (position & NEAR_CENTER_MASK).bit_count()
    score -= 3 * (opponent & NEAR_CENTER_MASK).bit_count()

    empty_mask = BOARD_MASK_ALL ^ mask

    for wm in WINDOW_MASKS:
        pcount = (position & wm).bit_count()
        ocount = (opponent & wm).bit_count()

        if pcount and ocount:
            continue

        if pcount:
            score += LINE_SCORES[pcount]
            if pcount == 3 and ((wm & empty_mask) & playable):
                score += PLAYABLE_THREE_BONUS
        elif ocount:
            score -= LINE_SCORES[ocount]
            if ocount == 3 and ((wm & empty_mask) & playable):
                score -= PLAYABLE_THREE_BONUS

    return score


def ordered_moves(moves_mask: int, hint_col: int = -1):
    if 0 <= hint_col < WIDTH:
        move = moves_mask & COLUMN_MASKS[hint_col]
        if move:
            yield hint_col, move

    for col in MOVE_ORDER:
        if col == hint_col:
            continue
        move = moves_mask & COLUMN_MASKS[col]
        if move:
            yield col, move


def root_ordered_moves(position: int, mask: int, moves_mask: int, hint_col: int = -1):
    items = []

    if 0 <= hint_col < WIDTH:
        move = moves_mask & COLUMN_MASKS[hint_col]
        if move:
            items.append((10**9, hint_col, move))

    opponent = position ^ mask

    for col in MOVE_ORDER:
        if col == hint_col:
            continue
        move = moves_mask & COLUMN_MASKS[col]
        if not move:
            continue

        child_mask = mask | move
        my_after = position | move

        score = 10 * (4 - abs(3 - col))
        score += 35 * (winning_position(my_after, child_mask) & possible(child_mask)).bit_count()
        score -= 80 * (winning_position(opponent, child_mask) & possible(child_mask)).bit_count()

        items.append((score, col, move))

    items.sort(reverse=True)
    return [(col, move) for _, col, move in items]


def negamax(position: int, mask: int, depth: int, alpha: int, beta: int) -> int:
    global NODE_COUNTER

    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    moves_played = mask.bit_count()

    if moves_played == WIDTH * HEIGHT:
        return 0

    if can_win_next_mask(position, mask):
        return WIN_SCORE - moves_played

    non_losing = possible_non_losing_moves(position, mask)
    if non_losing == 0:
        return -WIN_SCORE + moves_played

    forced = (non_losing & (non_losing - 1)) == 0
    if depth <= 0 and not forced:
        return evaluate(position, mask)

    key = position + mask + BOTTOM_MASK_ALL
    alpha0, beta0 = alpha, beta
    hint_col = -1

    entry = TT.get(key)
    if entry is not None:
        e_depth, e_flag, e_score, e_col = entry
        hint_col = e_col
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            if e_flag == LOWER:
                if e_score > alpha:
                    alpha = e_score
            else:
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    next_depth = depth if forced else depth - 1
    best = -10**18
    best_col = -1

    for col, move in ordered_moves(non_losing, hint_col):
        child_position = position ^ mask
        child_mask = mask | move
        score = -negamax(child_position, child_mask, next_depth, -beta, -alpha)

        if score > best:
            best = score
            best_col = col
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    flag = EXACT
    if best <= alpha0:
        flag = UPPER
    elif best >= beta0:
        flag = LOWER

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, flag, best, best_col)

    return best


def search_root(position: int, mask: int, depth: int) -> tuple[int, int]:
    key = position + mask + BOTTOM_MASK_ALL
    entry = TT.get(key)
    hint_col = entry[3] if entry is not None else -1

    safe_moves = possible_non_losing_moves(position, mask)
    moves_mask = safe_moves if safe_moves else possible(mask)

    moves = root_ordered_moves(position, mask, moves_mask, hint_col)
    if not moves:
        return choose_col_from_mask(possible(mask)), -WIN_SCORE

    alpha = -10**18
    beta = 10**18
    best_score = -10**18
    best_col = moves[0][0]

    for col, move in moves:
        child_position = position ^ mask
        child_mask = mask | move
        score = -negamax(child_position, child_mask, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_col = col
        if score > alpha:
            alpha = score

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, EXACT, best_score, best_col)

    return best_col, best_score


def policy(board: list[list[int]]) -> int:
    legal = [c for c in MOVE_ORDER if board[0][c] == 0]
    if not legal:
        return 0

    fallback = legal[0]

    try:
        global DEADLINE, NODE_COUNTER

        if len(TT) > MAX_TT_SIZE:
            TT.clear()

        position, mask = board_to_bitboards(board)
        moves_played = mask.bit_count()

        # Very strong opening bias and guaranteed legal.
        if moves_played <= 1 and (mask & TOP_MASKS[3]) == 0:
            return 3

        wins = can_win_next_mask(position, mask)
        if wins:
            return choose_col_from_mask(wins)

        safe_moves = possible_non_losing_moves(position, mask)
        if safe_moves and (safe_moves & (safe_moves - 1)) == 0:
            col = choose_col_from_mask(safe_moves)
            return col if col in legal else fallback

        if len(legal) == 1:
            return legal[0]

        initial_moves_mask = safe_moves if safe_moves else possible(mask)
        ordered = root_ordered_moves(position, mask, initial_moves_mask, -1)
        best_col = ordered[0][0] if ordered else fallback

        DEADLINE = time.perf_counter() + 0.90
        NODE_COUNTER = 0

        remaining = WIDTH * HEIGHT - moves_played
        depth = 1

        while depth <= remaining and time.perf_counter() < DEADLINE:
            try:
                col, _ = search_root(position, mask, depth)
                if col in legal:
                    best_col = col
                depth += 1
            except SearchTimeout:
                break

        return best_col if best_col in legal else fallback

    except Exception:
        return fallback
