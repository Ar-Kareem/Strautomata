
from __future__ import annotations

BOARD_SIZE = 19
BOARD_CELLS = BOARD_SIZE * BOARD_SIZE
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAG_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

NEIGHBORS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
DIAGONALS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                NEIGHBORS[r][c].append((nr, nc))
        for dr, dc in DIAG_DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                DIAGONALS[r][c].append((nr, nc))

CORNER_44 = {(3, 3), (3, 15), (15, 3), (15, 15)}
SIDE_STARS = {(3, 9), (9, 3), (9, 15), (15, 9)}
CENTER = (9, 9)


def build_board(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> list[list[int]]:
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = -1
    return board


def encode_board(board: list[list[int]]) -> bytes:
    data = bytearray(BOARD_CELLS)
    k = 0
    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            data[k] = row[c] + 1  # -1 -> 0, 0 -> 1, 1 -> 2
            k += 1
    return bytes(data)


def is_hash_like(x) -> bool:
    return isinstance(x, (bytes, bytearray)) and len(x) == BOARD_CELLS


def collect_group(board: list[list[int]], r: int, c: int) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    color = board[r][c]
    if color == 0:
        return [], set()

    stack = [(r, c)]
    seen = {(r, c)}
    stones: list[tuple[int, int]] = []
    libs: set[tuple[int, int]] = set()

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


def analyze_groups(board: list[list[int]]) -> tuple[list[tuple[int, list[tuple[int, int]], set[tuple[int, int]]]], list[list[int]]]:
    gid_map = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    groups: list[tuple[int, list[tuple[int, int]], set[tuple[int, int]]]] = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = board[r][c]
            if color == 0 or gid_map[r][c] != -1:
                continue

            gid = len(groups)
            stack = [(r, c)]
            gid_map[r][c] = gid
            stones: list[tuple[int, int]] = []
            libs: set[tuple[int, int]] = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in NEIGHBORS[x][y]:
                    v = board[nx][ny]
                    if v == 0:
                        libs.add((nx, ny))
                    elif v == color and gid_map[nx][ny] == -1:
                        gid_map[nx][ny] = gid
                        stack.append((nx, ny))

            groups.append((color, stones, libs))

    return groups, gid_map


def simulate_move(board: list[list[int]], move: tuple[int, int], color: int):
    r, c = move
    if board[r][c] != 0:
        return None

    board2 = [row[:] for row in board]
    board2[r][c] = color

    checked: set[tuple[int, int]] = set()
    to_remove: list[list[tuple[int, int]]] = []

    # Check adjacent enemy groups before removing any, so simultaneous captures work correctly.
    for nr, nc in NEIGHBORS[r][c]:
        if board2[nr][nc] == -color and (nr, nc) not in checked:
            stones, libs = collect_group(board2, nr, nc)
            for pt in stones:
                checked.add(pt)
            if not libs:
                to_remove.append(stones)

    captured = 0
    captured_points: list[tuple[int, int]] = []
    for stones in to_remove:
        captured += len(stones)
        captured_points.extend(stones)
        for x, y in stones:
            board2[x][y] = 0

    own_stones, own_libs = collect_group(board2, r, c)
    if not own_libs:
        return None  # suicide

    after_hash = encode_board(board2)
    return board2, captured, own_stones, own_libs, after_hash, captured_points


def approx_true_eye(board: list[list[int]], move: tuple[int, int], color: int) -> bool:
    r, c = move
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] != color:
            return False

    bad_diagonals = 0
    for nr, nc in DIAGONALS[r][c]:
        if board[nr][nc] == -color:
            bad_diagonals += 1
    return bad_diagonals == 0


def global_eval(groups: list[tuple[int, list[tuple[int, int]], set[tuple[int, int]]]]) -> float:
    score = 0.0
    for color, stones, libs in groups:
        size = len(stones)
        lcount = len(libs)

        base = 0.25 * size + 0.7 * min(lcount, 4)
        if lcount == 1:
            base -= 5.0 * size
        elif lcount == 2:
            base -= 1.5 * size
        elif lcount >= 4:
            base += 0.2 * size

        if color == 1:
            score += base
        else:
            score -= base
    return score


