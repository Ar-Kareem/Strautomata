
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

# Direction order and deltas
DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

# Precompute neighboring cells and move direction strings.
NEIGH = [[] for _ in range(N)]
MOVE_STR = {}
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, d in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEIGH[i].append(j)
                MOVE_STR[(i, j)] = f"{r},{c},{d}"


class Timeout(Exception):
    pass


def _bit_at(board, r, c):
    """Accept either nested 5x6 lists or flat length-30 lists."""
    try:
        return board[r][c]
    except Exception:
        return board[r * COLS + c]


def _to_bits(board):
    b = 0
    for r in range(ROWS):
        for c in range(COLS):
            if _bit_at(board, r, c):
                b |= 1 << (r * COLS + c)
    return b


def _moves(a, b):
    """Legal moves for current player bitboard a capturing opponent bitboard b.

    Returns list of (from_index, to_index).
    """
    res = []
    x = a
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        for j in NEIGH[i]:
            if (b >> j) & 1:
                res.append((i, j))
        x ^= lsb
    return res


def _mobility(a, b):
    cnt = 0
    x = a
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        for j in NEIGH[i]:
            if (b >> j) & 1:
                cnt += 1
        x ^= lsb
    return cnt


def _popcount(x):
    return x.bit_count()


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    TIME_LIMIT = 0.92

    a0 = _to_bits(you)
    b0 = _to_bits(opponent)

    root_moves = _moves(a0, b0)

    # If the arena ever calls us in a lost/no-move state, no legal move exists.
    # Return a syntactically valid placeholder; normal valid states return below.
    if not root_moves:
        return "0,0,U"

    # Always keep a legal fallback.
    best_move = root_moves[0]
    previous_scores = {}

    INF = 10 ** 9
    WIN = 100000

    tt = {}

    def check_time():
        if time.perf_counter() - start_time > TIME_LIMIT:
            raise Timeout()

    def evaluate(a, b):
        """Static evaluation from side-to-move perspective."""
        ma = _mobility(a, b)
        mb = _mobility(b, a)

        # Mobility is the key factor in Clobber.
        score = 18 * (ma - mb)

        # Fewer opponent pieces can be good, but preserving useful pieces matters too.
        score += 2 * (_popcount(a) - _popcount(b))

        # Slight bonus for having pieces that touch multiple enemies.
        contact_a = 0
        contact_b = 0

        x = a
        while x:
            lsb = x & -x
            i = lsb.bit_length() - 1
            deg = 0
            for j in NEIGH[i]:
                if (b >> j) & 1:
                    deg += 1
            if deg:
                contact_a += min(deg, 2)
            x ^= lsb

        x = b
        while x:
            lsb = x & -x
            i = lsb.bit_length() - 1
            deg = 0
            for j in NEIGH[i]:
                if (a >> j) & 1:
                    deg += 1
            if deg:
                contact_b += min(deg, 2)
            x ^= lsb

        score += 4 * (contact_a - contact_b)
        return score

    def ordered_moves(a, b):
        ms = _moves(a, b)

        # Prefer moves that reduce opponent mobility and/or immediately leave
        # opponent with no reply.
        scored = []
        for f, t in ms:
            bit_f = 1 << f
            bit_t = 1 << t
            na = (a & ~bit_f) | bit_t
            nb = b & ~bit_t

            # After our move, opponent position is (nb, na).
            opp_mob = _mobility(nb, na)
            our_next_mob = _mobility(na, nb)
            s = -25 * opp_mob + 5 * our_next_mob

            # Capturing into central-ish squares is often more flexible.
            r, c = divmod(t, COLS)
            s -= abs(r - 2) + abs(c - 2.5)

            scored.append((s, f, t))

        scored.sort(reverse=True)
        return [(f, t) for _, f, t in scored]

    def negamax(a, b, depth, alpha, beta, ply):
        check_time()

        ms = _moves(a, b)
        if not ms:
            return -WIN + ply

        if depth == 0:
            return evaluate(a, b)

        key = (a, b, depth)
        if key in tt:
            return tt[key]

        orig_alpha = alpha
        best = -INF

        # Move ordering is crucial for alpha-beta.
        for f, t in ordered_moves(a, b):
            bit_f = 1 << f
            bit_t = 1 << t

            # Current player moves a piece f -> t, removing opponent piece at t.
            new_current_pieces = (a & ~bit_f) | bit_t
            new_opponent_pieces = b & ~bit_t

            # Swap perspective for opponent's turn.
            val = -negamax(new_opponent_pieces, new_current_pieces,
                           depth - 1, -beta, -alpha, ply + 1)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        # Store only exact values, not cutoffs.
        if alpha < beta or best <= orig_alpha:
            tt[key] = best
        elif best > orig_alpha and best < beta:
            tt[key] = best

        return best

    try:
        depth = 1

        # Iterative deepening. The maximum possible game length is bounded by
        # the number of captures, but time will usually stop us first.
        while depth <= 30:
            check_time()

            # Root ordering from previous completed iteration.
            root_moves.sort(key=lambda m: previous_scores.get(m, 0), reverse=True)

            current_best = best_move
            current_best_score = -INF
            current_scores = {}

            alpha = -INF
            beta = INF

            for f, t in root_moves:
                check_time()

                bit_f = 1 << f
                bit_t = 1 << t

                new_you = (a0 & ~bit_f) | bit_t
                new_opp = b0 & ~bit_t

                score = -negamax(new_opp, new_you, depth - 1,
                                 -beta, -alpha, 1)

                current_scores[(f, t)] = score

                if score > current_best_score:
                    current_best_score = score
                    current_best = (f, t)

                if score > alpha:
                    alpha = score

            # Completed this depth, so commit the result.
            best_move = current_best
            previous_scores = current_scores

            # If we found a forced win, no need to search further.
            if current_best_score >= WIN - 30:
                break

            depth += 1

    except Timeout:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        pass

    return MOVE_STR[best_move]
