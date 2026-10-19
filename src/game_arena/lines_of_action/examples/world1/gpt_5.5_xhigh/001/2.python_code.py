
import time
from functools import lru_cache

WIN_SCORE = 1_000_000
INF = 1_000_000_000

# Directions: N, S, W, E, NW, SE, NE, SW
DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
)


class _Timeout(Exception):
    pass


def _build_tables():
    bit = [1 << i for i in range(64)]
    neigh = [0] * 64
    center = [0] * 64
    edge = [0] * 64
    row = [0] * 64
    col = [0] * 64

    line_for_dir = [[0] * 64 for _ in range(8)]
    dest = [[[-1 for _ in range(9)] for _ in range(8)] for _ in range(64)]
    path = [[[0 for _ in range(9)] for _ in range(8)] for _ in range(64)]

    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            row[sq] = r
            col[sq] = c

            m = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8:
                        m |= bit[rr * 8 + cc]
            neigh[sq] = m

            # 0 at corners, 12 at the four central squares.
            center[sq] = 14 - (abs(2 * r - 7) + abs(2 * c - 7))
            edge[sq] = 1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0

    for r in range(8):
        for c in range(8):
            sq = r * 8 + c

            rowmask = 0
            colmask = 0
            diagmask = 0       # NW-SE, r-c constant
            antimask = 0       # NE-SW, r+c constant

            for k in range(8):
                rowmask |= bit[r * 8 + k]
                colmask |= bit[k * 8 + c]

            d0 = r - c
            s0 = r + c
            for rr in range(8):
                for cc in range(8):
                    if rr - cc == d0:
                        diagmask |= bit[rr * 8 + cc]
                    if rr + cc == s0:
                        antimask |= bit[rr * 8 + cc]

            # Direction groups.
            line_for_dir[0][sq] = colmask
            line_for_dir[1][sq] = colmask
            line_for_dir[2][sq] = rowmask
            line_for_dir[3][sq] = rowmask
            line_for_dir[4][sq] = diagmask
            line_for_dir[5][sq] = diagmask
            line_for_dir[6][sq] = antimask
            line_for_dir[7][sq] = antimask

            for d, (dr, dc) in enumerate(DIRS):
                for dist in range(1, 9):
                    nr = r + dr * dist
                    nc = c + dc * dist
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        dest[sq][d][dist] = nr * 8 + nc
                        pm = 0
                        for step in range(1, dist):
                            rr = r + dr * step
                            cc = c + dc * step
                            pm |= bit[rr * 8 + cc]
                        path[sq][d][dist] = pm

    cheb = [[0] * 64 for _ in range(64)]
    for i in range(64):
        for j in range(64):
            cheb[i][j] = max(abs(row[i] - row[j]), abs(col[i] - col[j]))

    return bit, neigh, center, edge, row, col, line_for_dir, dest, path, cheb


BIT, NEIGH, CENTER, EDGE, ROW, COL, LINE_FOR_DIR, DEST, PATH, CHEB = _build_tables()


def generate_moves(cur, opp):
    """Return legal moves for side 'cur' against side 'opp'. Move encoding: from*64+to."""
    occ = cur | opp
    moves = []
    pieces = cur
    line_for_dir = LINE_FOR_DIR
    dest = DEST
    path = PATH
    bit = BIT

    while pieces:
        lsb = pieces & -pieces
        fr = lsb.bit_length() - 1
        pieces ^= lsb
        base = fr << 6

        for d in range(8):
            dist = (occ & line_for_dir[d][fr]).bit_count()
            to = dest[fr][d][dist]
            if to >= 0:
                tb = bit[to]
                # Cannot land on own piece; cannot jump over enemy pieces.
                if (cur & tb) == 0 and (path[fr][d][dist] & opp) == 0:
                    moves.append(base | to)

    return moves


def apply_move(cur, opp, mv):
    fr = mv >> 6
    to = mv & 63
    tb = BIT[to]
    return ((cur & ~BIT[fr]) | tb, opp & ~tb)


def move_to_str(mv):
    fr = mv >> 6
    to = mv & 63
    return f"{fr // 8},{fr % 8}:{to // 8},{to % 8}"


@lru_cache(maxsize=200000)
def connected_bits(bits):
    if bits == 0:
        return False
    if bits & (bits - 1) == 0:
        return True

    seen = 0
    frontier = bits & -bits

    while frontier:
        seen |= frontier
        adj = 0
        f = frontier
        while f:
            lsb = f & -f
            adj |= NEIGH[lsb.bit_length() - 1]
            f ^= lsb
        frontier = adj & bits & ~seen

    return seen == bits


