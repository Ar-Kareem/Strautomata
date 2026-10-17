
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

NEIGHBORS = [[] for _ in range(N)]
ADJ_MASK = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, d in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGHBORS[i].append((j, d))
                ADJ_MASK[i] |= 1 << j

INF = 10 ** 9


class Timeout(Exception):
    pass


def _to_bits(board):
    bits = 0

    # Accept either nested 5x6 lists/arrays or flat length-30 lists/arrays.
    try:
        if len(board) == N and not hasattr(board[0], "__len__"):
            for i in range(N):
                if board[i]:
                    bits |= 1 << i
            return bits
    except Exception:
        pass

    for r in range(ROWS):
        row = board[r]
        for c in range(COLS):
            if row[c]:
                bits |= 1 << (r * COLS + c)
    return bits


def _bit_iter(x):
    while x:
        lsb = x & -x
        yield lsb.bit_length() - 1
        x ^= lsb


def _count_moves(you, opp):
    total = 0
    x = you
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        total += (ADJ_MASK[i] & opp).bit_count()
        x ^= lsb
    return total


def _has_move(you, opp):
    x = you
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        if ADJ_MASK[i] & opp:
            return True
        x ^= lsb
    return False


def _make_move(you, opp, frm, to):
    fb = 1 << frm
    tb = 1 << to

    new_you_after_move = (you ^ fb) | tb
    new_opp_after_move = opp ^ tb

    # Return board from the next player/opponent's perspective.
    return new_opp_after_move, new_you_after_move


def _move_string(frm, to, d):
    r = frm // COLS
    c = frm % COLS
    return f"{r},{c},{d}"


def _generate_moves(you, opp):
    moves = []
    x = you
    while x:
        lsb = x & -x
        frm = lsb.bit_length() - 1
        targets = ADJ_MASK[frm] & opp
        if targets:
            for to, d in NEIGHBORS[frm]:
                if targets & (1 << to):
                    moves.append((frm, to, d))
        x ^= lsb
    return moves


def _static_eval(you, opp):
    my_mob = _count_moves(you, opp)
    opp_mob = _count_moves(opp, you)

    if my_mob == 0:
        return -INF // 2
    if opp_mob == 0:
        return INF // 2

    my_pieces = you.bit_count()
    opp_pieces = opp.bit_count()

    active_me = 0
    x = you
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        if ADJ_MASK[i] & opp:
            active_me += 1
        x ^= lsb

    active_opp = 0
    x = opp
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        if ADJ_MASK[i] & you:
            active_opp += 1
        x ^= lsb

    # Mobility is the main signal.  Piece count and active-piece count are
    # secondary tie-breakers.
    return (
        120 * (my_mob - opp_mob)
        + 20 * (active_me - active_opp)
        + 6 * (my_pieces - opp_pieces)
    )


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    deadline = start_time + 0.92

    y = _to_bits(you)
    o = _to_bits(opponent)

    legal = _generate_moves(y, o)

    # A terminal position has no legal move.  In normal arena play this should
    # not be requested, because no legal move exists.  Return a harmless string
    # fallback anyway.
    if not legal:
        return "0,0,U"

    # Guaranteed legal fallback.
    best_move = legal[0]
    best_str = _move_string(*best_move)

    tt = {}

    def ordered_moves(a, b):
        ms = _generate_moves(a, b)

        def key(m):
            na, nb = _make_move(a, b, m[0], m[1])
            # After _make_move, na is next side to move.  Good moves leave that
            # side with few options and leave us with more future options.
            return (_count_moves(na, nb), -_count_moves(nb, na))

        ms.sort(key=key)
        return ms

    def search(a, b, depth, alpha, beta):
        if time.perf_counter() > deadline:
            raise Timeout()

        key = (a, b, depth, alpha, beta)
        hit = tt.get(key)
        if hit is not None:
            return hit

        ms = _generate_moves(a, b)
        if not ms:
            return -INF + depth

        if depth <= 0:
            return _static_eval(a, b)

        value = -INF
        for m in ordered_moves(a, b):
            na, nb = _make_move(a, b, m[0], m[1])
            score = -search(na, nb, depth - 1, -beta, -alpha)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        tt[key] = value
        return value

    # Iterative deepening.  Depths beyond this are usually unnecessary within
    # the time limit, but the loop can stop earlier on timeout.
    for depth in range(1, 30):
        try:
            current_best = best_move
            current_score = -INF

            root_moves = ordered_moves(y, o)
            for m in root_moves:
                if time.perf_counter() > deadline:
                    raise Timeout()

                ny, no = _make_move(y, o, m[0], m[1])
                score = -search(ny, no, depth - 1, -INF, INF)

                if score > current_score:
                    current_score = score
                    current_best = m

            best_move = current_best
            best_str = _move_string(*best_move)

            # Forced win found.
            if current_score > INF // 3:
                break

        except Timeout:
            break
        except Exception:
            # Never risk failing to return a legal move.
            break

    return best_str
