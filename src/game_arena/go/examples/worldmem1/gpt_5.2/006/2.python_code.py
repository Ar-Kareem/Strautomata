
from __future__ import annotations

from collections import deque
from typing import Dict, List, Tuple, Set, Optional
import random

BOARD_N = 19

Move = Tuple[int, int]
Memory = Dict


def policy(me: List[Move], opponent: List[Move], memory: dict) -> Tuple[Move, dict]:
    """
    Return (action, memory).
    action is (row, col) with 1..19, or (0,0) to pass.
    """
    # Build board: 0 empty, +1 = me, -1 = opponent
    board = [[0] * BOARD_N for _ in range(BOARD_N)]
    for r, c in me:
        if 1 <= r <= BOARD_N and 1 <= c <= BOARD_N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_N and 1 <= c <= BOARD_N:
            board[r - 1][c - 1] = -1

    # Ko handling: store the board hash from the start of our previous turn.
    last_start_hash = memory.get("last_start_hash", None)
    current_hash = _board_hash(board)

    # RNG for stable tie-breaking
    seed = memory.get("seed", 0)
    if not seed:
        # deterministic-ish but varies by position
        seed = (hash(current_hash) ^ (len(me) << 10) ^ (len(opponent) << 1)) & 0xFFFFFFFF
    rng = random.Random(seed)

    total_stones = len(me) + len(opponent)

    # 1) Urgent defense: if any of our groups are in atari, consider saving moves first.
    defense_moves = _urgent_defense_moves(board, color=1, ko_forbidden_hash=last_start_hash)

    # 2) Candidate move generation: local empty points near stones + opening points.
    candidates = _generate_candidates(board, total_stones)

    # Always allow pass as a last resort (legal).
    candidates.add((0, 0))

    legal_moves: List[Move] = []
    for mv in candidates:
        if mv == (0, 0):
            legal_moves.append(mv)
            continue
        if _is_legal_move(board, mv, color=1, ko_forbidden_hash=last_start_hash):
            legal_moves.append(mv)

    # If everything failed, fall back to any legal empty point; else pass.
    if not legal_moves:
        for r in range(1, BOARD_N + 1):
            for c in range(1, BOARD_N + 1):
                if board[r - 1][c - 1] == 0 and _is_legal_move(board, (r, c), color=1, ko_forbidden_hash=last_start_hash):
                    action = (r, c)
                    memory = dict(memory)
                    memory["last_start_hash"] = current_hash
                    memory["seed"] = seed
                    return action, memory
        action = (0, 0)
        memory = dict(memory)
        memory["last_start_hash"] = current_hash
        memory["seed"] = seed
        return action, memory

    # If we have urgent defense moves, restrict search to them (plus tactical captures among them).
    if defense_moves:
        legal_def = [m for m in defense_moves if (m == (0, 0) or _is_legal_move(board, m, 1, last_start_hash))]
        if legal_def:
            action = _pick_best_move(board, legal_def, rng, total_stones, last_start_hash)
            memory = dict(memory)
            memory["last_start_hash"] = current_hash
            memory["seed"] = seed
            return action, memory

    # General pick among legal moves
    action = _pick_best_move(board, legal_moves, rng, total_stones, last_start_hash)

    # Update memory with the current board hash (start-of-turn position for next ko check).
    memory = dict(memory)
    memory["last_start_hash"] = current_hash
    memory["seed"] = seed
    return action, memory


# ------------------------- Core move selection -------------------------


