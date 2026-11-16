
from __future__ import annotations

from typing import List, Tuple, Set, Optional
import random

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

Coord = Tuple[int, int]


def _inb(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _build_board(me: List[Coord], opp: List[Coord]) -> List[List[int]]:
    b = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            b[r - 1][c - 1] = 1
    for r, c in opp:
        if 1 <= r <= N and 1 <= c <= N:
            # If malformed input overlaps, keep "me" as priority (still avoid crash).
            if b[r - 1][c - 1] == 0:
                b[r - 1][c - 1] = -1
    return b


def _group_and_liberties(board: List[List[int]], sr: int, sc: int) -> Tuple[List[Tuple[int, int]], Set[Tuple[int, int]]]:
    color = board[sr][sc]
    stack = [(sr, sc)]
    seen = {(sr, sc)}
    stones: List[Tuple[int, int]] = []
    libs: Set[Tuple[int, int]] = set()
    while stack:
        r, c = stack.pop()
        stones.append((r, c))
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not _inb(nr, nc):
                continue
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return stones, libs


def _remove_stones(board: List[List[int]], stones: List[Tuple[int, int]]) -> None:
    for r, c in stones:
        board[r][c] = 0


def _simulate_move(board: List[List[int]], r: int, c: int, player: int = 1) -> Tuple[bool, int, int, List[List[int]]]:
    """
    Returns (legal, captured_count, my_liberties_after, new_board).
    Implements captures and suicide check. Does NOT implement ko (not possible with given API).
    """
    if not _inb(r, c) or board[r][c] != 0:
        return (False, 0, 0, board)

    nb = [row[:] for row in board]
    nb[r][c] = player
    opp = -player

    captured = 0
    # Capture any adjacent opponent groups with no liberties after placement.
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inb(nr, nc) or nb[nr][nc] != opp:
            continue
        stones, libs = _group_and_liberties(nb, nr, nc)
        if len(libs) == 0:
            captured += len(stones)
            _remove_stones(nb, stones)

    # Check for suicide: my group must have at least one liberty after captures.
    my_stones, my_libs = _group_and_liberties(nb, r, c)
    my_lib_count = len(my_libs)
    if my_lib_count == 0:
        return (False, 0, 0, board)

    return (True, captured, my_lib_count, nb)


def _is_simple_eye_like(board: List[List[int]], r: int, c: int, player: int = 1) -> bool:
    """
    Very simple eye-ish test: all adjacent points are either player stones or off-board.
    (Doesn't fully validate true eyes; only used as a soft penalty.)
    """
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inb(nr, nc):
            if board[nr][nc] != player:
                return False
    return True


def _candidate_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    """
    Generate a compact list of plausible candidates:
    - All empty points adjacent to any stone (both colors),
    - plus distance-2 neighbors,
    - plus opening points (4-4s, 3-4s, center).
    """
    occ: List[Tuple[int, int]] = []
    empties = 0
    for r in range(N):
        row = board[r]
        for c in range(N):
            if row[c] != 0:
                occ.append((r, c))
            else:
                empties += 1

    cand: Set[Tuple[int, int]] = set()

    if not occ:
        # Empty board: just return key points.
        return [(3, 3), (3, 15), (15, 3), (15, 15), (9, 9), (3, 9), (9, 3), (9, 15), (15, 9)]

    # Neighborhood around stones
    for r, c in occ:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if _inb(nr, nc) and board[nr][nc] == 0:
                cand.add((nr, nc))
            # distance 2 (via same direction)
            nr2, nc2 = r + 2 * dr, c + 2 * dc
            if _inb(nr2, nc2) and board[nr2][nc2] == 0:
                cand.add((nr2, nc2))
        # also add knight-ish (L) around stones
        for dr, dc in ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)):
            nr, nc = r + dr, c + dc
            if _inb(nr, nc) and board[nr][nc] == 0:
                cand.add((nr, nc))

    # Opening points / strategic anchors
    anchors = [
        (3, 3), (3, 15), (15, 3), (15, 15),      # 4-4
        (2, 3), (3, 2), (2, 15), (3, 16),        # 3-4 / 4-3 near corners
        (15, 2), (16, 3), (15, 16), (16, 15),
        (9, 9), (3, 9), (9, 3), (9, 15), (15, 9)
    ]
    for r, c in anchors:
        if board[r][c] == 0:
            cand.add((r, c))

    # If too few candidates (rare), add some random empties deterministically.
    if len(cand) < 12:
        empt = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        # deterministic shuffle seed based on board occupancy
        seed = 0
        for r, c in occ[:64]:
            seed = (seed * 1315423911 + (r * 19 + c + 1) * 2654435761) & 0xFFFFFFFF
        rng = random.Random(seed)
        rng.shuffle(empt)
        for p in empt[:40]:
            cand.add(p)

    return list(cand)


