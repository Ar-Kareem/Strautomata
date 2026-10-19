
from heapq import heappush, heappop
import math

N = 11

DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _other(color):
    return "w" if color == "b" else "b"


def _shortest_cost(player_stones, enemy_stones, color):
    """
    Minimum number of empty cells needed to complete a connection.
    Own stones cost 0, empty cells cost 1, enemy stones are blocked.
    """
    own = set(player_stones)
    enemy = set(enemy_stones)

    INF = 10 ** 9
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == "b":
        # black connects top to bottom
        for c in range(N):
            cell = (0, c)
            if cell in enemy:
                continue
            cost = 0 if cell in own else 1
            dist[0][c] = cost
            heappush(pq, (cost, 0, c))

        targets = lambda r, c: r == N - 1
    else:
        # white connects left to right
        for r in range(N):
            cell = (r, 0)
            if cell in enemy:
                continue
            cost = 0 if cell in own else 1
            dist[r][0] = cost
            heappush(pq, (cost, r, 0))

        targets = lambda r, c: c == N - 1

    best = INF

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if targets(r, c):
            best = d
            break

        for nr, nc in _neighbors(r, c):
            cell = (nr, nc)
            if cell in enemy:
                continue
            step = 0 if cell in own else 1
            nd = d + step
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    return best


def _center_penalty(r, c):
    # Small deterministic preference for central influence.
    return (abs(r - 5) + abs(c - 5)) * 0.015


def _connection_bonus(move, own):
    r, c = move
    bonus = 0.0
    for nb in _neighbors(r, c):
        if nb in own:
            bonus -= 0.08
    return bonus


def _static_score(my_stones, opp_stones, color, move=None):
    """
    Lower is better for us.
    """
    my_cost = _shortest_cost(my_stones, opp_stones, color)
    opp_cost = _shortest_cost(opp_stones, my_stones, _other(color))

    score = my_cost - 0.92 * opp_cost

    if move is not None:
        r, c = move
        score += _center_penalty(r, c)
        score += _connection_bonus(move, set(my_stones))

        # Mild orientation preference.
        # Black likes advancing vertically; white likes advancing horizontally.
        if color == "b":
            score -= 0.01 * min(r, N - 1 - r)
        else:
            score -= 0.01 * min(c, N - 1 - c)

    return score


def _all_empty(me, opp):
    occupied = set(me) | set(opp)
    return [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]


def _candidate_moves(me, opp):
    """
    Candidate generator. Includes all moves when the board is sparse enough,
    otherwise focuses on cells near existing stones plus central cells.
    """
    empties = _all_empty(me, opp)
    if len(empties) <= 70:
        return empties

    occupied = set(me) | set(opp)
    cand = set()

    for stone in occupied:
        r, c = stone
        cand.add(stone)
        for nb in _neighbors(r, c):
            if nb not in occupied:
                cand.add(nb)
            for nb2 in _neighbors(*nb):
                if nb2 not in occupied:
                    cand.add(nb2)

    # Always keep central region available.
    for r in range(3, 8):
        for c in range(3, 8):
            if (r, c) not in occupied:
                cand.add((r, c))

    cand = [m for m in cand if m not in occupied and 0 <= m[0] < N and 0 <= m[1] < N]
    return cand if cand else empties


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me = list(me)
    opp = list(opp)

    occupied = set(me) | set(opp)
    empties = _all_empty(me, opp)

    # Absolute fallback; should only occur on a full board.
    if not empties:
        return (0, 0)

    # Strong opening move.
    if not me and not opp:
        return (5, 5)

    candidates = _candidate_moves(me, opp)

    # 1. Immediate win.
    for mv in candidates:
        new_me = me + [mv]
        if _shortest_cost(new_me, opp, color) == 0:
            return mv

    # 2. Immediate block of opponent win.
    opp_color = _other(color)
    for mv in empties:
        new_opp = opp + [mv]
        if _shortest_cost(new_opp, me, opp_color) == 0:
            return mv

    # 3. Static ranking of our candidate moves.
    ranked = []
    for mv in candidates:
        new_me = me + [mv]
        sc = _static_score(new_me, opp, color, mv)
        ranked.append((sc, mv))

    ranked.sort(key=lambda x: (x[0], x[1][0], x[1][1]))

    # Search only the most promising moves to stay safely under time.
    top_my = ranked[:18]

    best_move = top_my[0][1]
    best_value = float("inf")

    for base_score, mv in top_my:
        new_me = me + [mv]
        new_occ = occupied | {mv}
        remaining = [e for e in empties if e != mv]

        # If move creates a completed path, take it.
        if _shortest_cost(new_me, opp, color) == 0:
            return mv

        # Rank likely opponent replies.
        opp_replies = []
        for omv in remaining:
            new_opp = opp + [omv]
            # From opponent's perspective lower is better for opponent.
            oscore = _static_score(new_opp, new_me, opp_color, omv)
            opp_replies.append((oscore, omv))

        opp_replies.sort(key=lambda x: (x[0], x[1][0], x[1][1]))
        opp_replies = opp_replies[:10]

        # Worst case after opponent reply.
        worst = -float("inf")
        if not opp_replies:
            worst = _static_score(new_me, opp, color, mv)
        else:
            for _, omv in opp_replies:
                after_opp = opp + [omv]
                val = _static_score(new_me, after_opp, color, mv)

                # Penalize allowing opponent to win immediately.
                if _shortest_cost(after_opp, new_me, opp_color) == 0:
                    val += 1000

                if val > worst:
                    worst = val

        # Blend static and minimax result.
        final_value = 0.35 * base_score + 0.65 * worst

        if final_value < best_value:
            best_value = final_value
            best_move = mv

    # Final legality guard.
    if best_move in occupied or not (0 <= best_move[0] < N and 0 <= best_move[1] < N):
        return empties[0]

    return best_move
