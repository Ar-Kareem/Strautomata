
import time

# =========================
# 4x4 Tic-Tac-Toe Policy
# =========================

FULL_MASK = (1 << 16) - 1
WIN_SCORE = 1_000_000
INF = 10**9

# Bit index = row * 4 + col
# Winning lines: 4 rows, 4 cols, 2 diagonals
WIN_MASKS = [
    0b0000000000001111,
    0b0000000011110000,
    0b0000111100000000,
    0b1111000000000000,
    0b0001000100010001,
    0b0010001000100010,
    0b0100010001000100,
    0b1000100010001000,
    0b1000010000100001,
    0b0001001001001000,
]

CENTER_MASK = (1 << 5) | (1 << 6) | (1 << 9) | (1 << 10)
CORNER_MASK = (1 << 0) | (1 << 3) | (1 << 12) | (1 << 15)

# Positional preference: centers > diagonal corners > edges
POSITION_WEIGHT = [
    3, 2, 2, 3,
    2, 4, 4, 2,
    2, 4, 4, 2,
    3, 2, 2, 3,
]

# Heuristic values for open lines
LINE_SCORES = [0, 4, 20, 180, 0]

# Move ordering bonuses for lines containing the candidate move
ATTACK_BONUS = [3, 12, 50, 400]   # if opponent absent, based on own count before move
BLOCK_BONUS  = [2, 8, 30, 250]    # if own absent, based on opp count before move

# Precompute which win lines touch each cell
CELL_TO_LINES = [[] for _ in range(16)]
for mask in WIN_MASKS:
    mm = mask
    while mm:
        b = mm & -mm
        idx = b.bit_length() - 1
        CELL_TO_LINES[idx].append(mask)
        mm ^= b

# Transposition table: (x_bits, o_bits, player) -> (depth, flag, value, best_move)
# flag: 0 exact, 1 lowerbound, -1 upperbound
TT = {}


class SearchTimeout(Exception):
    pass


class SearchCtx:
    __slots__ = ("deadline", "nodes")
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.nodes = 0


def iter_bits(bb: int):
    while bb:
        b = bb & -bb
        yield b
        bb ^= b


def bit_to_coord(bit: int):
    idx = bit.bit_length() - 1
    return (idx >> 2, idx & 3)


def board_to_bits(board):
    x = 0
    o = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                x |= bit
            elif v == -1:
                o |= bit
    return x, o


def first_legal_move(empties: int):
    if empties:
        return empties & -empties
    return 0


def winner(x: int, o: int) -> int:
    for mask in WIN_MASKS:
        if (x & mask) == mask:
            return 1
        if (o & mask) == mask:
            return -1
    return 0


def winning_moves(x: int, o: int, player: int) -> int:
    own = x if player == 1 else o
    opp = o if player == 1 else x
    empties = FULL_MASK ^ (x | o)
    res = 0
    for mask in WIN_MASKS:
        if opp & mask:
            continue
        if (own & mask).bit_count() == 3:
            res |= (mask & empties)
    return res


def fork_moves(x: int, o: int, player: int) -> int:
    empties = FULL_MASK ^ (x | o)
    res = 0
    for m in iter_bits(empties):
        if player == 1:
            wx = winning_moves(x | m, o, 1)
        else:
            wx = winning_moves(x, o | m, -1)
        if wx.bit_count() >= 2:
            res |= m
    return res


def static_eval(x: int, o: int) -> int:
    score = 0

    for mask in WIN_MASKS:
        xc = (x & mask).bit_count()
        oc = (o & mask).bit_count()
        if xc and oc:
            continue
        if xc:
            score += LINE_SCORES[xc]
        elif oc:
            score -= LINE_SCORES[oc]

    score += 3 * ((x & CENTER_MASK).bit_count() - (o & CENTER_MASK).bit_count())
    score += 2 * ((x & CORNER_MASK).bit_count() - (o & CORNER_MASK).bit_count())

    wx = winning_moves(x, o, 1).bit_count()
    wo = winning_moves(x, o, -1).bit_count()
    score += 500 * (wx - wo)

    return score


def ordered_moves(moves_bits: int, x: int, o: int, player: int, tt_move: int = 0):
    own = x if player == 1 else o
    opp = o if player == 1 else x
    scored = []

    for m in iter_bits(moves_bits):
        idx = m.bit_length() - 1
        s = POSITION_WEIGHT[idx]

        if m == tt_move:
            s += 100000

        for mask in CELL_TO_LINES[idx]:
            oc = (own & mask).bit_count()
            pc = (opp & mask).bit_count()
            if pc == 0:
                s += ATTACK_BONUS[oc]
            elif oc == 0:
                s += BLOCK_BONUS[pc]

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def check_time(ctx: SearchCtx):
    ctx.nodes += 1
    if (ctx.nodes & 2047) == 0 and time.perf_counter() >= ctx.deadline:
        raise SearchTimeout


