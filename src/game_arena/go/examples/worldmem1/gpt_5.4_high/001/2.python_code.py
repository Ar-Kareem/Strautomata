
from collections import defaultdict

BOARD_SIZE = 19

# Precompute orthogonal neighbors for every point.
NEIGHBORS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        if r > 0:
            NEIGHBORS[r][c].append((r - 1, c))
        if r + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r + 1, c))
        if c > 0:
            NEIGHBORS[r][c].append((r, c - 1))
        if c + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r, c + 1))

# Good opening points on 19x19, 0-based.
OPENING_ORDER = [
    (3, 3), (3, 15), (15, 3), (15, 15),   # 4-4 corners
    (3, 9), (9, 3), (9, 15), (15, 9),     # side star points
    (9, 9),                               # tengen
    (6, 6), (6, 12), (12, 6), (12, 12),   # 7-7 style influence points
    (3, 6), (6, 3), (3, 12), (12, 3),
    (15, 6), (6, 15), (15, 12), (12, 15),
]
OPENING_BONUS = {pt: 120 - 3 * i for i, pt in enumerate(OPENING_ORDER)}

STAR_AND_CENTER = [
    (3, 3), (3, 9), (3, 15),
    (9, 3), (9, 9), (9, 15),
    (15, 3), (15, 9), (15, 15),
]


def board_from_lists(me, opponent):
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = -1
    return board


def board_hash(board):
    return tuple(board[r][c] for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))


def collect_group(board, r, c):
    color = board[r][c]
    stones = {(r, c)}
    liberties = set()
    stack = [(r, c)]

    while stack:
        x, y = stack.pop()
        for nx, ny in NEIGHBORS[x][y]:
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in stones:
                stones.add((nx, ny))
                stack.append((nx, ny))
    return stones, liberties


def analyze_groups(board):
    visited = set()
    my_groups = []
    opp_groups = []
    my_map = {}
    opp_map = {}

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0 or (r, c) in visited:
                continue
            stones, liberties = collect_group(board, r, c)
            visited.update(stones)
            info = {
                "stones": stones,
                "libs": liberties,
                "size": len(stones),
                "lib_count": len(liberties),
            }
            if board[r][c] == 1:
                idx = len(my_groups)
                my_groups.append(info)
                for s in stones:
                    my_map[s] = idx
            else:
                idx = len(opp_groups)
                opp_groups.append(info)
                for s in stones:
                    opp_map[s] = idx

    return my_groups, opp_groups, my_map, opp_map


def simulate_move(board, move, ko_board_hash=None):
    r, c = move
    if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
        return None
    if board[r][c] != 0:
        return None

    new_board = [row[:] for row in board]
    new_board[r][c] = 1

    checked = set()
    captured = set()

    # Capture adjacent opponent groups with no liberties.
    for nx, ny in NEIGHBORS[r][c]:
        if new_board[nx][ny] == -1 and (nx, ny) not in checked:
            stones, liberties = collect_group(new_board, nx, ny)
            checked.update(stones)
            if not liberties:
                captured.update(stones)

    if captured:
        for x, y in captured:
            new_board[x][y] = 0

    # Suicide check.
    my_stones, my_libs = collect_group(new_board, r, c)
    if not my_libs:
        return None

    # Simple ko check against the board after our previous move.
    if ko_board_hash is not None and board_hash(new_board) == ko_board_hash:
        return None

    return new_board, len(captured), len(my_stones), len(my_libs)


def is_own_eye_fill(board, move):
    r, c = move
    if board[r][c] != 0:
        return False
    nbrs = NEIGHBORS[r][c]
    if not nbrs:
        return False
    # Rough eye detection: all orthogonal neighbors are ours.
    return all(board[nx][ny] == 1 for nx, ny in nbrs)


