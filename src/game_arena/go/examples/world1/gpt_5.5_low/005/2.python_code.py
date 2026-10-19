
from collections import deque
import math
import random

BOARD_SIZE = 19
N = BOARD_SIZE

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
}

OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (4, 17),
    (16, 3), (17, 4), (16, 17), (17, 16),
]


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Return a legal Go move for the current player on a 19x19 board.

    Coordinates are 1-indexed. Return (0, 0) to pass.
    """
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    board = [[0] * (N + 1) for _ in range(N + 1)]
    for r, c in me_set:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 1
    for r, c in opp_set:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 2

    total_stones = len(me_set) + len(opp_set)

    def on_board(r, c):
        return 1 <= r <= N and 1 <= c <= N

    def neighbors(r, c):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= N and 1 <= nc <= N:
                yield nr, nc

    def group_and_liberties(start_r, start_c, b):
        color = b[start_r][start_c]
        if color == 0:
            return set(), set()

        group = set()
        libs = set()
        q = deque([(start_r, start_c)])
        group.add((start_r, start_c))

        while q:
            r, c = q.popleft()
            for nr, nc in neighbors(r, c):
                v = b[nr][nc]
                if v == 0:
                    libs.add((nr, nc))
                elif v == color and (nr, nc) not in group:
                    group.add((nr, nc))
                    q.append((nr, nc))

        return group, libs

    def legal_and_features(move):
        """
        Returns:
            None if illegal.
            Otherwise dict with tactical features.
        """
        r, c = move
        if not on_board(r, c):
            return None
        if board[r][c] != 0:
            return None

        b = [row[:] for row in board]
        b[r][c] = 1

        captured = 0
        captured_groups = 0

        seen_opp = set()
        for nr, nc in neighbors(r, c):
            if b[nr][nc] == 2 and (nr, nc) not in seen_opp:
                g, libs = group_and_liberties(nr, nc, b)
                seen_opp |= g
                if len(libs) == 0:
                    captured += len(g)
                    captured_groups += 1
                    for gr, gc in g:
                        b[gr][gc] = 0

        own_group, own_libs = group_and_liberties(r, c, b)
        if len(own_libs) == 0:
            return None

        adjacent_friendly = 0
        adjacent_enemy = 0
        adjacent_empty = 0
        friendly_groups = set()
        enemy_groups = set()

        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 1:
                adjacent_friendly += 1
                g, libs = group_and_liberties(nr, nc, board)
                friendly_groups.add(tuple(sorted(g)))
            elif board[nr][nc] == 2:
                adjacent_enemy += 1
                g, libs = group_and_liberties(nr, nc, board)
                enemy_groups.add(tuple(sorted(g)))
            else:
                adjacent_empty += 1

        return {
            "captured": captured,
            "captured_groups": captured_groups,
            "libs": len(own_libs),
            "group_size": len(own_group),
            "adj_friend": adjacent_friendly,
            "adj_enemy": adjacent_enemy,
            "adj_empty": adjacent_empty,
            "friendly_groups_joined": len(friendly_groups),
            "enemy_groups_touched": len(enemy_groups),
        }

    # Precompute atari points.
    capture_points = {}
    save_points = set()

    seen = set()
    for stone in opponent:
        if stone in seen:
            continue
        r, c = stone
        if not on_board(r, c) or board[r][c] != 2:
            continue
        g, libs = group_and_liberties(r, c, board)
        seen |= g
        if len(libs) == 1:
            liberty = next(iter(libs))
            capture_points[liberty] = capture_points.get(liberty, 0) + len(g)

    seen = set()
    for stone in me:
        if stone in seen:
            continue
        r, c = stone
        if not on_board(r, c) or board[r][c] != 1:
            continue
        g, libs = group_and_liberties(r, c, board)
        seen |= g
        if len(libs) == 1:
            liberty = next(iter(libs))
            save_points.add(liberty)

    def distance_to_edge(r, c):
        return min(r - 1, c - 1, N - r, N - c)

    def opening_bonus(r, c):
        if (r, c) in STAR_POINTS:
            return 28.0
        # Prefer 3-4, 4-3, 4-4, 3-3-ish corner development.
        corners = [(4, 4), (4, 16), (16, 4), (16, 16),
                   (3, 4), (4, 3), (3, 16), (4, 17),
                   (16, 3), (17, 4), (16, 17), (17, 16),
                   (3, 3), (3, 17), (17, 3), (17, 17)]
        best = min(abs(r - a) + abs(c - b) for a, b in corners)
        return max(0.0, 18.0 - 3.0 * best)

    def proximity_score(r, c):
        if total_stones == 0:
            return 0.0

        best_friend = 99
        best_enemy = 99

        # Exact scan over stones is cheap enough for 19x19.
        for sr, sc in me_set:
            d = abs(r - sr) + abs(c - sc)
            if d < best_friend:
                best_friend = d
        for sr, sc in opp_set:
            d = abs(r - sr) + abs(c - sc)
            if d < best_enemy:
                best_enemy = d

        s = 0.0
        if best_friend <= 2:
            s += 8.0
        elif best_friend <= 4:
            s += 5.0
        elif best_friend <= 6:
            s += 2.0

        if best_enemy <= 2:
            s += 7.0
        elif best_enemy <= 4:
            s += 4.0
        elif best_enemy <= 6:
            s += 1.5

        # Avoid totally isolated late moves.
        if total_stones > 80 and min(best_friend, best_enemy) > 6:
            s -= 8.0

        return s

    def eye_penalty(r, c):
        friendly = 0
        enemy = 0
        empty = 0
        offboard = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not on_board(nr, nc):
                offboard += 1
            elif board[nr][nc] == 1:
                friendly += 1
            elif board[nr][nc] == 2:
                enemy += 1
            else:
                empty += 1

        # Strong penalty for filling a simple own eye.
        if enemy == 0 and empty == 0 and friendly + offboard == 4:
            return 45.0
        if enemy == 0 and empty <= 1 and friendly >= 2:
            return 12.0
        return 0.0

    def shape_score(r, c, f):
        score = 0.0

        # Liberties and connections.
        score += 3.2 * f["libs"]
        score += 5.5 * f["adj_friend"]
        score += 2.5 * f["adj_enemy"]
        score += 7.0 * max(0, f["friendly_groups_joined"] - 1)

        # Captures are very important.
        score += 90.0 * f["captured"]
        score += 25.0 * f["captured_groups"]

        # Atari capture / saving.
        if (r, c) in capture_points:
            score += 120.0 + 70.0 * capture_points[(r, c)]
        if (r, c) in save_points:
            score += 85.0

        # Avoid self-atari unless it captures or is tactically urgent.
        if f["libs"] == 1 and f["captured"] == 0:
            score -= 80.0
        elif f["libs"] == 2 and f["captured"] == 0:
            score -= 14.0

        # Good board geometry.
        edge_dist = distance_to_edge(r, c)
        if total_stones < 50:
            score += opening_bonus(r, c)
            # Avoid first/second line too early.
            if edge_dist == 0:
                score -= 35.0
            elif edge_dist == 1:
                score -= 12.0
            elif edge_dist in (2, 3):
                score += 8.0
        else:
            if edge_dist == 0:
                score -= 14.0
            elif edge_dist == 1:
                score -= 2.0
            elif edge_dist in (2, 3):
                score += 3.0

        # Center has moderate value, but not too much in opening.
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0.0, 8.0 - 0.45 * center_dist)

        score += proximity_score(r, c)

        # Penalize filling own eyes unless capturing.
        if f["captured"] == 0:
            score -= eye_penalty(r, c)

        # Tiny deterministic noise for tie-breaking.
        score += ((r * 37 + c * 101 + total_stones * 17) % 97) / 1000.0

        return score

    # Opening shortcut: play a good empty legal opening point if board is tiny.
    if total_stones < 8:
        for mv in OPENING_POINTS:
            if mv not in occupied and legal_and_features(mv) is not None:
                return mv

    best_move = None
    best_score = -10**18

    # Candidate generation: tactical points plus points near stones plus global good points.
    candidates = set()

    for p in capture_points:
        candidates.add(p)
    for p in save_points:
        candidates.add(p)

    for r, c in list(occupied):
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 4:
                    nr, nc = r + dr, c + dc
                    if on_board(nr, nc) and board[nr][nc] == 0:
                        candidates.add((nr, nc))

    for p in STAR_POINTS:
        if p not in occupied:
            candidates.add(p)

    # If sparse or candidates somehow empty, include all empty points.
    if total_stones < 20 or not candidates:
        for r in range(1, N + 1):
            for c in range(1, N + 1):
                if board[r][c] == 0:
                    candidates.add((r, c))

    for mv in candidates:
        f = legal_and_features(mv)
        if f is None:
            continue
        s = shape_score(mv[0], mv[1], f)
        if s > best_score:
            best_score = s
            best_move = mv

    if best_move is not None:
        return best_move

    # Absolute fallback: find any legal point.
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0 and legal_and_features((r, c)) is not None:
                return (r, c)

    return (0, 0)
