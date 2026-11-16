
from typing import List, Tuple, Dict, Set

SIZE = 19

# Precompute orthogonal neighbors for speed.
NEIGHBORS = [[[] for _ in range(SIZE)] for _ in range(SIZE)]
for r in range(SIZE):
    for c in range(SIZE):
        if r > 0:
            NEIGHBORS[r][c].append((r - 1, c))
        if r + 1 < SIZE:
            NEIGHBORS[r][c].append((r + 1, c))
        if c > 0:
            NEIGHBORS[r][c].append((r, c - 1))
        if c + 1 < SIZE:
            NEIGHBORS[r][c].append((r, c + 1))

# Opening / strategic points (0-based)
STRATEGIC_POINTS = [
    (3, 3), (3, 15), (15, 3), (15, 15),   # 4-4 points
    (9, 9),                                # center
    (3, 9), (9, 3), (9, 15), (15, 9),     # side star-ish
    (6, 6), (6, 12), (12, 6), (12, 12),   # central framework
]

LOCAL_OFFSETS_EARLY = [
    (dr, dc)
    for dr in range(-2, 3)
    for dc in range(-2, 3)
    if not (dr == 0 and dc == 0)
]
LOCAL_OFFSETS_LATE = [
    (dr, dc)
    for dr in range(-1, 2)
    for dc in range(-1, 2)
    if not (dr == 0 and dc == 0)
]


def board_hash(board: List[List[int]]):
    return tuple(tuple(row) for row in board)


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[List[int]]:
    board = [[0] * SIZE for _ in range(SIZE)]
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r - 1][c - 1] = -1
    return board


def group_and_liberties(board: List[List[int]], r: int, c: int):
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


def analyze_groups(board: List[List[int]]):
    visited = [[False] * SIZE for _ in range(SIZE)]
    group_of = [[-1] * SIZE for _ in range(SIZE)]
    groups = []
    occupied = []

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0:
                occupied.append((r, c))
            if board[r][c] == 0 or visited[r][c]:
                continue
            color = board[r][c]
            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in NEIGHBORS[x][y]:
                    v = board[nx][ny]
                    if v == 0:
                        libs.add((nx, ny))
                    elif v == color and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            gid = len(groups)
            for x, y in stones:
                group_of[x][y] = gid
            groups.append({
                "color": color,
                "stones": stones,
                "libs": libs,
            })

    return {
        "groups": groups,
        "group_of": group_of,
        "occupied": occupied,
    }


def simulate_move(board: List[List[int]], move: Tuple[int, int], color: int, ko_forbidden=None):
    """Return (new_board, captured_count, own_lib_count, new_hash) or None if illegal."""
    r, c = move
    if not (0 <= r < SIZE and 0 <= c < SIZE):
        return None
    if board[r][c] != 0:
        return None

    new_board = [row[:] for row in board]
    new_board[r][c] = color

    checked = set()
    captured = 0

    for nx, ny in NEIGHBORS[r][c]:
        if new_board[nx][ny] == -color and (nx, ny) not in checked:
            stones, libs = group_and_liberties(new_board, nx, ny)
            for s in stones:
                checked.add(s)
            if len(libs) == 0:
                captured += len(stones)
                for x, y in stones:
                    new_board[x][y] = 0

    my_stones, my_libs = group_and_liberties(new_board, r, c)
    if len(my_libs) == 0:
        return None  # suicide

    h = board_hash(new_board)
    if ko_forbidden is not None and h == ko_forbidden:
        return None  # simple ko

    return new_board, captured, len(my_libs), h


def eye_like(board: List[List[int]], r: int, c: int, color: int) -> bool:
    """Very cheap own-eye heuristic: all orthogonal neighbors friendly, no opponent orthogonal neighbors."""
    for nx, ny in NEIGHBORS[r][c]:
        if board[nx][ny] == -color:
            return False
        if board[nx][ny] == 0:
            return False
    return True if NEIGHBORS[r][c] else False


def nearest_occupied_distance(occupied: List[Tuple[int, int]], r: int, c: int) -> int:
    if not occupied:
        return 18
    best = 100
    for x, y in occupied:
        d = abs(x - r) + abs(y - c)
        if d < best:
            best = d
    return best


def generate_candidates(board: List[List[int]], analysis, total_stones: int) -> Set[Tuple[int, int]]:
    candidates = set()
    groups = analysis["groups"]
    occupied = analysis["occupied"]

    # Tactical liberties first: endangered groups and attack points.
    for g in groups:
        if len(g["libs"]) <= 2:
            candidates.update(g["libs"])

    # Local moves around stones.
    offsets = LOCAL_OFFSETS_EARLY if total_stones < 40 else LOCAL_OFFSETS_LATE
    for r, c in occupied:
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                candidates.add((nr, nc))

    # Strategic global points.
    for p in STRATEGIC_POINTS:
        if board[p[0]][p[1]] == 0:
            candidates.add(p)

    # If still too few candidates, broaden.
    if len(candidates) < 12:
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == 0:
                    candidates.add((r, c))

    return candidates


