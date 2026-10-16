
from time import perf_counter

WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1
SIZE = WIDTH * HEIGHT
KEY_SHIFT = WIDTH * H1

INF = 10**9
WIN_BASE = 10**6

EXACT = 0
LOWER = 1
UPPER = 2

ORDER = (3, 2, 4, 1, 5, 0, 6)
COL_WEIGHTS = (1, 2, 3, 4, 3, 2, 1)
WINDOW_SCORES = (0, 1, 8, 40, 0)

TIME_LIMIT = 0.92
MAX_DEPTH = 20

VERTICAL_SHIFT = 1
HORIZONTAL_SHIFT = H1
DIAG1_SHIFT = HEIGHT       # down-right / up-left
DIAG2_SHIFT = HEIGHT + 2   # up-right / down-left

BOTTOM_MASK_COL = tuple(1 << (c * H1) for c in range(WIDTH))
TOP_MASK_COL = tuple(1 << (c * H1 + HEIGHT - 1) for c in range(WIDTH))
COLUMN_MASK = tuple(((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH))
BOARD_MASK = sum(COLUMN_MASK)
BOTTOM_MASK_ALL = sum(BOTTOM_MASK_COL)

WINDOW_MASKS = []
# Horizontal
for r in range(HEIGHT):
    for c in range(WIDTH - 3):
        m = 0
        for i in range(4):
            m |= 1 << (((c + i) * H1) + r)
        WINDOW_MASKS.append(m)
# Vertical
for c in range(WIDTH):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c * H1) + (r + i))
        WINDOW_MASKS.append(m)
# Diagonal up-right
for c in range(WIDTH - 3):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << (((c + i) * H1) + (r + i))
        WINDOW_MASKS.append(m)
# Diagonal down-right
for c in range(WIDTH - 3):
    for r in range(3, HEIGHT):
        m = 0
        for i in range(4):
            m |= 1 << (((c + i) * H1) + (r - i))
        WINDOW_MASKS.append(m)
WINDOW_MASKS = tuple(WINDOW_MASKS)

TT = {}
DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def board_to_bitboards(board):
    position = 0
    mask = 0
    for c in range(WIDTH):
        base = c * H1
        for r in range(HEIGHT):
            cell = board[HEIGHT - 1 - r][c]
            if cell != 0:
                bit = 1 << (base + r)
                mask |= bit
                if cell == 1:
                    position |= bit
    return position, mask


def possible_mask(mask):
    return (mask + BOTTOM_MASK_ALL) & BOARD_MASK


def move_bit(mask, col):
    return (mask + BOTTOM_MASK_COL[col]) & COLUMN_MASK[col]


def has_won(pos):
    m = pos & (pos >> VERTICAL_SHIFT)
    if m & (m >> (2 * VERTICAL_SHIFT)):
        return True

    m = pos & (pos >> HORIZONTAL_SHIFT)
    if m & (m >> (2 * HORIZONTAL_SHIFT)):
        return True

    m = pos & (pos >> DIAG1_SHIFT)
    if m & (m >> (2 * DIAG1_SHIFT)):
        return True

    m = pos & (pos >> DIAG2_SHIFT)
    if m & (m >> (2 * DIAG2_SHIFT)):
        return True

    return False


