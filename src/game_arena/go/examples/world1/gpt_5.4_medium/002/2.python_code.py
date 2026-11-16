
from collections import defaultdict
from typing import List, Tuple

SIZE = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

OPENING_WEIGHTS = {
    (4, 4): 220, (4, 16): 220, (16, 4): 220, (16, 16): 220,
    (3, 4): 170, (4, 3): 170, (3, 16): 170, (4, 17): 170,
    (16, 3): 170, (17, 4): 170, (16, 17): 170, (17, 16): 170,
    (4, 10): 120, (10, 4): 120, (10, 16): 120, (16, 10): 120,
    (10, 10): 90,
}


def on_board(r: int, c: int) -> bool:
    return 1 <= r <= SIZE and 1 <= c <= SIZE


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 1 <= rr <= SIZE and 1 <= cc <= SIZE:
            yield rr, cc


def group_and_libs(board, r: int, c: int):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        sr, sc = stack.pop()
        stones.append((sr, sc))
        for nr, nc in neighbors(sr, sc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return stones, libs


def scan_groups(board):
    gid_board = [[-1] * (SIZE + 1) for _ in range(SIZE + 1)]
    groups = []
    gid = 0

    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if board[r][c] != 0 and gid_board[r][c] == -1:
                stones, libs = group_and_libs(board, r, c)
                for sr, sc in stones:
                    gid_board[sr][sc] = gid
                groups.append({
                    "color": board[r][c],
                    "stones": stones,
                    "size": len(stones),
                    "libs": libs,
                    "lib_count": len(libs),
                })
                gid += 1
    return groups, gid_board


def simulate_move(board, r: int, c: int):
    if board[r][c] != 0:
        return None

    b = [row[:] for row in board]
    b[r][c] = 1

    checked = set()
    captured = []
    captured_groups = 0

    for nr, nc in neighbors(r, c):
        if b[nr][nc] == -1 and (nr, nc) not in checked:
            stones, libs = group_and_libs(b, nr, nc)
            for s in stones:
                checked.add(s)
            if not libs:
                captured.extend(stones)
                captured_groups += 1

    for sr, sc in captured:
        b[sr][sc] = 0

    my_stones, my_libs = group_and_libs(b, r, c)
    if not my_libs:
        return None

    return b, len(captured), captured_groups, len(my_stones), len(my_libs)


def is_eye_like(board, r: int, c: int) -> bool:
    if board[r][c] != 0:
        return False

    total_orth = 0
    friendly_orth = 0
    for nr, nc in neighbors(r, c):
        total_orth += 1
        if board[nr][nc] == -1:
            return False
        if board[nr][nc] == 1:
            friendly_orth += 1

    if friendly_orth != total_orth:
        return False

    diag_total = 0
    bad_diags = 0
    for dr, dc in DIAGS:
        rr, cc = r + dr, c + dc
        if on_board(rr, cc):
            diag_total += 1
            if board[rr][cc] == -1:
                bad_diags += 1

    limit = 1 if diag_total == 4 else 0
    return bad_diags <= limit


def evaluate_move(
    board,
    newb,
    r: int,
    c: int,
    cap_count: int,
    cap_groups: int,
    my_group_size: int,
    my_lib_count: int,
    gid_board,
    own_atari_by_lib,
    own_two_by_lib,
    opp_two_by_lib,
    total_stones: int,
    stone_list,
):
    score = 0

    rescue = own_atari_by_lib.get((r, c), 0)

    # Tactical priorities
    score += 10000 * cap_count
    score += 400 * cap_groups
    score += 1800 * rescue
    score += 180 * own_two_by_lib.get((r, c), 0)
    score += 130 * opp_two_by_lib.get((r, c), 0)

    # Adjacency / connectivity on original board
    adj_my = set()
    adj_opp = set()
    for nr, nc in neighbors(r, c):
        v = board[nr][nc]
        if v == 1:
            adj_my.add(gid_board[nr][nc])
            score += 18
        elif v == -1:
            adj_opp.add(gid_board[nr][nc])
            score += 25

    score += 90 * len(adj_my)
    if len(adj_my) > 1:
        score += 160 * (len(adj_my) - 1)
    if len(adj_opp) > 1:
        score += 45 * (len(adj_opp) - 1)

    # Post-move liberties / shape
    score += 35 * min(my_lib_count, 6)
    score += 7 * my_group_size

    if my_lib_count == 1:
        score -= 1500 if cap_count == 0 else 500
    elif my_lib_count == 2:
        score -= 180 if cap_count == 0 else 50

    # Pressure adjacent enemy groups after the move
    checked = set()
    for nr, nc in neighbors(r, c):
        if newb[nr][nc] == -1 and (nr, nc) not in checked:
            stones, libs = group_and_libs(newb, nr, nc)
            for s in stones:
                checked.add(s)
            lc = len(libs)
            sz = len(stones)
            if lc == 1:
                score += 320 + 35 * sz
            elif lc == 2:
                score += 70 + 8 * sz

    # Avoid filling true-ish own eyes unless needed
    if is_eye_like(board, r, c) and cap_count == 0 and rescue == 0:
        score -= 1800

    # Locality / fighting relevance
    near_me = 0
    near_opp = 0
    r0 = max(1, r - 3)
    r1 = min(SIZE, r + 3)
    c0 = max(1, c - 3)
    c1 = min(SIZE, c + 3)
    for rr in range(r0, r1 + 1):
        for cc in range(c0, c1 + 1):
            d = abs(rr - r) + abs(cc - c)
            if d == 0 or d > 3:
                continue
            v = board[rr][cc]
            if v == 0:
                continue
            w = 4 - d
            if v == 1:
                near_me += w
            else:
                near_opp += w

    score += 10 * near_me + 13 * near_opp
    if near_me and near_opp:
        score += 40

    # Opening preferences
    if total_stones < 8:
        score += OPENING_WEIGHTS.get((r, c), 0)
        if stone_list:
            md = 999
            for sr, sc in stone_list:
                d = abs(sr - r) + abs(sc - c)
                if d < md:
                    md = d
            score += 3 * md
            if md < 3:
                score -= 120
    else:
        score += 2 * (18 - (abs(r - 10) + abs(c - 10)))

    return score


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    my_set = set()
    for r, c in me:
        if on_board(r, c):
            my_set.add((r, c))

    opp_set = set()
    for r, c in opponent:
        if on_board(r, c) and (r, c) not in my_set:
            opp_set.add((r, c))

    board = [[0] * (SIZE + 1) for _ in range(SIZE + 1)]
    for r, c in my_set:
        board[r][c] = 1
    for r, c in opp_set:
        board[r][c] = -1

    total_stones = len(my_set) + len(opp_set)
    if total_stones >= SIZE * SIZE:
        return (0, 0)

    if total_stones == 0:
        return (4, 4)

    groups, gid_board = scan_groups(board)

    own_atari_by_lib = defaultdict(int)
    own_two_by_lib = defaultdict(int)
    opp_two_by_lib = defaultdict(int)

    for g in groups:
        if g["color"] == 1:
            if g["lib_count"] == 1:
                for p in g["libs"]:
                    own_atari_by_lib[p] += g["size"]
            elif g["lib_count"] == 2:
                for p in g["libs"]:
                    own_two_by_lib[p] += g["size"]
        else:
            if g["lib_count"] == 2:
                for p in g["libs"]:
                    opp_two_by_lib[p] += g["size"]

    stone_list = list(my_set) + list(opp_set)

    best_safe = None
    best_safe_key = None
    any_legal = False

    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if board[r][c] != 0:
                continue

            sim = simulate_move(board, r, c)
            if sim is None:
                continue

            any_legal = True
            newb, cap_count, cap_groups, my_group_size, my_lib_count = sim

            # Conservative ko avoidance: without history, avoid ko-like one-stone recaptures.
            ko_like = (cap_count == 1 and my_lib_count == 1)

            score = evaluate_move(
                board,
                newb,
                r,
                c,
                cap_count,
                cap_groups,
                my_group_size,
                my_lib_count,
                gid_board,
                own_atari_by_lib,
                own_two_by_lib,
                opp_two_by_lib,
                total_stones,
                stone_list,
            )

            key = (score, -(abs(r - 10) + abs(c - 10)), -r, -c)

            if not ko_like and (best_safe_key is None or key > best_safe_key):
                best_safe_key = key
                best_safe = (r, c)

    if best_safe is not None:
        return best_safe

    # If only ko-like/risky legal moves exist, pass to guarantee legality.
    if any_legal:
        return (0, 0)

    return (0, 0)