@lru_cache(maxsize=100000)
def analyze_bits(bits):
    n = bits.bit_count()
    if n == 0:
        return (0, 64, 0, 64, 0, 99, 16, -999, 64, 999)

    squares = []
    b = bits
    minr, maxr = 8, -1
    minc, maxc = 8, -1
    center_sum = 0
    edge_count = 0
    adj_sum = 0

    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        squares.append(sq)

        r = ROW[sq]
        c = COL[sq]
        if r < minr:
            minr = r
        if r > maxr:
            maxr = r
        if c < minc:
            minc = c
        if c > maxc:
            maxc = c

        center_sum += CENTER[sq]
        edge_count += EDGE[sq]
        adj_sum += (NEIGH[sq] & bits).bit_count()

    adj_pairs = adj_sum // 2
    spread = (maxr - minr) + (maxc - minc)

    # Connected components.
    components = 0
    largest = 0
    singles = 0
    unseen = bits

    while unseen:
        components += 1
        start = unseen & -unseen
        comp = 0
        frontier = start

        while frontier:
            comp |= frontier
            adj = 0
            f = frontier
            while f:
                lsb = f & -f
                adj |= NEIGH[lsb.bit_length() - 1]
                f ^= lsb
            frontier = adj & bits & ~comp

        size = comp.bit_count()
        if size > largest:
            largest = size
        if size == 1:
            singles += 1
        unseen &= ~comp

    pair_sum = 0
    nearest_sum = 0

    if n > 1:
        for i in range(n):
            si = squares[i]
            dist_row = CHEB[si]
            nearest = 99
            for j in range(n):
                if i == j:
                    continue
                d = dist_row[squares[j]]
                if d < nearest:
                    nearest = d
                if j > i:
                    pair_sum += d
            nearest_sum += nearest

        pair_avg10 = (pair_sum * 10) // (n * (n - 1) // 2)
    else:
        pair_avg10 = 0

    return (
        n, components, largest, singles, adj_pairs,
        pair_avg10, spread, center_sum, edge_count, nearest_sum
    )


@lru_cache(maxsize=100000)
def evaluate(cur, opp):
    """
    Static score from the point of view of side 'cur' to move.
    At searched nodes, 'opp' is the previous mover, so if opp is connected,
    the previous mover has already won.
    """
    if cur == 0:
        return -WIN_SCORE
    if opp == 0:
        return WIN_SCORE
    if connected_bits(opp):
        return -WIN_SCORE
    if connected_bits(cur):
        return WIN_SCORE

    cn, cc, cl, csing, cadj, cpair, cspread, ccenter, cedge, cnear = analyze_bits(cur)
    on, oc, ol, osing, oadj, opair, ospread, ocenter, oedge, onear = analyze_bits(opp)

    cl_ratio = (cl * 100) // cn if cn else 0
    ol_ratio = (ol * 100) // on if on else 0

    score = 0

    # Primary LOA objective: reduce own components and keep opponent fragmented.
    score += (oc - cc) * 1200
    score += (cl_ratio - ol_ratio) * 10
    score += (osing - csing) * 180

    # Cohesion/compactness.
    score += (cadj - oadj) * 45
    score += (opair - cpair) * 22
    score += (onear - cnear) * 18
    score += (ospread - cspread) * 35

    # Mild positional preferences.
    score += (ccenter - ocenter) * 4
    score += (oedge - cedge) * 18

    # Material is only a small factor in LOA.
    score += (cn - on) * 4

    return score


def has_winning_move(cur, opp):
    if cur == 0:
        return False
    if connected_bits(cur):
        return True
    for mv in generate_moves(cur, opp):
        nc, no = apply_move(cur, opp, mv)
        if connected_bits(nc):
            return True
    return False