def evaluate_move(board: List[List[int]], analysis, move: Tuple[int, int], sim_result, total_stones: int) -> float:
    new_board, captured, own_libs, _ = sim_result
    r, c = move
    rr, cc = r + 1, c + 1

    groups = analysis["groups"]
    group_of = analysis["group_of"]
    occupied = analysis["occupied"]

    score = 0.0

    own_adj = set()
    opp_adj = set()
    for nx, ny in NEIGHBORS[r][c]:
        gid = group_of[nx][ny]
        if gid == -1:
            continue
        if board[nx][ny] == 1:
            own_adj.add(gid)
        elif board[nx][ny] == -1:
            opp_adj.add(gid)

    # Captures are excellent.
    score += 120.0 * captured + 8.0 * captured * captured

    # Connecting multiple friendly groups is valuable.
    if len(own_adj) >= 2:
        score += 18.0 * (len(own_adj) - 1)

    # Saving endangered own groups.
    for gid in own_adj:
        g = groups[gid]
        libs = len(g["libs"])
        size = len(g["stones"])
        if move in g["libs"]:
            if libs == 1:
                score += 150.0 + 10.0 * size
            elif libs == 2:
                score += 35.0 + 2.0 * size
            else:
                score += 4.0

    # Attacking opponent groups.
    for gid in opp_adj:
        g = groups[gid]
        libs = len(g["libs"])
        size = len(g["stones"])
        if move in g["libs"]:
            if libs == 1:
                score += 140.0 + 12.0 * size
            elif libs == 2:
                score += 42.0 + 3.0 * size
            elif libs == 3:
                score += 10.0

    # Self-atari penalty.
    if own_libs == 1:
        score -= 90.0 if captured > 0 else 160.0
    elif own_libs == 2:
        score -= 12.0
    else:
        score += min(own_libs, 4) * 3.0

    # Bonus for leaving adjacent opponent groups weak after the move.
    seen = set()
    for nx, ny in NEIGHBORS[r][c]:
        if new_board[nx][ny] == -1 and (nx, ny) not in seen:
            stones, libs = group_and_liberties(new_board, nx, ny)
            for s in stones:
                seen.add(s)
            l = len(libs)
            size = len(stones)
            if l == 1:
                score += 20.0 + 2.0 * size
            elif l == 2:
                score += 4.0

    # Avoid filling our own obvious eye unless tactical.
    if captured == 0 and eye_like(board, r, c, 1):
        score -= 45.0

    # Opening / shape preference.
    if total_stones < 8:
        if (rr, cc) in ((4, 4), (4, 16), (16, 4), (16, 16)):
            score += 28.0
        elif (rr, cc) == (10, 10):
            score += 20.0
        elif (rr, cc) in ((4, 10), (10, 4), (10, 16), (16, 10)):
            score += 14.0
        score += 2.0 * min(nearest_occupied_distance(occupied, r, c), 8)
    else:
        line = min(rr, cc, 20 - rr, 20 - cc)  # 1..10
        if line == 4:
            score += 6.0
        elif line == 3:
            score += 4.0
        elif line == 2:
            score += 1.0
        elif line == 1 and captured == 0:
            score -= 6.0

        if not own_adj and not opp_adj:
            d = nearest_occupied_distance(occupied, r, c)
            if d >= 4:
                score -= 10.0
            elif d == 3:
                score -= 4.0

    # Tiny center tiebreaker for determinism.
    score += 0.01 * (10 - (abs(rr - 10) + abs(cc - 10)))

    return score


def choose_best_move(board: List[List[int]], analysis, ko_forbidden, total_stones: int):
    candidates = generate_candidates(board, analysis, total_stones)

    best_move = None
    best_score = -10**18
    best_hash = None

    # Evaluate candidate set first.
    for move in candidates:
        sim = simulate_move(board, move, 1, ko_forbidden)
        if sim is None:
            continue
        score = evaluate_move(board, analysis, move, sim, total_stones)
        if score > best_score or (score == best_score and (best_move is None or move < best_move)):
            best_score = score
            best_move = move
            best_hash = sim[3]

    if best_move is not None:
        return best_move, best_hash

    # Full-board legal fallback to guarantee a legal move if one exists.
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0:
                continue
            sim = simulate_move(board, (r, c), 1, ko_forbidden)
            if sim is not None:
                return (r, c), sim[3]

    return None, board_hash(board)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = build_board(me, opponent)
    total_stones = len(me) + len(opponent)

    # Simple ko defense: forbid recreating the board after our previous move.
    ko_forbidden = memory.get("my_last_result_hash")

    analysis = analyze_groups(board)
    move, result_hash = choose_best_move(board, analysis, ko_forbidden, total_stones)

    if move is None:
        # No legal move found: pass.
        return (0, 0), {"my_last_result_hash": board_hash(board)}

    return (move[0] + 1, move[1] + 1), {"my_last_result_hash": result_hash}
