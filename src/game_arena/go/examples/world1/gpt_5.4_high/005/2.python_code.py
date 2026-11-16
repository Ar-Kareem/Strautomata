
from typing import List, Tuple, Dict, Set

SIZE = 19
CENTER = (9, 9)

CORNER_STAR = [(3, 3), (3, 15), (15, 3), (15, 15)]
SIDE_STAR = [(3, 9), (9, 3), (9, 15), (15, 9)]
CENTER_STAR = [(9, 9)]
STAR_POINTS = CORNER_STAR + SIDE_STAR + CENTER_STAR

ALL_POINTS = [(r, c) for r in range(SIZE) for c in range(SIZE)]

NEIGHBORS: Dict[Tuple[int, int], Tuple[Tuple[int, int], ...]] = {}
for r in range(SIZE):
    for c in range(SIZE):
        nbs = []
        if r > 0:
            nbs.append((r - 1, c))
        if r + 1 < SIZE:
            nbs.append((r + 1, c))
        if c > 0:
            nbs.append((r, c - 1))
        if c + 1 < SIZE:
            nbs.append((r, c + 1))
        NEIGHBORS[(r, c)] = tuple(nbs)

# Static preference: stars first, then generally good whole-board shape points.
def _edge_dist(p: Tuple[int, int]) -> int:
    r, c = p
    return min(r, c, SIZE - 1 - r, SIZE - 1 - c)

_star_set = set(STAR_POINTS)
_rest = [p for p in ALL_POINTS if p not in _star_set]
_rest.sort(key=lambda p: (abs(_edge_dist(p) - 3), abs(p[0] - 9) + abs(p[1] - 9), p[0], p[1]))
PREFERRED_ORDER = CORNER_STAR + SIDE_STAR + CENTER_STAR + _rest
PREFERRED_RANK = {p: i for i, p in enumerate(PREFERRED_ORDER)}


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[List[int]]:
    board = [[0] * SIZE for _ in range(SIZE)]

    for stones, color in ((me, 1), (opponent, -1)):
        for item in stones:
            if not isinstance(item, tuple) or len(item) != 2:
                continue
            r, c = item
            if not isinstance(r, int) or not isinstance(c, int):
                continue
            if 1 <= r <= SIZE and 1 <= c <= SIZE:
                rr, cc = r - 1, c - 1
                if board[rr][cc] == 0:
                    board[rr][cc] = color
    return board


def occupied_count(board: List[List[int]]) -> int:
    return sum(1 for r in range(SIZE) for c in range(SIZE) if board[r][c] != 0)


def collect_group(board: List[List[int]], r: int, c: int) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    color = board[r][c]
    stones: Set[Tuple[int, int]] = set()
    libs: Set[Tuple[int, int]] = set()
    stack = [(r, c)]
    stones.add((r, c))

    while stack:
        cr, cc = stack.pop()
        for nr, nc in NEIGHBORS[(cr, cc)]:
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in stones:
                stones.add((nr, nc))
                stack.append((nr, nc))
    return stones, libs


def analyze_groups(board: List[List[int]]) -> Tuple[List[List[int]], List[dict]]:
    gid_map = [[-1] * SIZE for _ in range(SIZE)]
    group_info: List[dict] = []

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0 or gid_map[r][c] != -1:
                continue
            stones, libs = collect_group(board, r, c)
            gid = len(group_info)
            for sr, sc in stones:
                gid_map[sr][sc] = gid
            group_info.append(
                {
                    "color": board[r][c],
                    "stones": stones,
                    "libs": libs,
                    "size": len(stones),
                    "lib_count": len(libs),
                }
            )
    return gid_map, group_info


def simulate_move(
    board: List[List[int]], player: int, move: Tuple[int, int]
) -> Tuple[List[List[int]], int, int, int, bool] | None:
    r, c = move
    if not (0 <= r < SIZE and 0 <= c < SIZE):
        return None
    if board[r][c] != 0:
        return None

    nb = [row[:] for row in board]
    nb[r][c] = player

    captured = 0
    seen_enemy: Set[Tuple[int, int]] = set()

    for nr, nc in NEIGHBORS[(r, c)]:
        if nb[nr][nc] == -player and (nr, nc) not in seen_enemy:
            stones, libs = collect_group(nb, nr, nc)
            seen_enemy.update(stones)
            if len(libs) == 0:
                captured += len(stones)
                for sr, sc in stones:
                    nb[sr][sc] = 0

    my_stones, my_libs = collect_group(nb, r, c)
    if len(my_libs) == 0:
        return None

    # Ko-like move: captures exactly one stone and leaves the new group with exactly one liberty.
    # Since history is hidden, avoid such moves to reduce illegal ko recapture risk.
    ko_like = (captured == 1 and len(my_libs) == 1)

    return nb, captured, len(my_libs), len(my_stones), ko_like