def _pick_best_move(board, legal_moves: List[Move], rng: random.Random, total_stones: int, ko_forbidden_hash) -> Move:
    # Prefer non-pass if any decent move exists.
    best_mv = (0, 0)
    best_sc = -10**18

    for mv in legal_moves:
        if mv == (0, 0):
            # passing is allowed but generally bad unless no alternative
            sc = -50.0
        else:
            sc = _score_move(board, mv, rng, total_stones, ko_forbidden_hash)
        if sc > best_sc:
            best_sc = sc
            best_mv = mv

    # If best is pass but there exists any non-pass legal move, take the best non-pass.
    if best_mv == (0, 0):
        best2_mv = (0, 0)
        best2_sc = -10**18
        for mv in legal_moves:
            if mv == (0, 0):
                continue
            sc = _score_move(board, mv, rng, total_stones, ko_forbidden_hash)
            if sc > best2_sc:
                best2_sc = sc
                best2_mv = mv
        if best2_mv != (0, 0):
            return best2_mv

    return best_mv


def _score_move(board, mv: Move, rng: random.Random, total_stones: int, ko_forbidden_hash) -> float:
    # Simulate our move
    new_board, captured, legal = _play_move(board, mv, color=1, ko_forbidden_hash=ko_forbidden_hash)
    if not legal:
        return -1e12

    r, c = mv
    rr, cc = r - 1, c - 1

    # Base: captures are huge
    score = 25.0 * captured

    # Avoid self-atari: penalize if our placed group is in atari (unless we captured a lot)
    gstones, glibs = _group_and_liberties(new_board, rr, cc)
    libs = len(glibs)
    if libs == 0:
        # Shouldn't happen for legal move, but guard.
        return -1e12
    if libs == 1:
        score -= 18.0
    elif libs == 2:
        score -= 2.0
    else:
        score += min(6.0, 0.8 * libs)

    # Reward making opponent groups atari; penalize leaving own groups in atari
    my_atari, opp_atari = _count_atari_groups(new_board)
    score -= 6.5 * my_atari
    score += 5.5 * opp_atari

    # Local connectivity / pressure
    adj_friend, adj_enemy = _adjacent_counts(new_board, rr, cc)
    score += 1.2 * adj_friend
    score += 0.4 * adj_enemy  # being adjacent can be good for fighting/cutting; handled by atari penalties too

    # Opening: prefer corners/star points a bit early
    if total_stones < 18:
        score += _opening_bonus(r, c)

    # Simple territory/influence heuristic: prefer moves not on first line unless purposeful
    line_dist = min(r - 1, c - 1, BOARD_N - r, BOARD_N - c)
    if total_stones < 40:
        if line_dist == 0:
            score -= 2.5
        elif line_dist == 1:
            score -= 0.8

    # Opponent immediate punishment: how big a capture can opponent do next because of our move?
    punish = _opponent_best_immediate_capture(new_board)
    score -= 22.0 * punish  # strong penalty

    # Mild preference for moves near action (reduce random far plays)
    score += _locality_bonus(board, r, c)

    # Tie-break noise (tiny)
    score += rng.random() * 0.01
    return score


# ------------------------- Candidate generation -------------------------


def _generate_candidates(board, total_stones: int) -> Set[Move]:
    empties: Set[Move] = set()
    stones: List[Tuple[int, int]] = []
    for r in range(BOARD_N):
        row = board[r]
        for c in range(BOARD_N):
            if row[c] != 0:
                stones.append((r, c))

    if not stones:
        # First move: take a 4-4 corner
        return {(4, 4), (4, 16), (16, 4), (16, 16), (10, 10)}

    # Local neighborhood within manhattan distance <= 2
    for (r, c) in stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) + abs(dc) > 2:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < BOARD_N and 0 <= cc < BOARD_N and board[rr][cc] == 0:
                    empties.add((rr + 1, cc + 1))

    # Add a few opening anchors
    if total_stones < 10:
        for pt in [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)]:
            r, c = pt
            if board[r - 1][c - 1] == 0:
                empties.add(pt)

    # If somehow too small, broaden to distance <= 3
    if len(empties) < 8:
        for (r, c) in stones:
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if abs(dr) + abs(dc) > 3:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < BOARD_N and 0 <= cc < BOARD_N and board[rr][cc] == 0:
                        empties.add((rr + 1, cc + 1))

    # Hard cap not needed, but keep set manageable by random thinning if enormous
    if len(empties) > 120:
        # deterministic-ish thinning: keep points closer to existing stones
        empties = set(list(empties)[:120])
    return empties


