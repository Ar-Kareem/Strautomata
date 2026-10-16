
from __future__ import annotations

from collections import deque
from typing import List, Tuple, Set, Dict

BOARD_N = 19
EMPTY, ME, OPP = 0, 1, 2

Coord = Tuple[int, int]


def policy(me: List[Coord], opponent: List[Coord]) -> Coord:
    board = [[EMPTY] * (BOARD_N + 1) for _ in range(BOARD_N + 1)]
    me_set = set(me)
    opp_set = set(opponent)

    for r, c in me_set:
        if 1 <= r <= BOARD_N and 1 <= c <= BOARD_N:
            board[r][c] = ME
    for r, c in opp_set:
        if 1 <= r <= BOARD_N and 1 <= c <= BOARD_N:
            # If inconsistent input overlaps, prefer "me" (we are to move).
            if board[r][c] == EMPTY:
                board[r][c] = OPP

    move_num = len(me_set) + len(opp_set)

    # Opening: prefer star points when board is empty / very early.
    star_points = [
        (4, 4), (4, 10), (4, 16),
        (10, 4), (10, 10), (10, 16),
        (16, 4), (16, 10), (16, 16),
    ]
    if move_num == 0:
        for sp in star_points:
            if is_empty(board, sp):
                return sp
        return (10, 10) if is_empty(board, (10, 10)) else first_legal(board, me_set, opp_set)

    # 1) Immediate captures of opponent groups in atari.
    cap_move = best_atari_capture(board)
    if cap_move is not None:
        return cap_move

    # 2) Save our own groups in atari.
    save_move = best_atari_save(board)
    if save_move is not None:
        return save_move

    # 3) Otherwise, search best scored move among a compact candidate set.
    candidates = generate_candidates(board, me_set, opp_set, move_num, star_points)

    best_mv = None
    best_sc = float("-inf")

    for mv in candidates:
        ok, sim = simulate_move(board, mv, ME)
        if not ok:
            continue
        sc = score_position(board, sim, mv, move_num)
        if sc > best_sc:
            best_sc, best_mv = sc, mv

    if best_mv is not None:
        return best_mv

    # Fallback: any legal move else pass
    fb = first_legal(board, me_set, opp_set)
    return fb if fb is not None else (0, 0)


def is_on_board(p: Coord) -> bool:
    r, c = p
    return 1 <= r <= BOARD_N and 1 <= c <= BOARD_N


def is_empty(board, p: Coord) -> bool:
    r, c = p
    return is_on_board(p) and board[r][c] == EMPTY


def neighbors(p: Coord):
    r, c = p
    if r > 1:
        yield (r - 1, c)
    if r < BOARD_N:
        yield (r + 1, c)
    if c > 1:
        yield (r, c - 1)
    if c < BOARD_N:
        yield (r, c + 1)


def get_group_and_liberties(board, start: Coord, color: int) -> Tuple[Set[Coord], Set[Coord]]:
    """BFS group and liberties for given color starting at start."""
    q = deque([start])
    group = set([start])
    libs = set()
    while q:
        p = q.popleft()
        for nb in neighbors(p):
            r, c = nb
            v = board[r][c]
            if v == EMPTY:
                libs.add(nb)
            elif v == color and nb not in group:
                group.add(nb)
                q.append(nb)
    return group, libs


def all_groups(board, color: int) -> List[Tuple[Set[Coord], Set[Coord]]]:
    visited = set()
    groups = []
    for r in range(1, BOARD_N + 1):
        row = board[r]
        for c in range(1, BOARD_N + 1):
            if row[c] == color and (r, c) not in visited:
                g, libs = get_group_and_liberties(board, (r, c), color)
                visited |= g
                groups.append((g, libs))
    return groups


def simulate_move(board, mv: Coord, color: int):
    """Return (legal, new_board). Handles captures; disallows suicide (unless capture makes it legal)."""
    r, c = mv
    if not (1 <= r <= BOARD_N and 1 <= c <= BOARD_N):
        return False, None
    if board[r][c] != EMPTY:
        return False, None

    newb = [row[:] for row in board]
    newb[r][c] = color
    opp = OPP if color == ME else ME

    # Capture any adjacent opponent groups with no liberties after placement.
    to_remove = set()
    for nb in neighbors(mv):
        rr, cc = nb
        if newb[rr][cc] == opp:
            g, libs = get_group_and_liberties(newb, nb, opp)
            if len(libs) == 0:
                to_remove |= g
    for rr, cc in to_remove:
        newb[rr][cc] = EMPTY

    # Check suicide: our placed stone's group must have liberties.
    g_me, libs_me = get_group_and_liberties(newb, mv, color)
    if len(libs_me) == 0:
        return False, None

    return True, newb


def best_atari_capture(board) -> None:
    best = None
    best_cap = -1
    best_tiebreak = float("-inf")

    for g, libs in all_groups(board, OPP):
        if len(libs) != 1:
            continue
        mv = next(iter(libs))
        ok, sim = simulate_move(board, mv, ME)
        if not ok:
            continue
        cap = count_removed(board, sim, OPP)
        if cap <= 0:
            # sometimes atari liberty may not capture due to shared liberty changes; ignore
            continue
        # Tiebreak: prefer capturing more and improving liberties
        _, libs_after = get_group_and_liberties(sim, mv, ME)
        tiebreak = cap * 1000 + len(libs_after)
        if cap > best_cap or (cap == best_cap and tiebreak > best_tiebreak):
            best_cap = cap
            best_tiebreak = tiebreak
            best = mv
    return best


