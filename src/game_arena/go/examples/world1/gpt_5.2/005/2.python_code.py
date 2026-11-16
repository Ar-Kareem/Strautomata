
from __future__ import annotations

from typing import List, Tuple, Set, Dict, Optional

N = 19
EMPTY, ME, OPP = 0, 1, 2

Coord = Tuple[int, int]


def policy(me: List[Coord], opponent: List[Coord]) -> Coord:
    """
    Returns next move (row, col) on 19x19 Go board (1-indexed). (0,0) = pass.
    Always returns a legal move under basic Go rules (no playing on occupied points,
    no suicide after captures). Ko is not enforced due to missing history.
    """
    board = [[EMPTY] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            # If both lists contain same point, prefer 'me' as already set.
            if board[r - 1][c - 1] == EMPTY:
                board[r - 1][c - 1] = OPP

    total_stones = len(me) + len(opponent)

    # Opening: prioritize strong central and star points if available.
    opening_points = [
        (10, 10),
        (4, 4), (4, 16), (16, 4), (16, 16),
        (4, 10), (10, 4), (10, 16), (16, 10),
        (7, 7), (7, 13), (13, 7), (13, 13),
    ]
    if total_stones < 6:
        for mv in opening_points:
            if is_legal_move(board, mv[0] - 1, mv[1] - 1, ME):
                return mv

    # If board empty (just in case), play center.
    if total_stones == 0:
        return (10, 10)

    # Precompute groups for both colors (for candidate generation & some scoring).
    my_groups, my_gid = compute_groups(board, ME)
    opp_groups, opp_gid = compute_groups(board, OPP)

    # Precompute "save moves" for own groups in atari: liberty -> total group size.
    save_atari: Dict[Tuple[int, int], int] = {}
    for g in my_groups:
        if len(g["liberties"]) == 1:
            (lr, lc) = next(iter(g["liberties"]))
            save_atari[(lr, lc)] = save_atari.get((lr, lc), 0) + g["size"]

    # Precompute capture moves for opponent groups in atari: liberty -> total group size.
    cap_atari: Dict[Tuple[int, int], int] = {}
    for g in opp_groups:
        if len(g["liberties"]) == 1:
            (lr, lc) = next(iter(g["liberties"]))
            cap_atari[(lr, lc)] = cap_atari.get((lr, lc), 0) + g["size"]

    # Candidate generation: urgent liberties + nearby points.
    candidates: Set[Tuple[int, int]] = set()

    # Always include atari saves/captures directly.
    for (lr, lc) in save_atari.keys():
        candidates.add((lr, lc))
    for (lr, lc) in cap_atari.keys():
        candidates.add((lr, lc))

    # Add empties within Manhattan distance 2 of existing stones.
    stones = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                stones.append((r, c))

    for (sr, sc) in stones:
        for dr in range(-2, 3):
            rem = 2 - abs(dr)
            for dc in range(-rem, rem + 1):
                rr, cc = sr + dr, sc + dc
                if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == EMPTY:
                    candidates.add((rr, cc))

    # If candidates somehow empty, consider whole board as fallback.
    if not candidates:
        for r in range(N):
            for c in range(N):
                if board[r][c] == EMPTY:
                    candidates.add((r, c))

    # Evaluate candidates.
    best_move: Optional[Tuple[int, int]] = None
    best_score = -10**18

    for (r, c) in candidates:
        if board[r][c] != EMPTY:
            continue
        sim = simulate_move(board, r, c, ME)
        if sim is None:
            continue
        board2, captured = sim

        score = 0

        # Huge priority: capture.
        if captured > 0:
            score += 100000 * captured

        # Saving own atari.
        if (r, c) in save_atari:
            score += 30000 * save_atari[(r, c)]

        # Capturing opponent in atari (even if multi-group sums).
        if (r, c) in cap_atari:
            score += 50000 * cap_atari[(r, c)]

        # Avoid filling real eyes unless it captures.
        if captured == 0 and is_simple_eye(board, r, c, ME):
            score -= 20000

        # Connection bonus: adjacent distinct friendly groups.
        adjacent_my_groups = set()
        for (nr, nc) in neighbors(r, c):
            if board[nr][nc] == ME:
                gid = my_gid[nr][nc]
                if gid != -1:
                    adjacent_my_groups.add(gid)
        if len(adjacent_my_groups) >= 2:
            score += 8000 * (len(adjacent_my_groups) - 1)

        # Tactical pressure: after the move, if adjacent enemy groups are put in atari.
        # Also mild bonus for reducing liberties.
        local_seen: Set[Tuple[int, int]] = set()
        for (nr, nc) in neighbors(r, c):
            if board2[nr][nc] == OPP and (nr, nc) not in local_seen:
                stones_set, libs = group_and_liberties(board2, nr, nc)
                local_seen |= stones_set
                libn = len(libs)
                size = len(stones_set)
                if libn == 1:
                    score += 12000 * size
                elif libn == 2:
                    score += 2000 * size
                elif libn == 3:
                    score += 500 * size

        # Self-atari avoidance: penalize if our new group has only 1 liberty and no capture.
        my_stones, my_libs = group_and_liberties(board2, r, c)
        my_libn = len(my_libs)
        if captured == 0 and my_libn == 1:
            score -= 40000
        elif my_libn >= 4:
            score += 500  # prefer freer shapes a little

        # Positional bias: center-ish, but not overwhelming.
        score += center_bias(r, c)

        # Small bias: play closer to opponent stones (keeps the game interactive).
        score += proximity_bias(board, r, c)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # Fallback: find the first legal move on the board.
    for r in range(N):
        for c in range(N):
            if is_legal_move(board, r, c, ME):
                return (r + 1, c + 1)

    return (0, 0)  # pass if nothing is legal


def neighbors(r: int, c: int):
    if r > 0:
        yield (r - 1, c)
    if r + 1 < N:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c + 1 < N:
        yield (r, c + 1)


def diag_neighbors(r: int, c: int):
    for dr in (-1, 1):
        for dc in (-1, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                yield (rr, cc)


def group_and_liberties(board: List[List[int]], sr: int, sc: int) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    color = board[sr][sc]
    stack = [(sr, sc)]
    stones: Set[Tuple[int, int]] = set()
    libs: Set[Tuple[int, int]] = set()
    while stack:
        r, c = stack.pop()
        if (r, c) in stones:
            continue
        stones.add((r, c))
        for nr, nc in neighbors(r, c):
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in stones:
                stack.append((nr, nc))
    return stones, libs


def simulate_move(board: List[List[int]], r: int, c: int, color: int) -> Optional[Tuple[List[List[int]], int]]:
    """Return (new_board, captured_count) if legal (non-suicide), else None."""
    if board[r][c] != EMPTY:
        return None
    opp = OPP if color == ME else ME

    b2 = [row[:] for row in board]
    b2[r][c] = color

    captured_total = 0
    checked: Set[Tuple[int, int]] = set()

    # Capture adjacent opponent groups that now have 0 liberties.
    for nr, nc in neighbors(r, c):
        if b2[nr][nc] == opp and (nr, nc) not in checked:
            stones, libs = group_and_liberties(b2, nr, nc)
            checked |= stones
            if len(libs) == 0:
                for (sr, sc) in stones:
                    b2[sr][sc] = EMPTY
                captured_total += len(stones)

    # Check suicide: our placed stone's group must have at least 1 liberty after captures.
    stones, libs = group_and_liberties(b2, r, c)
    if len(libs) == 0:
        return None

    return b2, captured_total


def is_legal_move(board: List[List[int]], r: int, c: int, color: int) -> bool:
    if not (0 <= r < N and 0 <= c < N):
        return False
    if board[r][c] != EMPTY:
        return False
    return simulate_move(board, r, c, color) is not None


def compute_groups(board: List[List[int]], color: int):
    visited = [[False] * N for _ in range(N)]
    gid = [[-1] * N for _ in range(N)]
    groups = []
    gidx = 0

    for r in range(N):
        for c in range(N):
            if board[r][c] != color or visited[r][c]:
                continue
            stack = [(r, c)]
            stones = []
            libs: Set[Tuple[int, int]] = set()
            visited[r][c] = True
            while stack:
                rr, cc = stack.pop()
                gid[rr][cc] = gidx
                stones.append((rr, cc))
                for nr, nc in neighbors(rr, cc):
                    v = board[nr][nc]
                    if v == EMPTY:
                        libs.add((nr, nc))
                    elif v == color and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            groups.append({"stones": stones, "liberties": libs, "size": len(stones)})
            gidx += 1

    return groups, gid


def is_simple_eye(board: List[List[int]], r: int, c: int, color: int) -> bool:
    """Conservative simple-eye detector to avoid wasting moves."""
    if board[r][c] != EMPTY:
        return False

    # All orthogonal neighbors must be our stones or off-board.
    for nr, nc in neighbors(r, c):
        if board[nr][nc] != color:
            return False

    # Diagonals: reject if any opponent diagonal is present; require strong corner support.
    opp = OPP if color == ME else ME
    opp_diag = 0
    good_diag = 0
    total_diag = 0
    for nr, nc in diag_neighbors(r, c):
        total_diag += 1
        if board[nr][nc] == opp:
            opp_diag += 1
        elif board[nr][nc] == color:
            good_diag += 1

    if opp_diag > 0:
        return False

    # If near edge/corner fewer diagonals exist; still require most diagonals be friendly.
    if total_diag == 4:
        return good_diag >= 3
    if total_diag == 2:
        return good_diag >= 1
    if total_diag == 1:
        return good_diag >= 1
    return False


def center_bias(r: int, c: int) -> int:
    # Peak at center (9,9) in 0-index; mild falloff.
    cr, cc = 9, 9
    d = abs(r - cr) + abs(c - cc)
    return max(0, 60 - 4 * d)


def proximity_bias(board: List[List[int]], r: int, c: int) -> int:
    # Encourage playing within 3 of opponent stones lightly.
    bonus = 0
    for dr in range(-3, 4):
        rr = r + dr
        if rr < 0 or rr >= N:
            continue
        rem = 3 - abs(dr)
        for dc in range(-rem, rem + 1):
            cc = c + dc
            if cc < 0 or cc >= N:
                continue
            if board[rr][cc] == OPP:
                dist = abs(dr) + abs(dc)
                bonus += max(0, 10 - 2 * dist)
    return bonus