def winning_positions(pos, mask):
    # Vertical
    r = (pos << 1) & (pos << 2) & (pos << 3)

    # Horizontal
    p = (pos << HORIZONTAL_SHIFT) & (pos << (2 * HORIZONTAL_SHIFT))
    r |= p & (pos << (3 * HORIZONTAL_SHIFT))
    r |= p & (pos >> HORIZONTAL_SHIFT)

    p = (pos >> HORIZONTAL_SHIFT) & (pos >> (2 * HORIZONTAL_SHIFT))
    r |= p & (pos << HORIZONTAL_SHIFT)
    r |= p & (pos >> (3 * HORIZONTAL_SHIFT))

    # Diagonal /
    p = (pos << DIAG1_SHIFT) & (pos << (2 * DIAG1_SHIFT))
    r |= p & (pos << (3 * DIAG1_SHIFT))
    r |= p & (pos >> DIAG1_SHIFT)

    p = (pos >> DIAG1_SHIFT) & (pos >> (2 * DIAG1_SHIFT))
    r |= p & (pos << DIAG1_SHIFT)
    r |= p & (pos >> (3 * DIAG1_SHIFT))

    # Diagonal \
    p = (pos << DIAG2_SHIFT) & (pos << (2 * DIAG2_SHIFT))
    r |= p & (pos << (3 * DIAG2_SHIFT))
    r |= p & (pos >> DIAG2_SHIFT)

    p = (pos >> DIAG2_SHIFT) & (pos >> (2 * DIAG2_SHIFT))
    r |= p & (pos << DIAG2_SHIFT)
    r |= p & (pos >> (3 * DIAG2_SHIFT))

    return r & (BOARD_MASK ^ mask)


def possible_non_losing_moves(position, mask):
    possible = possible_mask(mask)
    opponent = mask ^ position
    opp_wins = winning_positions(opponent, mask) & possible
    forced = possible & opp_wins
    if forced:
        if forced & (forced - 1):
            return 0
        possible = forced
    return possible & ~(opp_wins >> 1)


def bit_to_col(bit):
    return (bit.bit_length() - 1) // H1


def pick_best_col(move_mask):
    for c in ORDER:
        if move_mask & COLUMN_MASK[c]:
            return c
    return 3


def ordered_cols(move_mask, preferred=None, ttbest=None):
    cols = []

    if preferred is not None and (move_mask & COLUMN_MASK[preferred]):
        cols.append(preferred)

    if ttbest is not None and ttbest != preferred and (move_mask & COLUMN_MASK[ttbest]):
        cols.append(ttbest)

    for c in ORDER:
        if c != preferred and c != ttbest and (move_mask & COLUMN_MASK[c]):
            cols.append(c)

    return cols


def evaluate(position, mask):
    opponent = mask ^ position
    score = 0

    for c, w in enumerate(COL_WEIGHTS):
        score += w * ((position & COLUMN_MASK[c]).bit_count() - (opponent & COLUMN_MASK[c]).bit_count())

    for wm in WINDOW_MASKS:
        p = (position & wm).bit_count()
        o = (opponent & wm).bit_count()
        if p and o:
            continue
        if p:
            score += WINDOW_SCORES[p]
        elif o:
            score -= WINDOW_SCORES[o]

    poss = possible_mask(mask)
    score += 80 * (winning_positions(position, mask) & poss).bit_count()
    score -= 90 * (winning_positions(opponent, mask) & poss).bit_count()

    return score


