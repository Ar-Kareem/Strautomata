
from typing import List, Tuple, Dict

SIZE = 19
N = SIZE * SIZE

# Precompute neighbors and diagonals for each point.
NEIGHBORS: List[List[int]] = [[] for _ in range(N)]
DIAGONALS: List[List[int]] = [[] for _ in range(N)]
DIAG_OFFBOARD: List[int] = [0 for _ in range(N)]

for r in range(SIZE):
    for c in range(SIZE):
        i = r * SIZE + c
        if r > 0:
            NEIGHBORS[i].append((r - 1) * SIZE + c)
        if r + 1 < SIZE:
            NEIGHBORS[i].append((r + 1) * SIZE + c)
        if c > 0:
            NEIGHBORS[i].append(r * SIZE + (c - 1))
        if c + 1 < SIZE:
            NEIGHBORS[i].append(r * SIZE + (c + 1))

        off = 0
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                DIAGONALS[i].append(rr * SIZE + cc)
            else:
                off += 1
        DIAG_OFFBOARD[i] = off

OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
]
OPENING_IDX = [(r - 1) * SIZE + (c - 1) for r, c in OPENING_POINTS]


def idx_to_rc(i: int) -> Tuple[int, int]:
    return (i // SIZE + 1, i % SIZE + 1)


def board_hash(board: List[int]) -> bytes:
    return bytes(v + 1 for v in board)  # {-1,0,1} -> {0,1,2}


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[int]:
    board = [0] * N
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + (c - 1)] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + (c - 1)] = -1
    return board


def group_info(board: List[int], start: int):
    color = board[start]
    stones = []
    libs = set()
    stack = [start]
    seen = {start}
    while stack:
        p = stack.pop()
        stones.append(p)
        for nb in NEIGHBORS[p]:
            v = board[nb]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return stones, libs


def analyze(board: List[int]):
    visited = [False] * N
    stone_to_gid = [-1] * N
    groups = []

    for i in range(N):
        if visited[i] or board[i] == 0:
            continue
        color = board[i]
        stack = [i]
        visited[i] = True
        stones = []
        libs = set()

        while stack:
            p = stack.pop()
            stones.append(p)
            for nb in NEIGHBORS[p]:
                v = board[nb]
                if v == 0:
                    libs.add(nb)
                elif v == color and not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)

        gid = len(groups)
        for s in stones:
            stone_to_gid[s] = gid
        groups.append({
            "color": color,
            "stones": stones,
            "libs": tuple(libs),
            "lib_count": len(libs),
            "size": len(stones),
        })
    return groups, stone_to_gid


def is_true_eye(board: List[int], idx: int, color: int) -> bool:
    if board[idx] != 0:
        return False
    for nb in NEIGHBORS[idx]:
        if board[nb] != color:
            return False
    bad_diags = 0
    for d in DIAGONALS[idx]:
        if board[d] != color:
            bad_diags += 1
    allowance = 1 if DIAG_OFFBOARD[idx] > 0 else 0
    return bad_diags <= allowance


def play_move(board: List[int], idx: int, color: int, ko_forbid: bytes = None):
    if idx < 0 or idx >= N or board[idx] != 0:
        return None

    nb = board[:]
    nb[idx] = color
    captured = 0

    checked = set()
    for adj in NEIGHBORS[idx]:
        if nb[adj] == -color and adj not in checked:
            stones, libs = group_info(nb, adj)
            for s in stones:
                checked.add(s)
            if len(libs) == 0:
                captured += len(stones)
                for s in stones:
                    nb[s] = 0

    my_stones, my_libs = group_info(nb, idx)
    if len(my_libs) == 0:
        return None

    if ko_forbid is not None and board_hash(nb) == ko_forbid:
        return None

    return nb, captured, my_stones, my_libs


