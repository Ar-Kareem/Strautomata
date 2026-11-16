
from __future__ import annotations

from collections import deque
from typing import List, Tuple, Set, Dict, Iterable, Optional

N = 19
EMPTY = 0
ME = 1
OPP = -1

Point = Tuple[int, int]  # 1-indexed (row, col)


def _in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= N and 1 <= c <= N


def _neighbors(r: int, c: int) -> List[Point]:
    out = []
    if r > 1:
        out.append((r - 1, c))
    if r < N:
        out.append((r + 1, c))
    if c > 1:
        out.append((r, c - 1))
    if c < N:
        out.append((r, c + 1))
    return out


def _build_board(me: List[Point], opponent: List[Point]) -> List[List[int]]:
    b = [[EMPTY] * (N + 1) for _ in range(N + 1)]
    for r, c in me:
        if _in_bounds(r, c):
            b[r][c] = ME
    for r, c in opponent:
        if _in_bounds(r, c):
            b[r][c] = OPP
    return b


def _group_and_liberties(board: List[List[int]], start: Point) -> Tuple[Set[Point], Set[Point]]:
    sr, sc = start
    color = board[sr][sc]
    q = deque([start])
    stones: Set[Point] = set([start])
    libs: Set[Point] = set()

    while q:
        r, c = q.popleft()
        for nr, nc in _neighbors(r, c):
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in stones:
                stones.add((nr, nc))
                q.append((nr, nc))
    return stones, libs


def _all_groups(board: List[List[int]], color: int) -> List[Dict]:
    seen: Set[Point] = set()
    groups = []
    for r in range(1, N + 1):
        row = board[r]
        for c in range(1, N + 1):
            if row[c] == color and (r, c) not in seen:
                stones, libs = _group_and_liberties(board, (r, c))
                seen |= stones
                groups.append({"stones": stones, "libs": libs})
    return groups


def _simulate_move(board: List[List[int]], move: Point, color: int) -> Tuple[bool, Optional[List[List[int]]], int, int, int, int]:
    """
    Returns:
      (legal, new_board, captured_stones, captured_groups, own_liberties, own_group_size)
    """
    r, c = move
    if not _in_bounds(r, c):
        return (False, None, 0, 0, 0, 0)
    if board[r][c] != EMPTY:
        return (False, None, 0, 0, 0, 0)

    opp = -color
    b2 = [row[:] for row in board]
    b2[r][c] = color

    captured_stones = 0
    captured_groups = 0
    checked: Set[Point] = set()

    # Capture adjacent opponent groups that now have no liberties.
    for nr, nc in _neighbors(r, c):
        if b2[nr][nc] == opp and (nr, nc) not in checked:
            stones, libs = _group_and_liberties(b2, (nr, nc))
            checked |= stones
            if len(libs) == 0:
                captured_groups += 1
                captured_stones += len(stones)
                for pr, pc in stones:
                    b2[pr][pc] = EMPTY

    # Check for suicide: own group must have at least one liberty after captures.
    stones_me, libs_me = _group_and_liberties(b2, (r, c))
    if len(libs_me) == 0:
        return (False, None, 0, 0, 0, 0)

    return (True, b2, captured_stones, captured_groups, len(libs_me), len(stones_me))


def _star_points() -> List[Point]:
    pts = [4, 10, 16]
    return [(r, c) for r in pts for c in pts]


def _opening_points() -> List[Point]:
    # Mix of 4-4, 3-4, 4-3, 3-3
    base = []
    for a, b in [(4, 4), (3, 4), (4, 3), (3, 3)]:
        base.extend([(a, b), (a, N + 1 - b), (N + 1 - a, b), (N + 1 - a, N + 1 - b)])
    # Include star points explicitly
    base.extend(_star_points())
    # Dedup while preserving order
    seen = set()
    out = []
    for p in base:
        if p not in seen and _in_bounds(*p):
            seen.add(p)
            out.append(p)
    return out


def _candidate_moves(board: List[List[int]], me: List[Point], opponent: List[Point]) -> List[Point]:
    occupied = set(me) | set(opponent)
    if not occupied:
        return _opening_points()

    cand: Set[Point] = set()

    # Near any stone within manhattan distance 2
    for (r, c) in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) + abs(dc) > 2:
                    continue
                rr, cc = r + dr, c + dc
                if _in_bounds(rr, cc) and board[rr][cc] == EMPTY:
                    cand.add((rr, cc))

    # Add strategic fixed points
    for p in _opening_points():
        r, c = p
        if board[r][c] == EMPTY:
            cand.add(p)

    return list(cand)


def _center_distance_score(r: int, c: int) -> float:
    # Smaller distance => slightly higher score
    cr, cc = 10, 10
    d = abs(r - cr) + abs(c - cc)
    return -0.3 * d


def _count_adjacent_distinct_groups(board: List[List[int]], move: Point, color: int) -> int:
    r, c = move
    seen_groups: Set[Point] = set()
    distinct = 0
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == color:
            # Identify group by its first found stone's root via BFS but cheap because few neighbors
            stones, _ = _group_and_liberties(board, (nr, nc))
            rep = next(iter(stones))
            if rep not in seen_groups:
                seen_groups.add(rep)
                distinct += 1
    return distinct


