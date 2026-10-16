
from time import perf_counter

BOARD_SIZE = 4
FULL_MASK = (1 << 16) - 1
MATE_SCORE = 1_000_000
INF = 10**9

# Precompute win masks: 4 rows, 4 cols, 2 diagonals
WIN_MASKS = []

# Rows
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

# Cols
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

# Diagonals
m = 0
for i in range(4):
    m |= 1 << (4 * i + i)
WIN_MASKS.append(m)

m = 0
for i in range(4):
    m |= 1 << (4 * i + (3 - i))
WIN_MASKS.append(m)

MASKS_BY_CELL = [[] for _ in range(16)]
for mask in WIN_MASKS:
    for idx in range(16):
        if (mask >> idx) & 1:
            MASKS_BY_CELL[idx].append(mask)

# Slight preference for center-ish squares and corners over edges
POS_WEIGHTS = [
    3, 2, 2, 3,
    2, 4, 4, 2,
    2, 4, 4, 2,
    3, 2, 2, 3,
]

LINE_SCORES = (0, 2, 12, 90, 0)


class SearchTimeout(Exception):
    pass


def idx_to_rc(idx: int) -> tuple[int, int]:
    return divmod(idx, 4)


def rc_to_idx(r: int, c: int) -> int:
    return 4 * r + c


def board_to_bits(board: list[list[int]]) -> tuple[int, int, list[int]]:
    my_bits = 0
    opp_bits = 0
    empties = []
    for r in range(4):
        for c in range(4):
            idx = 4 * r + c
            v = board[r][c]
            if v == 1:
                my_bits |= 1 << idx
            elif v == -1:
                opp_bits |= 1 << idx
            else:
                empties.append(idx)
    return my_bits, opp_bits, empties


def has_win(bits: int) -> bool:
    for mask in WIN_MASKS:
        if (bits & mask) == mask:
            return True
    return False


def first_legal_move(board: list[list[int]]) -> tuple[int, int]:
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def empty_indices(my_bits: int, opp_bits: int) -> list[int]:
    empties = FULL_MASK & ~(my_bits | opp_bits)
    out = []
    while empties:
        bit = empties & -empties
        out.append(bit.bit_length() - 1)
        empties ^= bit
    return out


def would_win(bits: int, idx: int) -> bool:
    bit = 1 << idx
    new_bits = bits | bit
    for mask in MASKS_BY_CELL[idx]:
        if (new_bits & mask) == mask:
            return True
    return False


def winning_moves(bits: int, other: int) -> list[int]:
    empties = FULL_MASK & ~(bits | other)
    out = []
    while empties:
        bit = empties & -empties
        idx = bit.bit_length() - 1
        if would_win(bits, idx):
            out.append(idx)
        empties ^= bit
    return out


def threat_line_count(bits: int, other: int) -> int:
    cnt = 0
    for mask in WIN_MASKS:
        if (other & mask) == 0 and (bits & mask).bit_count() == 3:
            cnt += 1
    return cnt


def count_distinct_winning_moves(bits: int, other: int) -> int:
    return len(winning_moves(bits, other))


def evaluate(cur: int, opp: int) -> int:
    score = 0

    # Line-based evaluation
    for mask in WIN_MASKS:
        a = (cur & mask).bit_count()
        b = (opp & mask).bit_count()
        if a and b:
            continue
        if a:
            score += LINE_SCORES[a]
        elif b:
            score -= LINE_SCORES[b]

    # Positional evaluation
    x = cur
    while x:
        bit = x & -x
        idx = bit.bit_length() - 1
        score += POS_WEIGHTS[idx]
        x ^= bit

    x = opp
    while x:
        bit = x & -x
        idx = bit.bit_length() - 1
        score -= POS_WEIGHTS[idx]
        x ^= bit

    # Threat emphasis
    score += 40 * threat_line_count(cur, opp)
    score -= 50 * threat_line_count(opp, cur)

    return score


