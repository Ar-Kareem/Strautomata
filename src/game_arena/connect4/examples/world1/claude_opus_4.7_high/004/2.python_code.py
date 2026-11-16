
import time

BOARD_MASK = 0
for _c in range(7):
    for _r in range(6):
        BOARD_MASK |= 1 << (_c * 7 + _r)

CENTER_MASK = 0
for _r in range(6):
    CENTER_MASK |= 1 << (3 * 7 + _r)

COL_TOP_BIT = [1 << (c * 7 + 5) for c in range(7)]
COLUMN_MASK = [0x3F << (c * 7) for c in range(7)]
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]


def is_win(pos):
    m = pos & (pos >> 7)
    if m & (m >> 14): return True
    m = pos & (pos >> 6)
    if m & (m >> 12): return True
    m = pos & (pos >> 8)
    if m & (m >> 16): return True
    m = pos & (pos >> 1)
    if m & (m >> 2): return True
    return False


def can_play(mask, col):
    return (mask & COL_TOP_BIT[col]) == 0


def make_move(pos, mask, col):
    empty = COLUMN_MASK[col] & ~mask
    bit = empty & (-empty)
    return pos | bit, mask | bit


def compute_winning_squares(pos):
    r = (pos << 1) & (pos << 2) & (pos << 3)
    p = (pos << 7) & (pos << 14)
    r |= p & (pos << 21)
    r |= p & (pos >> 7)
    p = (pos >> 7) & (pos >> 14)
    r |= p & (pos << 7)
    r |= p & (pos >> 21)
    p = (pos << 8) & (pos << 16)
    r |= p & (pos << 24)
    r |= p & (pos >> 8)
    p = (pos >> 8) & (pos >> 16)
    r |= p & (pos << 8)
    r |= p & (pos >> 24)
    p = (pos << 6) & (pos << 12)
    r |= p & (pos << 18)
    r |= p & (pos >> 6)
    p = (pos >> 6) & (pos >> 12)
    r |= p & (pos << 6)
    r |= p & (pos >> 18)
    return r & BOARD_MASK


def evaluate(pos, mask):
    opp = pos ^ mask
    non_mask = BOARD_MASK & ~mask
    my_w = compute_winning_squares(pos) & non_mask
    op_w = compute_winning_squares(opp) & non_mask
    my_total = bin(my_w).count('1')
    op_total = bin(op_w).count('1')
    my_c = bin(pos & CENTER_MASK).count('1')
    op_c = bin(opp & CENTER_MASK).count('1')
    return (my_total - op_total) * 4 + (my_c - op_c) * 2


class Timeout(Exception):
    pass


_deadline = 0
_nodes = 0


def negamax(pos, mask, alpha, beta, depth):
    global _nodes
    _nodes += 1
    if (_nodes & 2047) == 0:
        if time.time() > _deadline:
            raise Timeout()

    moves = bin(mask).count('1')
    if moves == 42:
        return 0

    for col in COLUMN_ORDER:
        if can_play(mask, col):
            new_pos, _ = make_move(pos, mask, col)
            if is_win(new_pos):
                return 1000 - moves

    if depth == 0:
        return evaluate(pos, mask)

    best = -100000
    for col in COLUMN_ORDER:
        if can_play(mask, col):
            new_pos, new_mask = make_move(pos, mask, col)
            opp_pos = new_mask ^ new_pos
            score = -negamax(opp_pos, new_mask, -beta, -alpha, depth - 1)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    return best


def policy(board):
    global _deadline, _nodes

    my_pos = 0
    opp_pos = 0
    for c in range(7):
        for r in range(6):
            br = 5 - r
            cell = board[br][c]
            if cell == 0:
                break
            bit = 1 << (c * 7 + r)
            if cell == 1:
                my_pos |= bit
            else:
                opp_pos |= bit

    mask = my_pos | opp_pos

    for col in COLUMN_ORDER:
        if can_play(mask, col):
            new_pos, _ = make_move(my_pos, mask, col)
            if is_win(new_pos):
                return col

    for col in COLUMN_ORDER:
        if can_play(mask, col):
            new_opp, _ = make_move(opp_pos, mask, col)
            if is_win(new_opp):
                return col

    best_move = 3
    if not can_play(mask, 3):
        for col in COLUMN_ORDER:
            if can_play(mask, col):
                best_move = col
                break

    start = time.time()
    _deadline = start + 0.85
    _nodes = 0

    try:
        for depth in range(2, 25):
            best_score = -100000
            current_best = best_move
            alpha = -100000
            beta = 100000
            found_any = False
            for col in COLUMN_ORDER:
                if can_play(mask, col):
                    new_pos, new_mask = make_move(my_pos, mask, col)
                    if is_win(new_pos):
                        return col
                    opp_p = new_mask ^ new_pos
                    score = -negamax(opp_p, new_mask, -beta, -alpha, depth - 1)
                    if not found_any or score > best_score:
                        best_score = score
                        current_best = col
                        found_any = True
                    if best_score > alpha:
                        alpha = best_score
            best_move = current_best
            if best_score >= 900 or best_score <= -900:
                break
    except Timeout:
        pass

    if not can_play(mask, best_move):
        for col in range(7):
            if can_play(mask, col):
                return col
    return best_move
