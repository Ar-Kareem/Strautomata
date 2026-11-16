
import time

# 6x6 Amazons policy.
# Board values: 0 empty, 1 us, 2 opponent, -1 arrow/block.

N = 6
SIZE = 36

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

ROWS = tuple(i // N for i in range(SIZE))
COLS = tuple(i % N for i in range(SIZE))

# Rays from every square in each of the 8 queen directions.
RAYS = []
for r in range(N):
    for c in range(N):
        rays_here = []
        for dr, dc in DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            rays_here.append(tuple(ray))
        RAYS.append(tuple(rays_here))
RAYS = tuple(RAYS)

# 8-neighbor adjacency for king-distance / components.
ADJ = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        ADJ.append(tuple(ns))
ADJ = tuple(ADJ)

# Center preference, small positional tie-breaker.
CENTER = []
for i in range(SIZE):
    r, c = ROWS[i], COLS[i]
    CENTER.append(int(10 - 2 * (abs(r - 2.5) + abs(c - 2.5))))
CENTER = tuple(CENTER)

# Precompute line alignment and between-squares for quick move ordering.
DIR_INDEX = {d: k for k, d in enumerate(DIRS)}
LINE_DIR = [[-1] * SIZE for _ in range(SIZE)]
BETWEEN = [[() for _ in range(SIZE)] for __ in range(SIZE)]

def _sgn(x):
    return (x > 0) - (x < 0)

for p in range(SIZE):
    rp, cp = ROWS[p], COLS[p]
    for q in range(SIZE):
        if p == q:
            continue
        rq, cq = ROWS[q], COLS[q]
        dr0, dc0 = rq - rp, cq - cp
        if dr0 == 0 or dc0 == 0 or abs(dr0) == abs(dc0):
            dr, dc = _sgn(dr0), _sgn(dc0)
            LINE_DIR[p][q] = DIR_INDEX[(dr, dc)]
            mids = []
            rr, cc = rp + dr, cp + dc
            while rr != rq or cc != cq:
                mids.append(rr * N + cc)
                rr += dr
                cc += dc
            BETWEEN[p][q] = tuple(mids)

LINE_DIR = tuple(tuple(row) for row in LINE_DIR)
BETWEEN = tuple(tuple(row) for row in BETWEEN)

INF_DIST = 99
MATE = 1_000_000

QVAL = [0] * (INF_DIST + 1)
KVAL = [0] * (INF_DIST + 1)
for d in range(1, INF_DIST):
    QVAL[d] = max(1, 16 // d)
    KVAL[d] = max(1, 12 // d)
QVAL[INF_DIST] = 0
KVAL[INF_DIST] = 0
QVAL = tuple(QVAL)
KVAL = tuple(KVAL)


class _Timeout(Exception):
    pass


def _flatten_board(board):
    if hasattr(board, "ravel"):
        flat = board.ravel()
        return [int(flat[i]) for i in range(SIZE)]
    return [int(board[r][c]) for r in range(N) for c in range(N)]


def _format_move(m):
    s, d, a = m
    return f"{s // N},{s % N}:{d // N},{d % N}:{a // N},{a % N}"


def _has_queen_move(b, side):
    for p, v in enumerate(b):
        if v == side:
            for ray in RAYS[p]:
                for x in ray:
                    if b[x] == 0:
                        return True
                    break
    return False


def _queen_mobility(b, side):
    cnt = 0
    for p, v in enumerate(b):
        if v == side:
            for ray in RAYS[p]:
                for x in ray:
                    if b[x] != 0:
                        break
                    cnt += 1
    return cnt


def _generate_moves(b, side):
    """Generate all legal (source, destination, arrow) moves."""
    moves = []
    append = moves.append

    for s, v in enumerate(b):
        if v != side:
            continue

        # Vacate source while generating arrows so arrows may pass through / land there.
        b[s] = 0

        for move_ray in RAYS[s]:
            for d in move_ray:
                if b[d] != 0:
                    break

                b[d] = side

                for arrow_ray in RAYS[d]:
                    for a in arrow_ray:
                        if b[a] != 0:
                            break
                        append((s, d, a))

                b[d] = 0

        b[s] = side

    return moves


def _make_move(b, side, m):
    s, d, a = m
    b[s] = 0
    b[d] = side
    b[a] = -1


def _undo_move(b, side, m):
    s, d, a = m
    b[a] = 0
    b[d] = 0
    b[s] = side


def _queen_distances(b, side):
    dist = [INF_DIST] * SIZE
    q = []

    for p, v in enumerate(b):
        if v == side:
            dist[p] = 0
            q.append(p)

    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1

        for ray in RAYS[p]:
            for x in ray:
                if b[x] != 0:
                    break
                if dist[x] == INF_DIST:
                    dist[x] = nd
                    q.append(x)

    return dist


def _king_distances(b, side):
    dist = [INF_DIST] * SIZE
    q = []

    for p, v in enumerate(b):
        if v == side:
            dist[p] = 0
            q.append(p)

    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1

        for x in ADJ[p]:
            if b[x] == 0 and dist[x] == INF_DIST:
                dist[x] = nd
                q.append(x)

    return dist


def _component_score(b, side):
    """Positive for empty chambers containing only our amazons, negative for opponent-only."""
    opp = 3 - side
    seen = [False] * SIZE
    score = 0

    for start in range(SIZE):
        if seen[start] or b[start] == -1:
            continue

        stack = [start]
        seen[start] = True
        empties = 0
        has_us = False
        has_them = False

        while stack:
            p = stack.pop()
            v = b[p]
            if v == 0:
                empties += 1
            elif v == side:
                has_us = True
            elif v == opp:
                has_them = True

            for nb in ADJ[p]:
                if not seen[nb] and b[nb] != -1:
                    seen[nb] = True
                    stack.append(nb)

        if has_us and not has_them:
            score += empties
        elif has_them and not has_us:
            score -= empties

    return score


def _center_balance(b, side):
    opp = 3 - side
    s = 0
    for i, v in enumerate(b):
        if v == side:
            s += CENTER[i]
        elif v == opp:
            s -= CENTER[i]
    return s


def _evaluate(b, side):
    """Static score from side-to-move's perspective."""
    opp = 3 - side

    my_mob = _queen_mobility(b, side)
    if my_mob == 0:
        return -MATE // 2

    op_mob = _queen_mobility(b, opp)
    # If opponent currently has no move and we do, we can move and shoot our source,
    # preserving all old blockers and winning immediately next ply.
    if op_mob == 0:
        return MATE // 2

    q_my = _queen_distances(b, side)
    q_op = _queen_distances(b, opp)
    k_my = _king_distances(b, side)
    k_op = _king_distances(b, opp)

    qterr = 0     # scaled by 10
    kterr = 0     # scaled by 10
    qclose = 0
    kclose = 0

    for i, v in enumerate(b):
        if v != 0:
            continue

        dm, do = q_my[i], q_op[i]
        if dm < do:
            qterr += 10
        elif do < dm:
            qterr -= 10
        elif dm != INF_DIST:
            qterr += 1  # tempo bonus for equal queen-distance squares
        qclose += QVAL[dm] - QVAL[do]

        km, ko = k_my[i], k_op[i]
        if km < ko:
            kterr += 10
        elif ko < km:
            kterr -= 10
        elif km != INF_DIST:
            kterr += 1
        kclose += KVAL[km] - KVAL[ko]

    comp = _component_score(b, side)
    center = _center_balance(b, side)

    return (
        9 * qterr
        + 3 * kterr
        + 3 * qclose
        + kclose
        + 7 * (my_mob - op_mob)
        + 24 * comp
        + 2 * center
    )


def _mobility_after_capped(b, player, s, d, a, cap):
    """Queen mobility for player after move s->d and arrow a, capped for speed."""
    cnt = 0

    for p, v in enumerate(b):
        if v != player:
            continue

        start = d if p == s else p

        for ray in RAYS[start]:
            for x in ray:
                if x == a:
                    break
                if x == d and start != d:
                    break
                if x == s:
                    cnt += 1
                else:
                    if b[x] != 0:
                        break
                    cnt += 1

                if cnt >= cap:
                    return cnt

    return cnt


def _visible_from_after(b, pos, s, a):
    """Mobility of moved amazon at pos after source s is vacated and arrow a is placed."""
    cnt = 0
    for ray in RAYS[pos]:
        for x in ray:
            if x == a:
                break
            if x == s:
                cnt += 1
            else:
                if b[x] != 0:
                    break
                cnt += 1
    return cnt


def _ray_block_value(b, op, target, s, d):
    """How many opponent ray squares are blocked by occupying/arrowing target after s->d."""
    dir_idx = LINE_DIR[op][target]
    if dir_idx < 0:
        return 0

    for x in BETWEEN[op][target]:
        if x == s:
            continue
        if x == d:
            return 0
        if b[x] != 0:
            return 0

    val = 1
    for x in RAYS[target][dir_idx]:
        if x == s:
            val += 1
        else:
            if x == d or b[x] != 0:
                break
            val += 1

    return val


def _quick_move_score(b, side, m, opp_positions):
    """Cheap move ordering score; exact value comes from search/evaluation."""
    s, d, a = m
    opp = 3 - side

    dest_lib = _visible_from_after(b, d, s, a)
    opp_mob = _mobility_after_capped(b, opp, s, d, a, 70)

    score = (
        5 * dest_lib
        - 3 * opp_mob
        + 6 * CENTER[d]
        - 2 * CENTER[s]
        + CENTER[a]
    )

    if opp_mob == 0:
        score += 200_000

    if dest_lib <= 1:
        score -= 25

    ar, ac = ROWS[a], COLS[a]

    for op in opp_positions:
        cheb = max(abs(ar - ROWS[op]), abs(ac - COLS[op]))
        if cheb == 1:
            score += 32
        elif cheb == 2:
            score += 12

        # Arrow blocks opponent lines.
        rb = _ray_block_value(b, op, a, s, d)
        if rb:
            score += 10 * rb

        # The amazon body at destination also blocks lines temporarily.
        body = _ray_block_value(b, op, d, s, d)
        if body:
            score += 4 * body

    return score


def _order_moves(b, side, moves, max_keep=None, preferred=None):
    opp = 3 - side
    opp_positions = [i for i, v in enumerate(b) if v == opp]

    scored = []
    for m in moves:
        sc = _quick_move_score(b, side, m, opp_positions)
        if preferred is not None and m == preferred:
            sc += 1_000_000
        scored.append((sc, m))

    scored.sort(key=lambda t: t[0], reverse=True)

    if max_keep is not None and len(scored) > max_keep:
        scored = scored[:max_keep]

    return [m for _, m in scored]


def _node_limit(depth, n_moves, empties):
    if n_moves <= 60 or empties <= 8:
        return n_moves
    if depth >= 4:
        return min(n_moves, 18)
    if depth == 3:
        return min(n_moves, 24)
    if depth == 2:
        return min(n_moves, 34)
    return min(n_moves, 56)


def _root_limit(depth, n_moves, empties):
    if n_moves <= 80 or empties <= 8:
        return n_moves
    if depth == 2:
        return min(n_moves, 180)
    if depth == 3:
        return min(n_moves, 70 if empties > 18 else 100)
    if depth == 4:
        return min(n_moves, 40)
    return min(n_moves, 25)


def _negamax(b, side, depth, alpha, beta, deadline, tt, nodes, ply):
    nodes[0] += 1
    if (nodes[0] & 127) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    opp = 3 - side

    if depth <= 0:
        if not _has_queen_move(b, side):
            return -MATE + ply
        return _evaluate(b, side)

    if not _has_queen_move(b, side):
        return -MATE + ply

    # Exact tactical theorem: if opponent has no move now and we have one,
    # we can shoot back to our source and keep them immobilized.
    if not _has_queen_move(b, opp):
        return MATE - ply - 1

    key = (side, tuple(b))
    entry = tt.get(key)
    preferred = None

    alpha0, beta0 = alpha, beta

    if entry is not None:
        edepth, eval_score, flag, best_move = entry
        preferred = best_move
        if edepth >= depth:
            if flag == 0:      # exact
                return eval_score
            elif flag == 1:    # lower bound
                if eval_score > alpha:
                    alpha = eval_score
            else:              # upper bound
                if eval_score < beta:
                    beta = eval_score
            if alpha >= beta:
                return eval_score

    moves = _generate_moves(b, side)
    if not moves:
        return -MATE + ply

    empties = b.count(0)
    keep = _node_limit(depth, len(moves), empties)
    ordered = _order_moves(b, side, moves, keep, preferred)

    best_val = -MATE * 2
    best_move = ordered[0]

    for m in ordered:
        _make_move(b, side, m)
        try:
            val = -_negamax(b, opp, depth - 1, -beta, -alpha, deadline, tt, nodes, ply + 1)
        finally:
            _undo_move(b, side, m)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val
            if alpha >= beta:
                break

    if best_val <= alpha0:
        flag = 2   # upper bound
    elif best_val >= beta0:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    tt[key] = (depth, best_val, flag, best_move)
    return best_val


def _choose_policy_move(board):
    start_time = time.perf_counter()
    deadline = start_time + 0.92

    b = _flatten_board(board)
    root_moves = _generate_moves(b, 1)

    if not root_moves:
        # No legal move exists; environment should not ask in this state.
        return "0,0:0,0:0,0"

    if len(root_moves) == 1:
        return _format_move(root_moves[0])

    # If opponent already has no move, shoot back to our source and preserve the lock.
    if not _has_queen_move(b, 2):
        for m in root_moves:
            if m[2] == m[0]:
                return _format_move(m)
        return _format_move(root_moves[0])

    # Static ordering of all root moves; also catch immediate wins.
    scored = []
    for m in root_moves:
        _make_move(b, 1, m)
        try:
            if not _has_queen_move(b, 2):
                sc = MATE
            else:
                sc = -_evaluate(b, 2)
        finally:
            _undo_move(b, 1, m)

        if sc >= MATE // 2:
            return _format_move(m)

        scored.append((sc, m))

    scored.sort(key=lambda t: t[0], reverse=True)

    best = scored[0][1]
    best_score = scored[0][0]
    root_order = [m for _, m in scored]

    if time.perf_counter() > deadline - 0.04:
        return _format_move(best)

    empties = b.count(0)
    if empties <= 8:
        max_depth = empties + 1
    elif empties <= 14:
        max_depth = 7
    elif empties <= 22:
        max_depth = 6
    else:
        max_depth = 5

    tt = {}
    nodes = [0]

    for depth in range(2, max_depth + 1):
        # Principal variation first.
        if root_order and root_order[0] != best:
            try:
                idx = root_order.index(best)
                root_order.pop(idx)
                root_order.insert(0, best)
            except ValueError:
                pass

        limit = _root_limit(depth, len(root_order), empties)
        current_scores = {}
        current_best = best
        current_best_val = -MATE * 2

        try:
            alpha, beta = -MATE, MATE

            for idx, m in enumerate(root_order[:limit]):
                if (idx & 7) == 0 and time.perf_counter() > deadline:
                    raise _Timeout()

                _make_move(b, 1, m)
                try:
                    val = -_negamax(b, 2, depth - 1, -beta, -alpha, deadline, tt, nodes, 1)
                finally:
                    _undo_move(b, 1, m)

                current_scores[m] = val

                if val > current_best_val:
                    current_best_val = val
                    current_best = m

                if val > alpha:
                    alpha = val

            if current_scores:
                best = current_best
                best_score = current_best_val

                searched_sorted = sorted(current_scores.keys(), key=lambda mv: current_scores[mv], reverse=True)
                searched_set = set(current_scores.keys())
                rest = [mv for mv in root_order if mv not in searched_set]
                root_order = searched_sorted + rest

                if best_score >= MATE // 2:
                    break

            if time.perf_counter() > deadline - 0.04:
                break

        except _Timeout:
            # If depth-2 was partially searched, using it is usually safer than pure static greed.
            if depth == 2 and current_scores:
                best = current_best
            break

    return _format_move(best)


def policy(board) -> str:
    try:
        return _choose_policy_move(board)
    except Exception:
        # Absolute safety fallback: regenerate and return the first legal move if possible.
        try:
            b = _flatten_board(board)
            moves = _generate_moves(b, 1)
            if moves:
                return _format_move(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
