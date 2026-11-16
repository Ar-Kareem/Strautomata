
import time
from functools import lru_cache

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precomputed adjacency and move metadata
NEIGH = [[] for _ in range(N)]          # list of (dst, dir_char)
ADJ_MASK = [0] * N                      # bitmask of orthogonal neighbors

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGH[i].append((j, ch))
                mask |= 1 << j
        ADJ_MASK[i] = mask

CENTER_BONUS = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        # Mild preference for central squares
        CENTER_BONUS[r * COLS + c] = 4 - abs(r - 2) - abs(c - 2.5)

WIN_SCORE = 1000000
TIME_LIMIT = 0.92


def _iter_bits(x: int):
    while x:
        lsb = x & -x
        yield lsb.bit_length() - 1
        x ^= lsb


def _to_bits(arr):
    bits = 0
    # Accepts list[int], nested lists, or numpy-like arrays
    for r in range(ROWS):
        row = arr[r]
        for c in range(COLS):
            if row[c]:
                bits |= 1 << (r * COLS + c)
    return bits


def _move_to_str(src: int, ch: str) -> str:
    return f"{src // COLS},{src % COLS},{ch}"


def _generate_moves(my_bits: int, opp_bits: int):
    moves = []
    x = my_bits
    while x:
        lsb = x & -x
        src = lsb.bit_length() - 1
        x ^= lsb
        opp_adj = ADJ_MASK[src] & opp_bits
        y = opp_adj
        while y:
            dlsb = y & -y
            dst = dlsb.bit_length() - 1
            y ^= dlsb
            # find direction char
            for j, ch in NEIGH[src]:
                if j == dst:
                    moves.append((src, dst, ch))
                    break
    return moves


def _apply_move(my_bits: int, opp_bits: int, src: int, dst: int):
    srcb = 1 << src
    dstb = 1 << dst
    # Current player moves src onto dst, capturing opponent at dst.
    my_after = (my_bits ^ srcb) | dstb
    opp_after = opp_bits ^ dstb
    # Roles swap for the next player to move.
    return opp_after, my_after


@lru_cache(maxsize=200000)
def _mobility(my_bits: int, opp_bits: int) -> int:
    cnt = 0
    x = my_bits
    while x:
        lsb = x & -x
        src = lsb.bit_length() - 1
        x ^= lsb
        cnt += (ADJ_MASK[src] & opp_bits).bit_count()
    return cnt


def _heuristic(my_bits: int, opp_bits: int) -> int:
    my_moves = _mobility(my_bits, opp_bits)
    if my_moves == 0:
        return -WIN_SCORE // 2

    opp_moves = _mobility(opp_bits, my_bits)

    my_count = my_bits.bit_count()
    opp_count = opp_bits.bit_count()

    # Piece activity: pieces adjacent to enemies are tactically useful
    my_active = 0
    x = my_bits
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        if ADJ_MASK[i] & opp_bits:
            my_active += 1

    opp_active = 0
    x = opp_bits
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        if ADJ_MASK[i] & my_bits:
            opp_active += 1

    # Mild centrality
    my_center = 0
    x = my_bits
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        my_center += CENTER_BONUS[i]

    opp_center = 0
    x = opp_bits
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        x ^= lsb
        opp_center += CENTER_BONUS[i]

    return (
        20 * (my_moves - opp_moves)
        + 7 * (my_active - opp_active)
        + 2 * (my_count - opp_count)
        + int(my_center - opp_center)
    )


def _ordered_moves(my_bits: int, opp_bits: int, tt_best=None):
    moves = _generate_moves(my_bits, opp_bits)
    if not moves:
        return moves

    scored = []
    for mv in moves:
        src, dst, ch = mv
        nmy, nopp = _apply_move(my_bits, opp_bits, src, dst)

        # Lower next player's mobility is good for us.
        next_mob = _mobility(nmy, nopp)

        # Tactical shape score around destination.
        local_pressure = (ADJ_MASK[dst] & nopp).bit_count() - (ADJ_MASK[dst] & nmy).bit_count()

        score = -12 * next_mob + 5 * local_pressure + 2 * CENTER_BONUS[dst]

        if tt_best is not None and mv == tt_best:
            score += 10000

        scored.append((score, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def policy(you, opponent) -> str:
    start = time.perf_counter()

    my_bits = _to_bits(you)
    opp_bits = _to_bits(opponent)

    legal = _generate_moves(my_bits, opp_bits)
    if not legal:
        # Terminal position; no legal move exists.
        # Return a syntactically valid placeholder, though arena should not call policy here.
        return "0,0,U"

    # Safe fallback
    best_move = legal[0]

    # TT entry: (depth, score, flag, best_move)
    # flag: 0 exact, -1 upperbound, 1 lowerbound
    tt = {}

    def negamax(cur_my, cur_opp, depth, alpha, beta):
        nonlocal start

        if time.perf_counter() - start > TIME_LIMIT:
            raise TimeoutError

        key = (cur_my, cur_opp)
        alpha0 = alpha

        entry = tt.get(key)
        if entry is not None:
            edepth, escore, eflag, emove = entry
            if edepth >= depth:
                if eflag == 0:
                    return escore
                elif eflag == 1:
                    alpha = max(alpha, escore)
                else:
                    beta = min(beta, escore)
                if alpha >= beta:
                    return escore
            tt_move = emove
        else:
            tt_move = None

        moves = _generate_moves(cur_my, cur_opp)
        if not moves:
            return -WIN_SCORE + (30 - (cur_my.bit_count() + cur_opp.bit_count()))

        if depth == 0:
            return _heuristic(cur_my, cur_opp)

        best_score = -10**18
        best_local = moves[0]

        for src, dst, ch in _ordered_moves(cur_my, cur_opp, tt_move):
            nmy, nopp = _apply_move(cur_my, cur_opp, src, dst)
            score = -negamax(nmy, nopp, depth - 1, -beta, -alpha)
            if score > best_score:
                best_score = score
                best_local = (src, dst, ch)
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        if best_score <= alpha0:
            flag = -1
        elif best_score >= beta:
            flag = 1
        else:
            flag = 0
        tt[key] = (depth, best_score, flag, best_local)
        return best_score

    # Iterative deepening
    max_depth = min(24, opp_bits.bit_count() + my_bits.bit_count())  # game cannot exceed remaining captures
    try:
        for depth in range(1, max_depth + 1):
            root_moves = _ordered_moves(my_bits, opp_bits, tt.get((my_bits, opp_bits), (None, None, None, None))[3] if (my_bits, opp_bits) in tt else None)
            local_best = root_moves[0]
            local_best_score = -10**18
            alpha = -10**18
            beta = 10**18

            for src, dst, ch in root_moves:
                if time.perf_counter() - start > TIME_LIMIT:
                    raise TimeoutError
                nmy, nopp = _apply_move(my_bits, opp_bits, src, dst)
                score = -negamax(nmy, nopp, depth - 1, -beta, -alpha)
                if score > local_best_score:
                    local_best_score = score
                    local_best = (src, dst, ch)
                if score > alpha:
                    alpha = score

            best_move = local_best
            tt[(my_bits, opp_bits)] = (depth, local_best_score, 0, local_best)

            # Early stop on proven win/loss
            if abs(local_best_score) >= WIN_SCORE // 2:
                break

    except TimeoutError:
        pass

    return _move_to_str(best_move[0], best_move[2])
