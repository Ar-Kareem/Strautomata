
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

SIZE = 19
N = SIZE * SIZE

# Precompute neighbors and diagonals on the 19x19 board.
NEIGHBORS = [[] for _ in range(N)]
DIAGONALS = [[] for _ in range(N)]
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

        if r > 0 and c > 0:
            DIAGONALS[i].append((r - 1) * SIZE + (c - 1))
        if r > 0 and c + 1 < SIZE:
            DIAGONALS[i].append((r - 1) * SIZE + (c + 1))
        if r + 1 < SIZE and c > 0:
            DIAGONALS[i].append((r + 1) * SIZE + (c - 1))
        if r + 1 < SIZE and c + 1 < SIZE:
            DIAGONALS[i].append((r + 1) * SIZE + (c + 1))

# Strong opening points on 19x19.
OPENING_POINTS_1B = [
    (4, 4), (4, 16), (16, 4), (16, 16),   # 4-4 corners
    (4, 10), (10, 4), (10, 16), (16, 10), # side stars
    (4, 3), (3, 4), (4, 17), (3, 16),
    (16, 3), (17, 4), (16, 17), (17, 16), # 3-4 / 4-3
    (10, 10),                              # center
]
OPENING_POINTS = [(r - 1) * SIZE + (c - 1) for r, c in OPENING_POINTS_1B]
CORNER_44 = {(4, 4), (4, 16), (16, 4), (16, 16)}
CORNER_34_43 = {
    (4, 3), (3, 4), (4, 17), (3, 16),
    (16, 3), (17, 4), (16, 17), (17, 16),
}
SIDE_STAR = {(4, 10), (10, 4), (10, 16), (16, 10)}


