
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

NEIGHBORS: dict[tuple[int, int], list[tuple[int, int]]] = {}
DIAGONALS: dict[tuple[int, int], list[tuple[int, int]]] = {}

for r in range(N):
    for c in range(N):
        ns = []
        ds = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                ns.append((nr, nc))
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                ds.append((nr, nc))
        NEIGHBORS[(r, c)] = ns
        DIAGONALS[(r, c)] = ds

CORNER_STARS = {(3, 3), (3, 15), (15, 3), (15, 15)}
SIDE_STARS = {(3, 9), (9, 3), (9, 15), (15, 9)}
CENTER_STAR = (9, 9)
ALL_STARS = CORNER_STARS | SIDE_STARS | {CENTER_STAR}


def build_board(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> list[list[int]]:
    board = [[0] * N for _ in range(N)]
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = -1
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    return board


def collect_group(board: list[list[int]], r: int, c: int) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    color = board[r][c]
    stones = []
    liberties: set[tuple[int, int]] = set()
    stack = [(r, c)]
    seen = {(r, c)}

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in NEIGHBORS[(x, y)]:
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))

    return stones, liberties


def analyze_groups(board: list[list[int]]) -> tuple[dict[int, list[dict]], dict[tuple[int, int], tuple[int, int]]]:
    visited = [[False] * N for _ in range(N)]
    groups: dict[int, list[dict]] = {1: [], -1: []}
    stone_to_group: dict[tuple[int, int], tuple[int, int]] = {}

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or visited[r][c]:
                continue

            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            liberties: set[tuple[int, int]] = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in NEIGHBORS[(x, y)]:
                    v = board[nx][ny]
                    if v == 0:
                        liberties.add((nx, ny))
                    elif v == color and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            idx = len(groups[color])
            g = {
                "stones": stones,
                "liberties": liberties,
                "size": len(stones),
                "lib_count": len(liberties),
            }
            groups[color].append(g)
            gid = (color, idx)
            for s in stones:
                stone_to_group[s] = gid

    return groups, stone_to_group


def simulate_move(
    board: list[list[int]], r: int, c: int, color: int = 1
) -> tuple[list[list[int]], int, int, int, bool] | None:
    if board[r][c] != 0:
        return None

    b = [row[:] for row in board]
    b[r][c] = color

    captured_positions: list[tuple[int, int]] = []
    checked: set[tuple[int, int]] = set()

    for nr, nc in NEIGHBORS[(r, c)]:
        if b[nr][nc] == -color and (nr, nc) not in checked:
            stones, liberties = collect_group(b, nr, nc)
            for s in stones:
                checked.add(s)
            if not liberties:
                captured_positions.extend(stones)

    if captured_positions:
        for x, y in captured_positions:
            b[x][y] = 0

    my_stones, my_libs = collect_group(b, r, c)
    if not my_libs:
        return None

    # Without history we cannot know ko for sure.
    # This pattern is a likely immediate ko recapture, so we avoid it.
    possible_ko = (
        len(captured_positions) == 1
        and len(my_stones) == 1
        and len(my_libs) == 1
    )

    return b, len(captured_positions), len(my_stones), len(my_libs), possible_ko


def is_true_eye_like(board: list[list[int]], r: int, c: int, color: int) -> bool:
    if board[r][c] != 0:
        return False

    # All orthogonal neighbors must be own stones.
    for nr, nc in NEIGHBORS[(r, c)]:
        if board[nr][nc] != color:
            return False

    # Diagonal heuristic for true eye.
    opponent_diagonals = 0
    friendly_or_edge = 0
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nr, nc = r + dr, c + dc
        if not (0 <= nr < N and 0 <= nc < N):
            friendly_or_edge += 1
        else:
            v = board[nr][nc]
            if v == -color:
                opponent_diagonals += 1
            elif v == color:
                friendly_or_edge += 1

    on_edge = (r == 0 or r == N - 1 or c == 0 or c == N - 1)
    if on_edge:
        return opponent_diagonals == 0
    return opponent_diagonals <= 1 and friendly_or_edge >= 3


def local_influence(board: list[list[int]], r: int, c: int) -> int:
    score = 0
    own_weights = {1: 35, 2: 15, 3: 5}
    opp_weights = {1: 45, 2: 20, 3: 8}

    for dr in range(-3, 4):
        for dc in range(-3, 4):
            dist = abs(dr) + abs(dc)
            if dist == 0 or dist > 3:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                v = board[nr][nc]
                if v == 1:
                    score += own_weights[dist]
                elif v == -1:
                    score += opp_weights[dist]
    return score


def line_number(r: int, c: int) -> int:
    return min(r + 1, c + 1, N - r, N - c)


def quadrant_index(r: int, c: int) -> int:
    return (2 if r >= 9 else 0) + (1 if c >= 9 else 0)