def _tactical_score(
    board: List[List[int]],
    move: Point,
    b2: List[List[int]],
    captured_stones: int,
    captured_groups: int,
    own_libs: int,
    own_group_size: int,
    me_atari_libs: Set[Point],
    opp_groups: List[Dict],
    early: bool,
) -> float:
    r, c = move
    score = 0.0

    # Big priority: captures
    if captured_stones > 0:
        score += 1200.0 * captured_stones + 200.0 * captured_groups

    # Saving own atari groups (playing on a current atari liberty)
    if move in me_atari_libs:
        score += 900.0

    # Create atari on adjacent opponent groups (post-move)
    # Check only groups adjacent to move in the new board to keep it fast.
    checked: Set[Point] = set()
    for nr, nc in _neighbors(r, c):
        if b2[nr][nc] == OPP and (nr, nc) not in checked:
            stones, libs = _group_and_liberties(b2, (nr, nc))
            checked |= stones
            if len(libs) == 1:
                score += 120.0 * len(stones)

    # Connection bonus
    distinct_adj = _count_adjacent_distinct_groups(board, move, ME)
    if distinct_adj >= 2:
        score += 120.0
    elif distinct_adj == 1:
        score += 15.0

    # Liberty shaping / self-atari avoidance
    score += 7.0 * own_libs
    if captured_stones == 0 and own_libs == 1:
        score -= 500.0
    if captured_stones == 0 and own_libs == 2 and own_group_size >= 4:
        score -= 80.0

    # Opening preferences
    if early:
        if move in _star_points():
            score += 45.0
        # mild corner-ish preference early (but not too strong)
        edge_dist = min(r - 1, N - r, c - 1, N - c)
        if edge_dist <= 3:
            score += 8.0

    # Mild centrality
    score += _center_distance_score(r, c)

    return score


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    board = _build_board(me, opponent)
    total_stones = len(me) + len(opponent)
    early = total_stones < 14

    # Precompute groups and urgent atari liberties
    my_groups = _all_groups(board, ME)
    opp_groups = _all_groups(board, OPP)

    me_atari_libs: Set[Point] = set()
    for g in my_groups:
        if len(g["libs"]) == 1:
            me_atari_libs |= set(g["libs"])

    opp_atari_libs: List[Tuple[int, Point]] = []
    for g in opp_groups:
        if len(g["libs"]) == 1:
            lib = next(iter(g["libs"]))
            opp_atari_libs.append((len(g["stones"]), lib))
    opp_atari_libs.sort(reverse=True)

    # 1) Urgent defense: save atari groups first
    best_move: Optional[Point] = None
    best_score = float("-inf")

    if me_atari_libs:
        for mv in list(me_atari_libs):
            legal, b2, cap_s, cap_g, own_libs, own_size = _simulate_move(board, mv, ME)
            if not legal:
                continue
            sc = _tactical_score(board, mv, b2, cap_s, cap_g, own_libs, own_size, me_atari_libs, opp_groups, early)
            sc += 200.0  # ensure defense dominates
            if sc > best_score:
                best_score = sc
                best_move = mv
        if best_move is not None:
            return best_move

    # 2) Immediate captures: take opponent atari if possible
    for size, lib in opp_atari_libs[:12]:
        legal, b2, cap_s, cap_g, own_libs, own_size = _simulate_move(board, lib, ME)
        if not legal:
            continue
        # Capturing big atari group is huge
        sc = 2000.0 + 200.0 * size + 50.0 * cap_s
        sc += _tactical_score(board, lib, b2, cap_s, cap_g, own_libs, own_size, me_atari_libs, opp_groups, early)
        if sc > best_score:
            best_score = sc
            best_move = lib
    if best_move is not None and best_score >= 1500.0:
        return best_move

    # 3) General search over candidates
    candidates = _candidate_moves(board, me, opponent)

    for mv in candidates:
        legal, b2, cap_s, cap_g, own_libs, own_size = _simulate_move(board, mv, ME)
        if not legal:
            continue
        sc = _tactical_score(board, mv, b2, cap_s, cap_g, own_libs, own_size, me_atari_libs, opp_groups, early)

        # Small bias toward playing adjacent to opponent (pressure) but not too much
        r, c = mv
        adj_opp = sum(1 for nr, nc in _neighbors(r, c) if board[nr][nc] == OPP)
        adj_me = sum(1 for nr, nc in _neighbors(r, c) if board[nr][nc] == ME)
        sc += 6.0 * adj_opp + 2.0 * adj_me

        if sc > best_score:
            best_score = sc
            best_move = mv

    if best_move is not None:
        return best_move

    # 4) Fallback: any legal move on the board
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == EMPTY:
                legal, _, _, _, _, _ = _simulate_move(board, (r, c), ME)
                if legal:
                    return (r, c)

    # 5) If no legal moves exist, pass
    return (0, 0)