def positional_bonus(move, total_stones):
    r, c = move
    d_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    score = 0

    if total_stones < 20:
        score += OPENING_BONUS.get(move, 0)
        if d_edge == 3:       # 4th line
            score += 30
        elif d_edge == 2:     # 3rd line
            score += 18
        elif d_edge == 4:     # 5th line
            score += 10
        elif d_edge == 1:     # 2nd line too early
            score -= 18
        elif d_edge == 0:     # 1st line too early
            score -= 40
    elif total_stones < 50:
        if d_edge == 0:
            score -= 8
        elif d_edge == 1:
            score -= 3

    return score


def generate_candidates(board, my_groups, opp_groups, total_stones):
    candidates = set()

    # Opening points.
    if total_stones < 10:
        for pt in OPENING_ORDER:
            if board[pt[0]][pt[1]] == 0:
                candidates.add(pt)

    # Tactical liberties of weak groups.
    for g in my_groups:
        if g["lib_count"] <= 3:
            candidates.update(g["libs"])
    for g in opp_groups:
        if g["lib_count"] <= 3:
            candidates.update(g["libs"])

    # Star points and center remain useful throughout.
    for pt in STAR_AND_CENTER:
        if board[pt[0]][pt[1]] == 0:
            candidates.add(pt)

    occupied = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                occupied.append((r, c))

    if not occupied:
        return candidates

    # Local neighborhood around existing stones.
    radius = 2 if total_stones < 60 else 1
    for r, c in occupied:
        for dr in range(-radius, radius + 1):
            nr = r + dr
            if not (0 <= nr < BOARD_SIZE):
                continue
            for dc in range(-radius, radius + 1):
                nc = c + dc
                if not (0 <= nc < BOARD_SIZE):
                    continue
                if board[nr][nc] == 0:
                    candidates.add((nr, nc))

    # If still too sparse, expand a little.
    if len(candidates) < 25 and total_stones > 0:
        for r, c in occupied:
            for dr in range(-2, 3):
                nr = r + dr
                if not (0 <= nr < BOARD_SIZE):
                    continue
                for dc in range(-2, 3):
                    nc = c + dc
                    if not (0 <= nc < BOARD_SIZE):
                        continue
                    if board[nr][nc] == 0:
                        candidates.add((nr, nc))

    return candidates


def evaluate_move(
    board,
    move,
    sim_result,
    total_stones,
    my_groups,
    opp_groups,
    my_map,
    opp_map,
    capture_targets,
    save_targets,
    pressure_targets,
    strengthen_targets,
):
    new_board, captured_count, new_size, new_libs = sim_result
    r, c = move

    score = 0

    # Big tactical priorities.
    score += captured_count * 1000
    score += capture_targets.get(move, 0) * 500
    score += save_targets.get(move, 0) * 350
    score += pressure_targets.get(move, 0) * 60
    score += strengthen_targets.get(move, 0) * 35

    # Opening / global placement.
    score += positional_bonus(move, total_stones)

    # Adjacent structure.
    adj_my_groups = set()
    adj_opp_groups = set()
    adj_my_stones = 0
    adj_opp_stones = 0

    for nx, ny in NEIGHBORS[r][c]:
        if board[nx][ny] == 1:
            adj_my_stones += 1
            adj_my_groups.add(my_map[(nx, ny)])
        elif board[nx][ny] == -1:
            adj_opp_stones += 1
            adj_opp_groups.add(opp_map[(nx, ny)])

    score += adj_my_stones * 6
    score += adj_opp_stones * 5

    # Connecting our own groups is good.
    if len(adj_my_groups) >= 2:
        score += 45 * (len(adj_my_groups) - 1)
        weak_connected = sum(1 for gid in adj_my_groups if my_groups[gid]["lib_count"] <= 2)
        score += 25 * weak_connected

    # Cutting / touching multiple opponent groups is often useful.
    if len(adj_opp_groups) >= 2:
        score += 30 * (len(adj_opp_groups) - 1)

    # Safety of the new group.
    score += min(new_libs, 4) * 18
    score += new_size * 2

    if new_libs == 1:
        score -= 450 if captured_count == 0 else 100
    elif new_libs == 2 and captured_count == 0 and new_size >= 4:
        score -= 40

    # Avoid filling obvious own eyes unless capturing.
    if captured_count == 0 and is_own_eye_fill(board, move):
        score -= 220

    # Reward successfully saving adjacent weak groups.
    for gid in adj_my_groups:
        g = my_groups[gid]
        if g["lib_count"] == 1 and new_libs >= 2:
            score += 140 * g["size"]
        elif g["lib_count"] == 2 and new_libs >= 3:
            score += 20 * g["size"]

    # Reward attacking adjacent opponent groups if they remain weak after the move.
    for gid in adj_opp_groups:
        g = opp_groups[gid]
        alive_stone = None
        for sx, sy in g["stones"]:
            if new_board[sx][sy] == -1:
                alive_stone = (sx, sy)
                break
        if alive_stone is None:
            continue  # already counted via capture
        _, libs2 = collect_group(new_board, alive_stone[0], alive_stone[1])
        nl = len(libs2)
        if nl == 1:
            score += 120 + 15 * g["size"]
        elif nl == 2 and g["lib_count"] > 2:
            score += 25 + 4 * g["size"]
        elif nl < g["lib_count"]:
            score += 10 * g["size"]

    # Small preference for moves that stay active rather than drifting.
    if total_stones >= 10 and adj_my_stones == 0 and adj_opp_stones == 0:
        score -= 15

    return score