def negamax(x: int, o: int, player: int, depth: int, alpha: int, beta: int, ctx: SearchCtx) -> int:
    check_time(ctx)

    empties = FULL_MASK ^ (x | o)
    n_empty = empties.bit_count()

    w = winner(x, o)
    if w:
        return w * player * (WIN_SCORE + n_empty)
    if not empties:
        return 0

    if depth <= 0:
        # Tactical extension on volatile nodes
        if winning_moves(x, o, player) or winning_moves(x, o, -player):
            depth = 1
        else:
            return player * static_eval(x, o)

    alpha_orig = alpha
    beta_orig = beta
    key = (x, o, player)
    tt_move = 0

    entry = TT.get(key)
    if entry is not None:
        entry_depth, flag, value, best_move = entry
        tt_move = best_move
        if entry_depth >= depth:
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    my_wins = winning_moves(x, o, player)
    if my_wins:
        moves_bits = my_wins
    else:
        opp_wins = winning_moves(x, o, -player)
        if opp_wins:
            # If opponent threatens an immediate win, blocking squares are forced
            moves_bits = opp_wins & empties
            if not moves_bits:
                moves_bits = empties
        else:
            moves_bits = empties

    moves = ordered_moves(moves_bits, x, o, player, tt_move)
    best = -INF
    best_move = moves[0]

    for m in moves:
        if player == 1:
            val = -negamax(x | m, o, -1, depth - 1, -beta, -alpha, ctx)
        else:
            val = -negamax(x, o | m, 1, depth - 1, -beta, -alpha, ctx)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = -1
    elif best >= beta_orig:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, flag, best, best_move)

    return best


def search_root(x: int, o: int, depth: int, ctx: SearchCtx):
    empties = FULL_MASK ^ (x | o)
    key = (x, o, 1)
    tt_move = TT[key][3] if key in TT else 0

    my_wins = winning_moves(x, o, 1)
    if my_wins:
        moves_bits = my_wins
    else:
        opp_wins = winning_moves(x, o, -1)
        if opp_wins:
            moves_bits = opp_wins & empties
            if not moves_bits:
                moves_bits = empties
        else:
            moves_bits = empties

    moves = ordered_moves(moves_bits, x, o, 1, tt_move)
    if not moves:
        return 0, first_legal_move(empties)

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = moves[0]

    for m in moves:
        val = -negamax(x | m, o, -1, depth - 1, -beta, -alpha, ctx)
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val

    return best_val, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    global TT

    # Avoid unbounded growth across many calls
    if len(TT) > 500000:
        TT.clear()

    x, o = board_to_bits(board)
    occupied = x | o
    empties = FULL_MASK ^ occupied

    # Safe fallback: always keep a legal move ready
    fallback = first_legal_move(empties)
    if fallback == 0:
        return (0, 0)  # should not happen in normal play

    # If called on a terminal state, still return a legal empty move
    if winner(x, o):
        return bit_to_coord(fallback)

    # Opening choices
    if occupied == 0:
        return (1, 1)
    if x == 0 and o.bit_count() == 1:
        centers = CENTER_MASK & empties
        if centers:
            best_center = ordered_moves(centers, x, o, 1)[0]
            return bit_to_coord(best_center)

    # Immediate tactical rules
    my_wins = winning_moves(x, o, 1)
    if my_wins:
        move = ordered_moves(my_wins, x, o, 1)[0]
        return bit_to_coord(move)

    opp_wins = winning_moves(x, o, -1)
    if opp_wins and opp_wins.bit_count() == 1:
        move = opp_wins & -opp_wins
        return bit_to_coord(move)

    my_forks = fork_moves(x, o, 1)
    if my_forks:
        move = ordered_moves(my_forks, x, o, 1)[0]
        return bit_to_coord(move)

    opp_forks = fork_moves(x, o, -1)
    if opp_forks and opp_forks.bit_count() == 1:
        move = opp_forks & -opp_forks
        return bit_to_coord(move)

    # Heuristic fallback before search
    best_move = ordered_moves(empties, x, o, 1)[0]

    # Iterative deepening alpha-beta
    deadline = time.perf_counter() + 0.92
    ctx = SearchCtx(deadline)

    max_depth = empties.bit_count()
    for depth in range(1, max_depth + 1):
        try:
            value, move = search_root(x, o, depth, ctx)
            if move:
                best_move = move

            # If fully solved or immediate forced result found, deeper search is less important
            if abs(value) >= WIN_SCORE and depth >= 3:
                break
        except SearchTimeout:
            break

    return bit_to_coord(best_move)
