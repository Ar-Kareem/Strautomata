
# Go policy for a 19x19 board.
# Required API:
#   policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict)
# returns:
#   ((row, col), memory)
#
# Rows/cols are 1-based. Pass is (0, 0).

from typing import Dict, List, Tuple, Set, Optional, Any

N = 19
EMPTY = 0
ME = 1
OPP = 2

STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
}

CORNER_STARS = {(4, 4), (4, 16), (16, 4), (16, 16)}
SIDE_STARS = STAR_POINTS - CORNER_STARS - {(10, 10)}

OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (3, 4), (4, 3), (3, 16), (4, 17),
    (16, 3), (17, 4), (16, 17), (17, 16),
    (3, 10), (10, 3), (10, 17), (17, 10),
]
OPENING_RANK = {p: i for i, p in enumerate(OPENING_POINTS)}


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r + 1 < N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < N:
        yield r, c + 1


def diag_neighbors(r: int, c: int):
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def make_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[List[int]]:
    board = [[EMPTY for _ in range(N)] for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = OPP
    return board


def board_signature(board: List[List[int]]) -> bytes:
    return bytes(cell for row in board for cell in row)


def get_group_and_liberties(
    board: List[List[int]], sr: int, sc: int
) -> Tuple[List[Tuple[int, int]], Set[Tuple[int, int]]]:
    color = board[sr][sc]
    if color == EMPTY:
        return [], set()

    stack = [(sr, sc)]
    seen = {(sr, sc)}
    stones = []
    libs = set()

    while stack:
        r, c = stack.pop()
        stones.append((r, c))
        for nr, nc in neighbors(r, c):
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return stones, libs


def find_groups(board: List[List[int]]):
    visited = [[False for _ in range(N)] for _ in range(N)]
    gid_grid = [[-1 for _ in range(N)] for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY or visited[r][c]:
                continue

            color = board[r][c]
            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in neighbors(x, y):
                    v = board[nx][ny]
                    if v == EMPTY:
                        libs.add((nx, ny))
                    elif v == color and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            gid = len(groups)
            for x, y in stones:
                gid_grid[x][y] = gid
            groups.append({"color": color, "stones": stones, "libs": libs})

    return groups, gid_grid


def simulate_move(
    board: List[List[int]], r: int, c: int
) -> Optional[Dict[str, Any]]:
    """Return simulation info, or None if occupied/suicide."""
    if board[r][c] != EMPTY:
        return None

    nb = [row[:] for row in board]
    nb[r][c] = ME

    captured = 0
    captured_sizes = []

    # Remove adjacent opponent groups with no liberties.
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == OPP:
            stones, libs = get_group_and_liberties(nb, nr, nc)
            if not libs:
                sz = len(stones)
                captured += sz
                captured_sizes.append(sz)
                for x, y in stones:
                    nb[x][y] = EMPTY

    # Suicide check.
    my_stones, my_libs = get_group_and_liberties(nb, r, c)
    if not my_libs:
        return None

    return {
        "board": nb,
        "captured": captured,
        "captured_sizes": captured_sizes,
        "new_libs": len(my_libs),
        "new_group_size": len(my_stones),
        "signature": board_signature(nb),
    }


def is_eye_like(board: List[List[int]], r: int, c: int, color: int) -> bool:
    """Conservative own-eye detector: orthogonal neighbors are color/off-board."""
    if board[r][c] != EMPTY:
        return False
    for nr, nc in neighbors(r, c):
        if board[nr][nc] != color:
            return False
    return True


def diagonal_badness(board: List[List[int]], r: int, c: int, color: int) -> int:
    other = OPP if color == ME else ME
    bad = 0
    for nr, nc in diag_neighbors(r, c):
        if board[nr][nc] == other:
            bad += 1
    return bad


def stable_noise(r: int, c: int, total: int) -> float:
    # Deterministic tiny tie-breaker.
    x = ((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ (total * 83492791)
    return (x % 1000) / 1000.0


def quadrant_counts(board: List[List[int]], rr: int, cc: int):
    """Counts stones near the corresponding corner area for opening decisions."""
    # rr/cc are 1-based.
    if rr <= 10:
        rs = range(0, 8)
    else:
        rs = range(11, 19)
    if cc <= 10:
        cs = range(0, 8)
    else:
        cs = range(11, 19)

    own = opp = 0
    for r in rs:
        for c in cs:
            if board[r][c] == ME:
                own += 1
            elif board[r][c] == OPP:
                opp += 1
    return own, opp


def strategic_position_score(board: List[List[int]], r: int, c: int, total: int) -> float:
    rr, cc = r + 1, c + 1
    score = 0.0

    # Prefer useful lines. First line is usually bad; 3rd/4th lines are efficient.
    edge_dist = min(rr, cc, N + 1 - rr, N + 1 - cc)
    if edge_dist == 1:
        score -= 85
    elif edge_dist == 2:
        score -= 20
    elif edge_dist == 3:
        score += 36
    elif edge_dist == 4:
        score += 52
    elif edge_dist == 5:
        score += 24
    elif edge_dist == 6:
        score += 10

    p = (rr, cc)

    # Opening: occupy corners and large framework points.
    if total < 36:
        if p in OPENING_RANK:
            score += max(20, 235 - 9 * OPENING_RANK[p])

        if p in CORNER_STARS:
            own_q, opp_q = quadrant_counts(board, rr, cc)
            if own_q == 0 and opp_q == 0:
                score += 95
            elif own_q == 0 and opp_q > 0:
                score += 35
            else:
                score -= 45
        elif p in SIDE_STARS:
            score += 70
        elif p == (10, 10):
            score += 55

    elif total < 90:
        if p in STAR_POINTS:
            score += 45
        if p in CORNER_STARS:
            own_q, opp_q = quadrant_counts(board, rr, cc)
            if own_q == 0:
                score += 50
            elif opp_q == 0:
                score += 12

    # Small centrality bonus, but not enough to override corner/side efficiency.
    center_dist = abs(rr - 10) + abs(cc - 10)
    score += max(0, 18 - center_dist) * 0.8

    return score


def local_influence_score(
    board: List[List[int]],
    r: int,
    c: int,
    total: int,
    tactical: bool,
    adj_own_count: int,
    adj_opp_count: int,
) -> float:
    score = 0.0

    min_own = 99
    min_opp = 99
    own_w = 0
    opp_w = 0
    any_near = False

    for dr in range(-4, 5):
        nr = r + dr
        if not (0 <= nr < N):
            continue
        for dc in range(-4, 5):
            nc = c + dc
            if not (0 <= nc < N) or (dr == 0 and dc == 0):
                continue
            v = board[nr][nc]
            if v == EMPTY:
                continue
            d = max(abs(dr), abs(dc))
            if d > 4:
                continue
            any_near = True
            w = 5 - d
            if v == ME:
                min_own = min(min_own, d)
                own_w += w
            else:
                min_opp = min(min_opp, d)
                opp_w += w

    if total < 28 and not tactical:
        # In the opening, avoid cramped plays unless tactically required.
        nearest = min(min_own, min_opp)
        if nearest <= 1:
            score -= 70
        elif nearest == 2:
            score -= 30
        elif nearest >= 4:
            score += 18
    elif total >= 28 and not tactical:
        # Later, completely isolated moves are usually smaller unless positional.
        if not any_near:
            score -= 45

    # Extensions and approaches.
    if min_own in (2, 3):
        score += 32
    elif min_own == 4:
        score += 15
    if min_opp in (2, 3):
        score += 35
    elif min_opp == 4:
        score += 12

    # Unsupported contact is often bad if not tactical.
    if adj_opp_count > 0 and adj_own_count == 0 and not tactical:
        score -= 35

    score += min(own_w, 18) * 2.4
    score += min(opp_w, 18) * 2.8

    return score


def score_move(
    board: List[List[int]],
    r: int,
    c: int,
    sim: Dict[str, Any],
    groups: List[Dict[str, Any]],
    gid_grid: List[List[int]],
    total: int,
    own_atari_libs: Dict[Tuple[int, int], int],
    largest_own_atari: int,
) -> float:
    captured = sim["captured"]
    new_libs = sim["new_libs"]
    new_group_size = sim["new_group_size"]

    adj_own = set()
    adj_opp = set()
    empty_adj = 0

    for nr, nc in neighbors(r, c):
        v = board[nr][nc]
        if v == EMPTY:
            empty_adj += 1
        else:
            gid = gid_grid[nr][nc]
            if gid >= 0:
                if v == ME:
                    adj_own.add(gid)
                else:
                    adj_opp.add(gid)

    tactical = False
    score = 0.0

    # Captures.
    if captured:
        tactical = True
        max_cap = max(sim["captured_sizes"]) if sim["captured_sizes"] else captured
        score += 900 + 210 * captured + 85 * max_cap
        if captured >= 3:
            score += 300
        if captured >= 8:
            score += 450

    # Save friendly groups, especially groups in atari.
    for gid in adj_own:
        g = groups[gid]
        libs = g["libs"]
        size = len(g["stones"])
        lcnt = len(libs)

        if (r, c) in libs:
            if lcnt == 1:
                tactical = True
                score += 820 + 115 * min(size, 12)
                if size >= 6:
                    score += 350
            elif lcnt == 2:
                score += 105 + 14 * min(size, 12)
            elif lcnt == 3:
                score += 35 + 5 * min(size, 10)

    # Attack opponent groups.
    for gid in adj_opp:
        g = groups[gid]
        libs = g["libs"]
        size = len(g["stones"])
        lcnt = len(libs)

        if (r, c) in libs:
            if lcnt == 1:
                tactical = True
                score += 760 + 95 * min(size, 12)
            elif lcnt == 2:
                tactical = True
                score += 290 + 42 * min(size, 12)
                if size >= 5:
                    score += 150
            elif lcnt == 3:
                score += 70 + 13 * min(size, 10)
            else:
                score += 12 + min(size, 8)

    # Connecting own groups.
    if len(adj_own) >= 2:
        total_connected = sum(len(groups[gid]["stones"]) for gid in adj_own)
        score += 125 + 16 * min(total_connected, 20)
        tactical = True

    # Cutting / separating opponent groups.
    if len(adj_opp) >= 2:
        total_cut = sum(len(groups[gid]["stones"]) for gid in adj_opp)
        score += 95 + 11 * min(total_cut, 20)

    # Liberties and self-atari avoidance.
    if new_libs == 1:
        if captured == 0:
            score -= 1050
        else:
            score -= 170
    elif new_libs == 2:
        if captured == 0 and new_group_size <= 2:
            score -= 135
        else:
            score -= 35
    else:
        score += min(new_libs, 8) * 11

    # Prefer not to ignore a sizeable friendly group in atari.
    if largest_own_atari >= 2 and (r, c) not in own_atari_libs and captured == 0:
        score -= 520 + 70 * min(largest_own_atari, 10)

    # Strong bonus for the exact liberty of a large group in atari.
    if (r, c) in own_atari_libs:
        score += 360 + 80 * min(own_atari_libs[(r, c)], 12)
        tactical = True

    # Avoid filling own eyes unless there is a capture/tactic.
    if captured == 0 and is_eye_like(board, r, c, ME):
        bad_diag = diagonal_badness(board, r, c, ME)
        penalty = 760
        if bad_diag == 0:
            penalty += 260
        if total < 320:
            penalty += 180
        score -= penalty

    # Playing in a point surrounded by opponent can be useful only if legal and tactical.
    if is_eye_like(board, r, c, OPP):
        if tactical or captured:
            score += 90
        else:
            score -= 120

    # Shape: empty adjacent points are useful liberties.
    score += empty_adj * 9

    # Positional and influence heuristics.
    score += strategic_position_score(board, r, c, total)
    score += local_influence_score(
        board, r, c, total, tactical, len(adj_own), len(adj_opp)
    )

    # Very tiny deterministic tie-breaker.
    score += stable_noise(r, c, total)

    return score


def policy(
    me: List[Tuple[int, int]],
    opponent: List[Tuple[int, int]],
    memory: Dict
) -> Tuple[Tuple[int, int], Dict]:
    if memory is None or not isinstance(memory, dict):
        memory = {}

    board = make_board(me, opponent)
    total = len(me) + len(opponent)

    current_sig = board_signature(board)

    seen = memory.get("seen_signatures")
    if not isinstance(seen, set):
        seen = set()
    seen.add(current_sig)

    last_after_our_sig = memory.get("last_after_our_sig")

    groups, gid_grid = find_groups(board)

    # Friendly atari liberties.
    own_atari_libs: Dict[Tuple[int, int], int] = {}
    largest_own_atari = 0
    for g in groups:
        if g["color"] == ME and len(g["libs"]) == 1:
            lib = next(iter(g["libs"]))
            size = len(g["stones"])
            largest_own_atari = max(largest_own_atari, size)
            own_atari_libs[lib] = max(own_atari_libs.get(lib, 0), size)

    best_move = None
    best_score = -10**18
    best_sig = None

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue

            sim = simulate_move(board, r, c)
            if sim is None:
                continue

            sig = sim["signature"]

            # Avoid immediate ko repetition and positional repeats when known.
            # Passing remains available if all non-repeating plays are impossible.
            if last_after_our_sig is not None and sig == last_after_our_sig:
                continue
            if sig in seen:
                continue

            s = score_move(
                board, r, c, sim, groups, gid_grid, total,
                own_atari_libs, largest_own_atari
            )

            if s > best_score:
                best_score = s
                best_move = (r, c)
                best_sig = sig

    if best_move is None:
        memory["seen_signatures"] = seen
        memory["last_after_our_sig"] = current_sig
        return (0, 0), memory

    # If the game is extremely late and the best available move is probably just
    # filling our own territory, pass instead. Otherwise keep playing active moves.
    if total > 330 and best_score < -250:
        memory["seen_signatures"] = seen
        memory["last_after_our_sig"] = current_sig
        return (0, 0), memory

    br, bc = best_move
    if best_sig is not None:
        seen.add(best_sig)
        memory["last_after_our_sig"] = best_sig
    else:
        memory["last_after_our_sig"] = current_sig

    # Keep memory bounded, though normal games are far smaller than this.
    if len(seen) > 2000:
        seen = set(list(seen)[-1000:])

    memory["seen_signatures"] = seen
    memory["last_move"] = (br + 1, bc + 1)

    return (br + 1, bc + 1), memory
