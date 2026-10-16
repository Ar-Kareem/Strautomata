
from heapq import heappush, heappop

N = 11
INF = 10 ** 9

DIRS = [
    (0, -1), (0, 1),
    (-1, 0), (-1, 1),
    (1, 0), (1, -1),
]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my = set(me)
    op = set(opp)
    occupied = my | op

    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not empties:
        return (0, 0)

    # Very reliable opening.
    if not my and not op:
        return (5, 5)
    if not my and (5, 5) in occupied:
        for mv in [(5, 4), (4, 5), (6, 5), (5, 6), (4, 6), (6, 4)]:
            if mv not in occupied:
                return mv

    opp_color = "w" if color == "b" else "b"

    # 1. Win immediately if possible.
    for mv in ordered_tactical_moves(my, op, color, limit=40):
        if mv in occupied:
            continue
        nm = set(my)
        nm.add(mv)
        if has_connection(nm, color):
            return mv

    # 2. Block opponent's immediate win.
    winning_blocks = []
    for mv in ordered_tactical_moves(op, my, opp_color, limit=50):
        if mv in occupied:
            continue
        no = set(op)
        no.add(mv)
        if has_connection(no, opp_color):
            winning_blocks.append(mv)

    if winning_blocks:
        # If several blocks exist, choose the one best for our own game too.
        best = None
        best_score = -INF
        for mv in winning_blocks:
            score = evaluate_after_move(my, op, color, mv)
            if score > best_score:
                best_score = score
                best = mv
        if best is not None:
            return best

    # 3. Candidate generation and shallow minimax.
    candidates = ordered_tactical_moves(my, op, color, limit=18)
    if not candidates:
        return empties[0]

    best_move = None
    best_score = -INF

    for mv in candidates:
        if mv in occupied:
            continue

        nm = set(my)
        nm.add(mv)

        # Strongly prefer actual win.
        if has_connection(nm, color):
            return mv

        # Opponent replies.
        reply_candidates = ordered_tactical_moves(op, nm, opp_color, limit=10)

        worst_score = INF
        if not reply_candidates:
            worst_score = evaluate_position(nm, op, color)
        else:
            for reply in reply_candidates:
                if reply in nm or reply in op:
                    continue
                nop = set(op)
                nop.add(reply)

                # Avoid allowing immediate loss.
                if has_connection(nop, opp_color):
                    score = -100000
                else:
                    score = evaluate_position(nm, nop, color)

                if score < worst_score:
                    worst_score = score

        # Small direct move quality bonus stabilizes choices.
        worst_score += 0.15 * local_shape_bonus(mv, my, op, color)

        if worst_score > best_score:
            best_score = worst_score
            best_move = mv

    if best_move is not None and best_move not in occupied:
        return best_move

    # Absolute legal fallback.
    center_sorted = sorted(
        empties,
        key=lambda x: abs(x[0] - 5) + abs(x[1] - 5)
    )
    return center_sorted[0]


def neighbors(cell):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield (nr, nc)


def has_connection(stones, color):
    if not stones:
        return False

    stack = []
    seen = set()

    if color == "b":
        for c in range(N):
            p = (0, c)
            if p in stones:
                stack.append(p)
                seen.add(p)

        while stack:
            p = stack.pop()
            if p[0] == N - 1:
                return True
            for q in neighbors(p):
                if q in stones and q not in seen:
                    seen.add(q)
                    stack.append(q)

    else:
        for r in range(N):
            p = (r, 0)
            if p in stones:
                stack.append(p)
                seen.add(p)

        while stack:
            p = stack.pop()
            if p[1] == N - 1:
                return True
            for q in neighbors(p):
                if q in stones and q not in seen:
                    seen.add(q)
                    stack.append(q)

    return False


