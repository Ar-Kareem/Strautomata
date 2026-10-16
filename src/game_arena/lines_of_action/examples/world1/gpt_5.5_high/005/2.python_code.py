
import time

# ---------- Precomputed board geometry ----------

WIN = 1_000_000
INF = 10**9

DIRS = (
    (-1, 0), (1, 0),      # vertical
    (0, -1), (0, 1),      # horizontal
    (-1, -1), (1, 1),     # main diagonal
    (-1, 1), (1, -1),     # anti diagonal
)

R = [i // 8 for i in range(64)]
C = [i % 8 for i in range(64)]

NEIGHBORS = [[] for _ in range(64)]
NEIGH_MASKS = [0 for _ in range(64)]
CENTER_TABLE = [0 for _ in range(64)]

for i in range(64):
    r, c = R[i], C[i]

    # 8-neighbor connectivity
    mask = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                j = nr * 8 + nc
                NEIGHBORS[i].append(j)
                mask |= 1 << j
    NEIGH_MASKS[i] = mask

    # Centrality: 12 near center, 0 near corners.
    CENTER_TABLE[i] = 14 - (abs(2 * r - 7) + abs(2 * c - 7))

# DESTS[sq][dir][distance] -> destination square or -1
# PATH_MASKS excludes source and destination; enemy pieces may not occur there.
DESTS = [[[-1 for _ in range(9)] for _ in range(8)] for _ in range(64)]
PATH_MASKS = [[[0 for _ in range(9)] for _ in range(8)] for _ in range(64)]

for sq in range(64):
    r, c = R[sq], C[sq]
    for d, (dr, dc) in enumerate(DIRS):
        for dist in range(1, 9):
            nr, nc = r + dr * dist, c + dc * dist
            if 0 <= nr < 8 and 0 <= nc < 8:
                DESTS[sq][d][dist] = nr * 8 + nc
                pm = 0
                for step in range(1, dist):
                    rr, cc = r + dr * step, c + dc * step
                    pm |= 1 << (rr * 8 + cc)
                PATH_MASKS[sq][d][dist] = pm


# ---------- Globals used during one search ----------

DEADLINE = 0.0
NODES = 0
TT = {}


class SearchTimeout(Exception):
    pass


# ---------- Basic utilities ----------

def board_to_tuple(board):
    return tuple(int(board[r][c]) for r in range(8) for c in range(8))


def move_to_str(m):
    fr = m >> 6
    to = m & 63
    return f"{fr // 8},{fr % 8}:{to // 8},{to % 8}"


def apply_move(board, m):
    """Apply current player's move, then swap perspective for negamax."""
    fr = m >> 6
    to = m & 63
    nb = list(board)
    nb[fr] = 0
    nb[to] = 1
    return tuple(-x for x in nb)


def connected_mask(mask):
    if mask == 0:
        return False
    if mask & (mask - 1) == 0:
        return True

    seen = 0
    frontier = mask & -mask

    while frontier:
        seen |= frontier
        nxt = 0
        f = frontier
        while f:
            bit = f & -f
            idx = bit.bit_length() - 1
            nxt |= NEIGH_MASKS[idx]
            f ^= bit
        frontier = nxt & mask & ~seen

    return seen == mask


def terminal_value(board, depth):
    """
    Return value for side to move, or None if nonterminal.
    At a node, -1 pieces belong to the player who just moved.
    If both sides are connected after a move, the mover wins, so -1 is checked first.
    """
    own_mask = 0
    opp_mask = 0

    for i, v in enumerate(board):
        if v == 1:
            own_mask |= 1 << i
        elif v == -1:
            opp_mask |= 1 << i

    if own_mask == 0:
        return -WIN - depth
    if opp_mask == 0:
        return WIN + depth

    if connected_mask(opp_mask):
        return -WIN - depth
    if connected_mask(own_mask):
        return WIN + depth

    return None


# ---------- Legal move generation ----------

def generate_moves(board):
    rows = [0] * 8
    cols = [0] * 8
    diag1 = [0] * 15  # r - c + 7
    diag2 = [0] * 15  # r + c

    own_positions = []
    own_mask = 0
    enemy_mask = 0

    for i, v in enumerate(board):
        if v:
            r, c = R[i], C[i]
            rows[r] += 1
            cols[c] += 1
            diag1[r - c + 7] += 1
            diag2[r + c] += 1

            if v == 1:
                own_positions.append(i)
                own_mask |= 1 << i
            else:
                enemy_mask |= 1 << i

    moves = []

    for sq in own_positions:
        r, c = R[sq], C[sq]

        for d in range(8):
            if d < 2:
                dist = cols[c]
            elif d < 4:
                dist = rows[r]
            elif d < 6:
                dist = diag1[r - c + 7]
            else:
                dist = diag2[r + c]

            to = DESTS[sq][d][dist]
            if to < 0:
                continue
            if own_mask & (1 << to):
                continue
            if PATH_MASKS[sq][d][dist] & enemy_mask:
                continue

            moves.append((sq << 6) | to)

    return moves


# ---------- Evaluation ----------

def compute_stats(board, side):
    positions = []
    mask = 0
    minr, maxr = 8, -1
    minc, maxc = 8, -1
    center = 0

    for i, v in enumerate(board):
        if v == side:
            positions.append(i)
            mask |= 1 << i
            r, c = R[i], C[i]
            if r < minr:
                minr = r
            if r > maxr:
                maxr = r
            if c < minc:
                minc = c
            if c > maxc:
                maxc = c
            center += CENTER_TABLE[i]

    n = len(positions)
    if n == 0:
        return (0, 99, 0, 64, 80, 0, 0)

    # Connected components and largest component.
    comps = 0
    largest = 0
    remaining = mask

    while remaining:
        comps += 1
        start = remaining & -remaining
        seen = 0
        frontier = start

        while frontier:
            seen |= frontier
            nxt = 0
            f = frontier
            while f:
                bit = f & -f
                idx = bit.bit_length() - 1
                nxt |= NEIGH_MASKS[idx]
                f ^= bit
            frontier = nxt & mask & ~seen

        size = seen.bit_count()
        if size > largest:
            largest = size
        remaining &= ~seen

    area = (maxr - minr + 1) * (maxc - minc + 1)

    # Average Chebyshev pair distance, scaled by 10.
    if n <= 1:
        pair10 = 0
    else:
        psum = 0
        for a in range(n):
            ia = positions[a]
            ra, ca = R[ia], C[ia]
            for b in range(a + 1, n):
                ib = positions[b]
                d = max(abs(ra - R[ib]), abs(ca - C[ib]))
                psum += d
        pair_count = n * (n - 1) // 2
        pair10 = (10 * psum) // pair_count

    # Number of friendly adjacent links.
    adj2 = 0
    for p in positions:
        adj2 += (NEIGH_MASKS[p] & mask).bit_count()
    adjacency = adj2 // 2

    return (n, comps, largest, area, pair10, adjacency, center)


def evaluate(board):
    """
    Static evaluation from the perspective of side to move.
    Terminal states are handled before this is called in search.
    """
    on, oc, ol, oa, opair, oadj, ocenter = compute_stats(board, 1)
    en, ec, el, ea, epair, eadj, ecenter = compute_stats(board, -1)

    if on == 0:
        return -WIN // 2
    if en == 0:
        return WIN // 2

    own_largest_ratio = (ol * 100) // on
    enemy_largest_ratio = (el * 100) // en

    score = 0

    # Primary LOA objective: fewer connected components.
    score += 1200 * (ec - oc)

    # Prefer having most pieces in one large cluster.
    score += 9 * (own_largest_ratio - enemy_largest_ratio)

    # Prefer compact formations.
    score += 20 * (epair - opair)
    score += 12 * (ea - oa)

    # Prefer pieces already adjacent/linked.
    score += 40 * (oadj - eadj)

    # Mild centralization and material stability.
    score += 3 * (ocenter - ecenter)
    score += 10 * (on - en)

    return score


# ---------- Move ordering and search ----------

def move_order_score(board, m):
    fr = m >> 6
    to = m & 63

    s = CENTER_TABLE[to] * 4

    if board[to] == -1:
        s += 25

    new_adj = 0
    enemy_adj = 0
    for nb in NEIGHBORS[to]:
        if nb != fr and board[nb] == 1:
            new_adj += 1
        elif board[nb] == -1:
            enemy_adj += 1

    old_adj = 0
    for nb in NEIGHBORS[fr]:
        if nb != to and board[nb] == 1:
            old_adj += 1

    s += new_adj * 90
    s -= old_adj * 8
    s += enemy_adj * 4

    if old_adj == 0:
        s += 20

    return s


def ordered_moves(board, moves, tt_best=None):
    if len(moves) <= 1:
        return moves

    scored = []
    for m in moves:
        s = move_order_score(board, m)
        if m == tt_best:
            s += 1_000_000
        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def negamax(board, depth, alpha, beta):
    global NODES, TT

    NODES += 1
    if (NODES & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout()

    tv = terminal_value(board, depth)
    if tv is not None:
        return tv

    if depth <= 0:
        return evaluate(board)

    entry = TT.get(board)
    tt_best = None

    if entry is not None:
        stored_depth, flag, val, best = entry
        tt_best = best

        if stored_depth >= depth:
            if flag == 0:
                return val
            if flag == 1 and val >= beta:
                return val
            if flag == -1 and val <= alpha:
                return val

    moves = generate_moves(board)
    if not moves:
        return -WIN // 4 - depth

    moves = ordered_moves(board, moves, tt_best)

    original_alpha = alpha
    best_val = -INF
    best_move = moves[0]

    for m in moves:
        child = apply_move(board, m)
        val = -negamax(child, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= original_alpha:
        flag = -1  # upper bound
    elif best_val >= beta:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    if len(TT) < 100000:
        TT[board] = (depth, flag, best_val, best_move)

    return best_val


def search_root(board, depth, root_moves):
    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = root_moves[0]
    results = []

    for m in root_moves:
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout()

        child = apply_move(board, m)
        val = -negamax(child, depth - 1, -beta, -alpha)
        results.append((val, m))

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    results.sort(reverse=True)
    ordered = [m for _, m in results]
    return best_val, best_move, ordered


# ---------- Public API ----------

def _policy(board):
    global DEADLINE, NODES, TT

    start = time.perf_counter()
    DEADLINE = start + 0.90
    NODES = 0
    TT = {}

    b = board_to_tuple(board)
    moves = generate_moves(b)

    if not moves:
        # Should not happen in normal LOA positions.
        return "0,0:0,0"

    if len(moves) == 1:
        return move_to_str(moves[0])

    # One-ply static ordering and safe fallback.
    scored = []
    safe_best = moves[0]
    safe_val = -INF

    for idx, m in enumerate(moves):
        if idx and (idx & 7) == 0 and time.perf_counter() >= DEADLINE:
            break

        child = apply_move(b, m)
        tv = terminal_value(child, 0)

        if tv is not None:
            val = -tv
        else:
            val = -evaluate(child)

        val += move_order_score(b, m) // 5

        # Immediate win: take it.
        if val > WIN // 2:
            return move_to_str(m)

        scored.append((val, m))

        if val > safe_val:
            safe_val = val
            safe_best = m

    if scored:
        scored.sort(reverse=True)
        root_moves = [m for _, m in scored]
        used = set(root_moves)
        root_moves.extend(m for m in moves if m not in used)
    else:
        root_moves = moves[:]

    best_move = safe_best
    last_order = root_moves

    # Static ordering already gives depth-1 information; start tactical search at depth 2.
    for depth in range(2, 10):
        if time.perf_counter() >= DEADLINE:
            break

        try:
            val, move, new_order = search_root(b, depth, last_order)
            best_move = move
            last_order = new_order

            # Proven forced win found.
            if val > WIN // 2:
                break

        except SearchTimeout:
            break

    return move_to_str(best_move)


def policy(board) -> str:
    """
    Return a legal move string: 'from_row,from_col:to_row,to_col'.
    A final exception guard preserves legality whenever possible.
    """
    try:
        return _policy(board)
    except Exception:
        try:
            b = board_to_tuple(board)
            moves = generate_moves(b)
            if moves:
                return move_to_str(moves[0])
        except Exception:
            pass
        return "0,0:0,0"
