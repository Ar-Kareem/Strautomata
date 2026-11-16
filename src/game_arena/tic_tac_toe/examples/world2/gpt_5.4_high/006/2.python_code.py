
import time

FULL_MASK = (1 << 16) - 1

# Bit i corresponds to cell (i // 4, i % 4)
WIN_MASKS = (
    0x000F, 0x00F0, 0x0F00, 0xF000,  # rows
    0x1111, 0x2222, 0x4444, 0x8888,  # cols
    0x8421, 0x1248,                  # diagonals
)

CELL_MASKS = tuple(
    tuple(mask for mask in WIN_MASKS if mask & (1 << i))
    for i in range(16)
)

IDX_TO_COORD = tuple((i // 4, i % 4) for i in range(16))

# Prefer center 2x2, then corners, then edges.
OPENING_PREF = (5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)

PREF_BONUS = [0] * 16
for rank, idx in enumerate(OPENING_PREF):
    PREF_BONUS[idx] = 16 - rank

# Positional weights: center 2x2 and corners are strongest.
POS_WEIGHTS = (
    4, 2, 2, 4,
    2, 5, 5, 2,
    2, 5, 5, 2,
    4, 2, 2, 4,
)

LINE_WEIGHTS = (0, 6, 28, 180, 0)
LOCAL_WEIGHTS = (0, 6, 24, 140, 0)
BLOCK_WEIGHTS = (0, 5, 22, 150, 0)

WIN_SCORE = 10_000_000
INF = 10**15
TIME_LIMIT = 0.93

EXACT, LOWER, UPPER = 0, 1, 2

# Precompute win table for all 16-bit boards.
WIN_TABLE = bytearray(1 << 16)
for bits in range(1 << 16):
    for mask in WIN_MASKS:
        if (bits & mask) == mask:
            WIN_TABLE[bits] = 1
            break

# Precompute positional score for all 16-bit boards.
POS_TABLE = [0] * (1 << 16)
for bits in range(1, 1 << 16):
    lsb = bits & -bits
    POS_TABLE[bits] = POS_TABLE[bits ^ lsb] + POS_WEIGHTS[lsb.bit_length() - 1]

TT = {}
_DEADLINE = 0.0
_NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def has_win(bits: int) -> bool:
    return bool(WIN_TABLE[bits])


def iter_bits(bits: int):
    while bits:
        lsb = bits & -bits
        yield lsb.bit_length() - 1
        bits ^= lsb


def encode_key(us: int, opp: int, to_move: int) -> int:
    return us | (opp << 16) | ((1 if to_move == 1 else 0) << 32)


def board_to_bits(board):
    us = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                us |= bit
            elif v == -1:
                opp |= bit
    return us, opp


def select_preferred(mask: int) -> int:
    if not mask:
        return 0
    for idx in OPENING_PREF:
        if mask & (1 << idx):
            return idx
    return mask.bit_length() - 1


def preferred_legal(legal_mask: int) -> int:
    return select_preferred(legal_mask)


def immediate_win_bits(us: int, opp: int, player: int) -> int:
    curr = us if player == 1 else opp
    other = opp if player == 1 else us
    occupied = us | opp
    wins = 0
    for mask in WIN_MASKS:
        if other & mask:
            continue
        if (curr & mask).bit_count() == 3:
            wins |= mask & ~occupied
    return wins & FULL_MASK


def is_winning_move(curr_bits: int, idx: int) -> bool:
    return has_win(curr_bits | (1 << idx))


def fork_bits(us: int, opp: int, player: int) -> int:
    occupied = us | opp
    empties = (~occupied) & FULL_MASK
    out = 0
    for idx in iter_bits(empties):
        bit = 1 << idx
        if player == 1:
            us2, opp2 = us | bit, opp
            if has_win(us2):
                continue
        else:
            us2, opp2 = us, opp | bit
            if has_win(opp2):
                continue
        if immediate_win_bits(us2, opp2, player).bit_count() >= 2:
            out |= bit
    return out


def heuristic(us: int, opp: int, to_move: int) -> int:
    score = POS_TABLE[us] - POS_TABLE[opp]

    for mask in WIN_MASKS:
        a = (us & mask).bit_count()
        b = (opp & mask).bit_count()
        if a and b:
            continue
        if a:
            score += LINE_WEIGHTS[a]
        elif b:
            score -= LINE_WEIGHTS[b]

    w_us = immediate_win_bits(us, opp, 1).bit_count()
    w_opp = immediate_win_bits(us, opp, -1).bit_count()

    if w_us >= 2:
        score += 220_000
    elif w_us == 1:
        score += 100_000 if to_move == 1 else 40_000

    if w_opp >= 2:
        score -= 220_000
    elif w_opp == 1:
        score -= 100_000 if to_move == -1 else 40_000

    return score


def move_order_score(us: int, opp: int, to_move: int, idx: int, opp_win_now: int) -> int:
    bit = 1 << idx
    curr = us if to_move == 1 else opp
    other = opp if to_move == 1 else us

    if is_winning_move(curr, idx):
        return 10_000_000

    score = POS_WEIGHTS[idx] * 10

    # If the opponent already has an immediate win, blocking it is critical.
    if opp_win_now:
        if opp_win_now & bit:
            score += 1_000_000
        else:
            score -= 1_000_000

    # Local line growth / blocking value.
    for mask in CELL_MASKS[idx]:
        mine = (curr & mask).bit_count()
        theirs = (other & mask).bit_count()
        if theirs == 0:
            score += LOCAL_WEIGHTS[mine + 1] - LOCAL_WEIGHTS[mine]
        elif mine == 0:
            score += BLOCK_WEIGHTS[theirs]

    # Late-game: prefer moves that create immediate threats/forks.
    if (us | opp).bit_count() >= 8:
        if to_move == 1:
            own_wins = immediate_win_bits(us | bit, opp, 1).bit_count()
        else:
            own_wins = immediate_win_bits(us, opp | bit, -1).bit_count()
        if own_wins >= 2:
            score += 120_000
        else:
            score += 15_000 * own_wins

    return score


def ordered_moves(us: int, opp: int, to_move: int, tt_move=None):
    occupied = us | opp
    empties = (~occupied) & FULL_MASK
    opp_win_now = immediate_win_bits(us, opp, -to_move)

    scored = []
    if tt_move is not None and (empties & (1 << tt_move)):
        scored.append((10**12, PREF_BONUS[tt_move], tt_move))

    for idx in iter_bits(empties):
        if idx == tt_move:
            continue
        s = move_order_score(us, opp, to_move, idx, opp_win_now)
        scored.append((s, PREF_BONUS[idx], idx))

    scored.sort(reverse=True)
    return [idx for _, __, idx in scored]


def alphabeta(us: int, opp: int, to_move: int, depth: int, alpha: int, beta: int) -> int:
    global _NODE_COUNTER

    _NODE_COUNTER += 1
    if (_NODE_COUNTER & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise SearchTimeout

    occupied = us | opp
    empties = 16 - occupied.bit_count()

    if has_win(us):
        return WIN_SCORE + empties
    if has_win(opp):
        return -WIN_SCORE - empties
    if empties == 0:
        return 0

    key = encode_key(us, opp, to_move)
    entry = TT.get(key)
    tt_move = None

    alpha0, beta0 = alpha, beta
    if entry is not None:
        edepth, flag, val, best = entry
        tt_move = best
        if edepth >= depth:
            if flag == EXACT:
                return val
            if flag == LOWER and val > alpha:
                alpha = val
            elif flag == UPPER and val < beta:
                beta = val
            if alpha >= beta:
                return val

    if depth == 0:
        return heuristic(us, opp, to_move)

    best_move = None

    if to_move == 1:
        value = -INF
        for idx in ordered_moves(us, opp, to_move, tt_move):
            bit = 1 << idx
            v = alphabeta(us | bit, opp, -1, depth - 1, alpha, beta)
            if v > value:
                value = v
                best_move = idx
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = INF
        for idx in ordered_moves(us, opp, to_move, tt_move):
            bit = 1 << idx
            v = alphabeta(us, opp | bit, 1, depth - 1, alpha, beta)
            if v < value:
                value = v
                best_move = idx
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    flag = EXACT
    if value <= alpha0:
        flag = UPPER
    elif value >= beta0:
        flag = LOWER

    TT[key] = (depth, flag, value, best_move)
    return value


def root_search(us: int, opp: int, depth: int):
    if time.perf_counter() >= _DEADLINE:
        raise SearchTimeout

    key = encode_key(us, opp, 1)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else None

    moves = ordered_moves(us, opp, 1, tt_move)
    best_move = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for idx in moves:
        if time.perf_counter() >= _DEADLINE:
            raise SearchTimeout
        score = alphabeta(us | (1 << idx), opp, -1, depth - 1, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = idx
        if best_score > alpha:
            alpha = best_score

    TT[key] = (depth, EXACT, best_score, best_move)
    return best_move, best_score


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODE_COUNTER

    us, opp = board_to_bits(board)
    occupied = us | opp
    legal = (~occupied) & FULL_MASK

    # No legal move should normally never happen, but keep a safe return.
    if not legal:
        return (0, 0)

    # If only one move exists, play it.
    if (legal & (legal - 1)) == 0:
        return IDX_TO_COORD[legal.bit_length() - 1]

    # If the state is already terminal, just return a legal move.
    if has_win(us) or has_win(opp):
        return IDX_TO_COORD[preferred_legal(legal)]

    # Keep TT from growing forever across many calls/games.
    if len(TT) > 300_000:
        TT.clear()

    # Strong opening shortcut.
    if occupied == 0:
        return (1, 1)

    # Forced tactics first.
    my_wins = immediate_win_bits(us, opp, 1)
    if my_wins:
        return IDX_TO_COORD[select_preferred(my_wins)]

    opp_wins = immediate_win_bits(us, opp, -1)
    if opp_wins:
        # If there is one threat, block it. If there are many, the position is
        # already lost unless we had a win above, so block one legal threat.
        return IDX_TO_COORD[select_preferred(opp_wins)]

    my_forks = fork_bits(us, opp, 1)
    if my_forks:
        return IDX_TO_COORD[select_preferred(my_forks)]

    # Search fallback.
    best_move = preferred_legal(legal)
    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODE_COUNTER = 0

    max_depth = 16 - occupied.bit_count()
    depth = 1

    while depth <= max_depth:
        try:
            move, score = root_search(us, opp, depth)
            if move is not None:
                best_move = move
            if abs(score) >= WIN_SCORE // 2:
                break
            depth += 1
        except SearchTimeout:
            break

    return IDX_TO_COORD[best_move]
