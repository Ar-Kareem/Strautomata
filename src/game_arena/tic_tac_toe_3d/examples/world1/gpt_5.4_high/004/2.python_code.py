
import time


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coord(m):
    return (m // 9, (m % 9) // 3, m % 3)


def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append((_idx(0, j, k), _idx(1, j, k), _idx(2, j, k)))
    for i in range(3):
        for k in range(3):
            lines.append((_idx(i, 0, k), _idx(i, 1, k), _idx(i, 2, k)))
    for i in range(3):
        for j in range(3):
            lines.append((_idx(i, j, 0), _idx(i, j, 1), _idx(i, j, 2)))

    # Face diagonals
    for i in range(3):
        lines.append((_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)))
        lines.append((_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)))
    for j in range(3):
        lines.append((_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)))
        lines.append((_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)))
    for k in range(3):
        lines.append((_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)))
        lines.append((_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)))

    # Space diagonals
    lines.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
    lines.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
    lines.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
    lines.append((_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)))

    return lines


LINES = _generate_lines()
WIN_MASKS = [sum(1 << p for p in line) for line in LINES]

CELL_MASKS = [[] for _ in range(27)]
for mask in WIN_MASKS:
    t = mask
    while t:
        b = t & -t
        CELL_MASKS[b.bit_length() - 1].append(mask)
        t ^= b

POSITIONAL = [len(CELL_MASKS[i]) for i in range(27)]
FULL_MASK = (1 << 27) - 1
CENTER = _idx(1, 1, 1)
CORNERS = [_idx(i, j, k) for i in (0, 2) for j in (0, 2) for k in (0, 2)]

WIN_BASE = 1_000_000
INF = 10_000_000


def _winning_moves_mask(bits_self, bits_opp, empties_mask):
    wins = 0
    for mask in WIN_MASKS:
        if mask & bits_opp:
            continue
        if (mask & bits_self).bit_count() == 2:
            wins |= mask & empties_mask
    return wins


def _move_wins(bits_self, move_idx):
    for mask in CELL_MASKS[move_idx]:
        if (bits_self & mask) == mask:
            return True
    return False


def _evaluate(cur_bits, opp_bits):
    score = 0
    my_twos = 0
    opp_twos = 0

    for mask in WIN_MASKS:
        a = (mask & cur_bits).bit_count()
        b = (mask & opp_bits).bit_count()

        if a and b:
            continue

        if b == 0:
            if a == 1:
                score += 6
            elif a == 2:
                score += 120
                my_twos += 1
        elif a == 0:
            if b == 1:
                score -= 6
            elif b == 2:
                score -= 120
                opp_twos += 1

    if my_twos > 1:
        score += 35 * my_twos * (my_twos - 1)
    if opp_twos > 1:
        score -= 35 * opp_twos * (opp_twos - 1)

    return score