def opening_bonus(move: tuple[int, int], occupied: list[tuple[int, int]], total_stones: int) -> float:
    if total_stones >= 16:
        return 0.0

    r, c = move
    d_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    score = 0.0

    if d_edge == 0:
        score -= 25.0
    elif d_edge == 1:
        score -= 10.0
    elif d_edge == 2:
        score += 8.0
    elif d_edge == 3:
        score += 14.0
    elif d_edge == 4:
        score += 10.0

    if (r, c) in CORNER_44:
        score += 35.0
    elif (r, c) in SIDE_STARS:
        score += 28.0
    elif (r, c) == CENTER:
        score += 12.0

    if occupied:
        min_d = min(abs(r - x) + abs(c - y) for x, y in occupied)
        if total_stones <= 2:
            score += 0.8 * min_d
        else:
            score += float(min(min_d, 8))
        if total_stones < 8 and min_d < 3:
            score -= 10.0 * (3 - min_d)

    return score


def local_shape_bonus(
    move: tuple[int, int],
    board: list[list[int]],
    total_stones: int,
    last_opp_move: tuple[int, int] | None,
) -> float:
    r, c = move
    adj_my = 0
    adj_opp = 0
    diag_my = 0
    diag_opp = 0

    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 1:
            adj_my += 1
        elif v == -1:
            adj_opp += 1

    for nr, nc in DIAGONALS[r][c]:
        v = board[nr][nc]
        if v == 1:
            diag_my += 1
        elif v == -1:
            diag_opp += 1

    d_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)

    score = 4.0 * adj_my + 1.5 * adj_opp + 1.5 * diag_my - 1.0 * diag_opp

    if total_stones > 8 and adj_my == 0 and adj_opp == 0:
        score -= 8.0
    if adj_my >= 2:
        score += 4.0
    if adj_opp >= 2 and adj_my >= 1:
        score += 4.0

    if total_stones > 20:
        if d_edge == 0:
            score -= 15.0
        elif d_edge == 1:
            score -= 6.0

    if last_opp_move is not None and total_stones > 6:
        d = abs(r - last_opp_move[0]) + abs(c - last_opp_move[1])
        if d == 1:
            score += 10.0
        elif d == 2:
            score += 5.0
        elif d == 3:
            score += 2.0

    return score


