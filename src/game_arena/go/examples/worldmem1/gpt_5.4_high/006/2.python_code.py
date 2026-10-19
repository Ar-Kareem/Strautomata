
from collections import defaultdict

BOARD_SIZE = 19
ORTHO = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

STAR_POINTS = {
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (7, 7), (7, 13), (13, 7), (13, 13),
}

OPENING_LINE_BONUS = {
    1: -340,
    2: -110,
    3: 180,
    4: 260,
    5: 135,
    6: 70,
    7: 30,
    8: 0,
    9: -15,
    10: -30,
}

MIDGAME_LINE_BONUS = {
    1: -180,
    2: -45,
    3: 75,
    4: 95,
    5: 65,
    6: 35,
    7: 15,
    8: 0,
    9: -5,
    10: -10,
}


def inside(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def build_board(me, opponent):
    board = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if inside(r, c):
            board[r][c] = 1
    for r, c in opponent:
        if inside(r, c):
            board[r][c] = -1
    return board


def board_hash(board):
    return tuple(tuple(board[r][1:BOARD_SIZE + 1]) for r in range(1, BOARD_SIZE + 1))


def group_and_liberties(board, start):
    sr, sc = start
    color = board[sr][sc]
    if color == 0:
        return [], set()

    stack = [(sr, sc)]
    seen = {(sr, sc)}
    stones = []
    liberties = set()

    while stack:
        r, c = stack.pop()
        stones.append((r, c))
        for dr, dc in ORTHO:
            nr, nc = r + dr, c + dc
            if not inside(nr, nc):
                continue
            v = board[nr][nc]
            if v == 0:
                liberties.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return stones, liberties


def collect_groups(board, color):
    seen = set()
    groups = []
    pos_to_gid = {}

    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] != color or (r, c) in seen:
                continue
            stones, liberties = group_and_liberties(board, (r, c))
            gid = len(groups)
            for p in stones:
                seen.add(p)
                pos_to_gid[p] = gid
            groups.append({"stones": stones, "libs": liberties})

    return groups, pos_to_gid


def is_simple_eye(board, move, color):
    r, c = move
    if not inside(r, c) or board[r][c] != 0:
        return False

    for dr, dc in ORTHO:
        nr, nc = r + dr, c + dc
        if inside(nr, nc) and board[nr][nc] != color:
            return False

    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc) and board[nr][nc] == -color:
            return False

    return True


def local_activity(board, r, c, radius=2):
    own = 0
    opp = 0
    r0 = max(1, r - radius)
    r1 = min(BOARD_SIZE, r + radius)
    c0 = max(1, c - radius)
    c1 = min(BOARD_SIZE, c + radius)

    for rr in range(r0, r1 + 1):
        for cc in range(c0, c1 + 1):
            if rr == r and cc == c:
                continue
            v = board[rr][cc]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1
    return own, opp


def simulate_play(board, move, ko_forbidden_hash=None):
    r, c = move
    if not inside(r, c) or board[r][c] != 0:
        return None

    newb = [row[:] for row in board]
    newb[r][c] = 1

    checked = set()
    captured = 0

    for dr, dc in ORTHO:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            continue
        if newb[nr][nc] != -1 or (nr, nc) in checked:
            continue

        stones, libs = group_and_liberties(newb, (nr, nc))
        for p in stones:
            checked.add(p)

        if not libs:
            captured += len(stones)
            for sr, sc in stones:
                newb[sr][sc] = 0

    my_stones, my_libs = group_and_liberties(newb, (r, c))
    if not my_libs:
        return None

    if ko_forbidden_hash is not None:
        h = board_hash(newb)
        if h == ko_forbidden_hash:
            return None

    return newb, captured, len(my_libs), len(my_stones)


def build_tactical_bonus(my_groups, opp_groups):
    bonus = defaultdict(int)

    for g in opp_groups:
        libs = len(g["libs"])
        size = len(g["stones"])
        if libs == 1:
            m = next(iter(g["libs"]))
            bonus[m] += 60000 + 3500 * size
        elif libs == 2:
            for m in g["libs"]:
                bonus[m] += 2200 + 140 * size
        elif libs == 3:
            for m in g["libs"]:
                bonus[m] += 300 + 20 * size

    for g in my_groups:
        libs = len(g["libs"])
        size = len(g["stones"])
        if libs == 1:
            m = next(iter(g["libs"]))
            bonus[m] += 35000 + 3000 * size
        elif libs == 2:
            for m in g["libs"]:
                bonus[m] += 1800 + 120 * size
        elif libs == 3:
            for m in g["libs"]:
                bonus[m] += 220 + 18 * size

    return bonus


def move_tiebreak(move, total_stones):
    r, c = move
    line = min(r, c, BOARD_SIZE + 1 - r, BOARD_SIZE + 1 - c)
    star = 1 if move in STAR_POINTS else 0
    center_bias = -((r - 10) * (r - 10) + (c - 10) * (c - 10))

    if total_stones < 24:
        return (star, -abs(line - 4), center_bias, -r, -c)
    return (star, -abs(line - 4), center_bias, -r, -c)


