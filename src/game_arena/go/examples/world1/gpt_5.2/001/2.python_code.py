
from __future__ import annotations

from collections import deque
from typing import List, Tuple, Set, Dict

BOARD_SIZE = 19
EMPTY, ME, OP = 0, 1, -1


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Build board
    board = [[EMPTY] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r][c] = ME
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r][c] = OP

    # Opening: empty board
    if not me and not opponent:
        return (10, 10)

    def in_bounds(r: int, c: int) -> bool:
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

    def neighbors(r: int, c: int):
        if r > 1:
            yield (r - 1, c)
        if r < BOARD_SIZE:
            yield (r + 1, c)
        if c > 1:
            yield (r, c - 1)
        if c < BOARD_SIZE:
            yield (r, c + 1)

    def get_group_and_liberties(bd, sr: int, sc: int):
        color = bd[sr][sc]
        q = deque([(sr, sc)])
        visited = {(sr, sc)}
        stones = []
        libs: Set[Tuple[int, int]] = set()
        while q:
            r, c = q.popleft()
            stones.append((r, c))
            for nr, nc in neighbors(r, c):
                v = bd[nr][nc]
                if v == EMPTY:
                    libs.add((nr, nc))
                elif v == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return stones, libs

    # Precompute our atari defenses (liberty -> size of group)
    def compute_atari_map(bd, color: int) -> Dict[Tuple[int, int], int]:
        seen: Set[Tuple[int, int]] = set()
        atari: Dict[Tuple[int, int], int] = {}
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if bd[r][c] == color and (r, c) not in seen:
                    stones, libs = get_group_and_liberties(bd, r, c)
                    for s in stones:
                        seen.add(s)
                    if len(libs) == 1:
                        lib = next(iter(libs))
                        atari[lib] = atari.get(lib, 0) + len(stones)
        return atari

    my_atari_map = compute_atari_map(board, ME)
    op_atari_map = compute_atari_map(board, OP)

    def simulate_move(bd, move: Tuple[int, int]):
        r, c = move
        if not in_bounds(r, c) or bd[r][c] != EMPTY:
            return None  # illegal: off board or occupied

        # Copy board (19x19 is small)
        nb = [row[:] for row in bd]
        nb[r][c] = ME

        captured = 0
        # Capture adjacent opponent groups with no liberties after placement
        checked: Set[Tuple[int, int]] = set()
        for nr, nc in neighbors(r, c):
            if nb[nr][nc] == OP and (nr, nc) not in checked:
                stones, libs = get_group_and_liberties(nb, nr, nc)
                for s in stones:
                    checked.add(s)
                if len(libs) == 0:
                    for gr, gc in stones:
                        nb[gr][gc] = EMPTY
                    captured += len(stones)

        # Check for suicide (allow if captures created liberties)
        stones, libs = get_group_and_liberties(nb, r, c)
        if len(libs) == 0:
            return None  # illegal suicide

        # Evaluate adjacent opponent groups' post-move liberties for atari pressure
        opp_atari_threat = 0
        checked2: Set[Tuple[int, int]] = set()
        for nr, nc in neighbors(r, c):
            if nb[nr][nc] == OP and (nr, nc) not in checked2:
                g, l = get_group_and_liberties(nb, nr, nc)
                for s in g:
                    checked2.add(s)
                if len(l) == 1:
                    opp_atari_threat += len(g)

        # Own liberties count for self-atari avoidance
        own_libs = len(libs)

        return nb, captured, opp_atari_threat, own_libs

    # Candidate generation: empty points adjacent to any stone
    occupied = set(me) | set(opponent)
    candidates: Set[Tuple[int, int]] = set()
    for (r, c) in occupied:
        if not in_bounds(r, c):
            continue
        for nr, nc in neighbors(r, c):
            if board[nr][nc] == EMPTY:
                candidates.add((nr, nc))

    # Add opening/star points if free (simple positional bias)
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10)]
    for sp in star_points:
        rr, cc = sp
        if board[rr][cc] == EMPTY:
            candidates.add(sp)

    # If still none, consider all empties
    if not candidates:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if board[r][c] == EMPTY:
                    candidates.add((r, c))

    def local_features(bd, r: int, c: int):
        # Quick local heuristic: count friendly/enemy adjacent and empty
        fr = en = em = 0
        for nr, nc in neighbors(r, c):
            v = bd[nr][nc]
            if v == ME:
                fr += 1
            elif v == OP:
                en += 1
            else:
                em += 1
        return fr, en, em

    def center_bonus(r: int, c: int) -> float:
        # smaller distance -> higher score
        dr = abs(r - 10)
        dc = abs(c - 10)
        return -0.15 * (dr + dc)

    best_move = None
    best_score = float("-inf")

    # Deterministic tie-break: prefer lower row then col
    def better_tie(m1, m2):
        if m2 is None:
            return True
        return m1 < m2

    for mv in candidates:
        sim = simulate_move(board, mv)
        if sim is None:
            continue
        nb, captured, opp_atari_threat, own_libs = sim
        r, c = mv

        # Defense: if move is the sole liberty of our atari group(s), reward
        defense = my_atari_map.get(mv, 0)

        # Immediate capture threat: if move is sole liberty of opponent group(s)
        # (often overlaps with captured; still useful if move captures via snapback shapes)
        capture_threat = op_atari_map.get(mv, 0)

        fr, en, em = local_features(board, r, c)

        # Avoid self-atari (but allow if capturing big)
        self_atari_penalty = 0.0
        if own_libs == 1 and captured == 0:
            self_atari_penalty = 60.0
        elif own_libs == 2 and captured == 0:
            self_atari_penalty = 10.0

        # Base scoring
        score = 0.0
        score += 120.0 * captured
        score += 90.0 * defense
        score += 35.0 * opp_atari_threat
        score += 20.0 * capture_threat  # encourages taking atari points
        score += 6.0 * fr - 7.0 * en + 2.0 * em
        score += center_bonus(r, c)
        score -= self_atari_penalty

        # Slight preference for connecting (adjacent friendly stones)
        if fr >= 2:
            score += 8.0

        if score > best_score or (score == best_score and better_tie(mv, best_move)):
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Fallback: any legal move (should be rare)
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] != EMPTY:
                continue
            if simulate_move(board, (r, c)) is not None:
                return (r, c)

    # No legal move found - pass
    return (0, 0)
