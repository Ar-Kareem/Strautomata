
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

STAR_POINTS = {
    (3, 3), (3, 9), (3, 15),
    (9, 3), (9, 9), (9, 15),
    (15, 3), (15, 9), (15, 15),
}
CORNER_STARS = {(3, 3), (3, 15), (15, 3), (15, 15)}
SIDE_STARS = STAR_POINTS - CORNER_STARS - {(9, 9)}


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    try:
        return _policy(me, opponent, memory)
    except Exception:
        if not isinstance(memory, dict):
            memory = {}
        return (0, 0), memory


def _policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    input_total = len(me) + len(opponent)
    last_total = memory.get("last_total")
    if input_total == 0 or (
        isinstance(last_total, int) and last_total > 80 and input_total < 30
    ):
        memory = {}

    board = build_board(me, opponent)
    total = count_stones(board)
    current_hash = board_hash(board)

    seen = get_seen(memory)
    last_my_hash = memory.get("last_my_hash")
    if isinstance(last_my_hash, bytes):
        seen.add(last_my_hash)
    seen.add(current_hash)

    groups, gid_at = collect_groups(board)
    my_inf, opp_inf = build_influence(board)
    corner_data = corner_counts(board)
    empty_owner, empty_size = analyze_empty_regions(board)

    seed = memory.get("seed")
    if not isinstance(seed, int):
        seed = seed_from_hash(current_hash) ^ (len(me) * 1000003) ^ (len(opponent) * 9176)
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF

    candidates = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            sim = simulate_move(board, groups, gid_at, r, c)
            if sim is None:
                continue

            # Avoid immediate ko recapture and also older positional repeats if remembered.
            if sim["hash"] in seen:
                continue

            score = evaluate_move(
                board,
                groups,
                gid_at,
                r,
                c,
                sim,
                total,
                my_inf,
                opp_inf,
                corner_data,
                empty_owner,
                empty_size,
            )
            score += 0.25 * deterministic_jitter(seed, r, c)
            candidates.append((score, r, c, sim))

    if not candidates:
        return pass_response(memory, current_hash, total, seed, seen)

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_r, best_c, best_sim = candidates[0]

    empty_count = N * N - total
    if should_pass(best_score, total, empty_count):
        return pass_response(memory, current_hash, total, seed, seen)

    seen.add(best_sim["hash"])
    memory["seen"] = seen
    memory["last_my_hash"] = best_sim["hash"]
    memory["last_total"] = count_stones_hash(best_sim["hash"])
    memory["seed"] = seed
    memory["last_action"] = (best_r + 1, best_c + 1)

    return (best_r + 1, best_c + 1), memory


def pass_response(memory: dict, current_hash: bytes, total: int, seed: int, seen: set) -> tuple[tuple[int, int], dict]:
    seen.add(current_hash)
    memory["seen"] = seen
    memory["last_my_hash"] = current_hash
    memory["last_total"] = total
    memory["seed"] = seed
    memory["last_action"] = (0, 0)
    return (0, 0), memory


def build_board(me, opponent):
    board = [[0 for _ in range(N)] for _ in range(N)]
    for r, c in me:
        rr, cc = r - 1, c - 1
        if 0 <= rr < N and 0 <= cc < N:
            board[rr][cc] = 1
    for r, c in opponent:
        rr, cc = r - 1, c - 1
        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
            board[rr][cc] = 2
    return board


def count_stones(board) -> int:
    return sum(1 for r in range(N) for c in range(N) if board[r][c] != 0)


def count_stones_hash(h: bytes) -> int:
    return sum(1 for x in h if x)


def board_hash(board) -> bytes:
    return bytes([board[r][c] for r in range(N) for c in range(N)])


def get_seen(memory: dict) -> set:
    raw = memory.get("seen", set())
    if isinstance(raw, set):
        return raw
    seen = set()
    if isinstance(raw, (list, tuple)):
        for h in raw:
            if isinstance(h, bytes):
                seen.add(h)
            elif isinstance(h, bytearray):
                seen.add(bytes(h))
    return seen


def seed_from_hash(h: bytes) -> int:
    x = 0x9E3779B9
    for i in range(0, len(h), 37):
        x = ((x * 1315423911) ^ (h[i] + i * 97)) & 0xFFFFFFFF
    return x


