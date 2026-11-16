
import time
from collections import deque

N = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

INF = 10 ** 9
WIN = 10 ** 7
DEADLINE = 0.0


class TimeoutSearch(Exception):
    pass


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def check_time():
    if time.perf_counter() > DEADLINE:
        raise TimeoutSearch()


def amazon_positions(board, player):
    out = []
    for r in range(N):
        for c in range(N):
            if board[r, c] == player:
                out.append((r, c))
    return out


def reachable_from(board, r, c):
    """Empty squares reachable by queen movement from r,c on current board."""
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while inside(nr, nc) and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def mobility_count(board, player):
    cnt = 0
    for r, c in amazon_positions(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc) and board[nr, nc] == 0:
                cnt += 1
                nr += dr
                nc += dc
    return cnt


def has_any_move(board, player):
    # If an amazon can move to any empty square, it can always shoot back
    # to the vacated square, so this is enough.
    for r, c in amazon_positions(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if inside(nr, nc) and board[nr, nc] == 0:
                return True
    return False


def generate_moves(board, player):
    """Return legal moves as tuples: (fr,fc,tr,tc,ar,ac)."""
    moves = []
    for fr, fc in amazon_positions(board, player):
        for dr, dc in DIRS:
            tr, tc = fr + dr, fc + dc
            while inside(tr, tc) and board[tr, tc] == 0:
                # Shoot arrow from landing square. The original from-square is
                # treated as empty for arrow purposes.
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc
                    while inside(ar, ac):
                        if ar == fr and ac == fc:
                            moves.append((fr, fc, tr, tc, ar, ac))
                        elif board[ar, ac] == 0:
                            moves.append((fr, fc, tr, tc, ar, ac))
                        else:
                            break
                        ar += adr
                        ac += adc

                tr += dr
                tc += dc
    return moves


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def queen_distances(board, player):
    """Minimum number of queen moves from any amazon of player to each empty square."""
    dist = [[99 for _ in range(N)] for __ in range(N)]
    q = deque()

    for r, c in amazon_positions(board, player):
        dist[r][c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc) and board[nr, nc] == 0:
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def secured_component_score(board):
    """Reward regions containing only our amazons; penalize opponent-only regions."""
    seen = [[False for _ in range(N)] for __ in range(N)]
    score = 0

    for sr in range(N):
        for sc in range(N):
            if seen[sr][sc] or board[sr, sc] == -1:
                continue

            stack = [(sr, sc)]
            seen[sr][sc] = True
            empties = 0
            ours = 0
            opps = 0

            while stack:
                r, c = stack.pop()
                v = board[r, c]
                if v == 0:
                    empties += 1
                elif v == 1:
                    ours += 1
                elif v == 2:
                    opps += 1

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if inside(nr, nc) and not seen[nr][nc] and board[nr, nc] != -1:
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            if ours and not opps:
                score += empties + 2 * ours
            elif opps and not ours:
                score -= empties + 2 * opps

    return score


def evaluate(board):
    """Static evaluation from player 1's perspective."""
    m1 = mobility_count(board, 1)
    m2 = mobility_count(board, 2)

    if m2 == 0 and m1 > 0:
        return WIN
    if m1 == 0 and m2 > 0:
        return -WIN
    if m1 == 0 and m2 == 0:
        return 0

    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)

    territory = 0
    distance_edge = 0

    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue
            a = d1[r][c]
            b = d2[r][c]
            if a == 99 and b == 99:
                continue
            if a < b:
                territory += 1
                distance_edge += min(4, b - a if b < 99 else 4)
            elif b < a:
                territory -= 1
                distance_edge -= min(4, a - b if a < 99 else 4)

    comp = secured_component_score(board)

    center = 0.0
    for r, c in amazon_positions(board, 1):
        center += 5.0 - (abs(r - 2.5) + abs(c - 2.5))
    for r, c in amazon_positions(board, 2):
        center -= 5.0 - (abs(r - 2.5) + abs(c - 2.5))

    return (
        12.0 * territory
        + 3.0 * distance_edge
        + 5.5 * (m1 - m2)
        + 18.0 * comp
        + 0.8 * center
    )