def order_moves(moves, cur, opp, hash_move, ply, killers, history):
    scored = []
    bit = BIT
    neigh = NEIGH
    center = CENTER

    k0 = k1 = None
    if ply < len(killers):
        k0, k1 = killers[ply]

    for mv in moves:
        fr = mv >> 6
        to = mv & 63
        fb = bit[fr]
        tb = bit[to]

        friends_after = cur & ~fb
        dest_friends = (neigh[to] & friends_after).bit_count()
        src_friends = (neigh[fr] & friends_after).bit_count()

        s = 0
        if mv == hash_move:
            s += 10_000_000
        if mv == k0:
            s += 800_000
        elif mv == k1:
            s += 700_000

        if opp & tb:
            s += 20_000

        s += history.get(mv, 0)
        s += dest_friends * 600
        s -= src_friends * 80
        s += (center[to] - center[fr]) * 40

        if src_friends == 0:
            s += 200
        if dest_friends == 0:
            s -= 200
        if EDGE[to] and not EDGE[fr]:
            s -= 80
        elif EDGE[fr] and not EDGE[to]:
            s += 80

        scored.append((s, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.88

    cur = 0
    opp = 0

    for r in range(8):
        br = board[r]
        for c in range(8):
            v = br[c]
            sq = r * 8 + c
            if v == 1:
                cur |= BIT[sq]
            elif v == -1:
                opp |= BIT[sq]

    moves = generate_moves(cur, opp)

    # This should not occur in normal LOA positions. No legal string exists then.
    if not moves:
        return "0,0:0,0"

    applied = []
    winning = []

    for mv in moves:
        nc, no = apply_move(cur, opp, mv)
        applied.append((mv, nc, no))

        # A move that connects our pieces wins immediately. Prefer non-simultaneous wins.
        if connected_bits(nc):
            capture = 1 if (opp & BIT[mv & 63]) else 0
            non_simultaneous = 0 if connected_bits(no) else 1
            winning.append((non_simultaneous, capture, CENTER[mv & 63], mv))

    if winning:
        winning.sort(reverse=True)
        return move_to_str(winning[0][3])

    # Static root ordering and emergency fallback.
    root_scores = {}
    root_items = []
    unsafe = {}

    do_safety = len(moves) <= 60 and time.perf_counter() < deadline - 0.10

    for mv, nc, no in applied:
        if no == 0:
            score = WIN_SCORE // 2
        elif connected_bits(no):
            # Avoid moves that make only the opponent connected.
            score = -WIN_SCORE // 2
        else:
            score = -evaluate(no, nc)

            # If search is interrupted early, still avoid one-ply opponent wins.
            if do_safety and score > -WIN_SCORE // 4:
                if time.perf_counter() > deadline - 0.10:
                    do_safety = False
                elif has_winning_move(no, nc):
                    unsafe[mv] = True
                    score -= 50_000

        root_scores[mv] = score
        root_items.append((score, mv))

    root_items.sort(reverse=True)
    best_move = root_items[0][1]
    best_score = root_items[0][0]

    branch = len(moves)
    total_pieces = (cur | opp).bit_count()

    if branch <= 10 or total_pieces <= 8:
        max_depth = 7
    elif branch <= 18 or total_pieces <= 12:
        max_depth = 6
    elif branch <= 34:
        max_depth = 5
    else:
        max_depth = 4

    tt = {}
    history = {}
    killers = [[None, None] for _ in range(max_depth + 10)]
    nodes = 0

    def negamax(c, o, depth, alpha, beta, ply):
        nonlocal nodes

        nodes += 1
        if (nodes & 2047) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

        if c == 0:
            return -WIN_SCORE - depth
        if o == 0:
            return WIN_SCORE + depth

        # Previous mover wins ties/simultaneous connections.
        if connected_bits(o):
            return -WIN_SCORE - depth
        if connected_bits(c):
            return WIN_SCORE + depth

        if depth <= 0:
            return evaluate(c, o)

        orig_alpha = alpha
        orig_beta = beta
        key = (c, o)
        hash_move = None

        entry = tt.get(key)
        if entry is not None:
            e_depth, e_val, e_flag, e_move = entry
            hash_move = e_move
            if e_depth >= depth:
                if e_flag == 0:      # exact
                    return e_val
                elif e_flag == 1:    # lower bound
                    if e_val > alpha:
                        alpha = e_val
                else:                # upper bound
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        ms = generate_moves(c, o)
        if not ms:
            return -WIN_SCORE // 3

        ordered = order_moves(ms, c, o, hash_move, ply, killers, history)

        best = -INF
        best_mv = ordered[0]

        for mv in ordered:
            nc, no = apply_move(c, o, mv)

            if connected_bits(nc):
                score = WIN_SCORE + depth
            elif no == 0:
                score = WIN_SCORE + depth
            elif connected_bits(no):
                score = -WIN_SCORE - depth
            else:
                score = -negamax(no, nc, depth - 1, -beta, -alpha, ply + 1)

            if score > best:
                best = score
                best_mv = mv

            if score > alpha:
                alpha = score
                if alpha >= beta:
                    if ply < len(killers):
                        if killers[ply][0] != mv:
                            killers[ply][1] = killers[ply][0]
                            killers[ply][0] = mv
                    history[mv] = min(history.get(mv, 0) + depth * depth * 32, 1_000_000)
                    break

        if best <= orig_alpha:
            flag = 2      # upper
        elif best >= orig_beta:
            flag = 1      # lower
        else:
            flag = 0      # exact

        tt[key] = (depth, best, flag, best_mv)
        return best

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline - 0.01:
            break

        try:
            ordered_root = sorted(moves, key=lambda m: root_scores.get(m, -INF), reverse=True)
            curr_scores = {}

            alpha = -INF
            beta = INF
            depth_best = best_move
            depth_best_score = -INF

            for mv in ordered_root:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                nc, no = apply_move(cur, opp, mv)

                if connected_bits(nc):
                    score = WIN_SCORE + depth
                elif no == 0:
                    score = WIN_SCORE + depth
                elif connected_bits(no):
                    score = -WIN_SCORE - depth
                else:
                    score = -negamax(no, nc, depth - 1, -beta, -alpha, 1)

                # Depth-1 alone cannot see the opponent reply, so keep safety penalty.
                if depth == 1 and unsafe.get(mv, False):
                    score -= 50_000

                curr_scores[mv] = score

                if score > depth_best_score:
                    depth_best_score = score
                    depth_best = mv

                if score > alpha:
                    alpha = score

            root_scores = curr_scores
            best_move = depth_best
            best_score = depth_best_score

            if best_score > WIN_SCORE // 2:
                break

        except _Timeout:
            break

    return move_to_str(best_move)
