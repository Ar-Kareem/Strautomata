
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)

BOTTOM_MASKS = [1 << (7 * c) for c in range(COLS)]
PLAYABLE_MASKS = [((1 << ROWS) - 1) << (7 * c) for c in range(COLS)]

FULL_MASK = 0
for _m in PLAYABLE_MASKS:
    FULL_MASK |= _m

CENTER_MASK = PLAYABLE_MASKS[3]
NEAR_CENTER_MASK = PLAYABLE_MASKS[2] | PLAYABLE_MASKS[4]

LINE_SCORES = (0, 1, 8, 50, 5000)

MATE = 1_000_000
INF = 10_000_000
TIME_BUDGET = 0.92
CHECK_MASK = 511

TT = {}


class _SearchTimeout(Exception):
    pass


def _build_win_masks():
    masks = []

    # Vertical
    for c in range(COLS):
        base = 7 * c
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << (base + r + i)
            masks.append(m)

    # Horizontal
    for c in range(COLS - 3):
        for r in range(ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + r)
            masks.append(m)

    # Diagonal up-right
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + (r + i))
            masks.append(m)

    # Diagonal down-right
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + (r - i))
            masks.append(m)

    return tuple(masks)


WIN_MASKS = _build_win_masks()


def _move_bit(occupied: int, col: int) -> int:
    return (occupied + BOTTOM_MASKS[col]) & PLAYABLE_MASKS[col]


def _is_win(bits: int) -> bool:
    # Vertical
    m = bits & (bits >> 1)
    if m & (m >> 2):
        return True

    # Horizontal
    m = bits & (bits >> 7)
    if m & (m >> 14):
        return True

    # Diagonal /
    m = bits & (bits >> 6)
    if m & (m >> 12):
        return True

    # Diagonal \
    m = bits & (bits >> 8)
    if m & (m >> 16):
        return True

    return False


def _first_legal(occupied: int) -> int:
    for c in ORDER:
        if _move_bit(occupied, c):
            return c
    return 0


def _board_to_bits(board: list[list[int]]) -> tuple[int, int]:
    curr = 0
    opp = 0
    for r in range(ROWS):
        ir = ROWS - 1 - r  # bottom row becomes bit row 0
        row = board[r]
        for c in range(COLS):
            cell = row[c]
            if cell == 0:
                continue
            bit = 1 << (7 * c + ir)
            if cell == 1:
                curr |= bit
            elif cell == -1:
                opp |= bit
    return curr, opp


def _has_immediate_win(curr: int, opp: int) -> bool:
    occupied = curr | opp
    for c in ORDER:
        bit = _move_bit(occupied, c)
        if bit and _is_win(curr | bit):
            return True
    return False


def _evaluate(curr: int, opp: int) -> int:
    score = 0

    score += 6 * ((curr & CENTER_MASK).bit_count() - (opp & CENTER_MASK).bit_count())
    score += 3 * ((curr & NEAR_CENTER_MASK).bit_count() - (opp & NEAR_CENTER_MASK).bit_count())

    for mask in WIN_MASKS:
        cb = curr & mask
        ob = opp & mask
        if cb and ob:
            continue
        if cb:
            score += LINE_SCORES[cb.bit_count()]
        elif ob:
            score -= LINE_SCORES[ob.bit_count()]

    occupied = curr | opp
    my_wins = 0
    opp_wins = 0
    for c in ORDER:
        bit = _move_bit(occupied, c)
        if not bit:
            continue
        if _is_win(curr | bit):
            my_wins += 1
        if _is_win(opp | bit):
            opp_wins += 1

    score += 90 * my_wins
    score -= 110 * opp_wins

    return score