def _urgent_saves(board: List[List[int]]) -> List[Tuple[int, int]]:
    """
    If any of my groups are in atari (1 liberty), return those liberty points as urgent candidates.
    """
    seen: Set[Tuple[int, int]] = set()
    saves: Set[Tuple[int, int]] = set()
    for r in range(N):
        for c in range(N):
            if board[r][c] != 1 or (r, c) in seen:
                continue
            stones, libs = _group_and_liberties(board, r, c)
            for s in stones:
                seen.add(s)
            if len(libs) == 1:
                (lr, lc) = next(iter(libs))
                if board[lr][lc] == 0:
                    saves.add((lr, lc))
    return list(saves)


def _capture_moves(board: List[List[int]]) -> List[Tuple[int, int, int]]:
    """
    Find moves that immediately capture opponent stones.
    Returns list of (r,c,captured_count).
    """
    caps: List[Tuple[int, int, int]] = []
    cand = _candidate_moves(board)
    for r, c in cand:
        legal, captured, my_libs, _nb = _simulate_move(board, r, c, player=1)
        if legal and captured > 0:
            caps.append((r, c, captured))
    caps.sort(key=lambda x: (-x[2], x[0], x[1]))
    return caps


def _score_move(board: List[List[int]], r: int, c: int) -> Tuple[int, int, int]:
    """
    Returns a tuple score (primary, secondary, tertiary) for lexicographic comparison.
    Higher is better.
    """
    legal, captured, my_libs, nb = _simulate_move(board, r, c, player=1)
    if not legal:
        return (-10**9, 0, 0)

    # Primary: tactical gains
    score = 0
    score += captured * 1000

    # Penalize self-atari unless it captured
    if captured == 0 and my_libs == 1:
        score -= 800

    # Slight penalty for filling (simple) own eye-ish point if not capturing.
    if captured == 0 and _is_simple_eye_like(board, r, c, player=1):
        score -= 200

    # Reward liberties after move (stability)
    score += my_libs * 8

    # Pressure: adjacent opponent groups in atari after the move
    atari_bonus = 0
    adjacent_opp_groups_seen: Set[Tuple[int, int]] = set()
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inb(nr, nc) or nb[nr][nc] != -1:
            continue
        if (nr, nc) in adjacent_opp_groups_seen:
            continue
        stones, libs = _group_and_liberties(nb, nr, nc)
        for s in stones:
            adjacent_opp_groups_seen.add(s)
        lcnt = len(libs)
        if lcnt == 1:
            atari_bonus += 120
        elif lcnt == 2:
            atari_bonus += 30
        else:
            atari_bonus += 5
    score += atari_bonus

    # Connection bonus: adjacent friendly stones
    conn = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inb(nr, nc) and board[nr][nc] == 1:
            conn += 1
    score += conn * 18

    # Prefer not-too-edge early unless tactical; gentle center bias
    # distance to center (9,9) in 0-based
    dc = abs(r - 9) + abs(c - 9)
    score += max(0, 20 - dc)

    # Secondary tie-breakers: captured, libs
    return (score, captured, my_libs)


def policy(me: List[Coord], opponent: List[Coord]) -> Coord:
    board = _build_board(me, opponent)

    # Deterministic RNG for any ordering needs
    seed = 1469598103934665603
    for (r, c) in (me[:64] + opponent[:64]):
        seed ^= (r * 31 + c + 7)
        seed *= 1099511628211
        seed &= (1 << 64) - 1
    rng = random.Random(seed)

    # 1) Immediate best captures
    caps = _capture_moves(board)
    if caps:
        # Pick highest capture, but break ties by evaluation score.
        best = None
        best_sc = (-10**18, 0, 0)
        topn = caps[:12]
        for r, c, _k in topn:
            sc = _score_move(board, r, c)
            if sc > best_sc:
                best_sc = sc
                best = (r, c)
        if best is not None:
            return (best[0] + 1, best[1] + 1)

    # 2) Save my groups in atari (urgent defense)
    saves = _urgent_saves(board)
    if saves:
        # Evaluate saves; pick best legal.
        rng.shuffle(saves)
        best = None
        best_sc = (-10**18, 0, 0)
        for r, c in saves:
            sc = _score_move(board, r, c)
            if sc > best_sc:
                best_sc = sc
                best = (r, c)
        if best is not None and best_sc[0] > -10**8:
            return (best[0] + 1, best[1] + 1)

    # 3) General move selection from candidates
    cand = _candidate_moves(board)
    rng.shuffle(cand)

    best = None
    best_sc = (-10**18, 0, 0)
    for r, c in cand:
        sc = _score_move(board, r, c)
        if sc > best_sc:
            best_sc = sc
            best = (r, c)

    if best is not None and best_sc[0] > -10**8:
        return (best[0] + 1, best[1] + 1)

    # 4) Fallback: any legal empty point (avoid disqualification)
    empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    rng.shuffle(empties)
    for r, c in empties:
        legal, _cap, _libs, _nb = _simulate_move(board, r, c, player=1)
        if legal:
            return (r + 1, c + 1)

    # 5) If board is full or no legal move, pass.
    return (0, 0)
