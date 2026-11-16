
import time
from collections import deque

N = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

WIN = 1000000
INF = 10 ** 9
_DEADLINE = 0.0


def policy(board) -> str:
    """
    Return a legal Amazons move for the side represented by value 1.
    Format: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    """
    global _DEADLINE
    _DEADLINE = time.perf_counter() + 0.92

    b = [[int(board[r][c]) for c in range(N)] for r in range(N)]

    moves = generate_moves(b, 1)
    if not moves:
        # The environment should not call policy here. No legal move exists.
        return "0,0:0,0:0,0"

    best_move = moves[0]
    scored = []

    try:
        # Static scoring of all root moves.
        for mv in moves:
            make_move(b, mv, 1)
            sc = evaluate(b)
            undo_move(b, mv, 1)

            if sc >= WIN // 2:
                return fmt(mv)

            scored.append((sc, mv))
            if time.perf_counter() > _DEADLINE:
                break

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best_move = scored[0][1]
            best_val = scored[0][0]
        else:
            return fmt(best_move)

        if time.perf_counter() > _DEADLINE:
            return fmt(best_move)

        total = len(moves)

        # Adaptive search settings for the small 6x6 board.
        if total <= 100:
            root_limit = 80
            depth = 3
        elif total <= 250:
            root_limit = 70
            depth = 2
        elif total <= 700:
            root_limit = 45
            depth = 1
        else:
            root_limit = 30
            depth = 1

        alpha = -INF
        beta = INF

        for _, mv in scored[:root_limit]:
            if time.perf_counter() > _DEADLINE:
                break

            make_move(b, mv, 1)
            val = minimax(b, 2, depth, alpha, beta)
            undo_move(b, mv, 1)

            if val > best_val:
                best_val = val
                best_move = mv

            if val > alpha:
                alpha = val

    except TimeoutError:
        pass
    except Exception:
        # Safety: always return the best legal move found so far.
        pass

    return fmt(best_move)


def fmt(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def generate_moves(b, player):
    moves = []

    for fr in range(N):
        for fc in range(N):
            if b[fr][fc] != player:
                continue

            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                while inside(tr, tc) and b[tr][tc] == 0:
                    # Temporarily move amazon to generate legal arrow shots.
                    b[fr][fc] = 0
                    b[tr][tc] = player

                    for adr, adc in DIRS:
                        ar, ac = tr + adr, tc + adc
                        while inside(ar, ac) and b[ar][ac] == 0:
                            moves.append((fr, fc, tr, tc, ar, ac))
                            ar += adr
                            ac += adc

                    b[tr][tc] = 0
                    b[fr][fc] = player

                    tr += dr
                    tc += dc

    return moves


def make_move(b, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    b[fr][fc] = 0
    b[tr][tc] = player
    b[ar][ac] = -1


def undo_move(b, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    b[ar][ac] = 0
    b[tr][tc] = 0
    b[fr][fc] = player


def count_destinations(b, player):
    total = 0

    for r in range(N):
        for c in range(N):
            if b[r][c] != player:
                continue

            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while inside(nr, nc) and b[nr][nc] == 0:
                    total += 1
                    nr += dr
                    nc += dc

    return total


def minimax(b, side, depth, alpha, beta):
    if time.perf_counter() > _DEADLINE:
        raise TimeoutError

    if depth <= 0:
        return evaluate(b)

    moves = generate_moves(b, side)

    if not moves:
        return -WIN - depth if side == 1 else WIN + depth

    # Candidate limits keep the search inside the one-second budget.
    if depth >= 3:
        limit = 18
    elif depth == 2:
        limit = 24
    else:
        limit = 38

    moves = order_moves(b, moves, side, limit)

    if side == 1:
        value = -INF
        for mv in moves:
            if time.perf_counter() > _DEADLINE:
                raise TimeoutError

            make_move(b, mv, side)
            value = max(value, minimax(b, 2, depth - 1, alpha, beta))
            undo_move(b, mv, side)

            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    else:
        value = INF
        for mv in moves:
            if time.perf_counter() > _DEADLINE:
                raise TimeoutError

            make_move(b, mv, side)
            value = min(value, minimax(b, 1, depth - 1, alpha, beta))
            undo_move(b, mv, side)

            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def order_moves(b, moves, side, limit):
    if len(moves) <= 1:
        return moves

    scored = []
    reverse = side == 1

    for mv in moves:
        if time.perf_counter() > _DEADLINE:
            raise TimeoutError

        make_move(b, mv, side)
        sc = light_evaluate(b)
        undo_move(b, mv, side)

        scored.append((sc, mv))

    scored.sort(key=lambda x: x[0], reverse=reverse)
    return [mv for _, mv in scored[:limit]]


def light_evaluate(b):
    m1 = count_destinations(b, 1)
    m2 = count_destinations(b, 2)

    if m1 == 0:
        return -WIN
    if m2 == 0:
        return WIN

    center_score = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == 1:
                center_score += 5 - abs(2.5 - r) - abs(2.5 - c)
            elif b[r][c] == 2:
                center_score -= 5 - abs(2.5 - r) - abs(2.5 - c)

    return 12 * (m1 - m2) + center_score


def evaluate(b):
    m1 = count_destinations(b, 1)
    m2 = count_destinations(b, 2)

    if m1 == 0:
        return -WIN
    if m2 == 0:
        return WIN

    d1 = queen_distances(b, 1)
    d2 = queen_distances(b, 2)

    territory = 0.0
    reach_diff = 0

    for r in range(N):
        for c in range(N):
            if b[r][c] != 0:
                continue

            a = d1[r][c]
            o = d2[r][c]

            if a < 99:
                reach_diff += 1
            if o < 99:
                reach_diff -= 1

            if a < 99 and o >= 99:
                territory += 4.0
            elif o < 99 and a >= 99:
                territory -= 4.0
            elif a < o:
                territory += 2.0 + 0.25 * (o - a)
            elif o < a:
                territory -= 2.0 + 0.25 * (a - o)

    center_score = 0.0
    amazon_spread = 0.0

    own = []
    opp = []

    for r in range(N):
        for c in range(N):
            if b[r][c] == 1:
                own.append((r, c))
                center_score += 5 - abs(2.5 - r) - abs(2.5 - c)
            elif b[r][c] == 2:
                opp.append((r, c))
                center_score -= 5 - abs(2.5 - r) - abs(2.5 - c)

    # Slightly reward keeping amazons with useful separation.
    for i in range(len(own)):
        for j in range(i + 1, len(own)):
            amazon_spread += abs(own[i][0] - own[j][0]) + abs(own[i][1] - own[j][1])
    for i in range(len(opp)):
        for j in range(i + 1, len(opp)):
            amazon_spread -= abs(opp[i][0] - opp[j][0]) + abs(opp[i][1] - opp[j][1])

    return (
        14.0 * (m1 - m2)
        + 24.0 * territory
        + 5.0 * reach_diff
        + 1.5 * center_score
        + 0.7 * amazon_spread
    )


def queen_distances(b, player):
    inf = 99
    dist = [[inf for _ in range(N)] for _ in range(N)]
    q = deque()

    for r in range(N):
        for c in range(N):
            if b[r][c] == player:
                dist[r][c] = 0
                q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc) and b[nr][nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist
