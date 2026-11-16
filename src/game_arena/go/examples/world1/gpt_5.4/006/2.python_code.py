
from collections import deque

BOARD_SIZE = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield nr, nc


def build_board(me, opponent):
    board = {}
    for p in me:
        board[p] = 1
    for p in opponent:
        board[p] = 2
    return board


def get_group_and_liberties(board, start):
    color = board.get(start, 0)
    if color == 0:
        return set(), set()
    group = set()
    liberties = set()
    stack = [start]
    group.add(start)
    while stack:
        p = stack.pop()
        for nb in neighbors(*p):
            v = board.get(nb, 0)
            if v == 0:
                liberties.add(nb)
            elif v == color and nb not in group:
                group.add(nb)
                stack.append(nb)
    return group, liberties


def play_move(board, move, color):
    if move == (0, 0):
        return dict(board)
    if move in board:
        return None

    new_board = dict(board)
    new_board[move] = color
    opp = 3 - color

    captured_any = False
    for nb in neighbors(*move):
        if new_board.get(nb, 0) == opp:
            grp, libs = get_group_and_liberties(new_board, nb)
            if len(libs) == 0:
                captured_any = True
                for s in grp:
                    del new_board[s]

    my_group, my_libs = get_group_and_liberties(new_board, move)
    if len(my_libs) == 0 and not captured_any:
        return None

    return new_board


def legal_moves(me, opponent):
    board = build_board(me, opponent)
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            mv = (r, c)
            if mv in board:
                continue
            if play_move(board, mv, 1) is not None:
                moves.append(mv)
    return moves


def all_groups(board, color):
    seen = set()
    groups = []
    for p, v in board.items():
        if v != color or p in seen:
            continue
        grp, libs = get_group_and_liberties(board, p)
        seen |= grp
        groups.append((grp, libs))
    return groups


def opening_move(board):
    prefs = [
        (10, 10),
        (4, 4), (4, 16), (16, 4), (16, 16),
        (4, 10), (10, 4), (10, 16), (16, 10),
        (7, 7), (7, 13), (13, 7), (13, 13),
        (10, 10), (9, 9), (9, 11), (11, 9), (11, 11),
    ]
    for mv in prefs:
        if mv not in board and play_move(board, mv, 1) is not None:
            return mv
    return None


def score_move(board, move):
    if move in board:
        return -10**9
    new_board = play_move(board, move, 1)
    if new_board is None:
        return -10**9

    score = 0.0
    opp = 2

    # Positional preference: center slightly better
    r, c = move
    center_dist = abs(r - 10) + abs(c - 10)
    score += 8.0 - 0.35 * center_dist

    # Prefer proximity to existing stones, especially tactical locality
    adjacent_my = 0
    adjacent_opp = 0
    empty_adj = 0
    for nb in neighbors(r, c):
        v = board.get(nb, 0)
        if v == 1:
            adjacent_my += 1
        elif v == 2:
            adjacent_opp += 1
        else:
            empty_adj += 1

    score += 2.5 * adjacent_my + 3.0 * adjacent_opp + 0.3 * empty_adj

    # Reward reducing opponent liberties / pressure
    touched_opp_groups = set()
    for nb in neighbors(r, c):
        if board.get(nb, 0) == opp:
            if nb in touched_opp_groups:
                continue
            grp, libs_before = get_group_and_liberties(board, nb)
            touched_opp_groups |= grp
            # group may be captured
            any_stone = next(iter(grp))
            if any_stone not in new_board:
                score += 1000 + 30 * len(grp)
            else:
                _, libs_after = get_group_and_liberties(new_board, any_stone)
                score += 4.0 * (len(libs_before) - len(libs_after))
                if len(libs_after) == 1:
                    score += 25
                if len(libs_after) == 2:
                    score += 6

    # Reward strengthening own groups
    touched_my_groups = set()
    for nb in neighbors(r, c):
        if board.get(nb, 0) == 1:
            if nb in touched_my_groups:
                continue
            grp, libs_before = get_group_and_liberties(board, nb)
            touched_my_groups |= grp
            _, libs_after = get_group_and_liberties(new_board, move)
            score += 1.5 * max(0, len(libs_after) - len(libs_before))

    # Prefer moves with healthy own liberties
    _, my_libs = get_group_and_liberties(new_board, move)
    score += 2.0 * len(my_libs)
    if len(my_libs) == 1:
        score -= 20
    elif len(my_libs) == 2:
        score -= 4

    # Mild pattern preference: avoid filling own eyes
    surrounded_by_me = 0
    for nb in neighbors(r, c):
        if board.get(nb, 0) == 1:
            surrounded_by_me += 1
    if surrounded_by_me >= 3 and adjacent_opp == 0:
        score -= 6

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)

    # If board empty or near-empty, play strong opening points
    if len(board) <= 2:
        mv = opening_move(board)
        if mv is not None:
            return mv

    # 1. Immediate captures of opponent groups in atari
    opp_groups = all_groups(board, 2)
    capture_moves = set()
    for grp, libs in opp_groups:
        if len(libs) == 1:
            mv = next(iter(libs))
            if play_move(board, mv, 1) is not None:
                capture_moves.add(mv)
    if capture_moves:
        best = max(capture_moves, key=lambda mv: score_move(board, mv))
        return best

    # 2. Save my own groups in atari
    my_groups = all_groups(board, 1)
    save_moves = set()
    for grp, libs in my_groups:
        if len(libs) == 1:
            mv = next(iter(libs))
            if play_move(board, mv, 1) is not None:
                save_moves.add(mv)
            # Also consider capturing neighboring attacker groups
            for stone in grp:
                for nb in neighbors(*stone):
                    if board.get(nb, 0) == 2:
                        ogrp, olibs = get_group_and_liberties(board, nb)
                        if len(olibs) == 1:
                            cap = next(iter(olibs))
                            if play_move(board, cap, 1) is not None:
                                save_moves.add(cap)
    if save_moves:
        best = max(save_moves, key=lambda mv: score_move(board, mv))
        return best

    # 3. Candidate moves near existing stones for speed and relevance
    candidates = set()
    stones = list(board.keys())
    if stones:
        for s in stones:
            for nb in neighbors(*s):
                if nb not in board:
                    candidates.add(nb)
            # radius-2 manhattan local expansion
            r, c = s
            for dr in (-2, -1, 0, 1, 2):
                rem = 2 - abs(dr)
                for dc in range(-rem, rem + 1):
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                        if (nr, nc) not in board:
                            candidates.add((nr, nc))
    else:
        mv = opening_move(board)
        if mv is not None:
            return mv

    # Add strategic points if candidate set is sparse
    strategic = [
        (10, 10),
        (4, 4), (4, 16), (16, 4), (16, 16),
        (4, 10), (10, 4), (10, 16), (16, 10),
        (7, 7), (7, 13), (13, 7), (13, 13),
        (10, 7), (10, 13), (7, 10), (13, 10),
        (9, 9), (9, 11), (11, 9), (11, 11),
    ]
    for mv in strategic:
        if mv not in board:
            candidates.add(mv)

    best_move = None
    best_score = -10**18
    for mv in candidates:
        sc = score_move(board, mv)
        if sc > best_score:
            best_score = sc
            best_move = mv

    if best_move is not None and play_move(board, best_move, 1) is not None:
        return best_move

    # 4. Guaranteed legal fallback: full board scan
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            mv = (r, c)
            if play_move(board, mv, 1) is not None:
                return mv

    # 5. If no legal board move exists, pass
    return (0, 0)
