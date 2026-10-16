
from time import perf_counter

N = 4
FULL_MASK = (1 << 16) - 1

# Bit index = row * 4 + col
BITS = [1 << i for i in range(16)]

# All 10 winning lines on a 4x4 board: 4 rows, 4 cols, 2 diagonals
LINES = []

for r in range(4):
    mask = 0
    for c in range(4):
        mask |= 1 << (r * 4 + c)
    LINES.append(mask)

for c in range(4):
    mask = 0
    for r in range(4):
        mask |= 1 << (r * 4 + c)
    LINES.append(mask)

LINES.append((1 << 0) | (1 << 5) | (1 << 10) | (1 << 15))
LINES.append((1 << 3) | (1 << 6) | (1 << 9) | (1 << 12))

CELL_LINES = [[] for _ in range(16)]
for line in LINES:
    m = line
    while m:
        b = m & -m
        idx = b.bit_length() - 1
        CELL_LINES[idx].append(line)
        m ^= b

# Prefer inner 2x2, then corners, then edges
POS_WEIGHTS = [
    5, 3, 3, 5,
    3, 6, 6, 3,
    3, 6, 6, 3,
    5, 3, 3, 5,
]

PREFERRED_ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

# Opening response book when moving second on move 1
OPENING_RESPONSE = {
    0: 5,  3: 6, 12: 9, 15: 10,  # corners -> matching inner diagonal square
    1: 5,  2: 6,  4: 5,  7: 6,   # upper/left/right edges -> nearby inner
    8: 9, 11: 10, 13: 9, 14: 10, # lower edges -> nearby inner
    5: 10, 6: 9, 9: 6, 10: 5,    # inner -> opposite inner
}

# Static evaluation weights
LINE_WEIGHTS = (0, 5, 30, 160, 0)
THREAT_WEIGHT = 220

# Move ordering weights
ORDER_ATTACK = (0, 12, 90, 1800, 0)
ORDER_BLOCK = (0, 0, 20, 500, 0)

MATE = 1_000_000
INF = 10_000_000

# Precompute positional score for every 16-bit mask
POS_SCORE = [0] * (1 << 16)
for mask in range(1, 1 << 16):
    lsb = mask & -mask
    idx = lsb.bit_length() - 1
    POS_SCORE[mask] = POS_SCORE[mask ^ lsb] + POS_WEIGHTS[idx]

TT = {}
MAX_TT_SIZE = 250_000

SEARCH_DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def idx_to_move(idx: int) -> tuple[int, int]:
    return (idx >> 2, idx & 3)


def choose_preferred_index(mask: int) -> int:
    for idx in PREFERRED_ORDER:
        if mask & (1 << idx):
            return idx
    if mask:
        bit = mask & -mask
        return bit.bit_length() - 1
    return 0


def has_win(bits: int) -> bool:
    for line in LINES:
        if (bits & line) == line:
            return True
    return False


def winning_moves_bits(cur: int, opp: int) -> int:
    """Bitmask of empty squares where cur can win immediately."""
    occ = cur | opp
    res = 0
    for line in LINES:
        if (opp & line) == 0 and (cur & line).bit_count() == 3:
            res |= line & ~occ
    return res & ~occ


def evaluate(cur: int, opp: int) -> int:
    """Static eval from current player's perspective."""
    score = POS_SCORE[cur] - POS_SCORE[opp]

    for line in LINES:
        c = (cur & line).bit_count()
        o = (opp & line).bit_count()
        if c and o:
            continue
        if o == 0:
            score += LINE_WEIGHTS[c]
        elif c == 0:
            score -= LINE_WEIGHTS[o]

    score += THREAT_WEIGHT * winning_moves_bits(cur, opp).bit_count()
    score -= THREAT_WEIGHT * winning_moves_bits(opp, cur).bit_count()
    return score


def ordered_moves(cur: int, opp: int, empties_mask: int, tt_move: int | None = None, opp_wins: int = 0) -> list[int]:
    scored = []
    m = empties_mask

    while m:
        bit = m & -m
        m ^= bit
        idx = bit.bit_length() - 1

        score = POS_WEIGHTS[idx]
        if tt_move is not None and idx == tt_move:
            score += 10_000_000
        if opp_wins & bit:
            score += 2_000_000

        new_cur = cur | bit
        local = 0
        made_threes = 0
        win_now = False

        for line in CELL_LINES[idx]:
            c = (cur & line).bit_count()
            o = (opp & line).bit_count()

            if o == 0:
                nc = c + 1
                local += ORDER_ATTACK[nc]
                if nc == 3:
                    made_threes += 1
                if (new_cur & line) == line:
                    win_now = True
            elif c == 0:
                local += ORDER_BLOCK[o]

        if win_now:
            local += 5_000_000
        if made_threes >= 2:
            local += 120_000 * made_threes
        elif made_threes == 1:
            local += 4_000

        scored.append((score + local, idx))

    scored.sort(reverse=True)
    return [idx for _, idx in scored]


