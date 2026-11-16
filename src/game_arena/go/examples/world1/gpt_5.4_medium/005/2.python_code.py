
from __future__ import annotations

N = 19
INF_NEG = -10**18

# Precompute neighbors and diagonals
NEIGHBORS = [[[] for _ in range(N)] for _ in range(N)]
DIAGONALS = [[[] for _ in range(N)] for _ in range(N)]
ALL_POS = []

for r in range(N):
    for c in range(N):
        ALL_POS.append((r, c))
        if r > 0:
            NEIGHBORS[r][c].append((r - 1, c))
        if r + 1 < N:
            NEIGHBORS[r][c].append((r + 1, c))
        if c > 0:
            NEIGHBORS[r][c].append((r, c - 1))
        if c + 1 < N:
            NEIGHBORS[r][c].append((r, c + 1))

        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                DIAGONALS[r][c].append((nr, nc))

STAR_POINTS = [
    (3, 3), (3, 15), (15, 3), (15, 15),
    (9, 9),
    (3, 9), (9, 3), (9, 15), (15, 9),
]
THREE_THREE = [(2, 2), (2, 16), (16, 2), (16, 16)]
SIDE_POINTS = [
    (3, 6), (3, 12), (6, 3), (12, 3),
    (6, 15), (12, 15), (15, 6), (15, 12),
]
OPENING_ORDER = STAR_POINTS + THREE_THREE + SIDE_POINTS


def build_board(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> list[list[int]]:
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1
    return board


def group_and_libs(board: list[list[int]], r: int, c: int):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in NEIGHBORS[x][y]:
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return stones, libs


def analyze_groups(board: list[list[int]], color: int):
    idmap = [[-1] * N for _ in range(N)]
    groups = []

    gid = 0
    for r in range(N):
        for c in range(N):
            if board[r][c] == color and idmap[r][c] == -1:
                stones, libs = group_and_libs(board, r, c)
                for x, y in stones:
                    idmap[x][y] = gid
                groups.append((stones, libs))
                gid += 1
    return groups, idmap


def simple_eye(board: list[list[int]], r: int, c: int, color: int) -> bool:
    if board[r][c] != 0:
        return False

    # All orthogonal neighbors must be friendly (off-board counts as okay implicitly)
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] != color:
            return False

    # Conservative false-eye check: if any visible diagonal is opponent, don't treat as true eye
    opp = -color
    for nr, nc in DIAGONALS[r][c]:
        if board[nr][nc] == opp:
            return False
    return True


def play_move(board: list[list[int]], r: int, c: int, color: int = 1):
    if not (0 <= r < N and 0 <= c < N):
        return None
    if board[r][c] != 0:
        return None

    b = [row[:] for row in board]
    b[r][c] = color
    opp = -color
    captured = 0

    checked = set()
    for nr, nc in NEIGHBORS[r][c]:
        if b[nr][nc] == opp and (nr, nc) not in checked:
            stones, libs = group_and_libs(b, nr, nc)
            for s in stones:
                checked.add(s)
            if not libs:
                captured += len(stones)
                for x, y in stones:
                    b[x][y] = 0

    if b[r][c] != color:
        return None

    my_stones, my_libs = group_and_libs(b, r, c)
    if not my_libs:
        return None

    return b, captured, len(my_libs), len(my_stones)


def opening_bonus(r: int, c: int, total_stones: int) -> int:
    p = (r, c)
    if total_stones == 0:
        if p == (3, 3):
            return 10000
    if total_stones < 8:
        if p in STAR_POINTS[:4]:
            return 220
        if p == (9, 9):
            return 150
        if p in STAR_POINTS[5:]:
            return 130
        if p in THREE_THREE:
            return 90
    elif total_stones < 20:
        if p in STAR_POINTS:
            return 80
        if p in THREE_THREE:
            return 40

    center_dist = abs(r - 9) + abs(c - 9)
    return max(0, 18 - center_dist)


def quick_candidate_score(
    board: list[list[int]],
    r: int,
    c: int,
    self_groups,
    self_idmap,
    opp_groups,
    opp_idmap,
    total_stones: int,
) -> int:
    if board[r][c] != 0:
        return -10**9

    score = opening_bonus(r, c, total_stones)

    # Nearby activity
    near = 0
    r0 = max(0, r - 2)
    r1 = min(N, r + 3)
    c0 = max(0, c - 2)
    c1 = min(N, c + 3)
    for x in range(r0, r1):
        for y in range(c0, c1):
            if board[x][y] != 0:
                d = abs(x - r) + abs(y - c)
                if d <= 3:
                    near += (4 - d)
    score += 3 * near

    adj_self = set()
    adj_opp = set()
    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 1:
            gid = self_idmap[nr][nc]
            if gid != -1:
                adj_self.add(gid)
                libs = self_groups[gid][1]
                if len(libs) == 1:
                    score += 500
                elif len(libs) == 2:
                    score += 90
        elif v == -1:
            gid = opp_idmap[nr][nc]
            if gid != -1:
                adj_opp.add(gid)
                libs = opp_groups[gid][1]
                if len(libs) == 1:
                    score += 900
                elif len(libs) == 2:
                    score += 180

    score += 60 * len(adj_self) + 40 * len(adj_opp)

    if simple_eye(board, r, c, 1):
        score -= 300

    return score


