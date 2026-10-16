
from typing import List, Tuple, Dict
import math

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def on_board(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if on_board(nr, nc):
            yield nr, nc


def board_from_lists(me, opponent):
    board = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if on_board(r, c):
            board[r][c] = 1
    for r, c in opponent:
        if on_board(r, c):
            board[r][c] = 2
    return board


def board_hash(board):
    # Fast immutable representation
    return tuple(tuple(board[r][1:BOARD_SIZE + 1]) for r in range(1, BOARD_SIZE + 1))


def get_group_and_liberties(board, r, c):
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


def apply_move(board, move, color):
    if move == (0, 0):
        return [row[:] for row in board], []
    r, c = move
    nb = [row[:] for row in board]
    nb[r][c] = color
    captured = []
    opp = 3 - color
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == opp:
            grp, libs = get_group_and_liberties(nb, nr, nc)
            if len(libs) == 0:
                captured.extend(grp)
    for x, y in captured:
        nb[x][y] = 0
    return nb, captured


def is_legal(board, move, color, prev_hash=None):
    if move == (0, 0):
        return True
    r, c = move
    if not on_board(r, c) or board[r][c] != 0:
        return False
    nb, _ = apply_move(board, move, color)
    grp, libs = get_group_and_liberties(nb, r, c)
    if len(libs) == 0:
        return False  # suicide
    if prev_hash is not None and board_hash(nb) == prev_hash:
        return False  # simple ko heuristic
    return True


def count_adj(board, r, c, color):
    s = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == color:
            s += 1
    return s


def eye_like(board, r, c, color):
    # Conservative eye-ish detector
    if board[r][c] != 0:
        return False
    orth = list(neighbors(r, c))
    if orth and all(board[x][y] == color for x, y in orth):
        enemy = 3 - color
        diag_bad = 0
        for dr in (-1, 1):
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if on_board(nr, nc) and board[nr][nc] == enemy:
                    diag_bad += 1
        if (r in (1, BOARD_SIZE)) and (c in (1, BOARD_SIZE)):
            return diag_bad == 0
        if (r in (1, BOARD_SIZE)) or (c in (1, BOARD_SIZE)):
            return diag_bad <= 1
        return diag_bad <= 1
    return False


def all_empty_points(board):
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 0:
                yield (r, c)


def tactical_candidates(board, color):
    opp = 3 - color
    capture_moves = set()
    save_moves = set()
    pressure_moves = set()

    seen = set()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == opp and (r, c) not in seen:
                grp, libs = get_group_and_liberties(board, r, c)
                seen |= grp
                if len(libs) == 1:
                    capture_moves |= libs
                elif len(libs) == 2:
                    pressure_moves |= libs

    seen = set()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == color and (r, c) not in seen:
                grp, libs = get_group_and_liberties(board, r, c)
                seen |= grp
                if len(libs) == 1:
                    save_moves |= libs

    return list(capture_moves), list(save_moves), list(pressure_moves)


def score_move(board, move, color, move_number):
    if move == (0, 0):
        return -999999
    r, c = move
    opp = 3 - color

    # Opening preference: star-ish and center-ish
    center_dist = abs(r - 10) + abs(c - 10)
    score = -0.35 * center_dist

    # Prefer adjacency to existing fight
    my_adj = count_adj(board, r, c, color)
    opp_adj = count_adj(board, r, c, opp)
    score += 1.8 * my_adj + 1.5 * opp_adj

    # Avoid overfilling own eye / overcrowding
    if eye_like(board, r, c, color):
        score -= 8.0
    if my_adj >= 3 and opp_adj == 0:
        score -= 2.0

    # Simulate for tactical impact
    nb, captured = apply_move(board, move, color)
    score += 7.0 * len(captured)

    grp, libs = get_group_and_liberties(nb, r, c)
    l = len(libs)
    if l == 1:
        score -= 10.0
    elif l == 2:
        score -= 2.5
    elif l >= 4:
        score += 1.0

    # Attack nearby opponent groups after move
    touched_attack = 0
    touched_save = 0
    checked = set()
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == opp and (nr, nc) not in checked:
            og, ol = get_group_and_liberties(nb, nr, nc)
            checked |= og
            if len(ol) == 1:
                touched_attack += len(og)
            elif len(ol) == 2:
                touched_attack += 0.5 * len(og)
    checked = set()
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == color and (nr, nc) not in checked:
            mg, ml = get_group_and_liberties(nb, nr, nc)
            checked |= mg
            if len(ml) >= 2:
                touched_save += min(len(mg), 6)

    score += 1.2 * touched_attack + 0.6 * touched_save

    # Opening spread: prefer 4-4 / 3-4 / 4-3 style regions early
    if move_number < 12:
        stars = {(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)}
        if move in stars:
            score += 2.0
        if r in (4, 16) or c in (4, 16):
            score += 0.6

    return score


def choose_legal_best(board, moves, color, prev_hash, move_number):
    best = None
    best_score = -10**18
    for mv in moves:
        if is_legal(board, mv, color, prev_hash):
            s = score_move(board, mv, color, move_number)
            if s > best_score:
                best_score = s
                best = mv
    return best


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if memory is None:
        memory = {}
    board = board_from_lists(me, opponent)
    prev_hash = memory.get("prev_board_hash", None)
    move_number = len(me) + len(opponent)

    # 1. Immediate tactical priorities
    captures, saves, pressures = tactical_candidates(board, 1)

    mv = choose_legal_best(board, captures, 1, prev_hash, move_number)
    if mv is None:
        mv = choose_legal_best(board, saves, 1, prev_hash, move_number)
    if mv is None:
        mv = choose_legal_best(board, pressures, 1, prev_hash, move_number)

    # 2. Local candidate generation near existing stones
    if mv is None:
        cand = set()
        occupied = set(me) | set(opponent)
        stones = list(occupied)

        if not stones:
            opening = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)]
            mv = choose_legal_best(board, opening, 1, prev_hash, move_number)
        else:
            for r, c in stones:
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if on_board(nr, nc) and board[nr][nc] == 0:
                            cand.add((nr, nc))

            # Add a few larger framework points
            for p in [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]:
                if board[p[0]][p[1]] == 0:
                    cand.add(p)

            mv = choose_legal_best(board, cand, 1, prev_hash, move_number)

    # 3. Fallback: scan all legal points
    if mv is None:
        mv = choose_legal_best(board, all_empty_points(board), 1, prev_hash, move_number)

    # 4. If somehow no legal point, pass
    if mv is None:
        mv = (0, 0)

    # Update simple ko memory: store current board hash for next turn
    memory = dict(memory)
    memory["prev_board_hash"] = board_hash(board)
    return mv, memory