def negamax(cur: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> tuple[int, int | None]:
    global NODE_COUNTER, SEARCH_DEADLINE, TT

    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and perf_counter() > SEARCH_DEADLINE:
        raise SearchTimeout

    # Terminal checks
    if has_win(cur):
        return MATE - ply, None
    if has_win(opp):
        return -(MATE - ply), None

    empties_mask = FULL_MASK ^ (cur | opp)
    if empties_mask == 0:
        return 0, None

    # Immediate tactical checks
    my_wins = winning_moves_bits(cur, opp)
    if my_wins:
        return MATE - ply, choose_preferred_index(my_wins)

    opp_wins = winning_moves_bits(opp, cur)
    if opp_wins:
        # If opponent has 2+ distinct winning squares, and we cannot win now, this is lost.
        if (opp_wins & (opp_wins - 1)) != 0:
            return -(MATE - (ply + 1)), choose_preferred_index(opp_wins)
        # Horizon extension: if only one forced block exists, search it even at depth 0.
        if depth == 0:
            depth = 1

    if depth == 0:
        return evaluate(cur, opp), None

    orig_alpha, orig_beta = alpha, beta
    state = (cur, opp)
    tt_move = None

    entry = TT.get(state)
    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:      # exact
                return e_score, e_move
            elif e_flag == 1:    # lower bound
                alpha = max(alpha, e_score)
            else:                # upper bound
                beta = min(beta, e_score)
            if alpha >= beta:
                return e_score, e_move

    if opp_wins:
        only_bit = opp_wins & -opp_wins
        moves = [only_bit.bit_length() - 1]
    else:
        moves = ordered_moves(cur, opp, empties_mask, tt_move=tt_move, opp_wins=opp_wins)

    best_val = -INF
    best_move = moves[0] if moves else None

    for idx in moves:
        bit = 1 << idx
        child_val, _ = negamax(opp, cur | bit, depth - 1, -beta, -alpha, ply + 1)
        val = -child_val

        if val > best_val:
            best_val = val
            best_move = idx

        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    # TT store
    flag = 0
    if best_val <= orig_alpha:
        flag = -1   # upper bound
    elif best_val >= orig_beta:
        flag = 1    # lower bound

    if len(TT) > MAX_TT_SIZE:
        TT.clear()
    prev = TT.get(state)
    if prev is None or depth >= prev[0]:
        TT[state] = (depth, flag, best_val, best_move)

    return best_val, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    global SEARCH_DEADLINE, NODE_COUNTER, TT

    cur = 0
    opp = 0

    # Robust parsing: anything other than 1 / -1 is treated as empty
    for r in range(4):
        row = board[r] if r < len(board) else []
        for c in range(4):
            v = row[c] if c < len(row) else 0
            idx = (r << 2) + c
            if v == 1:
                cur |= 1 << idx
            elif v == -1:
                opp |= 1 << idx

    occ = cur | opp
    empties_mask = FULL_MASK ^ occ

    # No legal move exists; return something in-range.
    if empties_mask == 0:
        return (0, 0)

    # If position is already terminal for any reason, still return a legal move.
    if has_win(cur) or has_win(opp):
        idx = choose_preferred_index(empties_mask)
        return idx_to_move(idx)

    # Tactical root checks
    my_wins = winning_moves_bits(cur, opp)
    if my_wins:
        return idx_to_move(choose_preferred_index(my_wins))

    opp_wins = winning_moves_bits(opp, cur)
    if opp_wins:
        if (opp_wins & (opp_wins - 1)) == 0:
            idx = (opp_wins & -opp_wins).bit_length() - 1
            return idx_to_move(idx)
        # Lost anyway; at least occupy one of the winning squares if possible.
        return idx_to_move(choose_preferred_index(opp_wins))

    occupied = occ.bit_count()

    # Opening move
    if occupied == 0:
        return (1, 1)

    # Simple opening reply book when moving second on the first turn
    if occupied == 1 and cur == 0:
        opp_idx = choose_preferred_index(opp)
        reply = OPENING_RESPONSE.get(opp_idx, 5)
        if empties_mask & (1 << reply):
            return idx_to_move(reply)

    # Default legal move before search starts
    tt_entry = TT.get((cur, opp))
    tt_move = tt_entry[3] if tt_entry is not None else None
    ordered = ordered_moves(cur, opp, empties_mask, tt_move=tt_move)
    best_move = ordered[0] if ordered else choose_preferred_index(empties_mask)

    # Fresh TT per call so mate-distance scores stay consistent
    TT.clear()
    NODE_COUNTER = 0

    empties = empties_mask.bit_count()
    budget = 0.98 if empties <= 10 else 0.92
    SEARCH_DEADLINE = perf_counter() + budget

    try:
        for depth in range(1, empties + 1):
            val, move = negamax(cur, opp, depth, -INF, INF, 0)
            if move is not None:
                best_move = move
            # Proven outcome or full search
            if abs(val) >= MATE - 32 or depth >= empties:
                break
    except SearchTimeout:
        pass

    # Final legality check
    if (empties_mask & (1 << best_move)) == 0:
        best_move = choose_preferred_index(empties_mask)

    return idx_to_move(best_move)