def connection_distance(stones, enemy, color):
    """
    Dijkstra distance from one target side to the other.
    Own stones cost 0, empty cells cost 1, enemy stones are blocked.
    """
    dist = [[INF] * N for _ in range(N)]
    heap = []

    if color == "b":
        for c in range(N):
            p = (0, c)
            if p in enemy:
                continue
            cost = 0 if p in stones else 1
            dist[0][c] = cost
            heappush(heap, (cost, 0, c))

        while heap:
            d, r, c = heappop(heap)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                return d
            for nr, nc in neighbors((r, c)):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in stones else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(heap, (nd, nr, nc))

    else:
        for r in range(N):
            p = (r, 0)
            if p in enemy:
                continue
            cost = 0 if p in stones else 1
            dist[r][0] = cost
            heappush(heap, (cost, r, 0))

        while heap:
            d, r, c = heappop(heap)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                return d
            for nr, nc in neighbors((r, c)):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in stones else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(heap, (nd, nr, nc))

    return INF


def evaluate_position(my, op, color):
    opp_color = "w" if color == "b" else "b"

    if has_connection(my, color):
        return 100000
    if has_connection(op, opp_color):
        return -100000

    my_d = connection_distance(my, op, color)
    op_d = connection_distance(op, my, opp_color)

    # Main Hex objective: reduce our connection distance and increase theirs.
    score = 12.0 * (op_d - my_d)

    # Add soft positional features.
    score += stone_activity(my, op, color)
    score -= 0.8 * stone_activity(op, my, opp_color)

    return score


def evaluate_after_move(my, op, color, mv):
    nm = set(my)
    nm.add(mv)
    return evaluate_position(nm, op, color) + local_shape_bonus(mv, my, op, color)


def ordered_tactical_moves(my, op, color, limit=20):
    occupied = my | op
    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    if not empties:
        return []

    if len(occupied) <= 2:
        return sorted(empties, key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))[:limit]

    cand = set()

    # Prefer moves near existing stones.
    for s in occupied:
        for nb in neighbors(s):
            if nb not in occupied:
                cand.add(nb)
            for nb2 in neighbors(nb):
                if nb2 not in occupied:
                    cand.add(nb2)

    # Always include central cells as fallback candidates.
    for r in range(3, 8):
        for c in range(3, 8):
            if (r, c) not in occupied:
                cand.add((r, c))

    if not cand:
        cand = set(empties)

    scored = []
    base_my_d = connection_distance(my, op, color)
    opp_color = "w" if color == "b" else "b"
    base_op_d = connection_distance(op, my, opp_color)

    for mv in cand:
        if mv in occupied:
            continue

        nm = set(my)
        nm.add(mv)

        my_d = connection_distance(nm, op, color)
        op_d = connection_distance(op, nm, opp_color)

        score = 0.0
        score += 15.0 * (base_my_d - my_d)
        score += 9.0 * (op_d - base_op_d)
        score += 2.0 * local_shape_bonus(mv, my, op, color)
        score += 0.25 * center_bonus(mv)

        # Orientation preference: black likes vertical development, white horizontal.
        r, c = mv
        if color == "b":
            score += 0.08 * (5 - abs(c - 5))
        else:
            score += 0.08 * (5 - abs(r - 5))

        scored.append((score, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored[:limit]]


def local_shape_bonus(mv, my, op, color):
    bonus = 0.0

    own_adj = 0
    opp_adj = 0

    for nb in neighbors(mv):
        if nb in my:
            own_adj += 1
        elif nb in op:
            opp_adj += 1

    bonus += 1.8 * own_adj
    bonus += 0.9 * opp_adj

    # Connecting two or more friendly groups locally is often excellent.
    if own_adj >= 2:
        bonus += 2.0

    # Edge relevance.
    r, c = mv
    if color == "b":
        if r == 0 or r == N - 1:
            bonus += 0.8
        # Avoid hugging irrelevant side edges too much.
        if c == 0 or c == N - 1:
            bonus -= 0.2
    else:
        if c == 0 or c == N - 1:
            bonus += 0.8
        if r == 0 or r == N - 1:
            bonus -= 0.2

    bonus += 0.2 * center_bonus(mv)
    return bonus


def center_bonus(mv):
    r, c = mv
    return 10 - (abs(r - 5) + abs(c - 5))


def stone_activity(my, op, color):
    if not my:
        return 0.0

    total = 0.0
    for s in my:
        total += 0.08 * center_bonus(s)
        own_adj = 0
        for nb in neighbors(s):
            if nb in my:
                own_adj += 1
        total += 0.25 * own_adj

    return total
