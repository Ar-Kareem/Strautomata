
from collections import deque

BOARD_SIZE = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    N = BOARD_SIZE

    board = [[0 for _ in range(N)] for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2

    def neighbors(r, c):
        if r > 0:
            yield r - 1, c
        if r < N - 1:
            yield r + 1, c
        if c > 0:
            yield r, c - 1
        if c < N - 1:
            yield r, c + 1

    def diagonals(r, c):
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                yield nr, nc

    def group_and_liberties(b, r, c):
        color = b[r][c]
        if color == 0:
            return set(), set()

        group = set()
        liberties = set()
        q = deque([(r, c)])
        group.add((r, c))

        while q:
            x, y = q.popleft()
            for nx, ny in neighbors(x, y):
                v = b[nx][ny]
                if v == 0:
                    liberties.add((nx, ny))
                elif v == color and (nx, ny) not in group:
                    group.add((nx, ny))
                    q.append((nx, ny))

        return group, liberties

    def play_move(b, r, c):
        if b[r][c] != 0:
            return None, 0

        nb = [row[:] for row in b]
        nb[r][c] = 1
        captured = 0

        checked = set()
        for nr, nc in neighbors(r, c):
            if nb[nr][nc] == 2 and (nr, nc) not in checked:
                g, libs = group_and_liberties(nb, nr, nc)
                checked |= g
                if not libs:
                    captured += len(g)
                    for x, y in g:
                        nb[x][y] = 0

        own_group, own_libs = group_and_liberties(nb, r, c)
        if not own_libs:
            return None, 0

        return nb, captured

    def is_legal(r, c):
        nb, _ = play_move(board, r, c)
        return nb is not None

    total_stones = len(me) + len(opponent)

    # Precompute nearby group info for speed.
    own_group_cache = {}
    opp_group_cache = {}

    def cached_group(color, r, c):
        cache = own_group_cache if color == 1 else opp_group_cache
        if (r, c) in cache:
            return cache[(r, c)]
        g, libs = group_and_liberties(board, r, c)
        result = (g, libs)
        for p in g:
            cache[p] = result
        return result

    star_points = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
    ]

    corner_44 = [(3, 3), (3, 15), (15, 3), (15, 15)]
    corner_33 = [(2, 2), (2, 16), (16, 2), (16, 16)]
    side_extensions = [(3, 9), (9, 3), (9, 15), (15, 9)]

    def positional_score(r, c):
        score = 0.0

        # Opening: prefer star points and balanced development.
        if total_stones < 40:
            for sr, sc in corner_44:
                d = abs(r - sr) + abs(c - sc)
                score += max(0, 18 - 4 * d)

            for sr, sc in corner_33:
                d = abs(r - sr) + abs(c - sc)
                score += max(0, 8 - 2 * d)

            for sr, sc in side_extensions:
                d = abs(r - sr) + abs(c - sc)
                score += max(0, 9 - 2 * d)

        # General board preference: not too close to edge, but corners/sides matter.
        edge_dist = min(r, c, N - 1 - r, N - 1 - c)
        if edge_dist == 0:
            score -= 4
        elif edge_dist == 1:
            score += 0
        elif edge_dist == 2:
            score += 5
        elif edge_dist == 3:
            score += 4
        else:
            score += 1

        # Mild central influence.
        center_dist = abs(r - 9) + abs(c - 9)
        score += max(0, 8 - center_dist) * 0.25

        return score

    def eye_fill_penalty(r, c):
        # Penalize filling a likely own eye unless it captures.
        friendly_or_edge = 0
        total_adj = 0
        for nr, nc in neighbors(r, c):
            total_adj += 1
            if board[nr][nc] == 1:
                friendly_or_edge += 1

        edge_count = 4 - total_adj
        friendly_or_edge += edge_count

        if friendly_or_edge < 4:
            return 0

        good_diag = 0
        bad_diag = 0
        for nr, nc in diagonals(r, c):
            if board[nr][nc] == 1:
                good_diag += 1
            elif board[nr][nc] == 2:
                bad_diag += 1

        if bad_diag == 0 and good_diag >= 2:
            return -80
        if bad_diag <= 1 and good_diag >= 2:
            return -35
        return 0

    def score_move(r, c):
        nb, captured = play_move(board, r, c)
        if nb is None:
            return None

        score = 0.0

        # Captures are very valuable.
        if captured:
            score += 120 * captured
            if captured >= 3:
                score += 80

        # Own resulting liberties.
        own_after, libs_after = group_and_liberties(nb, r, c)
        score += min(len(libs_after), 8) * 7
        score += min(len(own_after), 10) * 1.5

        # Save friendly groups in atari or connect weak stones.
        adjacent_own_groups = set()
        adjacent_opp_groups = set()

        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 1:
                g, libs = cached_group(1, nr, nc)
                key = next(iter(g))
                if key not in adjacent_own_groups:
                    adjacent_own_groups.add(key)
                    if len(libs) == 1 and (r, c) in libs:
                        score += 90 + 18 * len(g)
                    elif len(libs) == 2 and (r, c) in libs:
                        score += 25 + 5 * len(g)
                    else:
                        score += 8 + min(len(g), 6)

            elif board[nr][nc] == 2:
                g, libs = cached_group(2, nr, nc)
                key = next(iter(g))
                if key not in adjacent_opp_groups:
                    adjacent_opp_groups.add(key)
                    if len(libs) == 1 and (r, c) in libs:
                        score += 100 + 25 * len(g)
                    elif len(libs) == 2 and (r, c) in libs:
                        score += 55 + 10 * len(g)
                    elif len(libs) == 3 and (r, c) in libs:
                        score += 18 + 3 * len(g)
                    else:
                        score += 4

        # Connections between multiple own groups are useful.
        if len(adjacent_own_groups) >= 2:
            score += 35 * (len(adjacent_own_groups) - 1)

        # Cutting between multiple opponent groups can be useful.
        if len(adjacent_opp_groups) >= 2:
            score += 25 * (len(adjacent_opp_groups) - 1)

        # Local influence in radius 2.
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    dist = abs(dr) + abs(dc)
                    if dist == 0 or dist > 3:
                        continue
                    v = board[nr][nc]
                    weight = 4 - dist
                    if v == 1:
                        score += 1.5 * weight
                    elif v == 2:
                        score += 1.2 * weight

        score += positional_score(r, c)

        if captured == 0:
            score += eye_fill_penalty(r, c)

        # Avoid isolated first-line and pointless dame-like edge moves early.
        if total_stones < 120:
            if r == 0 or c == 0 or r == N - 1 or c == N - 1:
                score -= 15

        # Tiny deterministic tie-breaker.
        score += ((r + 1) * 37 + (c + 1) * 17) % 100 / 10000.0

        return score

    # Candidate generation: all legal moves is fine on 19x19, but prioritize relevant points.
    occupied = set((r - 1, c - 1) for r, c in me) | set((r - 1, c - 1) for r, c in opponent)
    candidates = set()

    if total_stones == 0:
        return (4, 4)

    # Tactical/local candidates near stones.
    for r, c in occupied:
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 4:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        candidates.add((nr, nc))

    # Add strategic points.
    for p in star_points + corner_44 + corner_33 + side_extensions:
        r, c = p
        if board[r][c] == 0:
            candidates.add((r, c))

    # If candidates are too few, include everything.
    if len(candidates) < 20:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    candidates.add((r, c))

    best_move = None
    best_score = None

    for r, c in candidates:
        s = score_move(r, c)
        if s is not None and (best_score is None or s > best_score):
            best_score = s
            best_move = (r, c)

    if best_move is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # Absolute fallback: find any legal move.
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 and is_legal(r, c):
                return (r + 1, c + 1)

    return (0, 0)