def idx_to_action(i: int) -> Tuple[int, int]:
    return (i // SIZE + 1, i % SIZE + 1)


def action_to_idx(r: int, c: int) -> int:
    return (r - 1) * SIZE + (c - 1)


def manhattan(a: int, b: int) -> int:
    ar, ac = divmod(a, SIZE)
    br, bc = divmod(b, SIZE)
    return abs(ar - br) + abs(ac - bc)


def group_and_liberties(board: List[int], start: int) -> Tuple[List[int], set]:
    color = board[start]
    stack = [start]
    seen = {start}
    stones = [start]
    libs = set()

    while stack:
        p = stack.pop()
        for nb in NEIGHBORS[p]:
            v = board[nb]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
                stones.append(nb)
    return stones, libs


def analyze_groups(board: List[int]) -> Tuple[Dict[int, int], Dict[int, dict]]:
    stone_to_gid: Dict[int, int] = {}
    groups: Dict[int, dict] = {}
    gid = 0
    for i, v in enumerate(board):
        if v != 0 and i not in stone_to_gid:
            stones, libs = group_and_liberties(board, i)
            for s in stones:
                stone_to_gid[s] = gid
            groups[gid] = {
                "color": v,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
                "lib_count": len(libs),
            }
            gid += 1
    return stone_to_gid, groups


def is_eyeish(board: List[int], idx: int, player: int) -> bool:
    if board[idx] != 0:
        return False

    # All orthogonal neighbors must be friendly or edge.
    for nb in NEIGHBORS[idx]:
        if board[nb] == -player:
            return False

    # Diagonal heuristic for "true eye"-ish points.
    r, c = divmod(idx, SIZE)
    on_edge = (r == 0 or r == SIZE - 1 or c == 0 or c == SIZE - 1)

    bad_diags = 0
    for d in DIAGONALS[idx]:
        if board[d] == -player:
            bad_diags += 1

    if on_edge:
        return bad_diags == 0
    return bad_diags <= 1


def play_move(
    board: List[int],
    idx: int,
    player: int,
    ko_forbidden: Optional[Tuple[int, ...]] = None,
) -> Tuple[bool, Optional[List[int]], int, int, int]:
    if idx < 0 or idx >= N:
        return False, None, 0, 0, 0
    if board[idx] != 0:
        return False, None, 0, 0, 0

    new_board = board[:]
    new_board[idx] = player

    # Find all adjacent enemy groups with no liberties after placement.
    checked = set()
    to_capture = []
    for nb in NEIGHBORS[idx]:
        if new_board[nb] == -player and nb not in checked:
            stones, libs = group_and_liberties(new_board, nb)
            checked.update(stones)
            if not libs:
                to_capture.extend(stones)

    if to_capture:
        for s in to_capture:
            new_board[s] = 0

    # Suicide check.
    my_stones, my_libs = group_and_liberties(new_board, idx)
    if not my_libs:
        return False, None, 0, 0, 0

    # Simple ko check: disallow recreating the board after our previous move.
    if ko_forbidden is not None and tuple(new_board) == ko_forbidden:
        return False, None, 0, 0, 0

    return True, new_board, len(to_capture), len(my_libs), len(my_stones)


def opening_bonus(idx: int, occupied: List[int], total_stones: int) -> float:
    if total_stones >= 16:
        return 0.0

    r, c = divmod(idx, SIZE)
    r1, c1 = r + 1, c + 1
    pt = (r1, c1)

    line = min(r, c, SIZE - 1 - r, SIZE - 1 - c)
    bonus = 0.0

    if pt in CORNER_44:
        bonus += 24.0 if total_stones < 6 else 10.0
    elif pt in CORNER_34_43:
        bonus += 20.0 if total_stones < 6 else 8.0
    elif pt in SIDE_STAR:
        bonus += 10.0 if total_stones < 10 else 4.0
    elif pt == (10, 10):
        bonus += 4.0 if total_stones < 4 else 0.0

    if total_stones < 8:
        if line == 3:
            bonus += 6.0
        elif line == 2:
            bonus += 4.0
        elif line <= 1:
            bonus -= 6.0

        if occupied:
            md = min(manhattan(idx, p) for p in occupied)
            bonus += 0.8 * min(md, 10)

    return bonus


def local_shape_bonus(board: List[int], idx: int) -> float:
    adj_me = 0
    adj_opp = 0
    empties = 0
    for nb in NEIGHBORS[idx]:
        if board[nb] == 1:
            adj_me += 1
        elif board[nb] == -1:
            adj_opp += 1
        else:
            empties += 1
    return 1.2 * adj_me + 2.0 * adj_opp + 0.8 * empties


def policy(
    me: List[Tuple[int, int]],
    opponent: List[Tuple[int, int]],
    memory: Dict,
) -> Tuple[Tuple[int, int], Dict]:
    if not isinstance(memory, dict):
        memory = {}

    # Build board from our perspective: our stones = +1, opponent = -1.
    board = [0] * N
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[action_to_idx(r, c)] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[action_to_idx(r, c)] = -1

    occupied = [i for i, v in enumerate(board) if v != 0]
    total_stones = len(occupied)

    # Recover last board after our previous move for simple ko detection
    # and for estimating the opponent's last move.
    last_my_board = memory.get("last_my_board")
    if not isinstance(last_my_board, tuple) or len(last_my_board) != N:
        last_my_board = None

    last_opp_move = None
    hot_points = set()
    if last_my_board is not None:
        for i in range(N):
            if last_my_board[i] != board[i]:
                hot_points.add(i)
                if last_my_board[i] == 0 and board[i] == -1:
                    last_opp_move = i

    # Group analysis on current board.
    stone_to_gid, groups = analyze_groups(board)

    capture_targets = defaultdict(int)
    save_targets = defaultdict(int)
    attack_targets = defaultdict(int)
    defend_targets = defaultdict(int)

    candidates = set()

    # Tactical candidate moves from weak groups.
    for gid, g in groups.items():
        libs = g["libs"]
        lib_count = g["lib_count"]
        size = g["size"]
        color = g["color"]

        if lib_count <= 3:
            candidates.update(libs)

        if color == -1:
            if lib_count == 1:
                only_lib = next(iter(libs))
                capture_targets[only_lib] += size
            elif lib_count == 2:
                for lib in libs:
                    attack_targets[lib] += size
        else:
            if lib_count == 1:
                only_lib = next(iter(libs))
                save_targets[only_lib] += size
            elif lib_count == 2:
                for lib in libs:
                    defend_targets[lib] += size

    # Add empty points neighboring existing stones.
    for i in occupied:
        for nb in NEIGHBORS[i]:
            if board[nb] == 0:
                candidates.add(nb)

    # Local response around recent changes.
    for hp in hot_points:
        if board[hp] == 0:
            candidates.add(hp)
        for nb in NEIGHBORS[hp]:
            if board[nb] == 0:
                candidates.add(nb)
            for nb2 in NEIGHBORS[nb]:
                if board[nb2] == 0:
                    candidates.add(nb2)

    # Opening points.
    if total_stones < 20:
        for p in OPENING_POINTS:
            if board[p] == 0:
                candidates.add(p)

    # If the board is still sparse, widen search a bit.
    if total_stones < 8:
        for i in occupied:
            for nb in NEIGHBORS[i]:
                if board[nb] == 0:
                    candidates.add(nb)
                for nb2 in NEIGHBORS[nb]:
                    if board[nb2] == 0:
                        candidates.add(nb2)

    # If no candidates somehow, consider all empties.
    if not candidates:
        candidates = {i for i, v in enumerate(board) if v == 0}

    best_idx = None
    best_board = None
    best_score = -10**18

    def score_move(idx: int, new_board: List[int], captured: int, own_libs: int, own_size: int) -> float:
        score = 0.0

        friendly_groups = set()
        enemy_groups = set()
        for nb in NEIGHBORS[idx]:
            if board[nb] == 1:
                friendly_groups.add(stone_to_gid[nb])
            elif board[nb] == -1:
                enemy_groups.add(stone_to_gid[nb])

        # Urgent tactical gains.
        score += 40.0 * captured
        score += 18.0 * capture_targets.get(idx, 0)
        score += 16.0 * save_targets.get(idx, 0)
        score += 7.0 * attack_targets.get(idx, 0)
        score += 6.0 * defend_targets.get(idx, 0)

        # Connecting our groups is valuable.
        if len(friendly_groups) > 1:
            score += 14.0 * (len(friendly_groups) - 1)
            for gid in friendly_groups:
                if groups[gid]["lib_count"] <= 2:
                    score += 8.0

        # Attack enemy groups with few liberties.
        for gid in enemy_groups:
            g = groups[gid]
            if idx in g["libs"]:
                if g["lib_count"] == 2:
                    score += 10.0 + 2.5 * g["size"]
                elif g["lib_count"] == 3:
                    score += 4.0 + 1.0 * g["size"]

        # Defend our nearby weak groups.
        for gid in friendly_groups:
            g = groups[gid]
            if idx in g["libs"]:
                if g["lib_count"] == 1:
                    score += 25.0 + 4.0 * g["size"]
                elif g["lib_count"] == 2:
                    score += 6.0 + 1.0 * g["size"]

        # Liberty / self-atari considerations.
        score += 3.0 * min(own_libs, 5)
        if own_libs == 1:
            score -= 120.0 if captured == 0 else 35.0
        elif own_libs == 2:
            score -= 10.0

        # Local shape preference.
        score += local_shape_bonus(board, idx)

        # Avoid filling our own likely eyes unless urgent.
        urgent = (captured > 0 or capture_targets.get(idx, 0) > 0 or save_targets.get(idx, 0) > 0)
        if is_eyeish(board, idx, 1) and not urgent:
            score -= 45.0

        # Opening direction.
        score += opening_bonus(idx, occupied, total_stones)

        # Answer local fights.
        if last_opp_move is not None:
            d = manhattan(idx, last_opp_move)
            if d == 1:
                score += 8.0
            elif d == 2:
                score += 5.0
            elif d == 3:
                score += 2.0

        # Early-game aversion to crawling on the first/second line.
        r, c = divmod(idx, SIZE)
        line = min(r, c, SIZE - 1 - r, SIZE - 1 - c)
        if total_stones < 25:
            if line == 0:
                score -= 12.0
            elif line == 1:
                score -= 6.0

        # Mild midgame centrality bonus.
        if 10 <= total_stones < 100:
            score += 0.15 * (18 - (abs(r - 9) + abs(c - 9)))

        # Tiny deterministic tie-breaker.
        score += 1e-6 * (N - idx)

        return score

    # Evaluate tactical candidates first.
    for idx in candidates:
        if board[idx] != 0:
            continue
        legal, new_board, captured, own_libs, own_size = play_move(board, idx, 1, last_my_board)
        if not legal:
            continue
        sc = score_move(idx, new_board, captured, own_libs, own_size)
        if sc > best_score:
            best_score = sc
            best_idx = idx
            best_board = new_board

    # Fallback: scan every empty point if needed.
    if best_idx is None:
        for idx in range(N):
            if board[idx] != 0:
                continue
            legal, new_board, captured, own_libs, own_size = play_move(board, idx, 1, last_my_board)
            if not legal:
                continue
            sc = score_move(idx, new_board, captured, own_libs, own_size)
            if sc > best_score:
                best_score = sc
                best_idx = idx
                best_board = new_board

    # If no legal board play exists, pass.
    if best_idx is None:
        new_memory = dict(memory)
        new_memory["last_my_board"] = tuple(board)
        return (0, 0), new_memory

    new_memory = dict(memory)
    new_memory["last_my_board"] = tuple(best_board)
    return idx_to_action(best_idx), new_memory
