
from heapq import heappush, heappop

N = 11
INF = 10 ** 9

# Hex neighbors for the coordinate system described in the prompt.
DIRS = [
    (0, -1), (0, 1),
    (-1, 0), (-1, 1),
    (1, -1), (1, 0),
]

CENTER = (N - 1) / 2.0


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _other_color(color):
    return "w" if color == "b" else "b"


def _connection_distance(stones, blockers, color):
    """
    Minimum number of empty cells still needed to connect the relevant sides.
    Own stones cost 0, empty cells cost 1, opponent stones are impassable.
    """
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == "b":
        # Connect top to bottom.
        for c in range(N):
            cell = (0, c)
            if cell in blockers:
                continue
            cost = 0 if cell in stones else 1
            dist[0][c] = cost
            heappush(pq, (cost, 0, c))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in blockers:
                    continue
                nd = d + (0 if (nr, nc) in stones else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    else:
        # Connect left to right.
        for r in range(N):
            cell = (r, 0)
            if cell in blockers:
                continue
            cost = 0 if cell in stones else 1
            dist[r][0] = cost
            heappush(pq, (cost, r, 0))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in blockers:
                    continue
                nd = d + (0 if (nr, nc) in stones else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    return INF


def _has_won(stones, color):
    """Exact connectivity win check."""
    if not stones:
        return False

    seen = set()
    stack = []

    if color == "b":
        for c in range(N):
            if (0, c) in stones:
                stack.append((0, c))
                seen.add((0, c))

        while stack:
            r, c = stack.pop()
            if r == N - 1:
                return True
            for nb in _neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    else:
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))

        while stack:
            r, c = stack.pop()
            if c == N - 1:
                return True
            for nb in _neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    return False


def _center_bonus(move):
    r, c = move
    return -0.035 * ((r - CENTER) ** 2 + (c - CENTER) ** 2)


def _local_bonus(move, own, opp):
    """
    Small positional bonus.
    Encourages friendly contact and mild blocking/contact with opponent.
    """
    r, c = move
    own_adj = 0
    opp_adj = 0
    empty_adj = 0

    for nb in _neighbors(r, c):
        if nb in own:
            own_adj += 1
        elif nb in opp:
            opp_adj += 1
        else:
            empty_adj += 1

    return 0.18 * own_adj + 0.11 * opp_adj + 0.015 * empty_adj


def _static_score(move, my_stones, opp_stones, my_color):
    """
    Higher is better for the player whose stones are my_stones.
    """
    opp_color = _other_color(my_color)

    new_my = set(my_stones)
    new_my.add(move)

    # Immediate win is overwhelmingly best.
    if _has_won(new_my, my_color):
        return 1_000_000.0

    my_d = _connection_distance(new_my, opp_stones, my_color)
    opp_d = _connection_distance(opp_stones, new_my, opp_color)

    # We value our own progress slightly more than blocking,
    # but both are important in Hex.
    score = 7.0 * opp_d - 9.0 * my_d
    score += _local_bonus(move, my_stones, opp_stones)
    score += _center_bonus(move)

    return score


def _all_empty(my_stones, opp_stones):
    occupied = my_stones | opp_stones
    return [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]


def _ordered_moves(my_stones, opp_stones, my_color):
    empties = _all_empty(my_stones, opp_stones)
    scored = [(_static_score(m, my_stones, opp_stones, my_color), m) for m in empties]
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_stones = set(me)
    opp_stones = set(opp)
    occupied = my_stones | opp_stones

    # Absolute safety fallback.
    fallback = None
    for r in range(N):
        for c in range(N):
            if (r, c) not in occupied:
                fallback = (r, c)
                break
        if fallback is not None:
            break

    if fallback is None:
        # Board should never be full when called, but keep API safe.
        return (0, 0)

    empties_count = N * N - len(occupied)

    # Opening preference: central Hex moves are generally strong.
    if not me and not opp:
        return (5, 5)

    if len(occupied) <= 2:
        opening_choices = [(5, 5), (5, 4), (4, 5), (6, 5), (5, 6), (4, 6), (6, 4)]
        for m in opening_choices:
            if m not in occupied:
                return m

    scored = _ordered_moves(my_stones, opp_stones, color)
    if not scored:
        return fallback

    # If we have an immediate winning move, play it.
    best_score, best_move = scored[0]
    if best_score >= 999_999:
        return best_move

    opp_color = _other_color(color)

    # Also check whether opponent has an immediate win threat.
    # If so, blocking it is usually mandatory.
    opp_scored = _ordered_moves(opp_stones, my_stones, opp_color)
    if opp_scored and opp_scored[0][0] >= 999_999:
        forced_block = opp_scored[0][1]
        if forced_block not in occupied:
            return forced_block

    # Limited two-ply search.
    # We examine the best candidate moves and assume opponent replies strongly.
    if empties_count > 80:
        my_limit = 18
        opp_limit = 8
    elif empties_count > 40:
        my_limit = 24
        opp_limit = 10
    else:
        my_limit = 32
        opp_limit = 14

    candidates = [m for _, m in scored[:my_limit]]

    best_final_score = -10 ** 18
    best_final_move = candidates[0]

    for move in candidates:
        new_my = set(my_stones)
        new_my.add(move)

        if _has_won(new_my, color):
            return move

        remaining_after_my = _all_empty(new_my, opp_stones)

        if not remaining_after_my:
            final_score = _static_score(move, my_stones, opp_stones, color)
            if final_score > best_final_score:
                best_final_score = final_score
                best_final_move = move
            continue

        # Get opponent's most dangerous replies.
        opp_replies_scored = []
        for om in remaining_after_my:
            s = _static_score(om, opp_stones, new_my, opp_color)
            opp_replies_scored.append((s, om))
        opp_replies_scored.sort(reverse=True, key=lambda x: x[0])
        opp_replies = [m for _, m in opp_replies_scored[:opp_limit]]

        worst_score = 10 ** 18

        for om in opp_replies:
            new_opp = set(opp_stones)
            new_opp.add(om)

            if _has_won(new_opp, opp_color):
                position_score = -1_000_000.0
            else:
                my_d = _connection_distance(new_my, new_opp, color)
                opp_d = _connection_distance(new_opp, new_my, opp_color)
                position_score = 7.0 * opp_d - 9.0 * my_d
                position_score += _local_bonus(move, my_stones, opp_stones)
                position_score += _center_bonus(move)

            if position_score < worst_score:
                worst_score = position_score

        # Slightly mix in the static value so proactive threats are not ignored.
        final_score = worst_score + 0.18 * _static_score(move, my_stones, opp_stones, color)

        if final_score > best_final_score:
            best_final_score = final_score
            best_final_move = move

    if best_final_move not in occupied and _inside(*best_final_move):
        return best_final_move

    return fallback