def is_eye_like(board: List[List[int]], move: Tuple[int, int], player: int) -> bool:
    r, c = move
    # All orthogonal neighbors must be friendly.
    for nr, nc in NEIGHBORS[(r, c)]:
        if board[nr][nc] != player:
            return False

    friendly_or_off = 0
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            if board[rr][cc] == player:
                friendly_or_off += 1
        else:
            friendly_or_off += 1

    # Interior needs 3/4 diagonals; edge/corner effectively needs all available diagonals.
    offboard_count = 0
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if not (0 <= rr < SIZE and 0 <= cc < SIZE):
            offboard_count += 1

    if offboard_count == 0:
        return friendly_or_off >= 3
    return friendly_or_off == 4


def add_weight(weight_map: Dict[Tuple[int, int], int], points: Set[Tuple[int, int]], value: int) -> None:
    for p in points:
        weight_map[p] = weight_map.get(p, 0) + value


def opening_bonus(move: Tuple[int, int], total_stones: int) -> int:
    r, c = move
    edge = _edge_dist(move)
    man_center = abs(r - 9) + abs(c - 9)

    score = 0
    if total_stones < 8:
        if move in CORNER_STAR:
            score += 2800
        elif move in SIDE_STAR:
            score += 2200
        elif move in CENTER_STAR:
            score += 1600

        if edge <= 1:
            score -= 1800
        else:
            score += 1000 - 250 * abs(edge - 3)
        score += max(0, 240 - 20 * man_center)

    elif total_stones < 25:
        if move in CORNER_STAR:
            score += 600
        elif move in SIDE_STAR:
            score += 400

        if edge <= 1:
            score -= 900
        else:
            score += 280 - 80 * abs(edge - 3)
        score += max(0, 80 - 8 * man_center)

    else:
        if edge == 0:
            score -= 120

    return score


def generate_candidates(
    board: List[List[int]],
    my_atari: Dict[Tuple[int, int], int],
    opp_atari: Dict[Tuple[int, int], int],
    my_weak: Dict[Tuple[int, int], int],
    opp_weak: Dict[Tuple[int, int], int],
    total_stones: int,
) -> Set[Tuple[int, int]]:
    if total_stones == 0:
        return {p for p in CORNER_STAR + SIDE_STAR + CENTER_STAR}

    cand: Set[Tuple[int, int]] = set()
    cand.update(my_atari.keys())
    cand.update(opp_atari.keys())
    cand.update(my_weak.keys())
    cand.update(opp_weak.keys())

    sparse = total_stones < 30
    very_sparse = total_stones < 10

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                continue

            for nr, nc in NEIGHBORS[(r, c)]:
                if board[nr][nc] == 0:
                    cand.add((nr, nc))

            if sparse:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == 0:
                            cand.add((rr, cc))

            if very_sparse:
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if dr == 0 and dc == 0:
                            continue
                        if max(abs(dr), abs(dc)) != 2:
                            continue
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == 0:
                            cand.add((rr, cc))

    for p in STAR_POINTS:
        if board[p[0]][p[1]] == 0:
            cand.add(p)

    return cand


