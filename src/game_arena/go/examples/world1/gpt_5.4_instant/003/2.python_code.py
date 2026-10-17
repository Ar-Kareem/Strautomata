
from typing import List, Tuple
import random

BOARD_SIZE = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def neighbors(pos: Tuple[int, int]):
    r, c = pos
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield (nr, nc)

def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
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
    stack = [start]
    group = set()
    libs = set()
    while stack:
        p = stack.pop()
        if p in group:
            continue
        group.add(p)
        for nb in neighbors(p):
            v = board.get(nb, 0)
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in group:
                stack.append(nb)
    return group, libs

def simulate_move(board, move, color):
    if move in board:
        return None
    new_board = dict(board)
    new_board[move] = color
    opp = 3 - color

    captured_any = False
    for nb in neighbors(move):
        if new_board.get(nb, 0) == opp:
            g, libs = get_group_and_liberties(new_board, nb)
            if len(libs) == 0:
                captured_any = True
                for p in g:
                    del new_board[p]

    g, libs = get_group_and_liberties(new_board, move)
    if len(libs) == 0 and not captured_any:
        return None
    return new_board

def is_legal(board, move, color=1):
    if move == (0, 0):
        return True
    return simulate_move(board, move, color) is not None

def all_empty_points(board):
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            p = (r, c)
            if p not in board:
                yield p

def count_adjacent(board, move, color):
    cnt = 0
    for nb in neighbors(move):
        if board.get(nb, 0) == color:
            cnt += 1
    return cnt

def local_density(board, move):
    r, c = move
    score = 0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) in board:
                score += 1
    return score

def distance_to_center(move):
    r, c = move
    return abs(r - 10) + abs(c - 10)

def candidate_moves(board):
    stones = list(board.keys())
    cand = set()
    if not stones:
        opening = [
            (4, 4), (4, 16), (16, 4), (16, 16),
            (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)
        ]
        return [p for p in opening if p not in board]

    for s in stones:
        r, c = s
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                p = (nr, nc)
                if in_bounds(nr, nc) and p not in board:
                    cand.add(p)

    if len(cand) < 30:
        extras = [
            (4, 4), (4, 16), (16, 4), (16, 16),
            (10, 10), (4, 10), (10, 4), (10, 16), (16, 10),
            (7, 7), (7, 13), (13, 7), (13, 13)
        ]
        for p in extras:
            if p not in board:
                cand.add(p)
    return list(cand)

def score_move(board, move):
    new_board = simulate_move(board, move, 1)
    if new_board is None:
        return -10**9

    score = 0.0

    # Reward captures
    captures = len(board) + 1 - len(new_board)
    # Since our move adds one stone, positive value beyond that means captures happened
    if captures > 0:
        score += 30 * captures

    # Liberties of the new group
    my_group, my_libs = get_group_and_liberties(new_board, move)
    score += 4.5 * len(my_libs)
    score += 1.5 * len(my_group)

    # Connection bonus to friendly groups
    touched_friendly_groups = set()
    for nb in neighbors(move):
        if board.get(nb, 0) == 1:
            g, _ = get_group_and_liberties(board, nb)
            touched_friendly_groups.add(min(g))
    score += 8 * len(touched_friendly_groups)

    # Pressure adjacent opponent groups
    seen = set()
    for nb in neighbors(move):
        if new_board.get(nb, 0) == 2 and nb not in seen:
            g, libs = get_group_and_liberties(new_board, nb)
            seen |= g
            if len(libs) == 1:
                score += 20
            elif len(libs) == 2:
                score += 8
            score += max(0, 5 - len(libs))

    # Save our own groups in atari / low liberties
    seen = set()
    for nb in neighbors(move):
        if board.get(nb, 0) == 1 and nb not in seen:
            g_before, libs_before = get_group_and_liberties(board, nb)
            seen |= g_before
            if len(libs_before) <= 2:
                anchor = next(iter(g_before))
                g_after, libs_after = get_group_and_liberties(new_board, anchor)
                score += 6 * (len(libs_after) - len(libs_before))

    # Prefer local moves generally, but not overcrowding
    score += 0.7 * local_density(board, move)

    # Opening/shape centrality
    num_stones = len(board)
    if num_stones < 12:
        score -= 0.8 * distance_to_center(move)
    else:
        score -= 0.15 * distance_to_center(move)

    # Avoid first-line/corner overuse unless tactical
    r, c = move
    edge_dist = min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
    if edge_dist == 0:
        score -= 4
    elif edge_dist == 1:
        score -= 1.5

    # Small preference for adjacency
    score += 1.2 * count_adjacent(board, move, 1)
    score += 0.8 * count_adjacent(board, move, 2)

    return score

def find_immediate_tactical_move(board):
    # 1. Capture opponent groups in atari
    checked_libs = set()
    for p, color in list(board.items()):
        if color != 2:
            continue
        g, libs = get_group_and_liberties(board, p)
        if len(libs) == 1:
            lib = next(iter(libs))
            if lib not in checked_libs:
                checked_libs.add(lib)
                if is_legal(board, lib, 1):
                    return lib

    # 2. Save our own groups in atari
    checked_libs = set()
    for p, color in list(board.items()):
        if color != 1:
            continue
        g, libs = get_group_and_liberties(board, p)
        if len(libs) == 1:
            lib = next(iter(libs))
            if lib not in checked_libs:
                checked_libs.add(lib)
                if is_legal(board, lib, 1):
                    return lib
    return None

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    board = build_board(me, opponent)

    tactical = find_immediate_tactical_move(board)
    if tactical is not None:
        return tactical

    cands = candidate_moves(board)
    legal_scored = []
    for mv in cands:
        sc = score_move(board, mv)
        if sc > -10**8:
            legal_scored.append((sc, mv))

    if legal_scored:
        legal_scored.sort(key=lambda x: (x[0], -distance_to_center(x[1])), reverse=True)
        best_score = legal_scored[0][0]
        best_moves = [mv for sc, mv in legal_scored if sc == best_score]
        return random.choice(best_moves)

    # Fallback: return first legal move on board
    for p in all_empty_points(board):
        if is_legal(board, p, 1):
            return p

    return (0, 0)
