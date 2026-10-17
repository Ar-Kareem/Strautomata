
import time

INF = 10 ** 9
WIN = 10 ** 7

MAN_DIRS = {
    "b": ((-1, -1), (-1, 1)),  # black moves toward lower row numbers
    "w": ((1, -1), (1, 1)),    # white moves toward higher row numbers
}
KING_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))

DEADLINE = 0.0
NODES = 0
TT = {}


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return a legal checkers move: ((from_row, from_col), (to_row, to_col)).
    Captures are generated as mandatory.
    """
    global DEADLINE, NODES, TT

    start = time.time()
    DEADLINE = start + 0.92
    NODES = 0
    TT = {}

    my_men = frozenset(tuple(p) for p in my_men)
    my_kings = frozenset(tuple(p) for p in my_kings)
    opp_men = frozenset(tuple(p) for p in opp_men)
    opp_kings = frozenset(tuple(p) for p in opp_kings)

    if color == "b":
        state = (my_men, my_kings, opp_men, opp_kings, "b")
    else:
        state = (opp_men, opp_kings, my_men, my_kings, "w")

    legal = generate_moves(state)
    if not legal:
        # This should only happen if the game is already over.
        # Return a harmless fallback using one of our pieces if possible.
        pieces = list(my_men or my_kings)
        if pieces:
            p = pieces[0]
            return (p, p)
        return ((0, 0), (0, 0))

    if len(legal) == 1:
        return legal[0]

    legal = order_moves(state, legal)
    best_move = legal[0]

    # Iterative deepening: always keep the best fully completed depth.
    max_depth = 14
    depth = 1

    try:
        while depth <= max_depth:
            alpha = -INF
            beta = INF
            depth_best = best_move
            depth_best_score = -INF

            root_moves = order_moves(state, legal)
            for mv in root_moves:
                if time.time() > DEADLINE:
                    raise TimeoutError

                child = apply_move(state, mv)
                score = -alphabeta(child, depth - 1, -beta, -alpha, 4)

                if score > depth_best_score:
                    depth_best_score = score
                    depth_best = mv

                if score > alpha:
                    alpha = score

            best_move = depth_best
            depth += 1

    except TimeoutError:
        pass

    return best_move


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def generate_moves(state):
    bm, bk, wm, wk, side = state
    return generate_moves_for(bm, bk, wm, wk, side)


def generate_moves_for(bm, bk, wm, wk, side):
    if side == "b":
        own_men, own_kings = bm, bk
        opp_men, opp_kings = wm, wk
    else:
        own_men, own_kings = wm, wk
        opp_men, opp_kings = bm, bk

    occupied = bm | bk | wm | wk
    opp_all = opp_men | opp_kings

    captures = []

    # Men: American checkers style, move/capture forward only.
    for r, c in own_men:
        for dr, dc in MAN_DIRS[side]:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    # Kings: move/capture all diagonal directions.
    for r, c in own_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    if captures:
        return captures

    quiets = []

    for r, c in own_men:
        for dr, dc in MAN_DIRS[side]:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                quiets.append(((r, c), (tr, tc)))

    for r, c in own_kings:
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                quiets.append(((r, c), (tr, tc)))

    return quiets


def apply_move(state, move):
    bm, bk, wm, wk, side = state
    frm, to = move
    fr, fc = frm
    tr, tc = to

    bm = set(bm)
    bk = set(bk)
    wm = set(wm)
    wk = set(wk)

    if side == "b":
        moving_king = frm in bk

        if moving_king:
            bk.remove(frm)
        else:
            bm.remove(frm)

        if abs(tr - fr) == 2:
            mid = ((fr + tr) // 2, (fc + tc) // 2)
            wm.discard(mid)
            wk.discard(mid)

        if moving_king or tr == 0:
            bk.add(to)
        else:
            bm.add(to)

        return (frozenset(bm), frozenset(bk), frozenset(wm), frozenset(wk), "w")

    else:
        moving_king = frm in wk

        if moving_king:
            wk.remove(frm)
        else:
            wm.remove(frm)

        if abs(tr - fr) == 2:
            mid = ((fr + tr) // 2, (fc + tc) // 2)
            bm.discard(mid)
            bk.discard(mid)

        if moving_king or tr == 7:
            wk.add(to)
        else:
            wm.add(to)

        return (frozenset(bm), frozenset(bk), frozenset(wm), frozenset(wk), "b")


def alphabeta(state, depth, alpha, beta, qdepth):
    global NODES, TT

    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise TimeoutError

    bm, bk, wm, wk, side = state
    key = (bm, bk, wm, wk, side, depth, qdepth)

    old_alpha = alpha
    old_beta = beta

    cached = TT.get(key)
    if cached is not None:
        cached_depth, flag, value = cached
        if cached_depth >= depth:
            if flag == 0:
                return value
            elif flag == 1:
                alpha = max(alpha, value)
            elif flag == 2:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    moves = generate_moves(state)

    if not moves:
        return -WIN - depth

    has_capture = abs(moves[0][1][0] - moves[0][0][0]) == 2

    # Quiescence: if depth is exhausted but a capture is forced, search a few
    # more plies to avoid obvious tactical blunders.
    if depth <= 0 and (not has_capture or qdepth <= 0):
        return evaluate(state)

    moves = order_moves(state, moves)

    best = -INF

    next_depth = depth - 1 if depth > 0 else 0
    next_qdepth = qdepth if depth > 0 else qdepth - 1

    for mv in moves:
        child = apply_move(state, mv)
        score = -alphabeta(child, next_depth, -beta, -alpha, next_qdepth)

        if score > best:
            best = score

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best <= old_alpha:
        flag = 2  # upper bound
    elif best >= old_beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    TT[key] = (depth, flag, best)
    return best


def evaluate(state):
    bm, bk, wm, wk, side = state

    black = 0
    white = 0

    # Material.
    black += 100 * len(bm) + 178 * len(bk)
    white += 100 * len(wm) + 178 * len(wk)

    # Positional value for black men.
    for r, c in bm:
        black += 4 * (7 - r)  # advancement toward row 0
        if r == 7:
            black += 6          # back-row guard
        if r == 1:
            black += 12         # near promotion
        if 2 <= r <= 5 and 2 <= c <= 5:
            black += 5
        if c == 0 or c == 7:
            black += 3          # edge is harder to capture

    # Positional value for white men.
    for r, c in wm:
        white += 4 * r          # advancement toward row 7
        if r == 0:
            white += 6
        if r == 6:
            white += 12
        if 2 <= r <= 5 and 2 <= c <= 5:
            white += 5
        if c == 0 or c == 7:
            white += 3

    # Kings like mobility and central squares.
    for r, c in bk:
        if 2 <= r <= 5 and 2 <= c <= 5:
            black += 8
        if c == 0 or c == 7:
            black += 2

    for r, c in wk:
        if 2 <= r <= 5 and 2 <= c <= 5:
            white += 8
        if c == 0 or c == 7:
            white += 2

    # Mobility and immediate tactical pressure.
    b_moves = generate_moves_for(bm, bk, wm, wk, "b")
    w_moves = generate_moves_for(bm, bk, wm, wk, "w")

    black += 2 * len(b_moves)
    white += 2 * len(w_moves)

    b_caps = count_captures_for(bm, bk, wm, wk, "b")
    w_caps = count_captures_for(bm, bk, wm, wk, "w")

    black += 18 * b_caps
    white += 18 * w_caps

    score = black - white

    return score if side == "b" else -score


def count_captures_for(bm, bk, wm, wk, side):
    if side == "b":
        own_men, own_kings = bm, bk
        opp_all = wm | wk
    else:
        own_men, own_kings = wm, wk
        opp_all = bm | bk

    occupied = bm | bk | wm | wk
    total = 0

    for r, c in own_men:
        for dr, dc in MAN_DIRS[side]:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                total += 1

    for r, c in own_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                total += 1

    return total


def order_moves(state, moves):
    bm, bk, wm, wk, side = state

    if side == "b":
        own_kings = bk
        opp_kings = wk
        promotion_row = 0
    else:
        own_kings = wk
        opp_kings = bk
        promotion_row = 7

    def score_move(mv):
        frm, to = mv
        fr, fc = frm
        tr, tc = to
        s = 0

        is_capture = abs(tr - fr) == 2
        is_king = frm in own_kings

        if is_capture:
            s += 10000
            mid = ((fr + tr) // 2, (fc + tc) // 2)
            if mid in opp_kings:
                s += 900
            else:
                s += 450

        if not is_king and tr == promotion_row:
            s += 1200

        if is_king:
            s += 80

        # Prefer central destinations, but edges are mildly safe.
        if 2 <= tr <= 5 and 2 <= tc <= 5:
            s += 35
        if tc == 0 or tc == 7:
            s += 12

        # Small deterministic tie-breaker.
        s += tr * 2 + tc

        return s

    return sorted(moves, key=score_move, reverse=True)