def nearest_stone_distance(r: int, c: int, occupied: list[tuple[int, int]]) -> int:
    if not occupied:
        return 0
    best = 10**9
    for x, y in occupied:
        d = abs(r - x) + abs(c - y)
        if d < best:
            best = d
    return best


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)
    groups, stone_to_group = analyze_groups(board)

    occupied: list[tuple[int, int]] = []
    quad_counts = [0, 0, 0, 0]
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                occupied.append((r, c))
                quad_counts[quadrant_index(r, c)] += 1

    nstones = len(occupied)

    best_move: tuple[int, int] | None = None
    best_score = -10**18

    found_non_risky = False

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            sim = simulate_move(board, r, c, 1)
            if sim is None:
                continue

            _, captured, own_size, own_libs, possible_ko = sim

            # Safer to avoid likely ko recaptures entirely because history is unavailable.
            if possible_ko:
                continue

            found_non_risky = True
            score = 0

            seen_own: set[tuple[int, int]] = set()
            seen_opp: set[tuple[int, int]] = set()

            rescue_size = 0
            extend_size = 0
            atari_size = 0
            pressure_size = 0
            connect_sizes = 0
            weak_connect = 0
            cut_sizes = 0

            adj_empty = 0
            adj_own_ct = 0
            adj_opp_ct = 0

            for nr, nc in NEIGHBORS[(r, c)]:
                v = board[nr][nc]
                if v == 0:
                    adj_empty += 1
                elif v == 1:
                    adj_own_ct += 1
                    gid = stone_to_group[(nr, nc)]
                    if gid not in seen_own:
                        seen_own.add(gid)
                        g = groups[1][gid[1]]
                        connect_sizes += g["size"]
                        if (r, c) in g["liberties"]:
                            if g["lib_count"] == 1:
                                rescue_size += g["size"]
                            elif g["lib_count"] == 2:
                                extend_size += g["size"]
                        if g["lib_count"] <= 2:
                            weak_connect += g["size"]
                else:
                    adj_opp_ct += 1
                    gid = stone_to_group[(nr, nc)]
                    if gid not in seen_opp:
                        seen_opp.add(gid)
                        g = groups[-1][gid[1]]
                        cut_sizes += g["size"]
                        if (r, c) in g["liberties"]:
                            if g["lib_count"] == 2:
                                atari_size += g["size"]
                            elif g["lib_count"] == 3:
                                pressure_size += g["size"]

            # Tactical priorities
            score += captured * 10000
            score += rescue_size * 3500
            score += atari_size * 900
            score += pressure_size * 180
            score += extend_size * 450

            # Connections and cuts
            if len(seen_own) >= 2:
                score += 500 * len(seen_own) + 120 * connect_sizes + 250 * weak_connect
            elif len(seen_own) == 1:
                score += 40 * connect_sizes

            if len(seen_opp) >= 2:
                score += 220 * len(seen_opp) + 70 * cut_sizes

            # Shape / liberties
            score += 60 * min(own_libs, 5) + 12 * own_size + 25 * adj_empty
            score += 45 * adj_opp_ct + 30 * adj_own_ct

            if own_libs == 1:
                score -= 3000 + 120 * own_size
            elif own_libs == 2:
                score -= 180

            if is_true_eye_like(board, r, c, 1):
                score -= 2000

            # Positional / opening heuristics
            line = line_number(r, c)

            if nstones < 12:
                if (r, c) in CORNER_STARS:
                    score += 900
                elif (r, c) in SIDE_STARS:
                    score += 500
                elif (r, c) == CENTER_STAR:
                    score += 350

                if line == 1:
                    score -= 500
                elif line == 2:
                    score -= 180
                elif line in (3, 4):
                    score += 80

                if not seen_own and not seen_opp and (r, c) not in ALL_STARS:
                    score -= 250

                score += max(0, 4 - quad_counts[quadrant_index(r, c)]) * 40

            elif nstones < 60:
                if line == 1:
                    score -= 250
                elif line == 2:
                    score -= 80
                elif line in (3, 4):
                    score += 20

                if not seen_own and not seen_opp:
                    score -= 35 * min(nearest_stone_distance(r, c, occupied), 6)

            else:
                if line == 1:
                    score -= 120
                if not seen_own and not seen_opp:
                    score -= 20 * min(nearest_stone_distance(r, c, occupied), 6)

            # Local fighting bias
            score += local_influence(board, r, c)

            move = (r + 1, c + 1)
            if (
                best_move is None
                or score > best_score
                or (score == best_score and move < best_move)
            ):
                best_score = score
                best_move = move

    if best_move is not None:
        return best_move

    # If only risky ko-like recaptures or no legal plays remain, pass safely.
    if not found_non_risky:
        return (0, 0)

    return (0, 0)
