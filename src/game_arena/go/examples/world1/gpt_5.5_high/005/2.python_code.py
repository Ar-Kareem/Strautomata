
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

# 1-based opening/strategic points.
OPENING_BONUS = {
    (4, 4): 40, (4, 16): 40, (16, 4): 40, (16, 16): 40,
    (4, 10): 28, (10, 4): 28, (10, 16): 28, (16, 10): 28,
    (10, 10): 16,
    (3, 4): 20, (4, 3): 20, (3, 16): 20, (4, 17): 20,
    (16, 3): 20, (17, 4): 20, (16, 17): 20, (17, 16): 20,
    (3, 3): 14, (3, 17): 14, (17, 3): 14, (17, 17): 14,
}

# Coordinates relative to a corner, e.g. (4,4) means 4-4 in that corner.
EMPTY_CORNER_PATTERNS = {
    (4, 4): 110,
    (3, 4): 92, (4, 3): 92,
    (3, 3): 78,
    (4, 5): 54, (5, 4): 54,
    (3, 5): 45, (5, 3): 45,
}

APPROACH_PATTERNS = {
    (3, 3): 48,
    (4, 6): 52, (6, 4): 52,
    (3, 6): 42, (6, 3): 42,
    (5, 6): 36, (6, 5): 36,
    (3, 5): 34, (5, 3): 34,
    (6, 6): 28,
    (4, 7): 22, (7, 4): 22,
}

ENCLOSURE_PATTERNS = {
    (3, 3): 24,
    (3, 5): 28, (5, 3): 28,
    (4, 6): 26, (6, 4): 26,
    (3, 6): 22, (6, 3): 22,
    (5, 5): 18,
}


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0 for _ in range(N)] for _ in range(N)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = -1

    groups, gid = _analyze(board)
    phase = len(me) + len(opponent)
    corner_info = _corner_info(board)
    seed = _seed_from_position(me, opponent)

    own_atari_lib = {}
    own_atari_total = 0
    for i, g in enumerate(groups):
        color, stones, libs, size = g
        if color == 1 and len(libs) == 1:
            p = next(iter(libs))
            own_atari_lib[p] = own_atari_lib.get(p, 0) + size
            own_atari_total += size

    best_move = None
    best_score = -10**18

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            feat = _move_features(board, gid, groups, r, c)
            if feat is None:
                continue

            score = _score_move(
                board, groups, r, c, feat, phase, corner_info,
                own_atari_lib, own_atari_total, seed
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # If the only available plays are severe own-eye fills / ko-risk plays, pass.
    if best_score < -3000:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)


