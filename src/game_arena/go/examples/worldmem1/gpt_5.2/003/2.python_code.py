
from __future__ import annotations

from collections import deque
from typing import List, Tuple, Dict, Set, Optional

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = -1


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Returns (action, memory) where action is (row, col) in 1..19, or (0,0) to pass.
    Ensures legality: no playing on occupied, no suicide (unless capturing), simple-ko avoidance.
    """
    if memory is None:
        memory = {}

    board = _board_from_lists(me, opponent)
    move_num = int(memory.get("move_num", 0)) + 1

    # Precompute groups in atari (urgent points).
    my_atari_libs = _atari_liberties(board, ME)
    opp_atari_libs = _atari_liberties(board, OPP)

    candidates = _generate_candidates(board, me, opponent, my_atari_libs, opp_atari_libs, move_num)

    ko_forbidden = memory.get("my_last_board_hash", None)  # simple-ko: cannot recreate my previous position

    best_move = None
    best_score = float("-inf")
    best_after_hash = None

    # If there are no candidates (rare), consider all empties.
    if not candidates:
        candidates = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) if board[r - 1][c - 1] == EMPTY]

    # Evaluate candidates.
    for mv in candidates:
        after, captured, legal, my_libs = _simulate_move(board, mv, ME)
        if not legal:
            continue

        after_hash = _board_hash(after)
        if ko_forbidden is not None and after_hash == ko_forbidden:
            continue

        score = _score_move(board, after, mv, captured, my_libs, my_atari_libs, opp_atari_libs)

        if score > best_score:
            best_score = score
            best_move = mv
            best_after_hash = after_hash

    # If no legal move found, pass (always legal).
    if best_move is None:
        best_move = (0, 0)
        best_after_hash = _board_hash(board)

    # Update memory for next call: store hash after my move (for simple ko next time).
    memory = dict(memory)
    memory["move_num"] = move_num
    memory["my_last_board_hash"] = best_after_hash

    return best_move, memory


# ------------------------ Core Helpers ------------------------ #

def _board_from_lists(me: List[Tuple[int, int]], opp: List[Tuple[int, int]]) -> List[List[int]]:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for __ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = ME
    for r, c in opp:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = OPP
    return board


def _in_bounds(r0: int, c0: int) -> bool:
    return 0 <= r0 < BOARD_SIZE and 0 <= c0 < BOARD_SIZE


def _neighbors(r0: int, c0: int):
    if r0 > 0:
        yield (r0 - 1, c0)
    if r0 + 1 < BOARD_SIZE:
        yield (r0 + 1, c0)
    if c0 > 0:
        yield (r0, c0 - 1)
    if c0 + 1 < BOARD_SIZE:
        yield (r0, c0 + 1)


def _group_and_liberties(board: List[List[int]], sr: int, sc: int) -> tuple[Set[tuple[int, int]], Set[tuple[int, int]]]:
    """sr,sc are 0-indexed and assumed non-empty."""
    color = board[sr][sc]
    group: Set[tuple[int, int]] = set()
    libs: Set[tuple[int, int]] = set()
    stack = [(sr, sc)]
    group.add((sr, sc))
    while stack:
        r, c = stack.pop()
        for nr, nc in _neighbors(r, c):
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in group:
                group.add((nr, nc))
                stack.append((nr, nc))
    return group, libs


def _atari_liberties(board: List[List[int]], color: int) -> Set[Tuple[int, int]]:
    """Return set of 1-indexed liberty points for all groups of 'color' that are in atari (exactly 1 liberty)."""
    seen: Set[tuple[int, int]] = set()
    atari_libs: Set[Tuple[int, int]] = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != color or (r, c) in seen:
                continue
            grp, libs = _group_and_liberties(board, r, c)
            seen |= grp
            if len(libs) == 1:
                (lr, lc) = next(iter(libs))
                atari_libs.add((lr + 1, lc + 1))
    return atari_libs


def _simulate_move(board: List[List[int]], move: Tuple[int, int], color: int) -> tuple[List[List[int]], int, bool, int]:
    """
    Simulate placing 'color' at move (1-indexed), applying captures.
    Returns (new_board, captured_count, legal, my_group_liberty_count_after).
    """
    if move == (0, 0):
        return board, 0, True, 0

    r, c = move
    if not (1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE):
        return board, 0, False, 0
    r0, c0 = r - 1, c - 1

    if board[r0][c0] != EMPTY:
        return board, 0, False, 0

    newb = [row[:] for row in board]
    newb[r0][c0] = color
    opp = -color

    captured = 0
    checked_opp_groups: Set[tuple[int, int]] = set()

    # Check neighboring opponent groups for capture.
    for nr, nc in _neighbors(r0, c0):
        if newb[nr][nc] != opp or (nr, nc) in checked_opp_groups:
            continue
        grp, libs = _group_and_liberties(newb, nr, nc)
        checked_opp_groups |= grp
        if len(libs) == 0:
            # capture
            for gr, gc in grp:
                newb[gr][gc] = EMPTY
            captured += len(grp)

    # Check suicide: my new group must have liberties after captures.
    my_grp, my_libs = _group_and_liberties(newb, r0, c0)
    if len(my_libs) == 0:
        return board, 0, False, 0

    return newb, captured, True, len(my_libs)


def _board_hash(board: List[List[int]]) -> bytes:
    """
    Stable compact hash representation (361 bytes).
    Encodes cell values in {OPP=-1, EMPTY=0, ME=1} -> {0,1,2}.
    """
    b = bytearray(BOARD_SIZE * BOARD_SIZE)
    k = 0
    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            b[k] = row[c] + 1
            k += 1
    return bytes(b)


# ------------------------ Candidate Generation ------------------------ #

_STAR_POINTS = [
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
]
_OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 3), (3, 17), (17, 3), (17, 17),
]


def _generate_candidates(
    board: List[List[int]],
    me: List[Tuple[int, int]],
    opp: List[Tuple[int, int]],
    my_atari_libs: Set[Tuple[int, int]],
    opp_atari_libs: Set[Tuple[int, int]],
    move_num: int,
) -> List[Tuple[int, int]]:
    cand: Set[Tuple[int, int]] = set()

    # Always include urgent atari liberties first.
    cand |= set(my_atari_libs)
    cand |= set(opp_atari_libs)

    # Opening: include some known good points.
    total_stones = len(me) + len(opp)
    if total_stones <= 10:
        for p in _OPENING_POINTS:
            r, c = p
            if board[r - 1][c - 1] == EMPTY:
                cand.add(p)

    # Local candidates near existing stones (Manhattan distance <= 2).
    all_stones = me + opp
    for (r, c) in all_stones:
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                if abs(dr) + abs(dc) > 2:
                    continue
                rr, cc = r + dr, c + dc
                if 1 <= rr <= BOARD_SIZE and 1 <= cc <= BOARD_SIZE and board[rr - 1][cc - 1] == EMPTY:
                    cand.add((rr, cc))

    # If still empty (very first move), ensure center is candidate.
    if not cand and board[9][9] == EMPTY:
        cand.add((10, 10))

    return list(cand)


# ------------------------ Scoring ------------------------ #

def _score_move(
    before: List[List[int]],
    after: List[List[int]],
    mv: Tuple[int, int],
    captured: int,
    my_libs_after: int,
    my_atari_libs: Set[Tuple[int, int]],
    opp_atari_libs: Set[Tuple[int, int]],
) -> float:
    r, c = mv
    r0, c0 = r - 1, c - 1

    # Features
    adj_me = 0
    adj_opp = 0
    empty_adj = 0
    for nr, nc in _neighbors(r0, c0):
        v = before[nr][nc]
        if v == ME:
            adj_me += 1
        elif v == OPP:
            adj_opp += 1
        else:
            empty_adj += 1

    # Saving move if it fills the only liberty of a group in atari.
    save_bonus = 1 if mv in my_atari_libs else 0

    # Creating atari threats: count opponent groups adjacent that end up in atari (libs==1) after move.
    opp_atari_created = _count_new_adjacent_atari(after, r0, c0, OPP)

    # Connection bonus: if move touches 2+ distinct friendly groups in the "before" position.
    connect_bonus = _connects_groups(before, r0, c0, ME)

    # Self-atari penalty (unless it captured something big).
    self_atari = 1 if my_libs_after == 1 and captured == 0 else 0

    # Eye-fill-ish penalty: if surrounded by own stones and didn't capture.
    eye_fill = 1 if _looks_like_eye_fill(before, r0, c0) and captured == 0 else 0

    # Center preference (mild): lower distance is better.
    dist_center = abs(r - 10) + abs(c - 10)

    score = 0.0
    score += 1200.0 * captured
    score += 350.0 * save_bonus
    score += 120.0 * opp_atari_created
    score += 60.0 * connect_bonus
    score += 10.0 * adj_opp
    score += 3.0 * adj_me
    score -= 140.0 * self_atari
    score -= 80.0 * eye_fill
    score -= 0.6 * dist_center

    # If opponent already has atari liberties, prefer playing on them (tactical forcing).
    if mv in opp_atari_libs:
        score += 200.0

    # Slight preference to keep liberties (avoid cramped shapes).
    score += 1.5 * min(my_libs_after, 6)

    return score


def _count_new_adjacent_atari(board: List[List[int]], r0: int, c0: int, color: int) -> int:
    seen: Set[tuple[int, int]] = set()
    count = 0
    for nr, nc in _neighbors(r0, c0):
        if board[nr][nc] != color or (nr, nc) in seen:
            continue
        grp, libs = _group_and_liberties(board, nr, nc)
        seen |= grp
        if len(libs) == 1:
            count += 1
    return count


def _connects_groups(board: List[List[int]], r0: int, c0: int, color: int) -> int:
    """Returns 1 if placing at (r0,c0) would connect 2+ distinct adjacent friendly groups (in 'board')."""
    groups_seen: Set[tuple[int, int]] = set()
    reps: Set[tuple[int, int]] = set()
    for nr, nc in _neighbors(r0, c0):
        if board[nr][nc] != color:
            continue
        # Find representative for this group by BFS from the neighbor.
        if (nr, nc) in groups_seen:
            continue
        grp, _ = _group_and_liberties(board, nr, nc)
        groups_seen |= grp
        # Pick stable rep
        rep = min(grp)
        reps.add(rep)
        if len(reps) >= 2:
            return 1
    return 0


def _looks_like_eye_fill(board: List[List[int]], r0: int, c0: int) -> bool:
    """
    Crude eye-fill detector: all orthogonal neighbors are ME (or edge treated as ME),
    and no adjacent opponent stones. Only uses 'before' position.
    """
    # If any adjacent opponent stone exists, it's not a quiet eye fill.
    for nr, nc in _neighbors(r0, c0):
        if board[nr][nc] == OPP:
            return False

    # Count orthogonal neighbors; require at least 3 to be ME (edges help make true eyes).
    me_adj = 0
    total_adj = 0
    for nr, nc in _neighbors(r0, c0):
        total_adj += 1
        if board[nr][nc] == ME:
            me_adj += 1
        elif board[nr][nc] == EMPTY:
            return False  # still open, not an eye fill

    # If point has 4 neighbors, need 4 ME neighbors. If edge (3 neighbors), need 3.
    return me_adj == total_adj and total_adj >= 2
