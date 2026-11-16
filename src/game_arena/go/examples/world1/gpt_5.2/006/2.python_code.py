
from __future__ import annotations

from typing import List, Tuple, Dict, Set
import random

BOARD_SIZE = 19

# Common opening / framework points (1-indexed)
OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (3, 3), (3, 17), (17, 3), (17, 17),
]


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Returns one legal move (row, col) in 1..19, or (0,0) to pass.
    Implements basic legality: no playing on occupied points; no suicide (unless captures save it).
    Does not enforce ko (no history is provided).
    """
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = -1

    move_count = len(me) + len(opponent)

    # Precompute groups once for urgent tactics
    my_groups, _ = compute_groups(board, 1)
    opp_groups, _ = compute_groups(board, -1)

    # 1) Urgent captures: capture any opponent group with 1 liberty
    capture_moves = []
    for stones, libs in opp_groups:
        if len(libs) == 1:
            (lr, lc) = next(iter(libs))
            newb, cap, legal = simulate_move(board, lr, lc, 1)
            if legal and cap > 0:
                capture_moves.append((cap, len(stones), (lr, lc)))
    if capture_moves:
        capture_moves.sort(reverse=True)
        return to_1idx(capture_moves[0][2])

    # 2) Urgent saves: save any of our groups with 1 liberty
    save_moves = []
    for stones, libs in my_groups:
        if len(libs) == 1:
            (lr, lc) = next(iter(libs))
            newb, cap, legal = simulate_move(board, lr, lc, 1)
            if legal:
                # Prefer saving bigger groups; capturing while saving is a plus.
                save_moves.append((len(stones) * 10 + cap * 20, (lr, lc)))
    if save_moves:
        save_moves.sort(reverse=True)
        return to_1idx(save_moves[0][1])

    # Generate all legal moves (361 is small enough)
    legal_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue
            _, _, legal = simulate_move(board, r, c, 1)
            if legal:
                legal_moves.append((r, c))

    if not legal_moves:
        return (0, 0)

    # Deterministic-ish tiebreak noise
    rng = random.Random(board_hash(me, opponent))

    # Small opening preference: if an opening point is legal, consider it strongly
    if move_count < 10:
        opening_legals = []
        legal_set = set(legal_moves)
        for (rr, cc) in OPENING_POINTS:
            r0, c0 = rr - 1, cc - 1
            if (r0, c0) in legal_set:
                opening_legals.append((r0, c0))
        if opening_legals:
            # Still do a light evaluation among them to avoid obvious self-atari/eye-fill
            best_m = opening_legals[0]
            best_s = -10**18
            for m in opening_legals:
                s = score_move(board, m[0], m[1], move_count, rng)
                if s > best_s:
                    best_s, best_m = s, m
            return to_1idx(best_m)

    # General evaluation: pick the max scoring legal move
    best_move = legal_moves[0]
    best_score = -10**18
    for (r, c) in legal_moves:
        s = score_move(board, r, c, move_count, rng)
        if s > best_score:
            best_score = s
            best_move = (r, c)

    return to_1idx(best_move)


# ----------------- Core Go Helpers -----------------

def neighbors(r: int, c: int):
    if r > 0:
        yield (r - 1, c)
    if r + 1 < BOARD_SIZE:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c + 1 < BOARD_SIZE:
        yield (r, c + 1)


def compute_groups(board: List[List[int]], color: int):
    """
    Returns (groups, pos_to_group):
      groups: list of (stones_set, liberties_set), where each is a set of (r,c) 0-index
      pos_to_group: dict mapping (r,c)->group_index
    """
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    groups = []
    pos_to_group: Dict[Tuple[int, int], int] = {}

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if visited[r][c] or board[r][c] != color:
                continue
            stack = [(r, c)]
            visited[r][c] = True
            stones: Set[Tuple[int, int]] = set()
            libs: Set[Tuple[int, int]] = set()

            while stack:
                rr, cc = stack.pop()
                stones.add((rr, cc))
                for nr, nc in neighbors(rr, cc):
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            idx = len(groups)
            for p in stones:
                pos_to_group[p] = idx
            groups.append((stones, libs))

    return groups, pos_to_group


def get_group_and_liberties(board: List[List[int]], r: int, c: int):
    """Flood-fill group at (r,c); returns (stones_set, liberties_set)."""
    color = board[r][c]
    stack = [(r, c)]
    stones: Set[Tuple[int, int]] = set()
    libs: Set[Tuple[int, int]] = set()
    seen = set([(r, c)])

    while stack:
        rr, cc = stack.pop()
        stones.add((rr, cc))
        for nr, nc in neighbors(rr, cc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return stones, libs


def simulate_move(board: List[List[int]], r: int, c: int, color: int):
    """
    Simulate placing 'color' at (r,c) (0-index).
    Returns: (new_board, captured_count, legal_bool)
    """
    if board[r][c] != 0:
        return board, 0, False

    newb = [row[:] for row in board]
    newb[r][c] = color
    captured = 0
    opp = -color

    # Capture adjacent opponent groups that lose last liberty
    checked = set()
    for nr, nc in neighbors(r, c):
        if newb[nr][nc] != opp:
            continue
        if (nr, nc) in checked:
            continue
        stones, libs = get_group_and_liberties(newb, nr, nc)
        checked |= stones
        if len(libs) == 0:
            for (sr, sc) in stones:
                newb[sr][sc] = 0
            captured += len(stones)

    # Check suicide (after captures)
    stones, libs = get_group_and_liberties(newb, r, c)
    if len(libs) == 0:
        return board, 0, False

    return newb, captured, True


# ----------------- Heuristic Scoring -----------------

def score_move(board: List[List[int]], r: int, c: int, move_count: int, rng: random.Random) -> float:
    newb, cap, legal = simulate_move(board, r, c, 1)
    if not legal:
        return -1e18

    # Base from captures
    score = cap * 20.0

    # Liberties of the placed stone's resulting group
    my_stones, my_libs = get_group_and_liberties(newb, r, c)
    my_lib_n = len(my_libs)

    # Avoid (most) self-atari
    if cap == 0 and my_lib_n == 1:
        score -= 15.0
    else:
        score += min(my_lib_n, 6) * 1.6

    # Connection bonus: adjacent friendly stones
    adj_friend = 0
    adj_opp = 0
    for nr, nc in neighbors(r, c):
        if newb[nr][nc] == 1:
            adj_friend += 1
        elif newb[nr][nc] == -1:
            adj_opp += 1
    score += adj_friend * 0.8
    score += adj_opp * 0.2  # mild preference for contact when reasonable

    # Create atari on adjacent opponent groups
    atari_groups = 0
    atari_size = 0
    seen_opp = set()
    for nr, nc in neighbors(r, c):
        if newb[nr][nc] != -1 or (nr, nc) in seen_opp:
            continue
        stones, libs = get_group_and_liberties(newb, nr, nc)
        seen_opp |= stones
        if len(libs) == 1:
            atari_groups += 1
            atari_size += len(stones)
    score += atari_groups * 6.0 + atari_size * 1.2

    # Eye-filling penalty (unless it captured)
    if cap == 0 and is_eye_like(board, r, c, 1):
        score -= 6.0

    # Opening bias toward standard points
    if move_count < 12:
        rr, cc = r + 1, c + 1
        if (rr, cc) in OPENING_POINTS:
            score += 5.0 if move_count < 4 else 3.0

        # Slight corner/side preference early
        dist_to_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
        score += max(0, 3 - dist_to_edge) * 0.4

    # Prefer moves not too far from existing stones (reduce random wandering)
    score += proximity_bonus(board, r, c) * 0.15

    # Small deterministic noise for tie-breaking
    score += (rng.random() - 0.5) * 0.05
    return score


def is_eye_like(board: List[List[int]], r: int, c: int, color: int) -> bool:
    """
    Very rough 'eye-like' detector:
    point is empty; all orthogonal neighbors are 'color' or edge.
    """
    if board[r][c] != 0:
        return False
    for nr, nc in neighbors(r, c):
        if board[nr][nc] != color:
            return False
    # If it has 0-1 neighbors (corner) it can still be an eye; keep it simple.
    return True


def proximity_bonus(board: List[List[int]], r: int, c: int) -> int:
    """Counts stones within a small radius to encourage local play."""
    bonus = 0
    for dr in (-2, -1, 0, 1, 2):
        rr = r + dr
        if rr < 0 or rr >= BOARD_SIZE:
            continue
        for dc in (-2, -1, 0, 1, 2):
            cc = c + dc
            if cc < 0 or cc >= BOARD_SIZE:
                continue
            if dr == 0 and dc == 0:
                continue
            if board[rr][cc] != 0:
                bonus += 1
    return bonus


# ----------------- Utilities -----------------

def to_1idx(move_0: Tuple[int, int]) -> Tuple[int, int]:
    return (move_0[0] + 1, move_0[1] + 1)


def board_hash(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> int:
    # Stable hash based on sorted coordinates
    me_s = tuple(sorted(me))
    op_s = tuple(sorted(opponent))
    return hash((me_s, op_s))