def evaluate_move(
    board: List[int],
    idx: int,
    groups,
    stone_to_gid,
    bonus_map: Dict[int, int],
    ko_forbid: bytes,
    stage: int,
    occupied: List[int],
):
    sim = play_move(board, idx, 1, ko_forbid)
    if sim is None:
        return None

    nb, captured, my_stones, my_libs = sim
    score = float(bonus_map.get(idx, 0))

    # Immediate tactical value.
    score += 1100 * captured
    my_lib_count = len(my_libs)
    score += 18 * my_lib_count

    if captured == 0 and my_lib_count == 1:
        score -= 700
    elif captured == 0 and my_lib_count == 2:
        score -= 60

    if captured == 0 and is_true_eye(board, idx, 1):
        score -= 1000

    friendly_adj_groups = set()
    enemy_adj_groups = set()
    adj_friends = 0
    adj_enemies = 0

    for adj in NEIGHBORS[idx]:
        if board[adj] == 1:
            adj_friends += 1
            gid = stone_to_gid[adj]
            if gid >= 0:
                friendly_adj_groups.add(gid)
        elif board[adj] == -1:
            adj_enemies += 1
            gid = stone_to_gid[adj]
            if gid >= 0:
                enemy_adj_groups.add(gid)

    # Connection / extension.
    score += 8 * adj_friends
    score += 6 * adj_enemies
    if len(friendly_adj_groups) >= 2:
        score += 35 * (len(friendly_adj_groups) - 1)

    for gid in friendly_adj_groups:
        g = groups[gid]
        if g["color"] != 1:
            continue
        if g["lib_count"] == 1:
            score += 500 + 80 * g["size"]
        elif g["lib_count"] == 2:
            score += 60 + 10 * g["size"]

    for gid in enemy_adj_groups:
        g = groups[gid]
        if g["color"] != -1:
            continue
        if g["lib_count"] == 1:
            score += 800 + 40 * g["size"]
        elif g["lib_count"] == 2:
            score += 130 + 12 * g["size"]
        elif g["lib_count"] == 3:
            score += 30 + 4 * g["size"]

    # After-move local pressure: reward making neighboring enemy groups weak.
    seen_enemy_after = set()
    for adj in NEIGHBORS[idx]:
        if nb[adj] == -1 and adj not in seen_enemy_after:
            stones, libs = group_info(nb, adj)
            for s in stones:
                seen_enemy_after.add(s)
            lc = len(libs)
            if lc == 1:
                score += 140 + 10 * len(stones)
            elif lc == 2:
                score += 25

    r = idx // SIZE
    c = idx % SIZE
    edge_dist = min(r, SIZE - 1 - r, c, SIZE - 1 - c)

    # Opening heuristics.
    if stage < 12:
        if idx in OPENING_IDX:
            score += 220
        if edge_dist == 3:
            score += 55
        elif edge_dist in (2, 4):
            score += 25
        elif edge_dist <= 1:
            score -= 70

        if occupied:
            md = min(abs(r - (p // SIZE)) + abs(c - (p % SIZE)) for p in occupied)
            if md >= 6:
                score += 25
            elif md <= 2:
                score -= 40
    else:
        if adj_friends + adj_enemies == 0:
            score -= 25

    # Very slight center preference in non-opening tie situations.
    score += 0.5 * (9 - abs(r - 9)) + 0.5 * (9 - abs(c - 9))

    return score


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    memory = dict(memory or {})
    board = build_board(me, opponent)
    current_hash = board_hash(board)
    ko_forbid = memory.get("prev_board_hash")

    groups, stone_to_gid = analyze(board)
    stage = len(me) + len(opponent)
    occupied = [i for i, v in enumerate(board) if v != 0]

    # Tactical bonus map from current weak groups.
    bonus_map: Dict[int, int] = {}
    for g in groups:
        lc = g["lib_count"]
        libs = g["libs"]
        size = g["size"]
        color = g["color"]

        if lc == 1:
            l = libs[0]
            bonus_map[l] = bonus_map.get(l, 0) + (5200 if color == -1 else 4700) + 180 * size
        elif lc == 2:
            for l in libs:
                bonus_map[l] = bonus_map.get(l, 0) + (160 if color == -1 else 110) + 12 * size

    # Candidate moves: tactical liberties, near existing stones, and opening points.
    candidates = set()

    for l in bonus_map:
        if 0 <= l < N and board[l] == 0:
            candidates.add(l)

    for p in occupied:
        for n1 in NEIGHBORS[p]:
            if board[n1] == 0:
                candidates.add(n1)
            for n2 in NEIGHBORS[n1]:
                if board[n2] == 0:
                    candidates.add(n2)

    for p in OPENING_IDX:
        if board[p] == 0:
            candidates.add(p)

    if not candidates:
        candidates = {i for i, v in enumerate(board) if v == 0}

    best_idx = None
    best_score = None

    for idx in sorted(candidates):
        sc = evaluate_move(board, idx, groups, stone_to_gid, bonus_map, ko_forbid, stage, occupied)
        if sc is None:
            continue
        if best_score is None or sc > best_score:
            best_score = sc
            best_idx = idx

    # Fallback: scan all empties if needed.
    if best_idx is None:
        for idx in range(N):
            if board[idx] != 0:
                continue
            sc = evaluate_move(board, idx, groups, stone_to_gid, bonus_map, ko_forbid, stage, occupied)
            if sc is None:
                continue
            if best_score is None or sc > best_score:
                best_score = sc
                best_idx = idx

    new_memory = dict(memory)
    new_memory["prev_board_hash"] = current_hash

    if best_idx is None:
        return (0, 0), new_memory

    return idx_to_rc(best_idx), new_memory
