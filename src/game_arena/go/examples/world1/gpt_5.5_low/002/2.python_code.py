
from collections import deque
import random
import math

BOARD_SIZE = 19
N = BOARD_SIZE

# Good opening / positional points on a 19x19 board.
PRIORITY_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (4, 17),
    (16, 3), (17, 4), (16, 17), (17, 16),
    (3, 10), (10, 3), (10, 17), (17, 10),
]


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Return a legal Go move for the current player on a 19x19 board.

    Coordinates are 1-indexed. Passing is (0, 0).
    """
    my_set = set(me)
    op_set = set(opponent)
    occupied = my_set | op_set

    # Build board: 0 empty, 1 me, 2 opponent
    board = [[0] * N for _ in range(N)]
    for r, c in my_set:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in op_set:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2

    def neighbors(r, c):
        if r > 1:
            yield (r - 1, c)
        if r < N:
            yield (r + 1, c)
        if c > 1:
            yield (r, c - 1)
        if c < N:
            yield (r, c + 1)

    def group_and_liberties(start, b):
        sr, sc = start
        color = b[sr - 1][sc - 1]
        if color == 0:
            return set(), set()

        group = set()
        liberties = set()
        q = deque([start])
        group.add(start)

        while q:
            r, c = q.popleft()
            for nr, nc in neighbors(r, c):
                v = b[nr - 1][nc - 1]
                if v == 0:
                    liberties.add((nr, nc))
                elif v == color and (nr, nc) not in group:
                    group.add((nr, nc))
                    q.append((nr, nc))

        return group, liberties

    def analyze_move(move):
        """
        Returns:
            None if illegal
            otherwise dict with captured, own_liberties, saved, atari_targets, board_after
        """
        r, c = move
        if not (1 <= r <= N and 1 <= c <= N):
            return None
        if board[r - 1][c - 1] != 0:
            return None

        b = [row[:] for row in board]
        b[r - 1][c - 1] = 1

        captured = 0
        captured_groups = []
        seen_op = set()

        for nr, nc in neighbors(r, c):
            if b[nr - 1][nc - 1] == 2 and (nr, nc) not in seen_op:
                g, libs = group_and_liberties((nr, nc), b)
                seen_op |= g
                if len(libs) == 0:
                    captured += len(g)
                    captured_groups.append(g)
                    for gr, gc in g:
                        b[gr - 1][gc - 1] = 0

        own_group, own_libs = group_and_liberties((r, c), b)

        # Suicide is illegal unless it captured something and thereby gained liberties.
        if len(own_libs) == 0:
            return None

        # Count friendly groups adjacent to the move that were in atari before.
        saved = 0
        seen_my = set()
        for nr, nc in neighbors(r, c):
            if board[nr - 1][nc - 1] == 1 and (nr, nc) not in seen_my:
                g, libs = group_and_liberties((nr, nc), board)
                seen_my |= g
                if len(libs) == 1 and (r, c) in libs:
                    saved += len(g)

        # Count adjacent enemy groups that become atari after move.
        atari_targets = 0
        seen_op2 = set()
        for nr, nc in neighbors(r, c):
            if b[nr - 1][nc - 1] == 2 and (nr, nc) not in seen_op2:
                g, libs = group_and_liberties((nr, nc), b)
                seen_op2 |= g
                if len(libs) == 1:
                    atari_targets += len(g)

        return {
            "captured": captured,
            "own_liberties": len(own_libs),
            "own_group_size": len(own_group),
            "saved": saved,
            "atari_targets": atari_targets,
            "board_after": b,
        }

    def is_eye_like(move):
        """
        Conservative eye-filling detector.
        Avoids playing inside our own simple eyes unless tactically necessary.
        """
        r, c = move
        adj = list(neighbors(r, c))
        if not adj:
            return False

        # All orthogonal neighbors must be ours or board edge.
        for nr, nc in adj:
            if board[nr - 1][nc - 1] != 1:
                return False

        # Diagonal check. True eyes usually have mostly friendly/off-board diagonals.
        friendly_diag = 0
        bad_diag = 0
        for dr in (-1, 1):
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if nr < 1 or nr > N or nc < 1 or nc > N:
                    friendly_diag += 1
                elif board[nr - 1][nc - 1] == 1:
                    friendly_diag += 1
                elif board[nr - 1][nc - 1] == 2:
                    bad_diag += 1

        return friendly_diag >= 3 and bad_diag == 0

    def positional_score(r, c):
        # Corners and sides are valuable, first/second lines less so.
        dist_edge = min(r, c, N + 1 - r, N + 1 - c)

        # Prefer 3rd/4th/5th lines.
        if dist_edge == 1:
            edge_score = -20
        elif dist_edge == 2:
            edge_score = -4
        elif dist_edge == 3:
            edge_score = 12
        elif dist_edge == 4:
            edge_score = 18
        elif dist_edge == 5:
            edge_score = 12
        else:
            edge_score = 4

        # Opening point bonus.
        pp_bonus = 0
        for pr, pc in PRIORITY_POINTS:
            d = abs(r - pr) + abs(c - pc)
            if d == 0:
                pp_bonus = max(pp_bonus, 26)
            elif d == 1:
                pp_bonus = max(pp_bonus, 12)
            elif d == 2:
                pp_bonus = max(pp_bonus, 5)

        # Influence: be close enough to friendly stones, not too clumped.
        friendly_near = 0.0
        enemy_near = 0.0
        too_close_friend = 0

        # Local radius evaluation.
        for rr in range(max(1, r - 4), min(N, r + 4) + 1):
            for cc in range(max(1, c - 4), min(N, c + 4) + 1):
                v = board[rr - 1][cc - 1]
                if v == 0:
                    continue
                d = abs(r - rr) + abs(c - cc)
                if d == 0 or d > 6:
                    continue
                weight = 1.0 / d
                if v == 1:
                    friendly_near += weight
                    if d == 1:
                        too_close_friend += 1
                else:
                    enemy_near += weight

        # Prefer approaching enemy frameworks and extending from own stones.
        influence = 5.0 * friendly_near + 6.0 * enemy_near - 4.0 * too_close_friend

        # Mild center bonus later, but not too much.
        center_dist = abs(r - 10) + abs(c - 10)
        center_score = -0.25 * center_dist

        return edge_score + pp_bonus + influence + center_score

    def move_score(move, info):
        r, c = move
        score = 0.0

        # Tactical priorities.
        score += 120.0 * info["captured"]
        score += 75.0 * info["saved"]
        score += 28.0 * info["atari_targets"]
        score += 3.0 * info["own_liberties"]
        score += 0.7 * info["own_group_size"]

        # Positional judgment.
        score += positional_score(r, c)

        # Avoid filling our own eyes unless it captures or saves.
        if is_eye_like(move) and info["captured"] == 0 and info["saved"] == 0:
            score -= 200.0

        # Avoid needless self-atari unless capturing/saving significantly.
        if info["own_liberties"] == 1 and info["captured"] == 0 and info["saved"] == 0:
            score -= 90.0

        # Small deterministic noise for tie-breaking.
        score += ((r * 37 + c * 17 + len(me) * 13 + len(opponent) * 7) % 100) / 1000.0
        return score

    legal_moves = []
    best_move = None
    best_score = -10**18

    # If board is empty or nearly empty, use strong opening points if legal.
    if len(occupied) < 8:
        for p in PRIORITY_POINTS:
            if p not in occupied:
                info = analyze_move(p)
                if info is not None:
                    return p

    # Evaluate all legal moves.
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r - 1][c - 1] != 0:
                continue
            mv = (r, c)
            info = analyze_move(mv)
            if info is None:
                continue
            legal_moves.append(mv)
            s = move_score(mv, info)
            if s > best_score:
                best_score = s
                best_move = mv

    if best_move is not None:
        return best_move

    # Absolute safety fallback: return any empty point if somehow considered legal unavailable.
    # In a normal full/suicide-only position, pass is legal.
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r - 1][c - 1] == 0:
                return (r, c)

    return (0, 0)
