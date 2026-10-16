
from collections import deque, defaultdict

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = 2

STAR_POINTS = [
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
]
OPENING_PRIORITY = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)
]


def neighbors(r: int, c: int):
    if r > 1:
        yield (r - 1, c)
    if r < BOARD_SIZE:
        yield (r + 1, c)
    if c > 1:
        yield (r, c - 1)
    if c < BOARD_SIZE:
        yield (r, c + 1)


def diagonals(r: int, c: int):
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield (nr, nc)


def build_board(me, opponent):
    board = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]

    # Place opponent first, then me only on empty points.
    # This is robust to malformed input without crashing.
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r][c] = OPP
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE and board[r][c] == EMPTY:
            board[r][c] = ME
    return board


def group_and_liberties(board, r: int, c: int):
    color = board[r][c]
    if color == EMPTY:
        return [], set()

    stack = [(r, c)]
    visited = {(r, c)}
    stones = []
    libs = set()

    while stack:
        cr, cc = stack.pop()
        stones.append((cr, cc))
        for nr, nc in neighbors(cr, cc):
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in visited:
                visited.add((nr, nc))
                stack.append((nr, nc))

    return stones, libs


def analyze_color(board, color: int):
    visited = set()
    groups = []
    pos_to_gid = {}

    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == color and (r, c) not in visited:
                stones, libs = group_and_liberties(board, r, c)
                gid = len(groups)
                groups.append((stones, libs))
                for p in stones:
                    visited.add(p)
                    pos_to_gid[p] = gid
    return groups, pos_to_gid


def simulate_move(board, r: int, c: int):
    """Return move features if legal, else None."""
    if not (1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE):
        return None
    if board[r][c] != EMPTY:
        return None

    temp = [row[:] for row in board]
    temp[r][c] = ME

    # Find all adjacent opponent groups with zero liberties after placement.
    to_remove = []
    seen = set()
    for nr, nc in neighbors(r, c):
        if temp[nr][nc] == OPP and (nr, nc) not in seen:
            stones, libs = group_and_liberties(temp, nr, nc)
            for s in stones:
                seen.add(s)
            if len(libs) == 0:
                to_remove.extend(stones)

    if to_remove:
        for sr, sc in to_remove:
            temp[sr][sc] = EMPTY

    my_stones, my_libs = group_and_liberties(temp, r, c)
    if len(my_libs) == 0:
        return None  # suicide

    return {
        "board": temp,
        "captured": len(to_remove),
        "group_size": len(my_stones),
        "libs": len(my_libs),
        "stones": my_stones,
    }