def ordered_moves(cur: int, opp: int, tt_move: int | None = None) -> list[int]:
    empties = FULL_MASK & ~(cur | opp)
    scored = []

    while empties:
        bit = empties & -empties
        idx = bit.bit_length() - 1
        after = cur | bit

        score = POS_WEIGHTS[idx] * 2

        if tt_move is not None and idx == tt_move:
            score += 500_000

        # Immediate win
        if would_win(cur, idx):
            score += 300_000

        # Immediate block
        if would_win(opp, idx):
            score += 150_000

        # Local line quality
        forkish = 0
        for mask in MASKS_BY_CELL[idx]:
            opp_count = (opp & mask).bit_count()
            my_count_after = (after & mask).bit_count()
            my_count_before = (cur & mask).bit_count()

            if opp_count == 0:
                if my_count_after == 1:
                    score += 4
                elif my_count_after == 2:
                    score += 14
                elif my_count_after == 3:
                    score += 70
                    forkish += 1

            if my_count_before == 0 and opp_count > 0:
                if opp_count == 1:
                    score += 2
                elif opp_count == 2:
                    score += 8
                elif opp_count == 3:
                    score += 30

        if forkish >= 2:
            score += 10_000

        scored.append((score, idx))
        empties ^= bit

    scored.sort(reverse=True)
    return [idx for _, idx in scored]


def choose_move(my_bits: int, opp_bits: int, empties_list: list[int]) -> int:
    if not empties_list:
        return 0

    # If game is already over, just return a legal move.
    if has_win(my_bits) or has_win(opp_bits):
        return empties_list[0]

    # Fast tactical rules first
    my_wins = winning_moves(my_bits, opp_bits)
    if my_wins:
        return my_wins[0]

    opp_wins = winning_moves(opp_bits, my_bits)
    if len(opp_wins) == 1:
        return opp_wins[0]

    legal_order = ordered_moves(my_bits, opp_bits)
    fallback = legal_order[0] if legal_order else empties_list[0]

    # Create fork if available
    for idx in legal_order:
        bit = 1 << idx
        if count_distinct_winning_moves(my_bits | bit, opp_bits) >= 2:
            return idx

    # Block unique opponent fork if needed
    opp_forks = []
    for idx in empties_list:
        bit = 1 << idx
        if count_distinct_winning_moves(opp_bits | bit, my_bits) >= 2:
            opp_forks.append(idx)
    if len(opp_forks) == 1:
        return opp_forks[0]

    deadline = perf_counter() + 0.94
    tt = {}
    node_counter = [0]

    # TT flags
    EXACT, LOWER, UPPER = 0, 1, 2

    def negamax(cur: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        node_counter[0] += 1
        if (node_counter[0] & 2047) == 0 and perf_counter() >= deadline:
            raise SearchTimeout

        # Previous move won
        if has_win(opp):
            return -MATE_SCORE + ply

        occupied = cur | opp
        if occupied == FULL_MASK:
            return 0

        key = (cur, opp)
        tt_move = None
        alpha_orig = alpha
        beta_orig = beta

        entry = tt.get(key)
        if entry is not None:
            entry_depth, entry_val, entry_flag, entry_best = entry
            if entry_depth >= depth:
                if entry_flag == EXACT:
                    return entry_val
                elif entry_flag == LOWER:
                    alpha = max(alpha, entry_val)
                else:
                    beta = min(beta, entry_val)
                if alpha >= beta:
                    return entry_val
            tt_move = entry_best

        if depth <= 0:
            # Small tactical extension if immediate threats exist
            if threat_line_count(cur, opp) or threat_line_count(opp, cur):
                depth = 1
            else:
                return evaluate(cur, opp)

        best_val = -INF
        best_move = None

        for idx in ordered_moves(cur, opp, tt_move):
            bit = 1 << idx
            val = -negamax(opp, cur | bit, depth - 1, -beta, -alpha, ply + 1)

            if val > best_val:
                best_val = val
                best_move = idx

            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best_val <= alpha_orig:
            flag = UPPER
        elif best_val >= beta_orig:
            flag = LOWER
        else:
            flag = EXACT

        tt[key] = (depth, best_val, flag, best_move)
        return best_val

    best_move = fallback
    max_depth = len(empties_list)

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            local_best_val = -INF
            local_best_move = best_move

            for idx in ordered_moves(my_bits, opp_bits, best_move):
                bit = 1 << idx
                val = -negamax(opp_bits, my_bits | bit, depth - 1, -beta, -alpha, 1)

                if val > local_best_val:
                    local_best_val = val
                    local_best_move = idx

                if val > alpha:
                    alpha = val

            best_move = local_best_move

            # Proven win/loss found
            if abs(local_best_val) >= MATE_SCORE - 32:
                break

        except SearchTimeout:
            break

    return best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Safe legal fallback no matter what
    fallback = first_legal_move(board)

    try:
        my_bits, opp_bits, empties = board_to_bits(board)
        if not empties:
            return fallback

        idx = choose_move(my_bits, opp_bits, empties)
        r, c = idx_to_rc(idx)

        # Final legality guard
        if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
            return (r, c)
        return fallback
    except Exception:
        return fallback