def evaluate_move(
    board: List[List[int]],
    nb: List[List[int]],
    move: Tuple[int, int],
    total_stones: int,
    gid_map: List[List[int]],
    group_info: List[dict],
    my_atari: Dict[Tuple[int, int], int],
    opp_atari: Dict[Tuple[int, int], int],
    my_weak: Dict[Tuple[int, int], int],
    opp_weak: Dict[Tuple[int, int], int],
    captured: int,
    new_libs: int,
    new_size: int,
) -> int:
    r, c = move
    score = 0

    # Tactical urgency from current board.
    score += 32000 * opp_atari.get(move, 0)
    score += 24000 * my_atari.get(move, 0)
    score += 4500 * opp_weak.get(move, 0)
    score += 2500 * my_weak.get(move, 0)
    score += 2200 * captured

    adj_my_ids: Set[int] = set()
    adj_opp_ids: Set[int] = set()

    for nr, nc in NEIGHBORS[(r, c)]:
        v = board[nr][nc]
        if v == 1:
            gid = gid_map[nr][nc]
            if gid != -1:
                adj_my_ids.add(gid)
        elif v == -1:
            gid = gid_map[nr][nc]
            if gid != -1:
                adj_opp_ids.add(gid)

    # Connection / cutting.
    score += 900 * max(0, len(adj_my_ids) - 1)
    score += 700 * max(0, len(adj_opp_ids) - 1)

    for gid in adj_my_ids:
        info = group_info[gid]
        sz = min(info["size"], 5)
        libs = info["lib_count"]
        score += 120 * sz
        if libs == 1:
            score += 4000 + 700 * sz
        elif libs == 2:
            score += 600 + 120 * sz

    for gid in adj_opp_ids:
        info = group_info[gid]
        sz = min(info["size"], 5)
        libs = info["lib_count"]
        score += 150 * sz
        if libs == 1:
            score += 5000 + 800 * sz
        elif libs == 2:
            score += 900 + 150 * sz

    # Resulting liberties and shape.
    if new_libs == 1:
        if captured == 0:
            score -= 25000 + 1200 * min(new_size, 10)
        else:
            score -= 7000 + 500 * min(new_size, 10)
    else:
        score += 250 + 180 * min(new_libs, 6)

    if new_libs <= 2 and new_size > 4:
        score -= 400 * min(new_size - 4, 8)

    # Avoid filling own likely eye unless tactically justified.
    if captured == 0 and is_eye_like(board, move, 1):
        score -= 12000

    # Nearby tactical impact after the move: create atari / pressure.
    seen_enemy: Set[Tuple[int, int]] = set()
    newly_atari = 0
    newly_pressured = 0
    for nr, nc in NEIGHBORS[(r, c)]:
        if nb[nr][nc] == -1 and (nr, nc) not in seen_enemy:
            stones, libs = collect_group(nb, nr, nc)
            seen_enemy.update(stones)
            if len(libs) == 1:
                newly_atari += len(stones)
            elif len(libs) == 2:
                newly_pressured += len(stones)

    score += 1800 * newly_atari
    score += 250 * newly_pressured

    # Opening / whole-board geometry.
    score += opening_bonus(move, total_stones)

    # Avoid disconnected random jumps in non-opening positions.
    if total_stones >= 8 and not adj_my_ids and not adj_opp_ids:
        score -= 1200

    # Slight preference for fighting near both colors.
    if adj_my_ids and adj_opp_ids:
        score += 400

    return score


def emergency_legal_move(board: List[List[int]]) -> Tuple[int, int] | None:
    for move in PREFERRED_ORDER:
        r, c = move
        if board[r][c] != 0:
            continue
        sim = simulate_move(board, 1, move)
        if sim is not None:
            _, _, _, _, ko_like = sim
            if not ko_like:
                return move
    return None


def _policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    board = build_board(me, opponent)
    total_stones = occupied_count(board)

    if total_stones >= SIZE * SIZE:
        return (0, 0)

    gid_map, group_info = analyze_groups(board)

    my_atari: Dict[Tuple[int, int], int] = {}
    opp_atari: Dict[Tuple[int, int], int] = {}
    my_weak: Dict[Tuple[int, int], int] = {}
    opp_weak: Dict[Tuple[int, int], int] = {}

    for info in group_info:
        libs = info["libs"]
        size = info["size"]
        lib_count = info["lib_count"]
        color = info["color"]

        if color == 1:
            if lib_count == 1:
                add_weight(my_atari, libs, size)
            elif lib_count == 2:
                add_weight(my_weak, libs, size)
        else:
            if lib_count == 1:
                add_weight(opp_atari, libs, size)
            elif lib_count == 2:
                add_weight(opp_weak, libs, size)

    candidates = generate_candidates(board, my_atari, opp_atari, my_weak, opp_weak, total_stones)

    best_move = None
    best_score = None
    best_rank = 10**9

    for move in candidates:
        r, c = move
        if not (0 <= r < SIZE and 0 <= c < SIZE):
            continue
        if board[r][c] != 0:
            continue

        sim = simulate_move(board, 1, move)
        if sim is None:
            continue

        nb, captured, new_libs, new_size, ko_like = sim
        if ko_like:
            continue

        score = evaluate_move(
            board,
            nb,
            move,
            total_stones,
            gid_map,
            group_info,
            my_atari,
            opp_atari,
            my_weak,
            opp_weak,
            captured,
            new_libs,
            new_size,
        )

        rank = PREFERRED_RANK.get(move, 10**9)
        if best_move is None or score > best_score or (score == best_score and rank < best_rank):
            best_move = move
            best_score = score
            best_rank = rank

    if best_move is None:
        fallback = emergency_legal_move(board)
        if fallback is None:
            return (0, 0)
        return (fallback[0] + 1, fallback[1] + 1)

    return (best_move[0] + 1, best_move[1] + 1)


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    try:
        return _policy(me, opponent)
    except Exception:
        # Safety fallback: still return a legal move if possible.
        try:
            board = build_board(me, opponent)
            move = emergency_legal_move(board)
            if move is None:
                return (0, 0)
            return (move[0] + 1, move[1] + 1)
        except Exception:
            return (0, 0)