def _on(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _analyze(board):
    gid = [[-1 for _ in range(N)] for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or gid[r][c] != -1:
                continue

            idx = len(groups)
            stack = [(r, c)]
            gid[r][c] = idx
            stones = []
            libs = set()

            while stack:
                pr, pc = stack.pop()
                stones.append((pr, pc))

                for dr, dc in DIRS:
                    nr, nc = pr + dr, pc + dc
                    if not _on(nr, nc):
                        continue
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append((color, stones, libs, len(stones)))

    return groups, gid


def _move_features(board, gid, groups, r: int, c: int):
    own_adj = set()
    opp_adj = set()
    result_libs = set()
    empty_adj = 0
    adj_own = 0
    adj_opp = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _on(nr, nc):
            continue

        v = board[nr][nc]
        if v == 0:
            empty_adj += 1
            result_libs.add((nr, nc))
        elif v == 1:
            adj_own += 1
            own_adj.add(gid[nr][nc])
        elif v == -1:
            adj_opp += 1
            opp_adj.add(gid[nr][nc])

    cap_gids = []
    cap_size = 0
    for og in opp_adj:
        color, stones, libs, size = groups[og]
        if len(libs) == 1:
            cap_gids.append(og)
            cap_size += size

    for mg in own_adj:
        result_libs.update(groups[mg][2])
    result_libs.discard((r, c))

    for og in cap_gids:
        result_libs.update(groups[og][1])

    if not result_libs:
        return None

    result_size = 1
    for mg in own_adj:
        result_size += groups[mg][3]

    return (
        cap_size,
        cap_gids,
        own_adj,
        opp_adj,
        len(result_libs),
        result_size,
        empty_adj,
        adj_own,
        adj_opp,
    )


def _score_move(
    board, groups, r: int, c: int, feat, phase: int, corner_info,
    own_atari_lib, own_atari_total: int, seed: int
) -> float:
    (
        cap_size,
        cap_gids,
        own_adj,
        opp_adj,
        lib_count,
        result_size,
        empty_adj,
        adj_own,
        adj_opp,
    ) = feat

    p = (r, c)
    save_size = own_atari_lib.get(p, 0)

    score = 0.0

    # Urgent defense: save own groups in atari.
    if save_size:
        score += 950 + 230 * save_size + 36 * min(lib_count, 8)

    # Do not casually ignore own stones in atari, especially larger groups.
    if own_atari_total > save_size:
        score -= min(850, 60 + 90 * (own_atari_total - save_size))

    # Captures are usually the most concrete profit.
    if cap_size:
        score += 850 + 260 * cap_size
        if cap_size >= 3:
            score += 80 * cap_size

    # Avoid simple ko/snapback-looking one-stone captures with one liberty.
    if cap_size == 1 and lib_count == 1 and result_size == 1:
        score -= 20000

    cap_set = set(cap_gids)
    attack_size = 0

    # Attack weak neighboring opponent groups.
    for og in opp_adj:
        if og in cap_set:
            continue
        color, stones, libs, size = groups[og]
        l = len(libs)
        if l == 2:
            attack_size += size
            score += 180 + 48 * size
        elif l == 3:
            score += 42 + 9 * min(size, 12)
        elif l == 4:
            score += 12 + 3 * min(size, 10)

    # Reinforce weak neighboring own groups.
    for mg in own_adj:
        color, stones, libs, size = groups[mg]
        l = len(libs)
        if l == 2:
            score += 118 + 32 * size
        elif l == 3:
            score += 34 + 8 * min(size, 12)

    # Connections and cuts.
    if len(own_adj) >= 2:
        connected_size = sum(groups[mg][3] for mg in own_adj)
        score += 88 * (len(own_adj) - 1) + min(130, 8 * connected_size)

    if len(opp_adj) >= 2:
        score += 66 * (len(opp_adj) - 1)

    diag_own, diag_opp = _diag_counts(board, r, c)
    score += adj_own * 12 + adj_opp * 15
    score += diag_own * 4 + diag_opp * 6
    if adj_own and adj_opp:
        score += 38
    if adj_opp >= 2 and adj_own == 0:
        score += 14

    # Shape and liberties.
    score += min(lib_count, 8) * 14
    score += empty_adj * 3

    if lib_count == 1:
        penalty = 560 + 72 * result_size
        if cap_size + save_size >= 3:
            penalty *= 0.45
        score -= penalty
    elif lib_count == 2:
        score -= 86 + max(0, result_size - 4) * 12
    elif lib_count >= 5:
        score += 28

    # Filling one's own eye is almost always bad unless it captures or saves.
    if cap_size == 0 and save_size == 0 and _is_eye(board, r, c, 1):
        score -= 4200

    # Positional/opening values.
    score += _positional_score(board, r, c, phase, corner_info)

    # Local influence: prefer relevant frontier moves over random isolated plays.
    own_inf, opp_inf, nearest = _local_influence(board, r, c)
    tactical = cap_size + save_size + attack_size

    if phase < 20:
        if nearest == 1 and tactical == 0:
            score -= 18
    else:
        if nearest > 5:
            score -= min(65, phase * 0.45)

    if own_inf and opp_inf:
        score += 4.0 * min(own_inf, opp_inf) + 0.8 * max(own_inf, opp_inf)
    elif opp_inf:
        score += 2.2 * opp_inf
        if phase < 30 and nearest <= 2 and tactical == 0:
            score -= 10
    elif own_inf:
        score += 0.75 * own_inf
        if phase > 60:
            score -= min(36, 1.45 * own_inf)

    score += _jitter(r, c, seed)
    return score


def _positional_score(board, r: int, c: int, phase: int, corner_info) -> float:
    rr, cc = r + 1, c + 1
    d_edge = min(rr, cc, N + 1 - rr, N + 1 - cc)

    if phase < 80:
        line_values = {
            1: -38, 2: -6, 3: 24, 4: 34, 5: 20,
            6: 12, 7: 7, 8: 4, 9: 2, 10: 1,
        }
    else:
        line_values = {
            1: -12, 2: 7, 3: 18, 4: 16, 5: 9,
            6: 5, 7: 3, 8: 1, 9: 0, 10: 0,
        }

    score = float(line_values.get(d_edge, 0))

    if phase < 55:
        factor = 1.0 if phase < 24 else 0.62
        score += OPENING_BONUS.get((rr, cc), 0) * factor

    # Mild central value, useful after corners/sides are occupied.
    center_dist = abs(rr - 10) + abs(cc - 10)
    if center_dist <= 9:
        score += (9 - center_dist) * 0.7

    # Corner logic.
    for top, left, own_count, opp_count in corner_info:
        x = rr if top else N + 1 - rr
        y = cc if left else N + 1 - cc

        if x > 7 or y > 7:
            continue

        total = own_count + opp_count

        if total == 0 and phase < 70:
            score += EMPTY_CORNER_PATTERNS.get((x, y), 0) * (1.0 if phase < 35 else 0.55)
        elif opp_count > 0 and own_count == 0:
            score += APPROACH_PATTERNS.get((x, y), 0) * (0.9 if phase < 95 else 0.45)
        elif own_count > 0 and opp_count == 0:
            score += ENCLOSURE_PATTERNS.get((x, y), 0) * (0.75 if phase < 90 else 0.35)

    return score


def _corner_info(board):
    info = []
    for top, left in ((True, True), (True, False), (False, True), (False, False)):
        own = 0
        opp = 0
        for r in range(N):
            x = r + 1 if top else N - r
            if x > 6:
                continue
            for c in range(N):
                y = c + 1 if left else N - c
                if y > 6:
                    continue
                if board[r][c] == 1:
                    own += 1
                elif board[r][c] == -1:
                    opp += 1
        info.append((top, left, own, opp))
    return info


def _diag_counts(board, r: int, c: int):
    own = 0
    opp = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if not _on(nr, nc):
            continue
        if board[nr][nc] == 1:
            own += 1
        elif board[nr][nc] == -1:
            opp += 1
    return own, opp


def _local_influence(board, r: int, c: int):
    own = 0
    opp = 0
    nearest = 99

    for dr in range(-5, 6):
        rem = 5 - abs(dr)
        for dc in range(-rem, rem + 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if not _on(nr, nc):
                continue

            v = board[nr][nc]
            if v == 0:
                continue

            dist = abs(dr) + abs(dc)
            weight = 6 - dist
            nearest = min(nearest, dist)

            if v == 1:
                own += weight
            else:
                opp += weight

    return own, opp, nearest


def _is_eye(board, r: int, c: int, color: int) -> bool:
    # Orthogonals must be friendly stones or board edge.
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _on(nr, nc) and board[nr][nc] != color:
            return False

    bad_diag = 0
    off_diag = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if not _on(nr, nc):
            off_diag += 1
        elif board[nr][nc] == -color:
            bad_diag += 1

    # Conservative eye detection: avoid filling solid-looking own eyes.
    if off_diag >= 1:
        return bad_diag == 0
    return bad_diag <= 1


def _seed_from_position(me, opponent) -> int:
    s = (len(me) * 1000003) ^ (len(opponent) * 9176)
    for r, c in me:
        s = (s ^ (r * 73856093) ^ (c * 19349663)) & 0xFFFFFFFF
    for r, c in opponent:
        s = (s ^ (r * 83492791) ^ (c * 2654435761)) & 0xFFFFFFFF
    return s


def _jitter(r: int, c: int, seed: int) -> float:
    x = ((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ seed
    return ((x & 65535) / 65535.0) * 0.01
