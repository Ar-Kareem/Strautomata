
from __future__ import annotations

from collections import deque
from typing import Dict, List, Tuple, Set

BOARD_SIZE = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
STAR_POINTS = [
    (3, 3), (3, 9), (3, 15),
    (9, 3), (9, 9), (9, 15),
    (15, 3), (15, 9), (15, 15),
]  # 0-based: 4-4, 4-10, etc.


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc):
            yield rr, cc


def board_hash(board: List[List[int]]) -> bytes:
    return bytes(cell + 1 for row in board for cell in row)  # -1,0,1 -> 0,1,2


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[List[int]]:
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        r0, c0 = r - 1, c - 1
        if in_bounds(r0, c0):
            board[r0][c0] = 1
    for r, c in opponent:
        r0, c0 = r - 1, c - 1
        if in_bounds(r0, c0) and board[r0][c0] == 0:
            board[r0][c0] = -1
    return board


def flood_group(board: List[List[int]], r: int, c: int):
    color = board[r][c]
    q = deque([(r, c)])
    seen = {(r, c)}
    stones = []
    libs = set()

    while q:
        cr, cc = q.popleft()
        stones.append((cr, cc))
        for nr, nc in neighbors(cr, cc):
            val = board[nr][nc]
            if val == 0:
                libs.add((nr, nc))
            elif val == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return stones, libs


def analyze_groups(board: List[List[int]]):
    groups = []
    pos_to_gid = {}
    seen = set()

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0 or (r, c) in seen:
                continue
            stones, libs = flood_group(board, r, c)
            gid = len(groups)
            color = board[r][c]
            g = {
                "color": color,
                "stones": stones,
                "libs": libs,
            }
            groups.append(g)
            for p in stones:
                seen.add(p)
                pos_to_gid[p] = gid
    return groups, pos_to_gid


def is_eye_like(board: List[List[int]], r: int, c: int, player: int) -> bool:
    if not in_bounds(r, c) or board[r][c] != 0:
        return False

    # Orthogonals must be player stones or off-board
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc] != player:
            return False

    # Approximate true-eye check using diagonals
    bad_diags = 0
    on_edge = r == 0 or r == BOARD_SIZE - 1 or c == 0 or c == BOARD_SIZE - 1
    for dr, dc in DIAGS:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc] == -player:
            bad_diags += 1

    allowed_bad = 1 if on_edge else 0
    return bad_diags <= allowed_bad


def nearest_manhattan(move: Tuple[int, int], stones: List[Tuple[int, int]]) -> int:
    if not stones:
        return 99
    r, c = move
    return min(abs(r - sr) + abs(c - sc) for sr, sc in stones)


def local_nonempty_count(board: List[List[int]], r: int, c: int, radius: int = 2) -> int:
    cnt = 0
    for rr in range(max(0, r - radius), min(BOARD_SIZE, r + radius + 1)):
        for cc in range(max(0, c - radius), min(BOARD_SIZE, c + radius + 1)):
            if (rr != r or cc != c) and board[rr][cc] != 0:
                cnt += 1
    return cnt


def simulate_move(
    board: List[List[int]],
    move: Tuple[int, int],
    player: int,
    forbidden_hashes: Set[bytes],
):
    r, c = move
    if not in_bounds(r, c) or board[r][c] != 0:
        return False, None, None

    new_board = [row[:] for row in board]
    new_board[r][c] = player

    captured = 0
    checked_enemy = set()

    # Capture adjacent enemy groups with no liberties
    for nr, nc in neighbors(r, c):
        if new_board[nr][nc] == -player and (nr, nc) not in checked_enemy:
            stones, libs = flood_group(new_board, nr, nc)
            for s in stones:
                checked_enemy.add(s)
            if not libs:
                captured += len(stones)
                for sr, sc in stones:
                    new_board[sr][sc] = 0

    # Suicide check
    my_stones, my_libs = flood_group(new_board, r, c)
    if not my_libs:
        return False, None, None

    h = board_hash(new_board)
    if h in forbidden_hashes:
        return False, None, None

    info = {
        "captured": captured,
        "self_libs": len(my_libs),
        "self_group_size": len(my_stones),
        "hash": h,
    }
    return True, new_board, info


