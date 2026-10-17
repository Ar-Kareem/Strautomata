
from typing import List, Tuple, Dict, Set
from collections import deque

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def inside(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def neighbors(p: Tuple[int, int]):
    r, c = p
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc):
            yield (nr, nc)


def build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
    board = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if inside(r, c):
            board[r][c] = 1
    for r, c in opponent:
        if inside(r, c):
            board[r][c] = 2
    return board


def get_group_and_liberties(board, start: Tuple[int, int]):
    color = board[start[0]][start[1]]
    group = set()
    libs = set()
    q = [start]
    group.add(start)
    i = 0
    while i < len(q):
        p = q[i]
        i += 1
        for nb in neighbors(p):
            v = board[nb[0]][nb[1]]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in group:
                group.add(nb)
                q.append(nb)
    return group, libs


def simulate_move(board, move: Tuple[int, int], color: int):
    r, c = move
    if move == (0, 0):
        return None
    if not inside(r, c) or board[r][c] != 0:
        return None

    opp = 3 - color
    newb = [row[:] for row in board]
    newb[r][c] = color
    captured = []

    checked = set()
    for nb in neighbors(move):
        if newb[nb[0]][nb[1]] == opp and nb not in checked:
            g, libs = get_group_and_liberties(newb, nb)
            checked |= g
            if len(libs) == 0:
                captured.extend(g)
                for sr, sc in g:
                    newb[sr][sc] = 0

    my_group, my_libs = get_group_and_liberties(newb, move)
    if len(my_libs) == 0:
        return None

    return newb, captured, my_group, my_libs


def board_signature(board):
    me = []
    opp = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 1:
                me.append((r, c))
            elif board[r][c] == 2:
                opp.append((r, c))
    return (tuple(me), tuple(opp))


def estimate_phase(num_stones: int) -> float:
    # 0 early, 1 late
    return min(1.0, num_stones / 180.0)


def count_adjacent(board, move: Tuple[int, int], color: int):
    own = opp = empty = 0
    for nb in neighbors(move):
        v = board[nb[0]][nb[1]]
        if v == color:
            own += 1
        elif v == 3 - color:
            opp += 1
        else:
            empty += 1
    return own, opp, empty


def is_eye_like(board, move: Tuple[int, int], color: int):
    # crude eye test
    for nb in neighbors(move):
        if board[nb[0]][nb[1]] != color:
            return False
    r, c = move
    diag_friend = 0
    diag_opp = 0
    corners = 0
    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if inside(nr, nc):
                corners += 1
                if board[nr][nc] == color:
                    diag_friend += 1
                elif board[nr][nc] == 3 - color:
                    diag_opp += 1
    if corners == 4:
        return diag_opp <= 1
    else:
        return diag_opp == 0
        

def all_empty_points(board):
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 0:
                yield (r, c)


def candidate_moves(board, my_stones, opp_stones):
    occupied = set(my_stones) | set(opp_stones)
    cands = set()

    if not occupied:
        return [(10, 10), (10, 9), (9, 10), (10, 11), (11, 10), (4, 4), (4, 16), (16, 4), (16, 16)]

    # Near existing stones
    for p in occupied:
        for nb in neighbors(p):
            if board[nb[0]][nb[1]] == 0:
                cands.add(nb)
        r, c = p
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                nr, nc = r + dr, c + dc
                if inside(nr, nc) and board[nr][nc] == 0:
                    cands.add((nr, nc))

    # Add strategic fallback points
    strategic = [
        (10, 10), (4, 4), (4, 16), (16, 4), (16, 16),
        (10, 4), (10, 16), (4, 10), (16, 10),
        (7, 7), (7, 13), (13, 7), (13, 13),
        (10, 9), (10, 11), (9, 10), (11, 10)
    ]
    for p in strategic:
        if board[p[0]][p[1]] == 0:
            cands.add(p)

    return list(cands)