# ------------------------- Tactics: defense & punishment -------------------------


def _urgent_defense_moves(board, color: int, ko_forbidden_hash) -> Set[Move]:
    """
    If any of our groups have exactly one liberty, return moves that save them:
    - play at the liberty
    - or capture adjacent opponent group in atari if that capture would add liberties
    """
    urgent: Set[Move] = set()
    visited = [[False] * BOARD_N for _ in range(BOARD_N)]
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if board[r][c] == color and not visited[r][c]:
                stones, libs = _group_and_liberties_with_visited(board, r, c, visited)
                if len(libs) == 1:
                    (lr, lc) = next(iter(libs))
                    mv = (lr + 1, lc + 1)
                    if _is_legal_move(board, mv, color, ko_forbidden_hash):
                        urgent.add(mv)

                    # Also: if any adjacent opponent group is in atari, capturing it might save us
                    for (sr, sc) in stones:
                        for nr, nc in _neighbors(sr, sc):
                            if board[nr][nc] == -color:
                                og, olibs = _group_and_liberties(board, nr, nc)
                                if len(olibs) == 1:
                                    (cr, cc) = next(iter(olibs))
                                    cap_mv = (cr + 1, cc + 1)
                                    if _is_legal_move(board, cap_mv, color, ko_forbidden_hash):
                                        urgent.add(cap_mv)
    return urgent


def _opponent_best_immediate_capture(board_after_our_move) -> int:
    """
    Approximate opponent's best immediate capture size:
    find our groups in atari; assume opponent can take them by playing their liberty.
    Verify legality quickly by simulating that move for opponent.
    Return maximum captured size.
    """
    max_cap = 0
    visited = [[False] * BOARD_N for _ in range(BOARD_N)]
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if board_after_our_move[r][c] == 1 and not visited[r][c]:
                stones, libs = _group_and_liberties_with_visited(board_after_our_move, r, c, visited)
                if len(libs) == 1:
                    (lr, lc) = next(iter(libs))
                    mv = (lr + 1, lc + 1)
                    # opponent plays at mv
                    b2, cap, legal = _play_move(board_after_our_move, mv, color=-1, ko_forbidden_hash=None)
                    if legal and cap > max_cap:
                        max_cap = cap
    return max_cap


# ------------------------- Rules / legality -------------------------


def _is_legal_move(board, mv: Move, color: int, ko_forbidden_hash) -> bool:
    if mv == (0, 0):
        return True
    _, _, legal = _play_move(board, mv, color=color, ko_forbidden_hash=ko_forbidden_hash)
    return legal


def _play_move(board, mv: Move, color: int, ko_forbidden_hash=None):
    """
    Play mv for color (+1 or -1).
    Returns (new_board, captured_count, legal_bool).
    Implements:
      - no play on occupied
      - captures
      - suicide illegal
      - simple ko: resulting position cannot equal ko_forbidden_hash (if provided)
    """
    r, c = mv
    if not (1 <= r <= BOARD_N and 1 <= c <= BOARD_N):
        return board, 0, False
    rr, cc = r - 1, c - 1
    if board[rr][cc] != 0:
        return board, 0, False

    # Copy board (19x19 small)
    newb = [row[:] for row in board]
    newb[rr][cc] = color

    captured = 0
    # Capture any adjacent opponent groups with no liberties
    for nr, nc in _neighbors(rr, cc):
        if newb[nr][nc] == -color:
            stones, libs = _group_and_liberties(newb, nr, nc)
            if len(libs) == 0:
                captured += len(stones)
                for sr, sc in stones:
                    newb[sr][sc] = 0

    # Suicide check: our placed group must have liberties after captures
    stones, libs = _group_and_liberties(newb, rr, cc)
    if len(libs) == 0:
        return board, 0, False

    # Simple ko: forbid returning to previous start position (hash equals stored)
    if ko_forbidden_hash is not None:
        if _board_hash(newb) == ko_forbidden_hash:
            return board, 0, False

    return newb, captured, True