def generate_candidates(
    board: List[List[int]],
    groups,
    own_save_moves: Dict[Tuple[int, int], int],
    opp_kill_moves: Dict[Tuple[int, int], int],
    last_opp_moves: List[Tuple[int, int]],
):
    occupied = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                occupied.append((r, c))

    total_stones = len(occupied)
    cand = set()

    if total_stones == 0:
        return [
            (3, 3), (15, 15), (3, 15), (15, 3),
            (3, 9), (9, 3), (15, 9), (9, 15), (9, 9),
        ]

    radius = 3 if total_stones < 8 else 2
    for r, c in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if max(abs(dr), abs(dc)) > radius:
                    continue
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    cand.add((rr, cc))

    for mv in own_save_moves:
        cand.add(mv)
    for mv in opp_kill_moves:
        cand.add(mv)

    for g in groups:
        if len(g["libs"]) <= 2:
            cand.update(g["libs"])

    for mv in STAR_POINTS:
        if board[mv[0]][mv[1]] == 0:
            cand.add(mv)

    for mv in last_opp_moves:
        lr, lc = mv
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                rr, cc = lr + dr, lc + dc
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    cand.add((rr, cc))

    # If still too few, add all empty points with nearby stones in radius 3
    if len(cand) < 20:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != 0:
                    continue
                if local_nonempty_count(board, r, c, 3) > 0:
                    cand.add((r, c))

    return sorted(cand)


