
from typing import List, Tuple, Dict
from collections import deque

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = 2

STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16)
}

CORNER_POINTS = {
    (4, 4), (4, 16), (16, 4), (16, 16),
    (3, 3), (3, 17), (17, 3), (17, 17),
    (4, 3), (3, 4), (4, 17), (3, 16),
    (16, 3), (17, 4), (16, 17), (17, 16)
}


def neighbors(r: int, c: int):
    if r > 0:
        yield (r - 1, c)
    if r < BOARD_SIZE - 1:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c < BOARD_SIZE - 1:
        yield (r, c + 1)


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = ME
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = OPP
    return board


def board_hash(board):
    return tuple(tuple(row) for row in board)


def collect_group_and_liberties(board, r, c):
    color = board[r][c]
    group = []
    libs = set()
    q = deque([(r, c)])
    seen = {(r, c)}
    while q:
        x, y = q.popleft()
        group.append((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == EMPTY:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return group, libs


def simulate_move(board, move, player, ko_hash=None):
    r, c = move
    if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
        return None
    if board[r][c] != EMPTY:
        return None

    opp = OPP if player == ME else ME
    new_board = [row[:] for row in board]
    new_board[r][c] = player
    captured = 0

    checked = set()
    for nx, ny in neighbors(r, c):
        if new_board[nx][ny] == opp and (nx, ny) not in checked:
            grp, libs = collect_group_and_liberties(new_board, nx, ny)
            for p in grp:
                checked.add(p)
            if len(libs) == 0:
                captured += len(grp)
                for gx, gy in grp:
                    new_board[gx][gy] = EMPTY

    my_group, my_libs = collect_group_and_liberties(new_board, r, c)
    if len(my_libs) == 0:
        return None  # suicide

    if ko_hash is not None and board_hash(new_board) == ko_hash:
        return None  # simple ko safeguard

    return new_board, captured, len(my_group), len(my_libs)


def count_adjacent(board, r, c, color):
    s = 0
    for nx, ny in neighbors(r, c):
        if board[nx][ny] == color:
            s += 1
    return s


def is_eye_like(board, r, c, color):
    # Simple heuristic: all orthogonal neighbors are friendly or edge.
    enemy = OPP if color == ME else ME
    friendly = 0
    enemy_adj = 0
    empty_adj = 0
    for nx, ny in neighbors(r, c):
        v = board[nx][ny]
        if v == color:
            friendly += 1
        elif v == enemy:
            enemy_adj += 1
        else:
            empty_adj += 1
    if enemy_adj > 0:
        return False
    return friendly >= 3 and empty_adj == 0


def opening_bonus(move):
    if move in STAR_POINTS:
        return 180
    if move in CORNER_POINTS:
        return 120
    r, c = move
    # mild preference for side/corner framework over center in opening
    d_edge = min(r - 1, c - 1, BOARD_SIZE - r, BOARD_SIZE - c)
    if d_edge in (2, 3, 4):
        return 50
    return 0


def centrality_bonus(move):
    r, c = move
    # closer to center => larger bonus
    return 20 - (abs(r - 10) + abs(c - 10))


def analyze_groups(board, color):
    visited = set()
    groups = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == color and (r, c) not in visited:
                grp, libs = collect_group_and_liberties(board, r, c)
                for p in grp:
                    visited.add(p)
                groups.append((grp, libs))
    return groups


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if memory is None:
        memory = {}

    board = build_board(me, opponent)
    current_hash = board_hash(board)
    ko_hash = memory.get("last_turn_board")

    total_stones = len(me) + len(opponent)

    # Precompute urgent tactical moves.
    own_atari_moves = {}   # move -> stones saved
    opp_atari_moves = {}   # move -> stones capturable
    opp_pressure_moves = {}  # move -> pressure on 2-lib groups

    for grp, libs in analyze_groups(board, ME):
        if len(libs) == 1:
            mv = next(iter(libs))
            own_atari_moves[mv] = own_atari_moves.get(mv, 0) + len(grp)

    for grp, libs in analyze_groups(board, OPP):
        if len(libs) == 1:
            mv = next(iter(libs))
            opp_atari_moves[mv] = opp_atari_moves.get(mv, 0) + len(grp)
        elif len(libs) == 2:
            for mv in libs:
                opp_pressure_moves[mv] = opp_pressure_moves.get(mv, 0) + len(grp)

    legal_moves = []
    best_move = None
    best_score = -10**18

    # Deterministic move ordering: urgent moves first, then all points.
    candidate_set = set()
    for d in (own_atari_moves, opp_atari_moves, opp_pressure_moves):
        candidate_set.update(d.keys())

    # Add nearby empty points around existing stones for efficiency/quality.
    stones = [(r - 1, c - 1) for r, c in me + opponent]
    for r, c in stones:
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                    candidate_set.add((nr, nc))

    # Opening fallback points.
    for r, c in STAR_POINTS | CORNER_POINTS:
        rr, cc = r - 1, c - 1
        if board[rr][cc] == EMPTY:
            candidate_set.add((rr, cc))

    # If sparse or candidate set too small, include all empties.
    if total_stones < 8 or len(candidate_set) < 30:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == EMPTY:
                    candidate_set.add((r, c))

    # Evaluate candidates.
    for r, c in sorted(candidate_set):
        sim = simulate_move(board, (r, c), ME, ko_hash=ko_hash)
        if sim is None:
            continue
        new_board, captured, my_group_size, my_libs = sim
        legal_moves.append((r, c))

        score = 0

        # Tactical urgency.
        score += 9000 * opp_atari_moves.get((r, c), 0)
        score += 5000 * own_atari_moves.get((r, c), 0)
        score += 700 * opp_pressure_moves.get((r, c), 0)
        score += 1200 * captured

        # Shape / safety.
        score += 25 * min(my_libs, 8)
        if my_libs == 1 and captured == 0:
            score -= 1500  # self-atari
        elif my_libs == 1:
            score -= 300

        adj_me = count_adjacent(board, r, c, ME)
        adj_opp = count_adjacent(board, r, c, OPP)
        score += 18 * adj_me
        score += 22 * adj_opp

        # Avoid filling your own eye unless tactically useful.
        if is_eye_like(board, r, c, ME) and captured == 0 and opp_atari_moves.get((r, c), 0) == 0:
            score -= 800

        # Opening / positional guidance.
        move_1idx = (r + 1, c + 1)
        if total_stones < 12:
            score += opening_bonus(move_1idx)
            # Opening: avoid very close contact if no tactical reason.
            if adj_opp > 0 and captured == 0 and opp_atari_moves.get((r, c), 0) == 0:
                score -= 80
        else:
            score += 2 * centrality_bonus(move_1idx)

        # Mild preference for line 3/4 over first/second line early unless tactical.
        if total_stones < 30:
            dist_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
            if dist_edge == 0:
                score -= 120
            elif dist_edge == 1:
                score -= 60
            elif dist_edge in (2, 3):
                score += 30

        # Small deterministic tie-break.
        score += (19 - abs(r - 9)) * 0.001 + (19 - abs(c - 9)) * 0.0001

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If somehow no legal move among candidates, scan all points.
    if best_move is None:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                sim = simulate_move(board, (r, c), ME, ko_hash=ko_hash)
                if sim is not None:
                    best_move = (r, c)
                    break
            if best_move is not None:
                break

    # No legal move: pass.
    if best_move is None:
        memory["last_turn_board"] = current_hash
        return (0, 0), memory

    memory["last_turn_board"] = current_hash
    return (best_move[0] + 1, best_move[1] + 1), memory