def _board_hash(board) -> bytes:
    # Stable compact hash; bytes of ints in [-1,0,1] stored as signed bytes
    # Build row-major bytes.
    out = bytearray(BOARD_N * BOARD_N)
    k = 0
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            out[k] = board[r][c] & 0xFF
            k += 1
    return bytes(out)


# ------------------------- Group / liberties utilities -------------------------


def _neighbors(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r + 1 < BOARD_N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < BOARD_N:
        yield r, c + 1


def _group_and_liberties(board, r: int, c: int):
    color = board[r][c]
    q = deque([(r, c)])
    visited = set([(r, c)])
    stones = []
    libs: Set[Tuple[int, int]] = set()
    while q:
        rr, cc = q.popleft()
        stones.append((rr, cc))
        for nr, nc in _neighbors(rr, cc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in visited:
                visited.add((nr, nc))
                q.append((nr, nc))
    return stones, libs


def _group_and_liberties_with_visited(board, r: int, c: int, visited_grid):
    """
    Same as _group_and_liberties, but marks a provided visited_grid[19][19] for stones.
    """
    color = board[r][c]
    q = deque([(r, c)])
    visited_grid[r][c] = True
    stones = []
    libs: Set[Tuple[int, int]] = set()
    while q:
        rr, cc = q.popleft()
        stones.append((rr, cc))
        for nr, nc in _neighbors(rr, cc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and not visited_grid[nr][nc]:
                visited_grid[nr][nc] = True
                q.append((nr, nc))
    return stones, libs


def _count_atari_groups(board) -> Tuple[int, int]:
    """
    Returns (my_atari_count, opp_atari_count) for my=+1.
    """
    my_atari = 0
    opp_atari = 0
    visited = [[False] * BOARD_N for _ in range(BOARD_N)]
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if board[r][c] != 0 and not visited[r][c]:
                stones, libs = _group_and_liberties_with_visited(board, r, c, visited)
                if len(libs) == 1:
                    if board[r][c] == 1:
                        my_atari += 1
                    else:
                        opp_atari += 1
    return my_atari, opp_atari


def _adjacent_counts(board, r: int, c: int) -> Tuple[int, int]:
    friend = 0
    enemy = 0
    color = board[r][c]
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == color:
            friend += 1
        elif board[nr][nc] == -color:
            enemy += 1
    return friend, enemy


# ------------------------- Heuristics -------------------------


def _opening_bonus(r: int, c: int) -> float:
    # Favor 4-4 and 3-4 points early; mild center preference otherwise.
    star = [(4, 4), (4, 16), (16, 4), (16, 16)]
    komoku = [(4, 3), (3, 4), (4, 17), (3, 16), (16, 3), (17, 4), (16, 17), (17, 16)]
    tengen = (10, 10)

    if (r, c) in star:
        return 6.0
    if (r, c) in komoku:
        return 4.2
    if (r, c) == tengen:
        return 1.2

    # Otherwise reward closeness to corners a bit
    # (distance to nearest corner)
    corners = [(1, 1), (1, 19), (19, 1), (19, 19)]
    d = min(abs(r - cr) + abs(c - cc) for cr, cc in corners)
    return max(0.0, 2.5 - 0.15 * d)


def _locality_bonus(board, r: int, c: int) -> float:
    rr, cc = r - 1, c - 1
    # Bonus if within 2 of any stone
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if abs(dr) + abs(dc) > 2:
                continue
            nr, nc = rr + dr, cc + dc
            if 0 <= nr < BOARD_N and 0 <= nc < BOARD_N and board[nr][nc] != 0:
                return 1.0
    return -0.2