def score_move(board, move, color, phase):
    sim = simulate_move(board, move, color)
    if sim is None:
        return -10**18

    newb, captured, my_group, my_libs = sim
    opp = 3 - color
    score = 0.0

    # Strong tactical features
    capture_count = len(captured)
    score += capture_count * 100.0

    if capture_count > 0:
        # bonus for capturing larger neighboring danger
        score += 20.0

    # liberties and shape
    score += min(len(my_libs), 6) * 8.0

    if len(my_libs) == 1:
        score -= 80.0
    elif len(my_libs) == 2:
        score -= 12.0

    # connection bonus
    own_adj, opp_adj, empty_adj = count_adjacent(board, move, color)
    score += own_adj * 12.0
    score += opp_adj * 7.0

    # inspect affected neighboring groups
    seen_opp = set()
    for nb in neighbors(move):
        if board[nb[0]][nb[1]] == opp and nb not in seen_opp:
            g, libs = get_group_and_liberties(board, nb)
            seen_opp |= g
            if move in libs:
                if len(libs) == 1:
                    score += 150.0  # immediate capture already reflected, extra emphasis
                elif len(libs) == 2:
                    score += 45.0
                elif len(libs) == 3:
                    score += 10.0

    seen_me = set()
    for nb in neighbors(move):
        if board[nb[0]][nb[1]] == color and nb not in seen_me:
            g, libs = get_group_and_liberties(board, nb)
            seen_me |= g
            if move in libs:
                if len(libs) == 1:
                    score += 120.0  # saving atari
                elif len(libs) == 2:
                    score += 20.0

    # eye filling penalty
    if is_eye_like(board, move, color):
        score -= 60.0

    # centrality: stronger early
    r, c = move
    dist_center = abs(r - 10) + abs(c - 10)
    score += (1.0 - phase) * max(0, 18 - dist_center) * 1.8

    # corner/side opening preference early
    if phase < 0.2:
        if move in [(4, 4), (4, 16), (16, 4), (16, 16)]:
            score += 18.0
        if move in [(4, 10), (10, 4), (10, 16), (16, 10)]:
            score += 10.0

    # slight preference against first-line and crowded nonsense unless tactical
    if r in (1, 19) or c in (1, 19):
        score -= 8.0 if capture_count == 0 else 0.0

    # future pressure: count neighboring opponent groups after move in low liberties
    touched_opp = set()
    for nb in neighbors(move):
        if newb[nb[0]][nb[1]] == opp and nb not in touched_opp:
            g, libs = get_group_and_liberties(newb, nb)
            touched_opp |= g
            if len(libs) == 1:
                score += 35.0
            elif len(libs) == 2:
                score += 10.0

    return score


def choose_legal_fallback(board, color, ko_forbidden=None):
    # deterministic legal fallback, center outward
    pts = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 0:
                pts.append((abs(r - 10) + abs(c - 10), r, c))
    pts.sort()
    for _, r, c in pts:
        mv = (r, c)
        if ko_forbidden is not None and mv == ko_forbidden:
            continue
        if simulate_move(board, mv, color) is not None:
            return mv
    return (0, 0)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if memory is None or not isinstance(memory, dict):
        memory = {}

    board = build_board(me, opponent)
    total_stones = len(me) + len(opponent)
    phase = estimate_phase(total_stones)

    # Simple ko memory:
    # if previous move captured exactly one stone and created a ko point,
    # forbid immediate recapture at that point this turn.
    ko_forbidden = memory.get("ko_forbidden", None)

    cands = candidate_moves(board, me, opponent)

    # Tactical pre-pass: immediate captures / saves get naturally scored highly,
    # but we'll still evaluate all candidates.
    best_move = None
    best_score = -10**18
    best_sim = None

    for mv in cands:
        if ko_forbidden is not None and mv == tuple(ko_forbidden):
            continue
        sim = simulate_move(board, mv, 1)
        if sim is None:
            continue
        sc = score_move(board, mv, 1, phase)
        if sc > best_score:
            best_score = sc
            best_move = mv
            best_sim = sim

    if best_move is None:
        best_move = choose_legal_fallback(board, 1, ko_forbidden=tuple(ko_forbidden) if ko_forbidden else None)
        if best_move != (0, 0):
            best_sim = simulate_move(board, best_move, 1)

    if best_move == (0, 0) or best_sim is None:
        memory["ko_forbidden"] = None
        return (0, 0), memory

    # Update simple ko memory for opponent's next turn:
    # If we captured exactly one stone, and our played stone/group has exactly one liberty,
    # that liberty is often the ko recapture point. This is a conservative simple-ko detector.
    newb, captured, my_group, my_libs = best_sim
    new_ko = None
    if len(captured) == 1 and len(my_group) == 1 and len(my_libs) == 1:
        lib = next(iter(my_libs))
        new_ko = lib

    memory["ko_forbidden"] = new_ko
    return best_move, memory