def _negamax(curr: int, opp: int, depth: int, alpha: int, beta: int,
             deadline: float, counter: list[int]) -> tuple[int, int | None]:
    counter[0] += 1
    if (counter[0] & CHECK_MASK) == 0 and time.perf_counter() >= deadline:
        raise _SearchTimeout

    occupied = curr | opp
    ply = occupied.bit_count()
    key = (curr, opp)

    if _is_win(opp):
        val = -(MATE - ply)
        TT[key] = (depth, 0, val, None)
        return val, None

    if occupied == FULL_MASK:
        TT[key] = (depth, 0, 0, None)
        return 0, None

    alpha_orig = alpha
    beta_orig = beta

    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        edepth, flag, val, best = entry
        tt_move = best
        if edepth >= depth:
            if flag == 0:
                return val, best
            elif flag > 0:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val, best

    legal = []
    opp_wins = []
    forced_bit = 0

    for c in ORDER:
        bit = _move_bit(occupied, c)
        if not bit:
            continue

        if _is_win(curr | bit):
            val = MATE - (ply + 1)
            TT[key] = (depth, 0, val, c)
            return val, c

        legal.append((c, bit))

        if _is_win(opp | bit):
            opp_wins.append(c)
            if len(opp_wins) == 1:
                forced_bit = bit

    if not legal:
        TT[key] = (depth, 0, 0, None)
        return 0, None

    if len(opp_wins) >= 2:
        val = -(MATE - (ply + 2))
        TT[key] = (depth, 0, val, opp_wins[0])
        return val, opp_wins[0]

    if depth == 0:
        val = _evaluate(curr, opp)
        TT[key] = (depth, 0, val, tt_move if tt_move is not None else legal[0][0])
        return val, tt_move

    if len(opp_wins) == 1:
        moves = [(opp_wins[0], forced_bit)]
    else:
        safe = []
        for c, bit in legal:
            if not _has_immediate_win(opp, curr | bit):
                safe.append((c, bit))
        moves = safe if safe else legal

    if tt_move is not None and len(moves) > 1:
        moves.sort(key=lambda mv: 0 if mv[0] == tt_move else 1)

    best_val = -INF
    best_move = moves[0][0]

    for c, bit in moves:
        child_val, _ = _negamax(opp, curr | bit, depth - 1, -beta, -alpha, deadline, counter)
        val = -child_val

        if val > best_val:
            best_val = val
            best_move = c

        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = -1
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    TT[key] = (depth, flag, best_val, best_move)
    return best_val, best_move


def policy(board: list[list[int]]) -> int:
    TT.clear()

    curr, opp = _board_to_bits(board)
    occupied = curr | opp

    # Robust fallback for already-terminal / malformed calls.
    if _is_win(curr) or _is_win(opp):
        return _first_legal(occupied)

    # Strong opening.
    if occupied == 0:
        return 3

    legal = []
    opp_wins = []

    for c in ORDER:
        bit = _move_bit(occupied, c)
        if not bit:
            continue
        legal.append((c, bit))

        # Win immediately if possible.
        if _is_win(curr | bit):
            return c

        # Track opponent immediate wins (must block if exactly one).
        if _is_win(opp | bit):
            opp_wins.append(c)

    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0][0]

    if len(opp_wins) == 1:
        return opp_wins[0]

    if len(opp_wins) >= 2:
        threat_set = set(opp_wins)
        for c in ORDER:
            if c in threat_set:
                return c
        return legal[0][0]

    safe = []
    for c, bit in legal:
        if not _has_immediate_win(opp, curr | bit):
            safe.append((c, bit))

    candidates = safe if safe else legal

    if len(candidates) == 1:
        return candidates[0][0]

    best_move = candidates[0][0]
    deadline = time.perf_counter() + TIME_BUDGET
    counter = [0]
    empties = 42 - occupied.bit_count()

    try:
        for depth in range(1, empties + 1):
            entry = TT.get((curr, opp))
            tt_move = entry[3] if entry is not None else None

            moves = candidates[:]
            if tt_move is not None and len(moves) > 1:
                moves.sort(key=lambda mv: 0 if mv[0] == tt_move else 1)

            alpha = -INF
            beta = INF
            iter_best_val = -INF
            iter_best_move = best_move

            for c, bit in moves:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                val, _ = _negamax(opp, curr | bit, depth - 1, -beta, -alpha, deadline, counter)
                val = -val

                if val > iter_best_val:
                    iter_best_val = val
                    iter_best_move = c

                if val > alpha:
                    alpha = val

            best_move = iter_best_move
            TT[(curr, opp)] = (depth, 0, iter_best_val, best_move)

            if abs(iter_best_val) >= MATE - 50:
                break

    except _SearchTimeout:
        pass

    if _move_bit(occupied, best_move):
        return best_move

    return _first_legal(occupied)
