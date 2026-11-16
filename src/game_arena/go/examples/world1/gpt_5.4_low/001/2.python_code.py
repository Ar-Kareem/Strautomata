
from collections import deque

N = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1

    empties = []
    stones = 0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                empties.append((r, c))
            else:
                stones += 1

    my_groups, opp_groups, group_info = analyze_groups(board)

    candidates = set()

    # Tactical candidates: liberties of groups in danger or attackable groups.
    for gid in my_groups:
        info = group_info[gid]
        if info["libs_count"] <= 2:
            candidates.update(info["libs"])

    for gid in opp_groups:
        info = group_info[gid]
        if info["libs_count"] <= 2:
            candidates.update(info["libs"])

    # Local fighting moves around existing stones.
    for r, c in me:
        rr, cc = r - 1, c - 1
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    candidates.add((nr, nc))

    for r, c in opponent:
        rr, cc = r - 1, c - 1
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    candidates.add((nr, nc))

    # Opening / fallback shape points.
    opening_points = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
        (3, 15), (15, 3),
        (3, 9), (9, 3), (9, 15), (15, 9),
        (4, 4), (4, 10), (4, 16),
        (10, 4), (10, 10), (10, 16),
        (16, 4), (16, 10), (16, 16),
    ]
    for r, c in opening_points:
        rr, cc = r, c
        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
            candidates.add((rr, cc))

    # If still sparse, add all empties to avoid missing obvious legal moves.
    if stones < 8 or len(candidates) < 20:
        candidates.update(empties)

    best_move = None
    best_score = -10**18

    for move in candidates:
        if board[move[0]][move[1]] != 0:
            continue
        sim = simulate_move(board, 1, move)
        if sim is None:
            continue
        new_board, captured, own_libs = sim
        score = evaluate_move(board, group_info, move, new_board, captured, own_libs)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # Absolute fallback: return first legal move found.
    for r, c in empties:
        if simulate_move(board, 1, (r, c)) is not None:
            return (r + 1, c + 1)

    return (0, 0)


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def collect_group(board, r, c):
    color = board[r][c]
    q = deque([(r, c)])
    seen = {(r, c)}
    stones = []
    libs = set()

    while q:
        cr, cc = q.popleft()
        stones.append((cr, cc))
        for nr, nc in neighbors(cr, cc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return stones, libs


def analyze_groups(board):
    visited = [[False] * N for _ in range(N)]
    my_groups = []
    opp_groups = []
    group_info = {}
    gid = 0

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 or visited[r][c]:
                continue
            stones, libs = collect_group(board, r, c)
            for sr, sc in stones:
                visited[sr][sc] = True
            info = {
                "color": board[r][c],
                "stones": stones,
                "stones_count": len(stones),
                "libs": libs,
                "libs_count": len(libs),
            }
            group_info[gid] = info
            if board[r][c] == 1:
                my_groups.append(gid)
            else:
                opp_groups.append(gid)
            gid += 1

    return my_groups, opp_groups, group_info


def simulate_move(board, player, move):
    r, c = move
    if not (0 <= r < N and 0 <= c < N):
        return None
    if board[r][c] != 0:
        return None

    new_board = [row[:] for row in board]
    new_board[r][c] = player
    opponent = -player
    captured = 0
    checked = set()

    # Capture adjacent opponent groups with no liberties.
    for nr, nc in neighbors(r, c):
        if new_board[nr][nc] == opponent and (nr, nc) not in checked:
            stones, libs = collect_group(new_board, nr, nc)
            checked.update(stones)
            if len(libs) == 0:
                captured += len(stones)
                for sr, sc in stones:
                    new_board[sr][sc] = 0

    # Check suicide.
    stones, libs = collect_group(new_board, r, c)
    if len(libs) == 0:
        return None

    return new_board, captured, len(libs)


def evaluate_move(board, group_info, move, new_board, captured, own_libs):
    r, c = move
    score = 0

    # Highest priority: capturing.
    score += captured * 100000

    # Save own groups in atari by playing their last liberty.
    saved_size = 0
    saved_groups = 0
    for info in group_info.values():
        if info["color"] == 1 and info["libs_count"] == 1 and move in info["libs"]:
            saved_size += info["stones_count"]
            saved_groups += 1
    score += saved_size * 30000 + saved_groups * 20000

    # Attack opponent groups by taking one of their last liberties.
    pressured_size = 0
    kill_targets = 0
    atari_targets = 0
    for info in group_info.values():
        if info["color"] == -1 and move in info["libs"]:
            if info["libs_count"] == 1:
                kill_targets += info["stones_count"]
            elif info["libs_count"] == 2:
                atari_targets += info["stones_count"]
            pressured_size += info["stones_count"]
    score += kill_targets * 50000
    score += atari_targets * 8000
    score += pressured_size * 500

    # Connectivity / local shape.
    adjacent_my = 0
    adjacent_opp = 0
    distinct_my_groups = set()
    distinct_opp_groups = set()

    # Build quick group map near move from original board.
    stone_to_gid = {}
    for gid, info in group_info.items():
        for sr, sc in info["stones"]:
            stone_to_gid[(sr, sc)] = gid

    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1:
            adjacent_my += 1
            distinct_my_groups.add(stone_to_gid[(nr, nc)])
        elif board[nr][nc] == -1:
            adjacent_opp += 1
            distinct_opp_groups.add(stone_to_gid[(nr, nc)])

    score += adjacent_my * 1200
    score += adjacent_opp * 900

    # Connecting multiple groups is strong.
    if len(distinct_my_groups) >= 2:
        score += 5000 * len(distinct_my_groups)

    # Touching multiple opponent groups increases fighting value.
    if len(distinct_opp_groups) >= 2:
        score += 1800 * len(distinct_opp_groups)

    # Resulting liberties.
    score += own_libs * 250

    # Prefer central but not blindly.
    center_dist = abs(r - 9) + abs(c - 9)
    score += 120 - center_dist * 8

    # Opening preferences: star points / center.
    if (r, c) in {
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
        (4, 4), (4, 10), (4, 16),
        (10, 4), (10, 10), (10, 16),
        (16, 4), (16, 10), (16, 16),
    }:
        score += 300

    # Mild penalty for filling a quiet own eye.
    if looks_like_own_eye(board, move):
        score -= 6000

    # Bonus for reducing opponent liberties after the move.
    score += count_adjacent_opp_in_atari(new_board, move) * 2500

    return score


def looks_like_own_eye(board, move):
    r, c = move
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == -1:
            return False
    # All orthogonal neighbors are own stones or edge.
    own_like = True
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            if board[nr][nc] != 1:
                own_like = False
                break
    if not own_like:
        return False

    # Diagonal check: if too many bad diagonals, not a true eye but still interior.
    bad_diag = 0
    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if board[nr][nc] == -1:
                    bad_diag += 1
    return bad_diag == 0


def count_adjacent_opp_in_atari(board, move):
    r, c = move
    seen = set()
    cnt = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == -1 and (nr, nc) not in seen:
            stones, libs = collect_group(board, nr, nc)
            for s in stones:
                seen.add(s)
            if len(libs) == 1:
                cnt += len(stones)
    return cnt
