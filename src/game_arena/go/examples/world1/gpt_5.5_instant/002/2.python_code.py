
from collections import deque

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

# Good 19x19 opening / framework points.
OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (4, 17), (16, 3), (17, 4), (16, 17), (17, 16),
    (3, 10), (10, 3), (10, 17), (17, 10)
]

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    my = set(me)
    opp = set(opponent)
    occupied = my | opp

    def inb(p):
        r, c = p
        return 1 <= r <= N and 1 <= c <= N

    def neigh(p):
        r, c = p
        for dr, dc in DIRS:
            q = (r + dr, c + dc)
            if 1 <= q[0] <= N and 1 <= q[1] <= N:
                yield q

    def group_and_libs(start, stones, blockers):
        # blockers are the opponent stones; empty intersections are liberties.
        seen = {start}
        group = {start}
        libs = set()
        dq = deque([start])
        while dq:
            p = dq.popleft()
            for q in neigh(p):
                if q in stones and q not in seen:
                    seen.add(q)
                    group.add(q)
                    dq.append(q)
                elif q not in blockers and q not in stones:
                    libs.add(q)
        return group, libs

    # Cache current groups.
    my_group_cache = {}
    opp_group_cache = {}

    def get_group(p, stones, blockers, cache):
        if p in cache:
            return cache[p]
        g, l = group_and_libs(p, stones, blockers)
        result = (g, l)
        for x in g:
            cache[x] = result
        return result

    # Basic legality with capture/suicide handling. Ko is not provided in state, so cannot be enforced.
    def legal(move):
        if move == (0, 0):
            return True
        if not inb(move) or move in occupied:
            return False

        # If it has an empty neighbor, legal unless impossible? Empty adjacent guarantees at least one liberty.
        for q in neigh(move):
            if q not in occupied:
                return True

        # Capturing any adjacent opponent group in atari is legal.
        for q in neigh(move):
            if q in opp:
                g, libs = get_group(q, opp, my, opp_group_cache)
                if libs == {move}:
                    return True

        # Connecting to one of our groups with another liberty is legal.
        for q in neigh(move):
            if q in my:
                g, libs = get_group(q, my, opp, my_group_cache)
                if len(libs - {move}) > 0:
                    return True

        return False

    def liberties_after(move):
        # Returns own new group's liberties count and captured stones count after playing move.
        new_my = set(my)
        new_opp = set(opp)
        new_my.add(move)
        captured = 0
        for q in list(neigh(move)):
            if q in new_opp:
                g, libs = group_and_libs(q, new_opp, new_my)
                if not libs:
                    captured += len(g)
                    new_opp.difference_update(g)
        g, libs = group_and_libs(move, new_my, new_opp)
        return len(libs), captured

    # Candidate generation: tactical liberties, neighbors of stones, and opening points.
    cand = set()
    for p in occupied:
        for q in neigh(p):
            if q not in occupied:
                cand.add(q)
            for q in neigh(p):
                for x in neigh(q):
                    if x not in occupied:
                        cand.add(x)

    for p in OPENING_POINTS:
        if p not in occupied:
            cand.add(p)

    # If board sparse, add star point vicinity.
    if len(occupied) < 40:
        for r in (4, 10, 16):
            for c in (4, 10, 16):
                if (r, c) not in occupied:
                    cand.add((r, c))

    # Include all liberties of groups in atari for captures/saves.
    for p in list(opp):
        g, libs = get_group(p, opp, my, opp_group_cache)
        if len(libs) <= 2:
            cand.update(libs)
    for p in list(my):
        g, libs = get_group(p, my, opp, my_group_cache)
        if len(libs) <= 2:
            cand.update(libs)

    legal_cands = [p for p in cand if legal(p)]
    if not legal_cands:
        # Absolute fallback: scan full board.
        for r in range(1, N + 1):
            for c in range(1, N + 1):
                p = (r, c)
                if legal(p):
                    return p
        return (0, 0)

    # Strong tactical priority 1: capture largest adjacent atari group.
    best_cap = None
    best_cap_score = -1
    for m in legal_cands:
        cap = 0
        for q in neigh(m):
            if q in opp:
                g, libs = get_group(q, opp, my, opp_group_cache)
                if libs == {m}:
                    cap += len(g)
        if cap > best_cap_score:
            best_cap_score = cap
            best_cap = m
    if best_cap_score >= 2:
        return best_cap

    # Tactical priority 2: save largest own group in atari, if possible.
    best_save = None
    best_save_score = -1
    for p in my:
        g, libs = get_group(p, my, opp, my_group_cache)
        if len(libs) == 1:
            lib = next(iter(libs))
            if lib in legal_cands:
                after_libs, cap = liberties_after(lib)
                score = len(g) * 10 + after_libs + cap * 15
                if after_libs >= 2 or cap > 0:
                    if score > best_save_score:
                        best_save_score = score
                        best_save = lib
    if best_save is not None:
        return best_save

    def edge_penalty(p):
        r, c = p
        d = min(r, c, N + 1 - r, N + 1 - c)
        if d == 1:
            return -7
        if d == 2:
            return -2
        if d in (3, 4):
            return 2
        return 0

    def pos_value(p):
        r, c = p
        # Prefer corners/sides early, balanced center later.
        total = len(occupied)
        val = 0
        # 4-4 / 3-4 style points
        for sr in (4, 16):
            for sc in (4, 16):
                dist = abs(r - sr) + abs(c - sc)
                val += max(0, 8 - dist)
        if total > 80:
            val += max(0, 10 - (abs(r - 10) + abs(c - 10))) * 0.7
        else:
            val += max(0, 6 - (abs(r - 10) + abs(c - 10))) * 0.25
        val += edge_penalty(p)
        return val

    def score_move(m):
        score = pos_value(m)
        after_libs, captured = liberties_after(m)
        score += captured * 25
        score += min(after_libs, 8) * 2.2

        adj_my = 0
        adj_opp = 0
        empty_adj = 0

        for q in neigh(m):
            if q in my:
                adj_my += 1
                g, libs = get_group(q, my, opp, my_group_cache)
                # Help weak groups.
                if len(libs) <= 2:
                    score += 10 + len(g) * 0.8
                else:
                    score += 2
            elif q in opp:
                adj_opp += 1
                g, libs = get_group(q, opp, my, opp_group_cache)
                # Attack weak groups.
                if len(libs) <= 2:
                    score += 12 + len(g) * 1.0
                else:
                    score += 3
            else:
                empty_adj += 1

        score += adj_my * 1.5 + adj_opp * 2.0 + empty_adj * 0.8

        # Avoid self-atari unless capturing.
        if after_libs <= 1 and captured == 0:
            score -= 35
        elif after_libs == 2 and captured == 0:
            score -= 5

        # Avoid playing inside very surrounded opponent territory without gain.
        my_near = 0
        opp_near = 0
        r, c = m
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) + abs(dc) > 2:
                    continue
                q = (r + dr, c + dc)
                if not inb(q):
                    continue
                if q in my:
                    my_near += 1
                elif q in opp:
                    opp_near += 1
        score += my_near * 0.7
        score += opp_near * 0.45
        if opp_near >= 5 and my_near == 0 and captured == 0:
            score -= 12

        # Small deterministic tie-breaker favoring upper-left less predictably via arithmetic hash.
        score += ((m[0] * 37 + m[1] * 17) % 13) * 0.01
        return score

    best = max(legal_cands, key=score_move)

    # If best is a single-stone capture, still usually good.
    if legal(best):
        return best

    # Final safety fallback.
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            p = (r, c)
            if legal(p):
                return p
    return (0, 0)