def _ordered_moves(cur_bits, opp_bits, empties_mask, pv_move=-1):
    opp_wins = _winning_moves_mask(opp_bits, cur_bits, empties_mask)
    scored = []

    t = empties_mask
    while t:
        bit = t & -t
        m = bit.bit_length() - 1
        t ^= bit

        score = POSITIONAL[m] * 100
        if m == pv_move:
            score += 200000
        if opp_wins & bit:
            score += 150000

        new_cur = cur_bits | bit
        threat_count = 0

        for mask in CELL_MASKS[m]:
            if (mask & opp_bits) == 0:
                c = (mask & cur_bits).bit_count()
                if c == 1:
                    score += 250
                elif c == 0:
                    score += 25
                if (mask & new_cur).bit_count() == 2:
                    threat_count += 1

            if (mask & cur_bits) == 0:
                c = (mask & opp_bits).bit_count()
                if c == 2:
                    score += 50000
                elif c == 1:
                    score += 60

        if threat_count >= 2:
            score += 120000 + 10000 * threat_count
        elif threat_count == 1:
            score += 5000

        scored.append((score, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _best_from_mask(mask):
    best = -1
    best_score = -1
    t = mask
    while t:
        bit = t & -t
        m = bit.bit_length() - 1
        t ^= bit
        s = POSITIONAL[m]
        if s > best_score:
            best_score = s
            best = m
    return best


def policy(board):
    my_bits = 0
    opp_bits = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                m = _idx(i, j, k)
                if v == 1:
                    my_bits |= 1 << m
                elif v == -1:
                    opp_bits |= 1 << m

    occupied = my_bits | opp_bits
    empties_mask = FULL_MASK ^ occupied

    if empties_mask == 0:
        return (0, 0, 0)

    def first_empty():
        bit = empties_mask & -empties_mask
        return bit.bit_length() - 1

    occ_count = occupied.bit_count()

    # Opening preferences
    if occ_count == 0:
        return _coord(CENTER)
    if occ_count == 1:
        if empties_mask & (1 << CENTER):
            return _coord(CENTER)
        for m in CORNERS:
            if empties_mask & (1 << m):
                return _coord(m)

    # Exact root tactics
    my_wins = _winning_moves_mask(my_bits, opp_bits, empties_mask)
    if my_wins:
        return _coord(_best_from_mask(my_wins))

    opp_wins = _winning_moves_mask(opp_bits, my_bits, empties_mask)
    if opp_wins.bit_count() == 1:
        return _coord((opp_wins & -opp_wins).bit_length() - 1)

    if occ_count <= 2 and (empties_mask & (1 << CENTER)):
        return _coord(CENTER)

    # Direct fork detection
    for m in _ordered_moves(my_bits, opp_bits, empties_mask):
        bit = 1 << m
        new_my = my_bits | bit
        new_empty = empties_mask ^ bit
        if _winning_moves_mask(opp_bits, new_my, new_empty):
            continue
        if _winning_moves_mask(new_my, opp_bits, new_empty).bit_count() >= 2:
            return _coord(m)

    ordered_root = _ordered_moves(my_bits, opp_bits, empties_mask)
    best_move = ordered_root[0] if ordered_root else first_empty()

    n_empty = empties_mask.bit_count()
    if n_empty >= 20:
        max_depth = 4
    elif n_empty >= 15:
        max_depth = 5
    elif n_empty >= 11:
        max_depth = 6
    elif n_empty >= 8:
        max_depth = 8
    else:
        max_depth = n_empty

    start = time.perf_counter()
    time_limit = 0.88
    node_counter = 0

    class _Timeout(Exception):
        pass

    score_tt = {}
    move_tt = {}

    def check_time():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 1023) == 0 and (time.perf_counter() - start > time_limit):
            raise _Timeout

    def negamax(cur_bits, other_bits, empty_mask, depth, alpha, beta, last_move):
        check_time()

        if last_move != -1 and _move_wins(other_bits, last_move):
            return -(WIN_BASE + depth)

        if empty_mask == 0:
            return 0

        cur_wins = _winning_moves_mask(cur_bits, other_bits, empty_mask)
        if cur_wins:
            return WIN_BASE + depth

        other_wins = _winning_moves_mask(other_bits, cur_bits, empty_mask)
        other_win_count = other_wins.bit_count()

        if other_win_count >= 2:
            return -(WIN_BASE + depth)

        if depth == 0:
            if other_win_count == 1:
                block_move = (other_wins & -other_wins).bit_length() - 1
                bit = 1 << block_move
                return -_evaluate(other_bits, cur_bits | bit)
            return _evaluate(cur_bits, other_bits)

        key = (cur_bits, other_bits, empty_mask, depth)
        cached = score_tt.get(key)
        if cached is not None:
            return cached

        if other_win_count == 1:
            moves = [(other_wins & -other_wins).bit_length() - 1]
        else:
            pv_move = move_tt.get((cur_bits, other_bits, empty_mask), -1)
            moves = _ordered_moves(cur_bits, other_bits, empty_mask, pv_move)

        best = -INF
        best_local_move = moves[0] if moves else -1
        full_search = True

        for m in moves:
            bit = 1 << m
            score = -negamax(other_bits, cur_bits | bit, empty_mask ^ bit, depth - 1, -beta, -alpha, m)

            if score > best:
                best = score
                best_local_move = m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                full_search = False
                break

        move_tt[(cur_bits, other_bits, empty_mask)] = best_local_move
        if full_search:
            score_tt[key] = best
        return best

    try:
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            current_best = best_move
            current_score = -INF

            root_opp_wins = _winning_moves_mask(opp_bits, my_bits, empties_mask)
            if root_opp_wins.bit_count() == 1:
                only = (root_opp_wins & -root_opp_wins).bit_length() - 1
                return _coord(only)

            root_moves = _ordered_moves(my_bits, opp_bits, empties_mask, current_best)

            for m in root_moves:
                bit = 1 << m
                score = -negamax(opp_bits, my_bits | bit, empties_mask ^ bit, depth - 1, -beta, -alpha, m)

                if score > current_score:
                    current_score = score
                    current_best = m
                if current_score > alpha:
                    alpha = current_score

            best_move = current_best

            if abs(current_score) >= WIN_BASE:
                break

    except _Timeout:
        pass

    if not (empties_mask & (1 << best_move)):
        best_move = first_empty()

    return _coord(best_move)