def ordered_moves(board, player, maximizing, limit=None):
    moves = generate_moves(board, player)
    scored = []

    for i, mv in enumerate(moves):
        if i & 31 == 0:
            check_time()
        nb = apply_move(board, mv, player)
        sc = evaluate(nb)
        scored.append((sc, mv))

    scored.sort(reverse=maximizing, key=lambda x: x[0])

    if limit is not None and len(scored) > limit:
        scored = scored[:limit]

    return [mv for _, mv in scored]


def search(board, depth, side, alpha, beta):
    check_time()

    if not has_any_move(board, side):
        return -WIN if side == 1 else WIN

    if depth <= 0:
        return evaluate(board)

    maximizing = (side == 1)

    # At depth 1, exact one-ply static minimax over all legal moves.
    if depth == 1:
        best = -INF if maximizing else INF
        moves = generate_moves(board, side)
        if not moves:
            return -WIN if side == 1 else WIN

        for i, mv in enumerate(moves):
            if i & 31 == 0:
                check_time()
            nb = apply_move(board, mv, side)

            # Immediate terminal recognition.
            other = 2 if side == 1 else 1
            if not has_any_move(nb, other):
                val = WIN if side == 1 else -WIN
            else:
                val = evaluate(nb)

            if maximizing:
                if val > best:
                    best = val
                if best >= beta:
                    break
                alpha = max(alpha, best)
            else:
                if val < best:
                    best = val
                if best <= alpha:
                    break
                beta = min(beta, best)

        return best

    # Selective width keeps the policy safely under the time limit.
    if depth >= 4:
        width = 14
    elif depth == 3:
        width = 20
    else:
        width = 32

    moves = ordered_moves(board, side, maximizing, width)
    if not moves:
        return -WIN if side == 1 else WIN

    if maximizing:
        best = -INF
        for mv in moves:
            nb = apply_move(board, mv, side)
            val = search(nb, depth - 1, 2, alpha, beta)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        best = INF
        for mv in moves:
            nb = apply_move(board, mv, side)
            val = search(nb, depth - 1, 1, alpha, beta)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best


def move_to_string(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    global DEADLINE
    DEADLINE = time.perf_counter() + 0.92

    try:
        root_moves = generate_moves(board, 1)
        if not root_moves:
            # The environment should not call us here. No legal move exists.
            # Return a syntactically valid placeholder.
            return "0,0:0,0:0,0"

        best_move = root_moves[0]
        best_static = -INF
        scored = []

        # First pass: ensure a good legal fallback and catch immediate wins.
        for i, mv in enumerate(root_moves):
            if i & 31 == 0:
                check_time()
            nb = apply_move(board, mv, 1)

            if not has_any_move(nb, 2):
                return move_to_string(mv)

            sc = evaluate(nb)
            scored.append((sc, mv))
            if sc > best_static:
                best_static = sc
                best_move = mv

        scored.sort(reverse=True, key=lambda x: x[0])

        n = len(scored)
        if n <= 12:
            max_depth = 5
            root_width = n
        elif n <= 40:
            max_depth = 4
            root_width = n
        elif n <= 120:
            max_depth = 3
            root_width = min(n, 70)
        else:
            max_depth = 2
            root_width = min(n, 60)

        candidates = [mv for _, mv in scored[:root_width]]

        # Iterative deepening: any completed depth can replace the fallback.
        for depth in range(2, max_depth + 1):
            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            for mv in candidates:
                check_time()
                nb = apply_move(board, mv, 1)
                val = search(nb, depth - 1, 2, alpha, beta)

                if val > current_score:
                    current_score = val
                    current_best = mv

                alpha = max(alpha, current_score)

            best_move = current_best

            # Reorder candidates so the next depth searches the best line first.
            candidates.sort(
                key=lambda m: evaluate(apply_move(board, m, 1)),
                reverse=True
            )
            if best_move in candidates:
                candidates.remove(best_move)
                candidates.insert(0, best_move)

        return move_to_string(best_move)

    except TimeoutSearch:
        return move_to_string(best_move)
    except Exception:
        # Last-resort robustness: generate and return the first legal move.
        try:
            moves = generate_moves(board, 1)
            if moves:
                return move_to_string(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