def evaluate_move(
    board: List[List[int]],
    new_board: List[List[int]],
    move: Tuple[int, int],
    info: Dict,
    groups,
    pos_to_gid: Dict[Tuple[int, int], int],
    own_save_moves: Dict[Tuple[int, int], int],
    opp_kill_moves: Dict[Tuple[int, int], int],
    last_opp_moves: List[Tuple[int, int]],
    all_stones: List[Tuple[int, int]],
) -> float:
    r, c = move
    total_stones = len(all_stones)
    captured = info["captured"]
    self_libs = info["self_libs"]
    self_size = info["self_group_size"]

    score = 0.0

    # Immediate tactical priorities
    score += 2200.0 * opp_kill_moves.get(move, 0)
    score += 1800.0 * own_save_moves.get(move, 0)
    score += 360.0 * captured
    if captured > 0:
        score += 180.0

    # Adjacent current groups
    adj_friend_gids = set()
    adj_enemy_gids = set()
    adj_empty = 0
    for nr, nc in neighbors(r, c):
        val = board[nr][nc]
        if val == 0:
            adj_empty += 1
        elif val == 1:
            gid = pos_to_gid.get((nr, nc))
            if gid is not None:
                adj_friend_gids.add(gid)
        elif val == -1:
            gid = pos_to_gid.get((nr, nc))
            if gid is not None:
                adj_enemy_gids.add(gid)

    # Connect and strengthen own groups
    score += 120.0 * len(adj_friend_gids)
    if len(adj_friend_gids) >= 2:
        score += 280.0 * (len(adj_friend_gids) - 1)

    # Attack adjacent opponent groups based on their current liberties
    for gid in adj_enemy_gids:
        g = groups[gid]
        glibs = len(g["libs"])
        gsize = len(g["stones"])
        if glibs == 1:
            score += 1700.0 + 130.0 * gsize
        elif glibs == 2:
            score += 240.0 + 28.0 * gsize
        elif glibs == 3:
            score += 70.0 + 8.0 * gsize

    # Defend adjacent own groups based on their current liberties
    for gid in adj_friend_gids:
        g = groups[gid]
        glibs = len(g["libs"])
        gsize = len(g["stones"])
        if glibs == 1:
            score += 1200.0 + 90.0 * gsize
        elif glibs == 2:
            score += 180.0 + 18.0 * gsize

    # Resulting group health
    score += 60.0 * min(self_libs, 6)
    score += 16.0 * min(self_size, 12)

    if self_libs == 1 and captured == 0:
        score -= 2600.0 + 90.0 * self_size
    elif self_libs == 2:
        score -= 160.0

    # Look at newly pressured adjacent enemy groups after the move
    seen_enemy = set()
    for nr, nc in neighbors(r, c):
        if new_board[nr][nc] == -1 and (nr, nc) not in seen_enemy:
            stones, libs = flood_group(new_board, nr, nc)
            for s in stones:
                seen_enemy.add(s)
            if len(libs) == 1:
                score += 300.0 + 36.0 * len(stones)
            elif len(libs) == 2:
                score += 70.0 + 10.0 * len(stones)

    # Eye-filling penalty
    if is_eye_like(board, r, c, 1) and captured == 0 and own_save_moves.get(move, 0) == 0 and opp_kill_moves.get(move, 0) == 0:
        score -= 900.0

    # Opening preferences
    if total_stones < 10:
        if move in STAR_POINTS:
            score += 320.0
        if move == (9, 9):
            score += 120.0

        dist_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
        if dist_edge == 0:
            score -= 220.0
        elif dist_edge == 1:
            score -= 90.0
        elif dist_edge == 2:
            score += 50.0
        elif dist_edge == 3:
            score += 120.0

        nearest = nearest_manhattan(move, all_stones)
        if 4 <= nearest <= 8:
            score += 130.0
        elif nearest <= 1:
            score -= 140.0
    else:
        local = local_nonempty_count(board, r, c, 2)
        score += 12.0 * local
        if local == 0:
            score -= 160.0

    # React near inferred last opponent move
    if last_opp_moves:
        d = min(abs(r - lr) + abs(c - lc) for lr, lc in last_opp_moves)
        if d == 1:
            score += 110.0
        elif d == 2:
            score += 70.0
        elif d > 6:
            score -= 60.0

    # Slight preference for touching empty space
    score += 10.0 * adj_empty

    # Small centrality preference in non-opening middlegame
    if total_stones >= 10:
        center_dist = abs(r - 9) + abs(c - 9)
        score += max(0.0, 18.0 - center_dist) * 1.5

    return score


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if not isinstance(memory, dict):
        memory = {}

    board = build_board(me, opponent)

    me0 = [(r - 1, c - 1) for r, c in me if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE]
    opp0 = [(r - 1, c - 1) for r, c in opponent if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE]
    all_stones = me0 + opp0

    # Recover memory safely
    prev_opp_mem = memory.get("prev_opponent", [])
    if isinstance(prev_opp_mem, list):
        prev_opp = set(tuple(x) for x in prev_opp_mem)
    elif isinstance(prev_opp_mem, set):
        prev_opp = set(tuple(x) for x in prev_opp_mem)
    else:
        prev_opp = set()

    last_opp_moves = list(set(opp0) - prev_opp)
    if len(last_opp_moves) > 3:
        last_opp_moves = last_opp_moves[:3]

    seen_after = memory.get("after_my_hashes", set())
    if not isinstance(seen_after, set):
        try:
            seen_after = set(seen_after)
        except Exception:
            seen_after = set()

    groups, pos_to_gid = analyze_groups(board)

    own_save_moves: Dict[Tuple[int, int], int] = {}
    opp_kill_moves: Dict[Tuple[int, int], int] = {}

    for g in groups:
        libs = g["libs"]
        if len(libs) == 1:
            mv = next(iter(libs))
            if g["color"] == 1:
                own_save_moves[mv] = own_save_moves.get(mv, 0) + len(g["stones"])
            else:
                opp_kill_moves[mv] = opp_kill_moves.get(mv, 0) + len(g["stones"])

    candidates = generate_candidates(board, groups, own_save_moves, opp_kill_moves, last_opp_moves)

    best_move = None
    best_score = float("-inf")
    best_hash = None

    # Search candidate moves
    for mv in candidates:
        legal, new_board, info = simulate_move(board, mv, 1, seen_after)
        if not legal:
            continue
        score = evaluate_move(
            board, new_board, mv, info,
            groups, pos_to_gid,
            own_save_moves, opp_kill_moves,
            last_opp_moves, all_stones
        )
        if score > best_score:
            best_score = score
            best_move = mv
            best_hash = info["hash"]

    # Full-board fallback if necessary
    if best_move is None:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != 0:
                    continue
                legal, new_board, info = simulate_move(board, (r, c), 1, seen_after)
                if not legal:
                    continue
                score = evaluate_move(
                    board, new_board, (r, c), info,
                    groups, pos_to_gid,
                    own_save_moves, opp_kill_moves,
                    last_opp_moves, all_stones
                )
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                    best_hash = info["hash"]

    # If no legal move exists, pass
    if best_move is None:
        memory["prev_opponent"] = list(set(opp0))
        return (0, 0), memory

    # Update memory
    seen_after.add(best_hash)
    memory["after_my_hashes"] = seen_after
    memory["prev_opponent"] = list(set(opp0))

    return (best_move[0] + 1, best_move[1] + 1), memory