def best_atari_save(board) -> None:
    best = None
    best_sc = float("-inf")
    for g, libs in all_groups(board, ME):
        if len(libs) != 1:
            continue
        mv = next(iter(libs))
        ok, sim = simulate_move(board, mv, ME)
        if not ok:
            continue
        # Score saving move by resulting liberties + any captures.
        cap = count_removed(board, sim, OPP)
        _, libs_after = get_group_and_liberties(sim, mv, ME)
        # Strongly prefer moves that produce >=2 liberties.
        sc = cap * 500 + len(libs_after) * 10
        if len(libs_after) == 1:
            sc -= 50
        if sc > best_sc:
            best_sc = sc
            best = mv
    return best


def count_removed(before, after, color: int) -> int:
    cnt_before = 0
    cnt_after = 0
    for r in range(1, BOARD_N + 1):
        br = before[r]
        ar = after[r]
        for c in range(1, BOARD_N + 1):
            if br[c] == color:
                cnt_before += 1
            if ar[c] == color:
                cnt_after += 1
    return cnt_before - cnt_after


def generate_candidates(board, me_set: Set[Coord], opp_set: Set[Coord], move_num: int, star_points: List[Coord]) -> List[Coord]:
    stones = list(me_set | opp_set)

    cand = set()

    # Always include star points (opening influence) and center.
    for sp in star_points:
        if is_empty(board, sp):
            cand.add(sp)
    if is_empty(board, (10, 10)):
        cand.add((10, 10))

    if not stones:
        # No stones: just use star points/center
        return list(cand) if cand else [(10, 10)]

    # Neighborhood around stones up to Manhattan distance 2
    for (r, c) in stones:
        for dr in (-2, -1, 0, 1, 2):
            rr = r + dr
            if rr < 1 or rr > BOARD_N:
                continue
            # Remaining distance for columns
            rem = 2 - abs(dr)
            for dc in range(-rem, rem + 1):
                cc = c + dc
                if 1 <= cc <= BOARD_N and board[rr][cc] == EMPTY:
                    cand.add((rr, cc))

    # If too many, downselect by a cheap heuristic: adjacency to stones + centrality.
    if len(cand) > 250:
        scored = []
        for mv in cand:
            adj = 0
            for nb in neighbors(mv):
                rr, cc = nb
                if board[rr][cc] != EMPTY:
                    adj += 1
            # prefer not-too-edge early
            dist_center = abs(mv[0] - 10) + abs(mv[1] - 10)
            quick = adj * 5 - 0.3 * dist_center
            # in very early moves, boost star points
            if move_num < 8 and mv in set(star_points):
                quick += 3.0
            scored.append((quick, mv))
        scored.sort(reverse=True)
        cand = {mv for _, mv in scored[:250]}

    return list(cand)


def score_position(before_board, after_board, mv: Coord, move_num: int) -> float:
    # Captures are primary.
    captured = count_removed(before_board, after_board, OPP)
    score = captured * 1200.0

    # Liberties of the new group.
    _, libs = get_group_and_liberties(after_board, mv, ME)
    score += len(libs) * 6.0
    if len(libs) == 1:
        score -= 250.0  # self-atari

    # Create atari against opponent.
    atari_created = 0
    for nb in neighbors(mv):
        r, c = nb
        if after_board[r][c] == OPP:
            g, l = get_group_and_liberties(after_board, nb, OPP)
            if len(l) == 1:
                atari_created += 1
    score += atari_created * 60.0

    # Connection / shape: adjacency counts.
    adj_friend = 0
    adj_opp = 0
    for nb in neighbors(mv):
        r, c = nb
        if after_board[r][c] == ME:
            adj_friend += 1
        elif after_board[r][c] == OPP:
            adj_opp += 1
    score += adj_friend * 4.0 + adj_opp * 1.5
    if adj_friend >= 2:
        score += 8.0
    if adj_friend >= 3:
        score += 6.0

    # Mild central preference, stronger early.
    dist_center = abs(mv[0] - 10) + abs(mv[1] - 10)
    if move_num < 30:
        score += (12.0 - dist_center) * 0.9
    else:
        score += (10.0 - dist_center) * 0.3

    # Avoid very edgey plays early unless tactical.
    if move_num < 12:
        if mv[0] in (1, 19) or mv[1] in (1, 19):
            score -= 6.0
        elif mv[0] in (2, 18) or mv[1] in (2, 18):
            score -= 2.5

    return score


def first_legal(board, me_set: Set[Coord], opp_set: Set[Coord]) -> None:
    # Try nearby empties first for speed.
    union = list(me_set | opp_set)
    tried = set()
    for p in union[:50]:
        for nb in neighbors(p):
            if nb in tried:
                continue
            tried.add(nb)
            if is_empty(board, nb):
                ok, _ = simulate_move(board, nb, ME)
                if ok:
                    return nb

    # Otherwise scan all.
    for r in range(1, BOARD_N + 1):
        for c in range(1, BOARD_N + 1):
            if board[r][c] == EMPTY:
                ok, _ = simulate_move(board, (r, c), ME)
                if ok:
                    return (r, c)
    return None