def infer_last_opponent_move(last_after_board, current_hash: bytes) -> tuple[int, int] | None:
    if not is_hash_like(last_after_board):
        return None

    # Opponent stone appears as empty(1) -> opponent(0).
    for i, (a, b) in enumerate(zip(last_after_board, current_hash)):
        if a == 1 and b == 0:
            return (i // BOARD_SIZE, i % BOARD_SIZE)
    return None


def max_immediate_capture_against_us(board: list[list[int]], focus_move: tuple[int, int]) -> int:
    groups, _ = analyze_groups(board)
    pts: set[tuple[int, int]] = set()

    r, c = focus_move
    for x in range(max(0, r - 2), min(BOARD_SIZE, r + 3)):
        for y in range(max(0, c - 2), min(BOARD_SIZE, c + 3)):
            if board[x][y] == 0:
                pts.add((x, y))

    for color, stones, libs in groups:
        lcount = len(libs)
        if color == 1 and lcount <= 2:
            pts.update(libs)
        elif color == -1 and lcount == 1:
            pts.update(libs)

    best = 0
    for pt in pts:
        sim = simulate_move(board, pt, -1)
        if sim is None:
            continue
        captured = sim[1]
        if captured > best:
            best = captured
    return best


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    mem = dict(memory) if isinstance(memory, dict) else {}

    board = build_board(me, opponent)
    current_hash = encode_board(board)
    total_stones = len(me) + len(opponent)

    prev_turn_hash = mem.get("last_turn_hash")
    if not is_hash_like(prev_turn_hash):
        prev_turn_hash = None

    raw_seen = mem.get("seen_hashes")
    if isinstance(raw_seen, set):
        seen_hashes = set(x for x in raw_seen if is_hash_like(x))
    elif isinstance(raw_seen, (list, tuple)):
        seen_hashes = set(x for x in raw_seen if is_hash_like(x))
    else:
        seen_hashes = set()

    last_after_board = mem.get("last_after_board")
    last_opp_move = infer_last_opponent_move(last_after_board, current_hash)

    groups, gid_map = analyze_groups(board)

    occupied: list[tuple[int, int]] = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                occupied.append((r, c))

    my_atari: list[tuple[tuple[int, int], int]] = []
    opp_status: dict[tuple[int, int], tuple[int, int]] = {}
    largest_my_atari = 0

    for color, stones, libs in groups:
        rep = stones[0]
        size = len(stones)
        lcount = len(libs)
        if color == 1:
            if lcount == 1:
                my_atari.append((rep, size))
                if size > largest_my_atari:
                    largest_my_atari = size
        else:
            opp_status[rep] = (lcount, size)

    candidates: list[tuple[float, tuple[int, int], bytes]] = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue

            sim = simulate_move(board, (r, c), 1)
            if sim is None:
                continue

            board2, captured, placed_stones, placed_libs, after_hash, captured_points = sim

            # Simple-ko avoidance: disallow recreating the board from my previous turn.
            if prev_turn_hash is not None and after_hash == prev_turn_hash:
                continue

            groups2, gid2 = analyze_groups(board2)

            score = 0.0

            # Immediate tactical value.
            score += 125.0 * captured

            saved = 0
            for rep, size in my_atari:
                x, y = rep
                if board2[x][y] == 1:
                    libs2 = len(groups2[gid2[x][y]][2])
                    if libs2 > 1:
                        saved += size
            score += 95.0 * saved

            if my_atari and saved == 0 and captured == 0:
                score -= 22.0 * largest_my_atari

            new_atari = 0.0
            pressure = 0.0
            for rep, (before_libs, size) in opp_status.items():
                x, y = rep
                if board2[x][y] == -1:
                    after_libs = len(groups2[gid2[x][y]][2])
                    if before_libs == 2 and after_libs == 1:
                        new_atari += size
                    elif before_libs >= 3 and after_libs == 2:
                        pressure += size
            score += 30.0 * new_atari + 10.0 * pressure

            placed_gid = gid2[r][c]
            placed_size = len(groups2[placed_gid][1])
            libs_after = len(groups2[placed_gid][2])

            if libs_after == 1:
                if captured == 0:
                    score -= 200.0
                elif captured == 1 and placed_size == 1:
                    score -= 50.0
                else:
                    score -= 5.0
            elif libs_after == 2:
                score -= 15.0
            else:
                score += 7.0 * min(libs_after, 4)

            my_atari_after = 0
            my_two_after = 0
            opp_atari_after = 0
            opp_two_after = 0
            for color2, stones2, libs2 in groups2:
                size2 = len(stones2)
                l2 = len(libs2)
                if color2 == 1:
                    if l2 == 1:
                        my_atari_after += size2
                    elif l2 == 2:
                        my_two_after += size2
                else:
                    if l2 == 1:
                        opp_atari_after += size2
                    elif l2 == 2:
                        opp_two_after += size2

            score -= 12.0 * my_atari_after + 3.0 * my_two_after
            score += 9.0 * opp_atari_after + 2.5 * opp_two_after

            adj_my_groups = set()
            adj_opp_groups = set()
            for nr, nc in NEIGHBORS[r][c]:
                if board[nr][nc] == 1:
                    adj_my_groups.add(gid_map[nr][nc])
                elif board[nr][nc] == -1:
                    adj_opp_groups.add(gid_map[nr][nc])

            score += 18.0 * max(0, len(adj_my_groups) - 1)
            score += 8.0 * max(0, len(adj_opp_groups) - 1)

            score += local_shape_bonus((r, c), board, total_stones, last_opp_move)
            score += opening_bonus((r, c), occupied, total_stones)
            score += global_eval(groups2)

            if after_hash in seen_hashes:
                score -= 40.0

            if approx_true_eye(board, (r, c), 1) and captured == 0 and saved == 0 and new_atari == 0:
                score -= 250.0

            candidates.append((score, (r, c), after_hash))

    if not candidates:
        seen_hashes.add(current_hash)
        out_memory = {
            "seen_hashes": seen_hashes,
            "last_turn_hash": current_hash,
            "last_after_board": current_hash,
        }
        return (0, 0), out_memory

    candidates.sort(key=lambda item: item[0], reverse=True)

    best_move = candidates[0][1]
    best_after = candidates[0][2]
    best_refined = -10**18

    # Small safety filter on the top few moves: avoid moves that immediately lose many stones.
    for base_score, move, after_hash in candidates[:6]:
        sim = simulate_move(board, move, 1)
        if sim is None:
            continue
        board2 = sim[0]
        threat = max_immediate_capture_against_us(board2, move)
        penalty = 35.0 if threat == 1 else 55.0 * threat
        refined = base_score - penalty

        if refined > best_refined or (refined == best_refined and move < best_move):
            best_refined = refined
            best_move = move
            best_after = after_hash

    seen_hashes.add(current_hash)
    seen_hashes.add(best_after)
    out_memory = {
        "seen_hashes": seen_hashes,
        "last_turn_hash": current_hash,
        "last_after_board": best_after,
    }

    return (best_move[0] + 1, best_move[1] + 1), out_memory