def evaluate_move(
    board: list[list[int]],
    r: int,
    c: int,
    self_groups,
    self_idmap,
    opp_groups,
    opp_idmap,
    total_stones: int,
):
    sim = play_move(board, r, c, 1)
    if sim is None:
        return INF_NEG

    new_board, captured, my_libs, my_group_size = sim

    adj_self = set()
    adj_opp = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 1:
            gid = self_idmap[nr][nc]
            if gid != -1:
                adj_self.add(gid)
        elif board[nr][nc] == -1:
            gid = opp_idmap[nr][nc]
            if gid != -1:
                adj_opp.add(gid)

    rescue_ids = []
    for gid in adj_self:
        libs = self_groups[gid][1]
        if len(libs) == 1 and (r, c) in libs:
            rescue_ids.append(gid)

    score = 0

    # Captures dominate.
    score += 1500 * captured

    # Saving own groups in atari.
    for gid in rescue_ids:
        size = len(self_groups[gid][0])
        score += 380 + 80 * size

    # Connecting own groups is valuable.
    conn_sizes = sum(len(self_groups[gid][0]) for gid in adj_self)
    if len(adj_self) >= 2:
        score += 200 * (len(adj_self) - 1) + 20 * conn_sizes
    elif len(adj_self) == 1:
        score += 8 * conn_sizes

    # Resulting liberties / shape.
    if my_libs == 1:
        if captured == 0:
            score -= 1200
        else:
            score -= 150
    elif my_libs == 2:
        score += 50
    else:
        score += 90 + 20 * min(my_libs, 6)

    score += 3 * my_group_size

    # Pressure nearby opponent groups.
    seen_opp = set()
    for gid in adj_opp:
        if gid in seen_opp:
            continue
        seen_opp.add(gid)

        stones, libs = opp_groups[gid]
        before = len(libs)
        size = len(stones)
        rx, ry = stones[0]

        if new_board[rx][ry] != -1:
            # Already captured; capture reward handled above.
            continue

        _, after_libs = group_and_libs(new_board, rx, ry)
        after = len(after_libs)

        if after == 1 and before > 1:
            score += 190 + 25 * size
        score += 18 * (before - after) * size

    # Locality / contact
    empty_adj = 0
    for nr, nc in NEIGHBORS[r][c]:
        if new_board[nr][nc] == 0:
            empty_adj += 1
    score += 12 * len(adj_self) + 8 * len(adj_opp) + 4 * empty_adj

    # Avoid filling obvious own eyes unless tactical.
    if simple_eye(board, r, c, 1) and captured == 0 and not rescue_ids:
        score -= 800

    # Opening / influence preference.
    score += opening_bonus(r, c, total_stones)

    # Mild bias toward points that are not too close to the edge in the opening.
    if total_stones < 30:
        dist_edge = min(r, c, N - 1 - r, N - 1 - c)
        score += 8 * min(dist_edge, 4)

    return score


def generate_candidates(board, self_groups, opp_groups):
    cands = set()
    stones_all = []

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                stones_all.append((r, c))

    # Tactical liberties first.
    for stones, libs in opp_groups:
        if len(libs) <= 2:
            cands.update(libs)

    for stones, libs in self_groups:
        if len(libs) <= 2:
            cands.update(libs)

    # Local neighborhood around existing stones.
    for r, c in stones_all:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                if max(abs(dr), abs(dc)) <= 2 and abs(dr) + abs(dc) <= 3:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        cands.add((nr, nc))

    # Good global points.
    for p in OPENING_ORDER:
        if board[p[0]][p[1]] == 0:
            cands.add(p)

    # Emergency: if somehow empty, allow all empties.
    if not cands:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    cands.add((r, c))

    return cands


def first_legal_move(board):
    seen = set()

    for p in OPENING_ORDER:
        if p not in seen:
            seen.add(p)
            if play_move(board, p[0], p[1], 1) is not None:
                return p

    for p in ALL_POS:
        if p not in seen:
            if play_move(board, p[0], p[1], 1) is not None:
                return p

    return None


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)
    total_stones = len(me) + len(opponent)

    # Empty board opening.
    if total_stones == 0 and board[3][3] == 0:
        return (4, 4)

    self_groups, self_idmap = analyze_groups(board, 1)
    opp_groups, opp_idmap = analyze_groups(board, -1)

    candidates = list(generate_candidates(board, self_groups, opp_groups))

    # Pre-rank to keep evaluation fast.
    if len(candidates) > 120:
        candidates.sort(
            key=lambda p: quick_candidate_score(
                board, p[0], p[1],
                self_groups, self_idmap,
                opp_groups, opp_idmap,
                total_stones,
            ),
            reverse=True,
        )
        candidates = candidates[:120]

    best_move = None
    best_score = INF_NEG

    for r, c in candidates:
        score = evaluate_move(
            board, r, c,
            self_groups, self_idmap,
            opp_groups, opp_idmap,
            total_stones,
        )
        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move is not None and play_move(board, best_move[0], best_move[1], 1) is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # Fallback: always return a legal move if one exists.
    fallback = first_legal_move(board)
    if fallback is not None:
        return (fallback[0] + 1, fallback[1] + 1)

    return (0, 0)
