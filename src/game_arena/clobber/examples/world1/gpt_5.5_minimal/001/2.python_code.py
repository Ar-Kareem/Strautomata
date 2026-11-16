
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [
    (-1, 0, "U"),
    (0, 1, "R"),
    (1, 0, "D"),
    (0, -1, "L"),
]

NEG_INF = -10**9
POS_INF = 10**9


def _get_cell(arr, r, c):
    """Supports nested lists, numpy arrays, or flat length-30 lists."""
    try:
        return arr[r][c]
    except Exception:
        return arr[r * COLS + c]


def _to_bits(arr):
    bits = 0
    for r in range(ROWS):
        for c in range(COLS):
            if _get_cell(arr, r, c):
                bits |= 1 << (r * COLS + c)
    return bits


def _generate_moves(me, opp):
    moves = []
    for i in range(N):
        if not ((me >> i) & 1):
            continue
        r, c = divmod(i, COLS)
        for dr, dc, dch in DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                if (opp >> j) & 1:
                    moves.append((i, j, dch))
    return moves


def _move_to_string(m):
    i, _, d = m
    r, c = divmod(i, COLS)
    return f"{r},{c},{d}"


def _mobility(me, opp):
    count = 0
    for i in range(N):
        if not ((me >> i) & 1):
            continue
        r, c = divmod(i, COLS)

        if r > 0 and ((opp >> (i - COLS)) & 1):
            count += 1
        if r + 1 < ROWS and ((opp >> (i + COLS)) & 1):
            count += 1
        if c > 0 and ((opp >> (i - 1)) & 1):
            count += 1
        if c + 1 < COLS and ((opp >> (i + 1)) & 1):
            count += 1
    return count


def _apply_move(me, opp, move):
    src, dst, _ = move

    src_mask = 1 << src
    dst_mask = 1 << dst

    new_me = (me & ~src_mask) | dst_mask
    new_opp = opp & ~dst_mask

    # Return from next player's perspective.
    return new_opp, new_me


def _static_eval(me, opp):
    my_moves = _mobility(me, opp)
    opp_moves = _mobility(opp, me)

    if my_moves == 0:
        return -100000
    if opp_moves == 0:
        return 100000

    material = me.bit_count() - opp.bit_count()

    # Mobility is the most important feature in Clobber.
    # Material is useful but less decisive because having no move loses.
    return 22 * (my_moves - opp_moves) + 5 * material


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    time_limit = 0.92

    me = _to_bits(you)
    opp = _to_bits(opponent)

    root_moves = _generate_moves(me, opp)

    # The arena should not ask for a move in terminal positions, but if it does,
    # return a syntactically valid placeholder. In normal play this branch is not used.
    if not root_moves:
        return "0,0,U"

    if len(root_moves) == 1:
        return _move_to_string(root_moves[0])

    best_move = root_moves[0]
    trans = {}

    class Timeout(Exception):
        pass

    def check_time():
        if time.perf_counter() - start_time > time_limit:
            raise Timeout()

    def ordered_moves(a, b):
        ms = _generate_moves(a, b)

        # Prefer moves that leave the opponent with fewer replies.
        scored = []
        for mv in ms:
            ca, cb = _apply_move(a, b, mv)
            replies = _mobility(ca, cb)
            scored.append((replies, mv))
        scored.sort(key=lambda x: x[0])
        return [mv for _, mv in scored]

    def search(a, b, depth, alpha, beta, ply):
        check_time()

        key = (a, b, depth)
        cached = trans.get(key)
        if cached is not None:
            return cached

        moves = _generate_moves(a, b)
        if not moves:
            return -1000000 + ply

        if depth <= 0:
            return _static_eval(a, b)

        best = NEG_INF

        # Order tactical moves for stronger pruning.
        scored_moves = []
        for mv in moves:
            ca, cb = _apply_move(a, b, mv)
            scored_moves.append((_mobility(ca, cb), mv))
        scored_moves.sort(key=lambda x: x[0])

        for _, mv in scored_moves:
            ca, cb = _apply_move(a, b, mv)
            val = -search(ca, cb, depth - 1, -beta, -alpha, ply + 1)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        trans[key] = best
        return best

    # Iterative deepening. Keep the best fully completed depth.
    try:
        depth = 1
        while depth <= 30:
            check_time()

            alpha = NEG_INF
            beta = POS_INF
            depth_best_score = NEG_INF
            depth_best_move = best_move

            moves = ordered_moves(me, opp)

            # Try the previous best first if present.
            if best_move in moves:
                moves.remove(best_move)
                moves.insert(0, best_move)

            for mv in moves:
                check_time()
                ca, cb = _apply_move(me, opp, mv)
                val = -search(ca, cb, depth - 1, -beta, -alpha, 1)

                if val > depth_best_score:
                    depth_best_score = val
                    depth_best_move = mv

                if val > alpha:
                    alpha = val

            best_move = depth_best_move

            # Found a forced win; no need to spend more time.
            if depth_best_score > 900000:
                break

            depth += 1

    except Timeout:
        pass
    except Exception:
        # Safety fallback: never fail to return a legal move.
        return _move_to_string(root_moves[0])

    return _move_to_string(best_move)
