
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

# Bitboard precomputation.
NEI = [0] * N
DIR_MOVES = [[] for _ in range(N)]
CENTER_SCORE = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        CENTER_SCORE[i] = 20 - (abs(r - 2) * 3 + abs(2 * c - 5))
        for dr, dc, dch in ((-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")):
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEI[i] |= 1 << j
                DIR_MOVES[i].append((j, dch))

WIN = 1_000_000
EVAL_WIN = 100_000
INF = 10_000_000

# Persistent table can help across consecutive calls in the same game.
_TT = {}


class _Timeout(Exception):
    pass


def _bits_from_board(board):
    bits = 0
    try:
        for r in range(ROWS):
            row = board[r]
            for c in range(COLS):
                if row[c]:
                    bits |= 1 << (r * COLS + c)
        return bits
    except Exception:
        flat = list(board)
        for i, v in enumerate(flat[:N]):
            if v:
                bits |= 1 << i
        return bits


def _move_to_string(mv):
    src, dst, dch = mv
    r = src // COLS
    c = src % COLS
    return f"{r},{c},{dch}"


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    deadline = start_time + 0.93

    my0 = _bits_from_board(you)
    opp0 = _bits_from_board(opponent)

    trim_cache = {}
    node_counter = 0

    if len(_TT) > 300000:
        _TT.clear()

    def check_time():
        if time.perf_counter() > deadline:
            raise _Timeout()

    def gen_moves(my, opp):
        res = []
        m = my
        while m:
            b = m & -m
            src = b.bit_length() - 1
            t = NEI[src] & opp
            while t:
                db = t & -t
                dst = db.bit_length() - 1
                # Find direction.
                for j, dch in DIR_MOVES[src]:
                    if j == dst:
                        res.append((src, dst, dch))
                        break
                t ^= db
            m ^= b
        return res

    def legal_count(my, opp):
        cnt = 0
        m = my
        while m:
            b = m & -m
            i = b.bit_length() - 1
            cnt += (NEI[i] & opp).bit_count()
            m ^= b
        return cnt

    def trim(my, opp):
        key = (my, opp)
        got = trim_cache.get(key)
        if got is not None:
            return got

        occ = my | opp
        rem = occ
        keep = 0

        while rem:
            start = rem & -rem
            comp = 0
            frontier = start

            while frontier:
                b = frontier & -frontier
                frontier ^= b
                if comp & b:
                    continue
                comp |= b
                rem &= ~b
                i = b.bit_length() - 1
                frontier |= NEI[i] & occ & ~comp

            # A component containing only one color can never again affect play.
            if (comp & my) and (comp & opp):
                keep |= comp

        ans = (my & keep, opp & keep)
        trim_cache[key] = ans
        return ans

    def apply_move(my, opp, mv):
        src, dst, _ = mv
        sb = 1 << src
        db = 1 << dst

        # Next call is from the opponent's perspective.
        nmy = opp & ~db
        nopp = (my & ~sb) | db
        return trim(nmy, nopp)

    def order_score(my, opp, mv):
        nmy, nopp = apply_move(my, opp, mv)
        lc = legal_count(nmy, nopp)
        if lc == 0:
            return 1_000_000 + CENTER_SCORE[mv[1]]

        # Prefer moves that leave the opponent cramped.
        score = -120 * lc + CENTER_SCORE[mv[1]]

        # Slightly prefer captures from high-contact pieces; they often break components.
        src, dst, _ = mv
        score += 4 * ((NEI[src] & opp).bit_count())
        score -= 2 * ((NEI[dst] & (my | opp)).bit_count())

        return score

    def ordered_moves(my, opp, tt_best=None):
        mvs = gen_moves(my, opp)
        if not mvs:
            return mvs

        scored = []
        for mv in mvs:
            s = order_score(my, opp, mv)
            if tt_best is not None and mv == tt_best:
                s += 2_000_000
            scored.append((s, mv))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [mv for _, mv in scored]

    def evaluate(my, opp):
        mvs = gen_moves(my, opp)
        if not mvs:
            return -WIN - (my | opp).bit_count()

        active_n = (my | opp).bit_count()
        best = -EVAL_WIN

        for mv in mvs:
            nmy, nopp = apply_move(my, opp, mv)
            opp_replies = legal_count(nmy, nopp)

            if opp_replies == 0:
                val = EVAL_WIN + active_n
            else:
                val = -100 * opp_replies + CENTER_SCORE[mv[1]]

                # If the opponent has only a few replies, look one tactical ply deeper.
                if opp_replies <= 8:
                    omvs = gen_moves(nmy, nopp)
                    worst_after = INF
                    opp_can_win_now = False

                    for omv in omvs:
                        gmy, gopp = apply_move(nmy, nopp, omv)
                        our_replies = legal_count(gmy, gopp)
                        if our_replies == 0:
                            opp_can_win_now = True
                            break
                        if our_replies < worst_after:
                            worst_after = our_replies

                    if opp_can_win_now:
                        val -= EVAL_WIN // 2
                    elif worst_after != INF:
                        val += 28 * worst_after

            if val > best:
                best = val

        # Tiny material term; main value is tactical mobility.
        best += 2 * (my.bit_count() - opp.bit_count())
        return best

    def negamax(my, opp, depth, alpha, beta):
        nonlocal node_counter

        node_counter += 1
        if (node_counter & 2047) == 0:
            check_time()

        my, opp = trim(my, opp)
        key = (my, opp, depth)

        entry = _TT.get(key)
        if entry is not None:
            val, flag, best_mv = entry
            if flag == 0:
                return val
            if flag == 1:
                alpha = max(alpha, val)
            elif flag == 2:
                beta = min(beta, val)
            if alpha >= beta:
                return val
        else:
            best_mv = None

        mvs0 = gen_moves(my, opp)
        if not mvs0:
            return -WIN - (my | opp).bit_count()

        if depth <= 0:
            return evaluate(my, opp)

        orig_alpha = alpha
        best_val = -INF
        best_move_here = None

        # Use the transposition-table best move if available.
        mvs = ordered_moves(my, opp, best_mv)

        for mv in mvs:
            nmy, nopp = apply_move(my, opp, mv)
            val = -negamax(nmy, nopp, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_move_here = mv

            if val > alpha:
                alpha = val

            if alpha >= beta:
                break

        if best_val <= orig_alpha:
            flag = 2  # upper bound
        elif best_val >= beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact

        _TT[key] = (best_val, flag, best_move_here)
        return best_val

    root_my, root_opp = trim(my0, opp0)
    root_moves = gen_moves(root_my, root_opp)

    # If the game runner ever calls us in a lost position, no legal move exists.
    # In normal play this should not happen.
    if not root_moves:
        return "0,0,U"

    # Immediate legal fallback.
    root_moves.sort(key=lambda mv: order_score(root_my, root_opp, mv), reverse=True)
    best_move = root_moves[0]

    # Take an immediate win without spending time.
    for mv in root_moves:
        nmy, nopp = apply_move(root_my, root_opp, mv)
        if legal_count(nmy, nopp) == 0:
            return _move_to_string(mv)

    active_count = (root_my | root_opp).bit_count()
    max_depth = min(active_count + 1, 30)

    try:
        previous_best = best_move

        for depth in range(1, max_depth + 1):
            check_time()

            alpha = -INF
            beta = INF
            depth_best = previous_best
            depth_score = -INF

            # Search previous best first, then the tactical ordering.
            ordered = [previous_best] + [mv for mv in root_moves if mv != previous_best]

            for mv in ordered:
                check_time()
                nmy, nopp = apply_move(root_my, root_opp, mv)
                val = -negamax(nmy, nopp, depth - 1, -beta, -alpha)

                if val > depth_score:
                    depth_score = val
                    depth_best = mv

                if val > alpha:
                    alpha = val

            best_move = depth_best
            previous_best = depth_best

            # Proven forced win inside the completed search horizon.
            if depth_score >= WIN // 2:
                break

    except _Timeout:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move if one exists.
        pass

    return _move_to_string(best_move)
