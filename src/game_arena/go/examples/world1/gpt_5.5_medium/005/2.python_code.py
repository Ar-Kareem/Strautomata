
from collections import deque

N = 19
EMPTY = 0
ME = 1
OPP = -1


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[EMPTY for _ in range(N)] for _ in range(N)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = OPP

    move_count = len(me) + len(opponent)

    own_groups, own_gid = _groups(board, ME)
    opp_groups, opp_gid = _groups(board, OPP)

    if move_count == 0:
        return (4, 4)

    candidates = _candidate_moves(board, own_groups, opp_groups, move_count)

    # Add urgent liberties explicitly.
    for g in own_groups:
        if len(g["libs"]) <= 2:
            candidates.update(g["libs"])
    for g in opp_groups:
        if len(g["libs"]) <= 2:
            candidates.update(g["libs"])

    # Immediate tactical priorities: save large groups and capture groups in atari.
    tactical_best = None
    tactical_score = -10**18

    for g in own_groups:
        if len(g["libs"]) == 1:
            mv = next(iter(g["libs"]))
            sim = _simulate(board, mv, opp_groups, opp_gid)
            if sim is not None:
                _, captured, own_size, own_libs, koish = sim
                if not koish:
                    sc = 52000 + 3500 * len(g["stones"]) + 1200 * captured + 40 * own_libs
                    if sc > tactical_score:
                        tactical_score = sc
                        tactical_best = mv

    for g in opp_groups:
        if len(g["libs"]) == 1:
            mv = next(iter(g["libs"]))
            sim = _simulate(board, mv, opp_groups, opp_gid)
            if sim is not None:
                _, captured, own_size, own_libs, koish = sim
                if not koish:
                    sc = 50000 + 3200 * len(g["stones"]) + 50 * own_libs
                    if sc > tactical_score:
                        tactical_score = sc
                        tactical_best = mv

    if tactical_best is not None:
        return (tactical_best[0] + 1, tactical_best[1] + 1)

    best_move = None
    best_score = -10**18

    for mv in candidates:
        r, c = mv
        if not (0 <= r < N and 0 <= c < N) or board[r][c] != EMPTY:
            continue
        sim = _simulate(board, mv, opp_groups, opp_gid)
        if sim is None:
            continue
        score = _score_move(
            board,
            mv,
            sim,
            own_groups,
            own_gid,
            opp_groups,
            opp_gid,
            move_count,
        )
        # Deterministic tiny tie-breaker.
        score += ((r * 37 + c * 17) % 19) * 0.001
        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # Safe fallback: prefer legal moves that are not obvious simple-ko recaptures.
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                sim = _simulate(board, (r, c), opp_groups, opp_gid)
                if sim is not None and not sim[4]:
                    return (r + 1, c + 1)

    # Last fallback: any legal move.
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                sim = _simulate(board, (r, c), opp_groups, opp_gid)
                if sim is not None:
                    return (r + 1, c + 1)

    return (0, 0)


def _neighbors(r, c):
    if r > 0:
        yield r - 1, c
    if r + 1 < N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < N:
        yield r, c + 1


def _groups(board, color):
    visited = set()
    groups = []
    gid = {}

    for r in range(N):
        for c in range(N):
            if board[r][c] != color or (r, c) in visited:
                continue

            q = deque([(r, c)])
            visited.add((r, c))
            stones = set()
            libs = set()

            while q:
                x, y = q.popleft()
                stones.add((x, y))
                for nx, ny in _neighbors(x, y):
                    if board[nx][ny] == EMPTY:
                        libs.add((nx, ny))
                    elif board[nx][ny] == color and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        q.append((nx, ny))

            idx = len(groups)
            for s in stones:
                gid[s] = idx
            groups.append({"stones": stones, "libs": libs})

    return groups, gid


