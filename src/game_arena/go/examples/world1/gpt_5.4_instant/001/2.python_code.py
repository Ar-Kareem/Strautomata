
from typing import List, Tuple

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def inside(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc):
            yield nr, nc


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 2
    return board


def group_and_liberties(board, r: int, c: int):
    color = board[r][c]
    if color == 0:
        return set(), set()
    stack = [(r, c)]
    group = set()
    libs = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in group:
            continue
        group.add((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in group:
                stack.append((nx, ny))
    return group, libs


def apply_move(board, r: int, c: int, color: int):
    if not inside(r, c) or board[r][c] != 0:
        return None, 0
    opp = 3 - color
    newb = [row[:] for row in board]
    newb[r][c] = color
    captured = 0

    checked = set()
    for nr, nc in neighbors(r, c):
        if newb[nr][nc] == opp and (nr, nc) not in checked:
            grp, libs = group_and_liberties(newb, nr, nc)
            checked |= grp
            if len(libs) == 0:
                captured += len(grp)
                for x, y in grp:
                    newb[x][y] = 0

    mygrp, mylibs = group_and_liberties(newb, r, c)
    if len(mylibs) == 0:
        return None, 0

    return newb, captured


def legal_moves(board, color: int = 1):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                nb, _ = apply_move(board, r, c, color)
                if nb is not None:
                    moves.append((r, c))
    return moves


def all_groups(board, color: int):
    seen = set()
    groups = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == color and (r, c) not in seen:
                grp, libs = group_and_liberties(board, r, c)
                seen |= grp
                groups.append((grp, libs))
    return groups


def score_move(board, r: int, c: int):
    nb, captured = apply_move(board, r, c, 1)
    if nb is None:
        return -10**18

    score = 0.0

    # Strong tactical value for captures
    score += captured * 1000.0

    # Center preference
    cr, cc = 9, 9
    dist = abs(r - cr) + abs(c - cc)
    score += max(0, 18 - dist) * 1.5

    # Local neighborhood features
    friendly_adj = 0
    enemy_adj = 0
    empty_adj = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1:
            friendly_adj += 1
        elif board[nr][nc] == 2:
            enemy_adj += 1
        else:
            empty_adj += 1

    score += friendly_adj * 12.0
    score += enemy_adj * 8.0
    score += empty_adj * 1.5

    # Prefer resulting liberties for the new group
    grp, libs = group_and_liberties(nb, r, c)
    score += len(libs) * 9.0

    # Connection bonus: distinct adjacent friendly groups merged
    adj_friend_groups = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1:
            g, _ = group_and_liberties(board, nr, nc)
            adj_friend_groups.add(frozenset(g))
    if len(adj_friend_groups) >= 2:
        score += 35.0 * (len(adj_friend_groups) - 1)

    # Attack bonus against adjacent enemy groups with few liberties
    seen_enemy = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 2 and (nr, nc) not in seen_enemy:
            g, libs0 = group_and_liberties(board, nr, nc)
            seen_enemy |= g
            # after move/capture, if still present inspect pressure
            remaining = [(x, y) for (x, y) in g if nb[x][y] == 2]
            if remaining:
                x, y = remaining[0]
                _, libs1 = group_and_liberties(nb, x, y)
                score += max(0, 4 - len(libs1)) * 18.0
                if len(libs0) == 2 and len(libs1) == 1:
                    score += 60.0

    # Defense bonus if move saves our adjacent group in atari
    seen_me = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1 and (nr, nc) not in seen_me:
            g, libs0 = group_and_liberties(board, nr, nc)
            seen_me |= g
            if len(libs0) == 1 and (r, c) in libs0:
                score += 220.0
            # reward generally increasing liberties
            x, y = next(iter(g))
            _, libs1 = group_and_liberties(nb, x, y)
            score += max(0, len(libs1) - len(libs0)) * 10.0

    # Slight penalty for edges/corners unless justified
    edge_count = int(r in (0, 18)) + int(c in (0, 18))
    score -= edge_count * 6.0

    # Avoid isolated first-line-ish moves
    if friendly_adj == 0 and enemy_adj == 0:
        score -= 10.0

    return score


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    board = build_board(me, opponent)

    moves = legal_moves(board, 1)
    if not moves:
        return (0, 0)

    # 1. Immediate best capture
    best_cap = []
    max_cap = 0
    for r, c in moves:
        _, cap = apply_move(board, r, c, 1)
        if cap > max_cap:
            max_cap = cap
            best_cap = [(r, c)]
        elif cap == max_cap and cap > 0:
            best_cap.append((r, c))
    if max_cap > 0:
        best = max(best_cap, key=lambda mv: score_move(board, mv[0], mv[1]))
        return (best[0] + 1, best[1] + 1)

    # 2. Save our groups in atari
    rescue_candidates = set()
    for grp, libs in all_groups(board, 1):
        if len(libs) == 1:
            lr, lc = next(iter(libs))
            nb, _ = apply_move(board, lr, lc, 1)
            if nb is not None:
                rescue_candidates.add((lr, lc))
    if rescue_candidates:
        best = max(rescue_candidates, key=lambda mv: score_move(board, mv[0], mv[1]))
        return (best[0] + 1, best[1] + 1)

    # 3. Put opponent groups in more danger / capture threats
    attack_candidates = set()
    for grp, libs in all_groups(board, 2):
        if len(libs) == 1:
            lr, lc = next(iter(libs))
            nb, _ = apply_move(board, lr, lc, 1)
            if nb is not None:
                attack_candidates.add((lr, lc))
        elif len(libs) == 2:
            for lr, lc in libs:
                nb, _ = apply_move(board, lr, lc, 1)
                if nb is not None:
                    attack_candidates.add((lr, lc))
    if attack_candidates:
        best = max(attack_candidates, key=lambda mv: score_move(board, mv[0], mv[1]))
        return (best[0] + 1, best[1] + 1)

    # 4. Global heuristic best move
    best_move = None
    best_score = -10**18
    for r, c in moves:
        s = score_move(board, r, c)
        if s > best_score:
            best_score = s
            best_move = (r, c)

    if best_move is not None:
        return (best_move[0] + 1, best_move[1] + 1)

    # 5. Emergency fallback: first legal empty point, else pass
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                nb, _ = apply_move(board, r, c, 1)
                if nb is not None:
                    return (r + 1, c + 1)
    return (0, 0)