def evaluate_move(
    board,
    move,
    total_stones,
    tactical_bonus,
    my_groups,
    my_pos_to_gid,
    opp_groups,
    opp_pos_to_gid,
    ko_hash,
):
    sim = simulate_play(board, move, ko_hash)
    if sim is None:
        return None

    newb, captured, own_libs, new_group_size = sim
    r, c = move
    score = tactical_bonus.get(move, 0)

    adj_my = 0
    adj_opp = 0
    diag_my = 0
    diag_opp = 0
    adj_my_groups = set()
    adj_opp_groups = set()

    for dr, dc in ORTHO:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            continue
        v = board[nr][nc]
        if v == 1:
            adj_my += 1
            gid = my_pos_to_gid.get((nr, nc))
            if gid is not None:
                adj_my_groups.add(gid)
        elif v == -1:
            adj_opp += 1
            gid = opp_pos_to_gid.get((nr, nc))
            if gid is not None:
                adj_opp_groups.add(gid)

    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            continue
        v = board[nr][nc]
        if v == 1:
            diag_my += 1
        elif v == -1:
            diag_opp += 1

    score += captured * 8000
    score += 130 * adj_my + 110 * adj_opp + 45 * diag_my + 30 * diag_opp

    if len(adj_my_groups) >= 2:
        score += 550 * (len(adj_my_groups) - 1)

    for gid in adj_my_groups:
        libs = len(my_groups[gid]["libs"])
        size = len(my_groups[gid]["stones"])
        if libs == 1:
            score += 2500 + 180 * size
        elif libs == 2:
            score += 650 + 45 * size
        elif libs == 3:
            score += 100 + 12 * size

    for gid in adj_opp_groups:
        libs = len(opp_groups[gid]["libs"])
        size = len(opp_groups[gid]["stones"])
        if libs == 1:
            score += 3000 + 220 * size
        elif libs == 2:
            score += 900 + 55 * size
        elif libs == 3:
            score += 140 + 15 * size

    if is_simple_eye(board, move, 1) and captured == 0:
        score -= 30000

    if own_libs == 1:
        score -= 25000 if captured == 0 else 5000
    elif own_libs == 2:
        score -= 700
    else:
        score += 55 * min(own_libs, 4)

    line = min(r, c, BOARD_SIZE + 1 - r, BOARD_SIZE + 1 - c)
    if total_stones < 24:
        score += OPENING_LINE_BONUS.get(line, 0)
        if move in STAR_POINTS:
            score += 180
    else:
        score += MIDGAME_LINE_BONUS.get(line, 0)
        if move in STAR_POINTS:
            score += 30

    near_my, near_opp = local_activity(board, r, c, radius=2)
    local_nonempty = near_my + near_opp

    if 0 < total_stones < 12:
        if local_nonempty == 0:
            score += 80
        elif local_nonempty >= 6 and tactical_bonus.get(move, 0) < 1000:
            score -= 60
    elif total_stones >= 12:
        if local_nonempty == 0:
            score -= 260
        elif local_nonempty == 1:
            score -= 90

    checked_local = set()
    for dr, dc in ORTHO:
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            continue
        if newb[nr][nc] == 0 or (nr, nc) in checked_local:
            continue
        stones, libs = group_and_liberties(newb, (nr, nc))
        for p in stones:
            checked_local.add(p)
        size = len(stones)
        libn = len(libs)
        color = newb[nr][nc]
        if color == -1:
            if libn == 1:
                score += 1200 + 80 * size
            elif libn == 2:
                score += 180
        else:
            if libn == 1:
                score -= 1600 + 120 * size
            elif libn == 2:
                score -= 80

    if new_group_size >= 6 and own_libs >= 3:
        score += 120
    elif new_group_size >= 3 and own_libs >= 3:
        score += 50

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = build_board(me, opponent)
    current_hash = board_hash(board)

    if not isinstance(memory, dict):
        memory = {}

    ko_hash = memory.get("last_seen_hash")

    my_groups, my_pos_to_gid = collect_groups(board, 1)
    opp_groups, opp_pos_to_gid = collect_groups(board, -1)
    tactical_bonus = build_tactical_bonus(my_groups, opp_groups)

    total_stones = len(me) + len(opponent)

    best_move = None
    best_score = None
    best_tb = None

    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] != 0:
                continue

            move = (r, c)
            score = evaluate_move(
                board,
                move,
                total_stones,
                tactical_bonus,
                my_groups,
                my_pos_to_gid,
                opp_groups,
                opp_pos_to_gid,
                ko_hash,
            )
            if score is None:
                continue

            tb = move_tiebreak(move, total_stones)
            if (
                best_move is None
                or score > best_score
                or (score == best_score and tb > best_tb)
            ):
                best_move = move
                best_score = score
                best_tb = tb

    new_memory = {"last_seen_hash": current_hash}

    if best_move is None:
        return (0, 0), new_memory

    return best_move, new_memory