def choose_legal_fallback(board, ko_board_hash):
    # Prefer opening points if still legal.
    for move in OPENING_ORDER:
        if board[move[0]][move[1]] == 0:
            sim = simulate_move(board, move, ko_board_hash)
            if sim is not None:
                return move, sim

    # Otherwise first legal move found.
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                sim = simulate_move(board, (r, c), ko_board_hash)
                if sim is not None:
                    return (r, c), sim

    return None, None


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    board = board_from_lists(me, opponent)
    total_stones = len(me) + len(opponent)
    ko_board_hash = memory.get("ko_board")
    if not isinstance(ko_board_hash, tuple):
        ko_board_hash = None

    my_groups, opp_groups, my_map, opp_map = analyze_groups(board)

    # Tactical target maps from current position.
    capture_targets = defaultdict(int)     # move -> opponent stones captured now
    save_targets = defaultdict(int)        # move -> own stones saved from atari
    pressure_targets = defaultdict(int)    # move -> pressure on 2-lib opponent groups
    strengthen_targets = defaultdict(int)  # move -> strengthen 2-lib own groups

    for g in opp_groups:
        if g["lib_count"] == 1:
            lib = next(iter(g["libs"]))
            capture_targets[lib] += g["size"]
        elif g["lib_count"] == 2:
            for lib in g["libs"]:
                pressure_targets[lib] += g["size"]

    for g in my_groups:
        if g["lib_count"] == 1:
            lib = next(iter(g["libs"]))
            save_targets[lib] += g["size"]
        elif g["lib_count"] == 2:
            for lib in g["libs"]:
                strengthen_targets[lib] += g["size"]

    candidates = generate_candidates(board, my_groups, opp_groups, total_stones)

    best_move = None
    best_sim = None
    best_score = -10**18

    # Evaluate candidate moves.
    for move in candidates:
        sim = simulate_move(board, move, ko_board_hash)
        if sim is None:
            continue
        score = evaluate_move(
            board,
            move,
            sim,
            total_stones,
            my_groups,
            opp_groups,
            my_map,
            opp_map,
            capture_targets,
            save_targets,
            pressure_targets,
            strengthen_targets,
        )
        if best_move is None or score > best_score or (score == best_score and move < best_move):
            best_move = move
            best_sim = sim
            best_score = score

    # Safety fallback: full legal scan.
    if best_move is None:
        best_move, best_sim = choose_legal_fallback(board, ko_board_hash)

    # If no legal board move exists, pass.
    if best_move is None:
        return (0, 0), {"ko_board": board_hash(board)}

    new_board = best_sim[0]
    new_memory = {"ko_board": board_hash(new_board)}
    return (best_move[0] + 1, best_move[1] + 1), new_memory