def negamax(position, mask, depth, alpha, beta):
    global NODE_COUNTER

    NODE_COUNTER += 1
    if (NODE_COUNTER & 511) == 0 and perf_counter() > DEADLINE:
        raise SearchTimeout

    opponent = mask ^ position
    moves_played = mask.bit_count()

    if has_won(opponent):
        return -WIN_BASE + moves_played

    possible = possible_mask(mask)
    if possible == 0:
        return 0

    if winning_positions(position, mask) & possible:
        return WIN_BASE - moves_played

    safe = possible_non_losing_moves(position, mask)
    if safe == 0:
        return -WIN_BASE + moves_played + 1

    key = position | (mask << KEY_SHIFT)
    entry = TT.get(key)
    ttbest = entry[3] if entry is not None else None

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None and entry[0] >= depth:
        flag, val = entry[1], entry[2]
        if flag == EXACT:
            return val
        if flag == LOWER:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    if depth == 0:
        # Quiescence-like extension through forced tactical replies
        if safe & (safe - 1) == 0:
            col = bit_to_col(safe)
            mv = move_bit(mask, col)
            return -negamax(opponent, mask | mv, 0, -beta, -alpha)
        return evaluate(position, mask)

    best = -INF
    best_col = None
    first = True

    for col in ordered_cols(safe, ttbest=ttbest):
        mv = move_bit(mask, col)
        new_mask = mask | mv

        if first:
            score = -negamax(opponent, new_mask, depth - 1, -beta, -alpha)
            first = False
        else:
            score = -negamax(opponent, new_mask, depth - 1, -alpha - 1, -alpha)
            if alpha < score < beta:
                score = -negamax(opponent, new_mask, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_col = col

        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best_col is None:
        best_col = pick_best_col(safe)
        best = -WIN_BASE + moves_played + 1

    flag = EXACT
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER

    old = TT.get(key)
    if old is None or old[0] <= depth:
        TT[key] = (depth, flag, best, best_col)

    return best


def search_root(position, mask, root_moves, depth, preferred=None):
    key = position | (mask << KEY_SHIFT)
    entry = TT.get(key)
    if entry is not None and entry[0] >= depth and entry[1] == EXACT and entry[3] is not None:
        return entry[2], entry[3]

    ttbest = entry[3] if entry is not None else None
    opponent = mask ^ position

    best_col = preferred if preferred is not None and (root_moves & COLUMN_MASK[preferred]) else pick_best_col(root_moves)
    best_score = -INF
    alpha = -INF
    first = True

    for col in ordered_cols(root_moves, preferred=preferred, ttbest=ttbest):
        mv = move_bit(mask, col)
        new_mask = mask | mv

        if first:
            score = -negamax(opponent, new_mask, depth - 1, -INF, INF)
            first = False
        else:
            score = -negamax(opponent, new_mask, depth - 1, -alpha - 1, -alpha)
            if score > alpha:
                score = -negamax(opponent, new_mask, depth - 1, -INF, -alpha)

        if score > best_score:
            best_score = score
            best_col = col

        if score > alpha:
            alpha = score

    old = TT.get(key)
    if old is None or old[0] <= depth:
        TT[key] = (depth, EXACT, best_score, best_col)

    return best_score, best_col


def policy(board: list[list[int]]) -> int:
    global DEADLINE, NODE_COUNTER

    position, mask = board_to_bitboards(board)

    legal_cols = [c for c in ORDER if (mask & TOP_MASK_COL[c]) == 0]
    if not legal_cols:
        return 0
    if len(legal_cols) == 1:
        return legal_cols[0]

    if mask == 0:
        return 3

    if len(TT) > 200000:
        TT.clear()

    possible = possible_mask(mask)

    # Immediate win
    win_moves = winning_positions(position, mask) & possible
    if win_moves:
        return pick_best_col(win_moves)

    # Safe moves / forced blocks
    safe = possible_non_losing_moves(position, mask)
    if safe == 0:
        # Unavoidable tactical loss: at least block one direct winning column if possible
        opp_wins = winning_positions(mask ^ position, mask) & possible
        if opp_wins:
            return pick_best_col(opp_wins)
        return legal_cols[0]

    if safe & (safe - 1) == 0:
        return bit_to_col(safe)

    best_col = pick_best_col(safe)

    DEADLINE = perf_counter() + TIME_LIMIT
    NODE_COUNTER = 0

    for depth in range(1, MAX_DEPTH + 1):
        if perf_counter() > DEADLINE:
            break
        try:
            score, col = search_root(position, mask, safe, depth, preferred=best_col)
            if col is not None:
                best_col = col
            if abs(score) >= WIN_BASE - SIZE:
                break
        except SearchTimeout:
            break

    if (mask & TOP_MASK_COL[best_col]) == 0:
        return best_col

    for c in ORDER:
        if (mask & TOP_MASK_COL[c]) == 0:
            return c

    return legal_cols[0]
