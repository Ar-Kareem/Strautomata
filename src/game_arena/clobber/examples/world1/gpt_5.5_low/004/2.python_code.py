
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

INF = 10**9
WIN = 10**7

# Precompute board geometry.
NEIGHBORS = [[] for _ in range(N)]
MOVE_DIR = {}
CENTER_SCORE = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        # Mild preference for central squares.
        CENTER_SCORE[i] = 10 - (abs(r - 2) + abs(c - 2.5))
        for dr, dc, d in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGHBORS[i].append(j)
                MOVE_DIR[(i, j)] = d


class TimeoutSearch(Exception):
    pass


def _to_mask(board):
    """Accept nested lists, numpy arrays, or flat lists."""
    mask = 0
    try:
        # Nested / numpy-like 2D indexing.
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c]:
                    mask |= 1 << (r * COLS + c)
        return mask
    except Exception:
        pass

    # Flat fallback.
    for i, v in enumerate(board):
        if i >= N:
            break
        if v:
            mask |= 1 << i
    return mask


def _bitcount(x):
    return x.bit_count()


def _generate_moves(you, opp):
    moves = []
    y = you
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        for j in NEIGHBORS[i]:
            if opp & (1 << j):
                moves.append((i, j))
        y ^= lsb
    return moves


def _move_count(you, opp):
    cnt = 0
    y = you
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        for j in NEIGHBORS[i]:
            if opp & (1 << j):
                cnt += 1
        y ^= lsb
    return cnt


def _apply_move(you, opp, mv):
    """Return next position from opponent's perspective."""
    i, j = mv
    ib = 1 << i
    jb = 1 << j

    # Current player moves i -> j, capturing opponent at j.
    new_you_pieceboard = (you & ~ib) | jb
    new_opp_pieceboard = opp & ~jb

    # Perspective swaps.
    return new_opp_pieceboard, new_you_pieceboard


def _static_eval(you, opp):
    my_moves = _move_count(you, opp)
    op_moves = _move_count(opp, you)

    if my_moves == 0:
        return -WIN
    if op_moves == 0:
        return WIN

    score = 0
    score += 130 * (my_moves - op_moves)
    score += 22 * (_bitcount(you) - _bitcount(opp))

    # Positional centrality.
    y = you
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        score += CENTER_SCORE[i]
        y ^= lsb

    o = opp
    while o:
        lsb = o & -o
        i = lsb.bit_length() - 1
        score -= CENTER_SCORE[i]
        o ^= lsb

    return int(score)


def _ordered_moves(you, opp, moves):
    # Move ordering is important for alpha-beta. Prefer moves that leave the
    # opponent with few replies and place us centrally.
    scored = []
    for mv in moves:
        ny, no = _apply_move(you, opp, mv)
        replies = _move_count(ny, no)
        i, j = mv
        s = -40 * replies + CENTER_SCORE[j] * 3
        scored.append((s, mv))
    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    time_limit = 0.92

    you_mask = _to_mask(you)
    opp_mask = _to_mask(opponent)

    root_moves = _generate_moves(you_mask, opp_mask)

    # There is no legal move in a terminal losing state. The arena should not
    # request a move then, but return a syntactically valid placeholder anyway.
    if not root_moves:
        return "0,0,U"

    root_moves = _ordered_moves(you_mask, opp_mask, root_moves)
    best_move = root_moves[0]

    tt = {}

    def check_time():
        if time.perf_counter() - start_time > time_limit:
            raise TimeoutSearch()

    def negamax(y, o, depth, alpha, beta, ply):
        check_time()

        moves = _generate_moves(y, o)
        if not moves:
            return -WIN + ply

        if depth <= 0:
            return _static_eval(y, o)

        key = (y, o, depth)
        item = tt.get(key)
        if item is not None:
            stored_depth, stored_val, stored_flag, stored_alpha, stored_beta = item
            if stored_depth >= depth:
                if stored_flag == 0:
                    return stored_val
                if stored_flag == 1 and stored_val <= alpha:
                    return stored_val
                if stored_flag == 2 and stored_val >= beta:
                    return stored_val

        orig_alpha = alpha
        orig_beta = beta

        moves = _ordered_moves(y, o, moves)
        best = -INF

        for mv in moves:
            ny, no = _apply_move(y, o, mv)
            val = -negamax(ny, no, depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        # TT flags: 0 exact, 1 upper, 2 lower.
        if best <= orig_alpha:
            flag = 1
        elif best >= orig_beta:
            flag = 2
        else:
            flag = 0
        tt[key] = (depth, best, flag, orig_alpha, orig_beta)

        return best

    # Iterative deepening. On dense early boards depth 4-6 is usually feasible;
    # in tactical late boards this often searches much deeper.
    depth = 1
    try:
        while True:
            check_time()
            current_best = best_move
            current_score = -INF

            for mv in root_moves:
                check_time()
                ny, no = _apply_move(you_mask, opp_mask, mv)
                score = -negamax(ny, no, depth - 1, -INF, INF, 1)
                if score > current_score:
                    current_score = score
                    current_best = mv

            best_move = current_best

            # If we found a forced win, no need to spend more time.
            if current_score > WIN // 2:
                break

            depth += 1

            # Practical upper guard; positions are small, but avoid pathological
            # overhead if the clock behaves unexpectedly.
            if depth > 30:
                break

    except TimeoutSearch:
        pass
    except Exception:
        # Absolute safety fallback: never fail to return a legal move if one
        # exists.
        best_move = root_moves[0]

    i, j = best_move
    r, c = divmod(i, COLS)
    d = MOVE_DIR.get((i, j), "U")
    return f"{r},{c},{d}"