def _collect_group(board, r, c):
    color = board[r][c]
    q = deque([(r, c)])
    visited = {(r, c)}
    stones = set()
    libs = set()

    while q:
        x, y = q.popleft()
        stones.add((x, y))
        for nx, ny in _neighbors(x, y):
            if board[nx][ny] == EMPTY:
                libs.add((nx, ny))
            elif board[nx][ny] == color and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))

    return stones, libs


def _simulate(board, mv, opp_groups, opp_gid):
    r, c = mv
    if not (0 <= r < N and 0 <= c < N) or board[r][c] != EMPTY:
        return None

    temp = [row[:] for row in board]
    temp[r][c] = ME

    captured_gids = set()
    captured_count = 0

    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == OPP:
            gidx = opp_gid.get((nr, nc))
            if gidx is not None and gidx not in captured_gids:
                g = opp_groups[gidx]
                if len(g["libs"]) == 1 and mv in g["libs"]:
                    captured_gids.add(gidx)

    for gidx in captured_gids:
        for sr, sc in opp_groups[gidx]["stones"]:
            temp[sr][sc] = EMPTY
            captured_count += 1

    own_stones, own_libs = _collect_group(temp, r, c)

    if len(own_libs) == 0:
        return None

    # A likely simple-ko recapture shape: one stone captured, played stone alone,
    # and the resulting group has exactly one liberty.
    koish = captured_count == 1 and len(own_stones) == 1 and len(own_libs) == 1

    return temp, captured_count, len(own_stones), len(own_libs), koish


def _candidate_moves(board, own_groups, opp_groups, move_count):
    candidates = set()

    opening = [
        (3, 3), (3, 15), (15, 3), (15, 15),
        (3, 9), (9, 3), (9, 15), (15, 9),
        (9, 9),
        (2, 3), (3, 2), (2, 15), (3, 16),
        (15, 2), (16, 3), (15, 16), (16, 15),
        (2, 2), (2, 16), (16, 2), (16, 16),
    ]

    for p in opening:
        if board[p[0]][p[1]] == EMPTY:
            candidates.add(p)

    stones = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                stones.append((r, c))

    if not stones:
        return candidates

    # Local fighting candidates around stones.
    radius = 2
    for r, c in stones:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if abs(dr) + abs(dc) > 3:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == EMPTY:
                    candidates.add((nr, nc))

    # Include all liberties of weak groups.
    for g in own_groups:
        if len(g["libs"]) <= 4:
            candidates.update(g["libs"])
    for g in opp_groups:
        if len(g["libs"]) <= 4:
            candidates.update(g["libs"])

    # If the board is still open, keep more strategic points available.
    if move_count < 80:
        for p in opening:
            if board[p[0]][p[1]] == EMPTY:
                candidates.add(p)

    return candidates