def simple_true_eye(board, r: int, c: int, color: int):
    """Conservative eye detector to avoid pointless self-filling."""
    if board[r][c] != EMPTY:
        return False

    adj = list(neighbors(r, c))
    if not adj:
        return False
    if any(board[nr][nc] != color for nr, nc in adj):
        return False

    diag_points = list(diagonals(r, c))
    bad = 0
    for nr, nc in diag_points:
        if board[nr][nc] != color:
            bad += 1

    # On side/corner, require all existing diagonals friendly.
    if len(diag_points) < 4:
        return bad == 0
    # In center, allow at most one bad diagonal.
    return bad <= 1


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)
    occupied = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] != EMPTY:
                occupied.append((r, c))
    total_stones = len(occupied)

    # Opening heuristic: strong, stable points.
    if total_stones <= 2:
        best_open = None
        best_val = -10**9
        for mv in OPENING_PRIORITY:
            sim = simulate_move(board, mv[0], mv[1])
            if sim is None:
                continue
            if not occupied:
                return mv
            nearest = min(abs(mv[0] - r) + abs(mv[1] - c) for r, c in occupied)
            corner_bonus = 20 if mv in ((4, 4), (4, 16), (16, 4), (16, 16)) else 0
            val = corner_bonus + nearest
            if val > best_val:
                best_val = val
                best_open = mv
        if best_open is not None:
            return best_open

    my_groups, my_pos_to_gid = analyze_color(board, ME)
    opp_groups, opp_pos_to_gid = analyze_color(board, OPP)

    save_map = defaultdict(int)       # play here to save my atari groups
    defend2_map = defaultdict(int)    # play here to strengthen my 2-liberty groups
    capture_map = defaultdict(int)    # play here to capture opp atari groups
    attack2_map = defaultdict(int)    # play here to atari opp 2-liberty groups

    for stones, libs in my_groups:
        size = len(stones)
        if len(libs) == 1:
            p = next(iter(libs))
            save_map[p] += size
        elif len(libs) == 2:
            for p in libs:
                defend2_map[p] += size

    for stones, libs in opp_groups:
        size = len(stones)
        if len(libs) == 1:
            p = next(iter(libs))
            capture_map[p] += size
        elif len(libs) == 2:
            for p in libs:
                attack2_map[p] += size

    best_move = (0, 0)
    best_score = -10**18

    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] != EMPTY:
                continue

            sim = simulate_move(board, r, c)
            if sim is None:
                continue

            captured = sim["captured"]
            libs_after = sim["libs"]
            group_size = sim["group_size"]

            adj_my_ids = set()
            adj_opp_ids = set()
            adj_my = 0
            adj_opp = 0
            for nr, nc in neighbors(r, c):
                if board[nr][nc] == ME:
                    adj_my += 1
                    gid = my_pos_to_gid.get((nr, nc))
                    if gid is not None:
                        adj_my_ids.add(gid)
                elif board[nr][nc] == OPP:
                    adj_opp += 1
                    gid = opp_pos_to_gid.get((nr, nc))
                    if gid is not None:
                        adj_opp_ids.add(gid)

            save_score = save_map[(r, c)]
            defend2_score = defend2_map[(r, c)]
            capture_score = capture_map[(r, c)]
            attack2_score = attack2_map[(r, c)]

            connect_sizes = sum(len(my_groups[gid][0]) for gid in adj_my_ids)
            connect_bonus = 0
            if len(adj_my_ids) >= 2:
                connect_bonus += 30 * (len(adj_my_ids) - 1)
            connect_bonus += 3 * connect_sizes

            # Distance features
            dist_center = abs(r - 10) + abs(c - 10)
            if occupied:
                min_dist = min(abs(r - rr) + abs(c - cc) for rr, cc in occupied)
            else:
                min_dist = 10

            score = 0

            # Tactical priorities dominate.
            score += 1000 * captured
            score += 180 * capture_score
            score += 140 * save_score
            score += 70 * attack2_score
            score += 35 * defend2_score

            # Shape and safety.
            score += 22 * libs_after
            score += 4 * group_size
            score += connect_bonus
            score += 10 * adj_opp
            score += 6 * adj_my

            # Opening / positional bias.
            if total_stones < 12:
                if (r, c) in STAR_POINTS:
                    score += 30
                score += max(0, 18 - 2 * dist_center)
                if r in (1, 2, 18, 19) or c in (1, 2, 18, 19):
                    score -= 10
            else:
                if min_dist <= 2:
                    score += 14
                elif min_dist >= 6:
                    score -= 12
                score += max(0, 8 - dist_center // 2)

            # Penalize bad self-atari.
            if libs_after == 1 and captured == 0:
                score -= 700
            elif libs_after == 1:
                score -= 120

            # Avoid filling own eye unless there's a clear tactical reason.
            if simple_true_eye(board, r, c, ME) and (captured + save_score + attack2_score) == 0:
                score -= 900

            # Ko-like recapture shape is risky because history is unavailable.
            if captured == 1 and group_size == 1 and libs_after == 1:
                score -= 500

            # Slight preference for larger captures/saves in ties.
            score += 2 * (capture_score + save_score)

            # Deterministic tie-breaks.
            tie_break = (
                -dist_center,
                -min_dist,
                -r,
                -c,
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)
                best_tie = tie_break
            elif score == best_score:
                if tie_break > best_tie:
                    best_move = (r, c)
                    best_tie = tie_break

    # Passing is always legal and better than obviously terrible self-damage.
    if best_move == (0, 0):
        return (0, 0)
    if best_score < -150:
        return (0, 0)
    return best_move
