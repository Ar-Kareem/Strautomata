
from __future__ import annotations

SIZE = 19
N = SIZE * SIZE

IDX_TO_RC = [(i // SIZE + 1, i % SIZE + 1) for i in range(N)]


def rc_to_idx(r: int, c: int) -> int:
    return (r - 1) * SIZE + (c - 1)


NBS = [[] for _ in range(N)]
DIAGS = [[] for _ in range(N)]
NEAR2 = [[] for _ in range(N)]

for r in range(1, SIZE + 1):
    for c in range(1, SIZE + 1):
        i = rc_to_idx(r, c)

        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 1 <= rr <= SIZE and 1 <= cc <= SIZE:
                NBS[i].append(rc_to_idx(rr, cc))

        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            if 1 <= rr <= SIZE and 1 <= cc <= SIZE:
                DIAGS[i].append(rc_to_idx(rr, cc))

        near = set()
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                if abs(dr) + abs(dc) <= 2:
                    rr, cc = r + dr, c + dc
                    if 1 <= rr <= SIZE and 1 <= cc <= SIZE:
                        near.add(rc_to_idx(rr, cc))
        NEAR2[i] = list(near)

OPENING_SCORES = {}

for pt in [(4, 4), (4, 16), (16, 4), (16, 16)]:
    OPENING_SCORES[rc_to_idx(*pt)] = 350  # 4-4
for pt in [(4, 3), (3, 4), (4, 17), (3, 16), (16, 3), (17, 4), (16, 17), (17, 16)]:
    OPENING_SCORES[rc_to_idx(*pt)] = 320  # 3-4 / 4-3
for pt in [(4, 10), (10, 4), (10, 16), (16, 10)]:
    OPENING_SCORES[rc_to_idx(*pt)] = 240  # side star
for pt in [(3, 3), (3, 17), (17, 3), (17, 17)]:
    OPENING_SCORES[rc_to_idx(*pt)] = 180  # 3-3
for pt in [(3, 10), (10, 3), (10, 17), (17, 10)]:
    OPENING_SCORES[rc_to_idx(*pt)] = 140  # side third line
OPENING_SCORES[rc_to_idx(10, 10)] = 150  # center

OPENING_POINTS = list(OPENING_SCORES.keys())


def board_key(board: list[int]) -> bytes:
    # map -1,0,1 -> 0,1,2
    return bytes(v + 1 for v in board)


def group_and_libs(board: list[int], start: int) -> tuple[list[int], set[int]]:
    color = board[start]
    stones = []
    libs = set()
    stack = [start]
    seen = {start}

    while stack:
        p = stack.pop()
        stones.append(p)
        for nb in NBS[p]:
            v = board[nb]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return stones, libs


def analyze_board(board: list[int]):
    gid = [-1] * N
    groups = []
    libs = []
    colors = []

    for i, v in enumerate(board):
        if v == 0 or gid[i] != -1:
            continue
        g = len(groups)
        gid[i] = g
        stack = [i]
        stones = []
        libset = set()

        while stack:
            p = stack.pop()
            stones.append(p)
            for nb in NBS[p]:
                vv = board[nb]
                if vv == 0:
                    libset.add(nb)
                elif vv == v and gid[nb] == -1:
                    gid[nb] = g
                    stack.append(nb)

        groups.append(stones)
        libs.append(libset)
        colors.append(v)

    return gid, groups, libs, colors


def looks_like_own_eye(board: list[int], idx: int) -> bool:
    if board[idx] != 0:
        return False
    if not NBS[idx]:
        return False
    for nb in NBS[idx]:
        if board[nb] != 1:
            return False
    return True


def simulate_move(board: list[int], idx: int, seen: set[bytes] | None = None):
    if idx < 0 or idx >= N or board[idx] != 0:
        return None

    new_board = board[:]
    new_board[idx] = 1
    captured = 0
    checked = set()

    for nb in NBS[idx]:
        if new_board[nb] == -1 and nb not in checked:
            stones, libset = group_and_libs(new_board, nb)
            checked.update(stones)
            if not libset:
                captured += len(stones)
                for s in stones:
                    new_board[s] = 0

    my_stones, my_libs = group_and_libs(new_board, idx)
    if not my_libs:
        return None  # suicide

    if seen is not None:
        k = board_key(new_board)
        if k in seen:
            return None  # avoid ko / repetitions

    return new_board, captured, len(my_libs)


def rough_score(
    board: list[int],
    idx: int,
    gid: list[int],
    my_atari: dict[int, int],
    opp_atari: dict[int, int],
    my_weak: dict[int, int],
    opp_weak: dict[int, int],
    total_stones: int,
) -> float:
    score = 0.0

    score += 3200.0 * opp_atari.get(idx, 0)
    score += 2900.0 * my_atari.get(idx, 0)
    score += 420.0 * opp_weak.get(idx, 0)
    score += 360.0 * my_weak.get(idx, 0)

    own_adj = 0
    opp_adj = 0
    empty_adj = 0
    own_adj_groups = set()
    opp_adj_groups = set()

    for nb in NBS[idx]:
        v = board[nb]
        if v == 1:
            own_adj += 1
            own_adj_groups.add(gid[nb])
        elif v == -1:
            opp_adj += 1
            opp_adj_groups.add(gid[nb])
        else:
            empty_adj += 1

    score += 30.0 * own_adj + 20.0 * opp_adj + 6.0 * empty_adj
    if len(own_adj_groups) > 1:
        score += 170.0 * (len(own_adj_groups) - 1)
    if len(opp_adj_groups) > 1:
        score += 140.0 * (len(opp_adj_groups) - 1)
    if own_adj_groups and opp_adj_groups:
        score += 40.0

    if total_stones < 24:
        score += OPENING_SCORES.get(idx, 0) * (24 - total_stones) / 24.0

    if total_stones >= 10 and own_adj == 0 and opp_adj == 0:
        score -= 80.0

    if looks_like_own_eye(board, idx) and opp_atari.get(idx, 0) == 0 and my_atari.get(idx, 0) == 0:
        score -= 700.0

    return score


def post_score(board: list[int], new_board: list[int], idx: int, captured: int, new_libs: int, total_stones: int) -> float:
    score = 0.0

    score += 3600.0 * captured

    if new_libs == 1:
        score -= 2800.0 if captured == 0 else 700.0
    elif new_libs == 2:
        score -= 260.0
    else:
        score += 45.0 * min(new_libs, 8)

    checked = set()
    for nb in NBS[idx]:
        if new_board[nb] == -1 and nb not in checked:
            stones, libset = group_and_libs(new_board, nb)
            checked.update(stones)
            llib = len(libset)
            if llib == 1:
                score += 320.0 * len(stones)
            elif llib == 2:
                score += 85.0 * len(stones)

    if total_stones > 20 and all(board[nb] == 0 for nb in NBS[idx]):
        score -= 120.0

    if total_stones < 24:
        own_adj = sum(1 for nb in NBS[idx] if board[nb] == 1)
        opp_adj = sum(1 for nb in NBS[idx] if board[nb] == -1)
        if own_adj >= 3 and opp_adj == 0:
            score -= 120.0

    return score


def generate_candidates(
    board: list[int],
    gid: list[int],
    groups: list[list[int]],
    libs: list[set[int]],
    colors: list[int],
    total_stones: int,
) -> set[int]:
    cands = set()
    weakish = set()

    for g, libset in enumerate(libs):
        llib = len(libset)
        if llib <= 3:
            cands.update(libset)
            weakish.add(g)

    for i, v in enumerate(board):
        if v == 0:
            continue
        for nb in NBS[i]:
            if board[nb] == 0:
                cands.add(nb)
        if total_stones < 18 or gid[i] in weakish:
            for p in NEAR2[i]:
                if board[p] == 0:
                    cands.add(p)

    if total_stones < 24:
        for p in OPENING_POINTS:
            if board[p] == 0:
                cands.add(p)

    return cands


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    board = [0] * N
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[rc_to_idx(r, c)] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[rc_to_idx(r, c)] = -1

    total_stones = len(me) + len(opponent)

    raw_seen = memory.get("seen", ())
    try:
        seen = set(raw_seen)
    except Exception:
        seen = set()

    # defensive reset for fresh games if memory somehow leaks across games
    if total_stones == 0 or (total_stones <= 2 and len(seen) > 30):
        seen = set()

    seen.add(board_key(board))

    gid, groups, libs, colors = analyze_board(board)

    my_atari = {}
    opp_atari = {}
    my_weak = {}
    opp_weak = {}

    for g, stones in enumerate(groups):
        sz = len(stones)
        libset = libs[g]
        llib = len(libset)
        if colors[g] == 1:
            if llib == 1:
                lib = next(iter(libset))
                my_atari[lib] = my_atari.get(lib, 0) + sz
            elif llib == 2:
                for lib in libset:
                    my_weak[lib] = my_weak.get(lib, 0) + sz
        else:
            if llib == 1:
                lib = next(iter(libset))
                opp_atari[lib] = opp_atari.get(lib, 0) + sz
            elif llib == 2:
                for lib in libset:
                    opp_weak[lib] = opp_weak.get(lib, 0) + sz

    candidates = generate_candidates(board, gid, groups, libs, colors, total_stones)
    if not candidates:
        candidates = {i for i, v in enumerate(board) if v == 0}

    rough = {}
    for idx in candidates:
        if board[idx] == 0:
            rough[idx] = rough_score(board, idx, gid, my_atari, opp_atari, my_weak, opp_weak, total_stones)

    cand_list = sorted(rough, key=lambda i: (-rough[i], i))
    if len(cand_list) > 120:
        cand_list = cand_list[:120]

    best_idx = None
    best_new_board = None
    best_captured = 0
    best_score = float("-inf")

    for idx in cand_list:
        sim = simulate_move(board, idx, seen)
        if sim is None:
            continue
        new_board, captured, new_libs = sim
        score = rough[idx] + post_score(board, new_board, idx, captured, new_libs, total_stones)

        if score > best_score or (score == best_score and (best_idx is None or idx < best_idx)):
            best_score = score
            best_idx = idx
            best_new_board = new_board
            best_captured = captured

    if best_idx is None:
        for idx in range(N):
            if board[idx] != 0:
                continue
            sim = simulate_move(board, idx, seen)
            if sim is not None:
                best_idx = idx
                best_new_board, best_captured, _ = sim
                break

    if best_idx is None:
        return (0, 0), {"seen": list(seen), "last_total": total_stones}

    seen.add(board_key(best_new_board))
    stones_after = total_stones + 1 - best_captured

    return IDX_TO_RC[best_idx], {"seen": list(seen), "last_total": stones_after}