def _score_move(board, mv, sim, own_groups, own_gid, opp_groups, opp_gid, move_count):
    r, c = mv
    temp, captured, own_size_after, own_libs_after, koish = sim

    score = 0.0

    if koish:
        score -= 9000

    # Capture value.
    if captured:
        score += 1200 * captured + 200
        if captured >= 3:
            score += 500

    own_adj = set()
    opp_adj = set()

    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == ME:
            gidx = own_gid.get((nr, nc))
            if gidx is not None:
                own_adj.add(gidx)
        elif board[nr][nc] == OPP:
            gidx = opp_gid.get((nr, nc))
            if gidx is not None:
                opp_adj.add(gidx)

    # Save and connect friendly groups.
    connected_size = 0
    weak_save = 0
    for gidx in own_adj:
        g = own_groups[gidx]
        connected_size += len(g["stones"])
        if mv in g["libs"]:
            if len(g["libs"]) == 1:
                weak_save += len(g["stones"])
                score += 950 + 150 * len(g["stones"])
            elif len(g["libs"]) == 2:
                score += 180 + 35 * len(g["stones"])

    if len(own_adj) >= 2:
        score += 260 + 90 * len(own_adj) + 18 * min(connected_size, 20)

    # Attack adjacent opponent groups.
    for gidx in opp_adj:
        g = opp_groups[gidx]
        if mv in g["libs"]:
            if len(g["libs"]) == 1:
                score += 1500 + 260 * len(g["stones"])
            elif len(g["libs"]) == 2:
                score += 700 + 95 * len(g["stones"])
            elif len(g["libs"]) == 3:
                score += 170 + 25 * len(g["stones"])

    # Liberty and shape evaluation.
    score += 42 * min(own_libs_after, 10)
    if own_libs_after == 1:
        score -= 850
        if captured:
            score += 300
    elif own_libs_after == 2:
        score -= 160
    elif own_libs_after >= 5:
        score += 80

    if own_size_after >= 3:
        score += 20 * min(own_size_after, 12)

    # Avoid filling own eyes unless capturing.
    own_or_edge = 0
    empty_orth = 0
    opp_orth = 0
    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if not (0 <= nr < N and 0 <= nc < N):
            own_or_edge += 1
        elif board[nr][nc] == ME:
            own_or_edge += 1
        elif board[nr][nc] == EMPTY:
            empty_orth += 1
        else:
            opp_orth += 1

    if captured == 0 and own_or_edge >= 4:
        score -= 1000
    elif captured == 0 and own_or_edge == 3 and empty_orth == 1:
        score -= 250

    # Diagonal eye-shape penalty.
    diag_own_edge = 0
    for nr, nc in ((r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)):
        if not (0 <= nr < N and 0 <= nc < N):
            diag_own_edge += 1
        elif board[nr][nc] == ME:
            diag_own_edge += 1
    if captured == 0 and own_or_edge >= 3 and diag_own_edge >= 3:
        score -= 300

    # Positional opening/middlegame heuristics.
    edge_dist = min(r, c, N - 1 - r, N - 1 - c) + 1

    if move_count < 80:
        if edge_dist == 4:
            score += 60
        elif edge_dist == 3:
            score += 40
        elif edge_dist == 2:
            score -= 15
        elif edge_dist == 1:
            score -= 90
    else:
        if edge_dist == 1:
            score -= 25

    # Star points and good opening points.
    rb, cb = r + 1, c + 1
    star_points = {
        (4, 4), (4, 10), (4, 16),
        (10, 4), (10, 10), (10, 16),
        (16, 4), (16, 10), (16, 16),
    }
    corner_34 = {
        (3, 4), (4, 3), (3, 16), (4, 17),
        (16, 3), (17, 4), (16, 17), (17, 16),
    }
    corner_33 = {(3, 3), (3, 17), (17, 3), (17, 17)}

    if move_count < 40:
        if (rb, cb) in star_points:
            score += 240
        elif (rb, cb) in corner_34:
            score += 190
        elif (rb, cb) in corner_33:
            score += 120
    elif move_count < 100:
        if (rb, cb) in star_points:
            score += 70

    # Prefer not to play too close to existing stones in the very early opening
    # unless there is a tactical reason.
    min_dist = 99
    own_near = 0
    opp_near = 0
    for x in range(max(0, r - 2), min(N, r + 3)):
        for y in range(max(0, c - 2), min(N, c + 3)):
            if board[x][y] != EMPTY:
                d = abs(x - r) + abs(y - c)
                if d < min_dist:
                    min_dist = d
                if board[x][y] == ME:
                    own_near += 1
                else:
                    opp_near += 1

    if move_count < 30 and captured == 0 and weak_save == 0:
        if min_dist <= 1:
            score -= 80
        elif min_dist >= 6:
            score += 40

    score += 7 * own_near + 5 * opp_near

    # Center influence is mildly useful, but corners/sides matter more early.
    center_dist = abs(r - 9) + abs(c - 9)
    score += max(0, 18 - center_dist) * 1.5

    # Contact move caution: touching opponent with few liberties is dangerous.
    if opp_orth > 0 and own_libs_after <= 2 and captured == 0:
        score -= 220

    return score