def deterministic_jitter(seed: int, r: int, c: int) -> float:
    x = seed ^ ((r + 1) * 73856093) ^ ((c + 1) * 19349663)
    x &= 0xFFFFFFFF
    x ^= (x >> 13)
    x = (x * 1274126177) & 0xFFFFFFFF
    return (x & 1023) / 1024.0


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def collect_groups(board):
    gid_at = [[-1 for _ in range(N)] for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or gid_at[r][c] != -1:
                continue

            idx = len(groups)
            stack = [(r, c)]
            gid_at[r][c] = idx
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))
                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    if not in_bounds(nr, nc):
                        continue
                    val = board[nr][nc]
                    if val == 0:
                        libs.add((nr, nc))
                    elif val == color and gid_at[nr][nc] == -1:
                        gid_at[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append({"color": color, "stones": stones, "libs": libs})

    return groups, gid_at


def flood_group(board, r: int, c: int):
    color = board[r][c]
    if color == 0:
        return set(), []

    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        sr, sc = stack.pop()
        stones.append((sr, sc))

        for dr, dc in DIRS:
            nr, nc = sr + dr, sc + dc
            if not in_bounds(nr, nc):
                continue
            val = board[nr][nc]
            if val == 0:
                libs.add((nr, nc))
            elif val == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return libs, stones


def simulate_move(board, groups, gid_at, r: int, c: int):
    if board[r][c] != 0:
        return None

    captured_ids = []
    used = set()

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        if board[nr][nc] == 2:
            gid = gid_at[nr][nc]
            if gid not in used:
                used.add(gid)
                if len(groups[gid]["libs"]) == 1:
                    captured_ids.append(gid)

    new_board = [row[:] for row in board]
    new_board[r][c] = 1

    captured_count = 0
    for gid in captured_ids:
        for sr, sc in groups[gid]["stones"]:
            new_board[sr][sc] = 0
            captured_count += 1

    libs, stones = flood_group(new_board, r, c)
    if not libs:
        return None

    return {
        "board": new_board,
        "hash": board_hash(new_board),
        "captured_ids": captured_ids,
        "captured_count": captured_count,
        "libs": libs,
        "stones": stones,
    }


def build_influence(board):
    my_inf = [[0 for _ in range(N)] for _ in range(N)]
    opp_inf = [[0 for _ in range(N)] for _ in range(N)]
    weights = [0, 9, 5, 3, 1]

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0:
                continue

            arr = my_inf if color == 1 else opp_inf
            for dr in range(-4, 5):
                nr = r + dr
                if not (0 <= nr < N):
                    continue
                rem = 4 - abs(dr)
                for dc in range(-rem, rem + 1):
                    d = abs(dr) + abs(dc)
                    if d == 0:
                        continue
                    nc = c + dc
                    if 0 <= nc < N:
                        arr[nr][nc] += weights[d]

    return my_inf, opp_inf


def analyze_empty_regions(board):
    owner = [[0 for _ in range(N)] for _ in range(N)]
    size_map = [[0 for _ in range(N)] for _ in range(N)]
    seen = [[False for _ in range(N)] for _ in range(N)]

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0 or seen[r][c]:
                continue

            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            borders = set()

            while stack:
                sr, sc = stack.pop()
                cells.append((sr, sc))

                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    if not in_bounds(nr, nc):
                        continue
                    val = board[nr][nc]
                    if val == 0:
                        if not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                    else:
                        borders.add(val)

            own = 0
            if len(borders) == 1:
                own = next(iter(borders))

            sz = len(cells)
            for sr, sc in cells:
                owner[sr][sc] = own
                size_map[sr][sc] = sz

    return owner, size_map


def corner_norm(idx: int, r: int, c: int):
    if idx == 0:       # top-left
        return r, c
    if idx == 1:       # top-right
        return r, N - 1 - c
    if idx == 2:       # bottom-left
        return N - 1 - r, c
    return N - 1 - r, N - 1 - c


def corner_denorm(idx: int, nr: int, nc: int):
    if idx == 0:
        return nr, nc
    if idx == 1:
        return nr, N - 1 - nc
    if idx == 2:
        return N - 1 - nr, nc
    return N - 1 - nr, N - 1 - nc


def corner_counts(board):
    data = []
    for idx in range(4):
        myc = 0
        oppc = 0
        for nr in range(6):
            for nc in range(6):
                r, c = corner_denorm(idx, nr, nc)
                if board[r][c] == 1:
                    myc += 1
                elif board[r][c] == 2:
                    oppc += 1
        data.append((myc, oppc))
    return data


def positional_score(r: int, c: int, total: int) -> float:
    # Index is board line from nearest edge: 1..10.
    early = [0, -45, -10, 18, 24, 13, 7, 3, 1, 0, 0]
    late = [0, -5, 5, 10, 8, 5, 2, 1, 0, 0, 0]

    lr = min(r + 1, N - r)
    lc = min(c + 1, N - c)
    phase = min(1.0, total / 180.0)

    return (
        (1.0 - phase) * (early[lr] + early[lc])
        + phase * (late[lr] + late[lc])
    )


def corner_bonus(r: int, c: int, total: int, corner_data) -> float:
    b = 0.0
    scale = max(0.25, 1.0 - total / 180.0)

    empty_corner_points = {(3, 3), (2, 3), (3, 2), (2, 2)}
    approach_points = {(2, 4), (4, 2), (2, 5), (5, 2), (3, 5), (5, 3)}
    enclosure_points = {(2, 4), (4, 2), (2, 5), (5, 2), (3, 5), (5, 3)}

    for idx, (myc, oppc) in enumerate(corner_data):
        nr, nc = corner_norm(idx, r, c)
        if nr >= 6 or nc >= 6:
            continue

        p = (nr, nc)

        if myc == 0 and oppc == 0:
            if p in empty_corner_points:
                if p == (3, 3):
                    b += 95.0 * scale
                elif p in {(2, 3), (3, 2)}:
                    b += 88.0 * scale
                else:
                    b += 70.0 * scale

        elif oppc > 0 and myc == 0:
            if p in approach_points:
                b += 55.0 * scale
            if p == (2, 2):
                b += (45.0 if total > 20 else 22.0) * scale

        elif myc > 0 and oppc == 0:
            if p in enclosure_points:
                b += 28.0 * scale
            if p == (2, 2) and total > 60:
                b += 12.0 * scale

    return b


def eye_like(board, r: int, c: int, color: int) -> int:
    if board[r][c] != 0:
        return 0

    off_orth = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            off_orth += 1
        elif board[nr][nc] != color:
            return 0

    opp = 3 - color
    bad_diag = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and board[nr][nc] == opp:
            bad_diag += 1

    if off_orth >= 1:
        true_eye = bad_diag == 0
    else:
        true_eye = bad_diag <= 1

    return 2 if true_eye else 1


def evaluate_move(
    board,
    groups,
    gid_at,
    r: int,
    c: int,
    sim,
    total: int,
    my_inf,
    opp_inf,
    corner_data,
    empty_owner,
    empty_size,
) -> float:
    captured_ids = sim["captured_ids"]
    cap_set = set(captured_ids)
    cap_count = sim["captured_count"]
    new_libs = len(sim["libs"])
    new_size = len(sim["stones"])

    adj_my = set()
    adj_opp = set()
    empty_neighbors = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        val = board[nr][nc]
        if val == 0:
            empty_neighbors += 1
        elif val == 1:
            adj_my.add(gid_at[nr][nc])
        elif val == 2:
            adj_opp.add(gid_at[nr][nc])

    score = 0.0
    score += positional_score(r, c, total)
    score += corner_bonus(r, c, total, corner_data)

    if total < 110:
        star_scale = max(0.0, 1.0 - total / 130.0)
        if (r, c) in CORNER_STARS:
            score += 35.0 * star_scale
        elif (r, c) in SIDE_STARS:
            score += 18.0 * star_scale
        elif (r, c) == (9, 9) and total > 8:
            score += 10.0 * star_scale

    tactical = 0.0

    # Captures are urgent and usually profitable.
    for gid in captured_ids:
        sz = len(groups[gid]["stones"])
        tactical += 1400.0 + 380.0 * sz

    # Save and strengthen friendly weak groups.
    for gid in adj_my:
        g = groups[gid]
        libs = len(g["libs"])
        sz = len(g["stones"])

        if libs == 1:
            if new_libs >= 2 or cap_count > 0:
                tactical += 1700.0 + 420.0 * sz + 80.0 * min(new_libs, 6)
            else:
                tactical += 250.0 + 60.0 * sz
        elif libs == 2:
            tactical += 190.0 + 35.0 * min(sz, 10)
        elif libs == 3:
            tactical += 45.0 + 8.0 * min(sz, 10)

    # Attack opponent groups by capturing or putting them in atari.
    for gid in adj_opp:
        if gid in cap_set:
            continue
        g = groups[gid]
        libs = len(g["libs"])
        sz = len(g["stones"])
        remaining = libs - 1

        if remaining == 1:
            tactical += 360.0 + 125.0 * sz
        elif remaining == 2:
            tactical += 60.0 + 12.0 * min(sz, 12)
        elif remaining == 3:
            tactical += 15.0 + 4.0 * min(sz, 12)

    # Connecting friendly groups is valuable; touching multiple enemy groups may cut.
    if len(adj_my) >= 2:
        connected_size = sum(min(len(groups[gid]["stones"]), 12) for gid in adj_my)
        tactical += 90.0 * (len(adj_my) - 1) + 8.0 * connected_size

    if len(adj_opp) >= 2 and new_libs >= 3:
        tactical += 45.0 * (len(adj_opp) - 1)

    score += tactical

    # Liberties and self-atari avoidance.
    score += 8.0 * min(new_libs, 8)
    if new_libs == 1:
        score -= 850.0 + 100.0 * min(new_size, 12)
    elif new_libs == 2:
        score -= max(25.0, 110.0 - 20.0 * min(cap_count, 4))
    elif new_libs >= 4:
        score += 18.0

    # Avoid snapback-like captures where a large group remains in atari.
    if cap_count == 1 and new_libs == 1 and new_size > 1:
        score -= 900.0 + 80.0 * min(new_size, 12)

    # Shape and local breathing room.
    score += 4.0 * empty_neighbors
    score += 3.0 * len(adj_my)
    if len(adj_opp) > 0 and new_libs <= 2 and cap_count == 0:
        score -= 20.0 * len(adj_opp)

    diag_friend = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and board[nr][nc] == 1:
            diag_friend += 1
    if diag_friend and not adj_my:
        score += 8.0
    score += 3.0 * diag_friend

    # Do not fill our own eyes unless it captures something.
    eye = eye_like(board, r, c, 1)
    if eye and cap_count == 0:
        score -= 1350.0 if eye == 2 else 450.0

    # Avoid filling our own small/endgame territory; consider invasions of large enemy zones.
    owner = empty_owner[r][c]
    region_size = empty_size[r][c]
    if cap_count == 0 and tactical < 600.0:
        if owner == 1 and (region_size <= 30 or total > 190):
            score -= 130.0 + 2.0 * min(region_size, 60)
        elif owner == 2:
            if region_size <= 6 and total > 80:
                score -= 80.0
            elif region_size >= 12 and total < 230:
                score += min(45.0, 1.5 * region_size)

    # Influence: prefer supported moves, approaches, and reductions; avoid hopeless deep moves.
    mi = my_inf[r][c]
    oi = opp_inf[r][c]

    if total < 100:
        score += 0.9 * mi + 0.6 * min(oi, mi + 8)
    else:
        score += 0.8 * mi + 0.8 * oi

    if oi > mi + 10 and tactical < 500.0:
        score -= 3.5 * (oi - mi - 10)

    if mi > oi + 22 and tactical < 300.0 and owner == 1:
        score -= 1.5 * (mi - oi - 22)

    # Fuseki spacing: avoid early unnecessary contact and over-concentration.
    if total < 70 and tactical < 500.0:
        near1 = len(adj_my) + len(adj_opp)
        near2 = 0
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                d = abs(dr) + abs(dc)
                if d == 0 or d > 2:
                    continue
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and board[nr][nc] != 0:
                    near2 += 1

        if near1 >= 2:
            score -= 18.0 * (near1 - 1)
        elif near1 == 1:
            score -= 4.0
        if near2 >= 5:
            score -= 20.0

    return score


def should_pass(best_score: float, total: int, empty_count: int) -> bool:
    # Pass only when the best move is clearly harmful. This prevents eye-filling while
    # still playing dame/reductions that have non-negative value.
    if total < 140:
        return best_score < -500.0
    if best_score < -150.0:
        return True
    if total > 220 and best_score < -25.0:
        return True
    return False
