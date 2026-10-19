
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


def board_from_lists(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
    board = {}
    for p in me:
        board[p] = 1
    for p in opponent:
        board[p] = 2
    return board


def group_and_liberties(board: Dict[Tuple[int, int], int], start: Tuple[int, int]):
    color = board.get(start, 0)
    if color == 0:
        return set(), set()
    group = set()
    liberties = set()
    stack = [start]
    group.add(start)
    while stack:
        p = stack.pop()
        for nb in neighbors(p):
            v = board.get(nb, 0)
            if v == 0:
                liberties.add(nb)
            elif v == color and nb not in group:
                group.add(nb)
                stack.append(nb)
    return group, liberties


def play_move(board: Dict[Tuple[int, int], int], move: Tuple[int, int], color: int):
    if move == (0, 0):
        return dict(board), True, 0
    if move in board:
        return board, False, 0

    new_board = dict(board)
    new_board[move] = color
    opp = 3 - color
    captured = 0

    checked = set()
    for nb in neighbors(move):
        if new_board.get(nb) == opp and nb not in checked:
            grp, libs = group_and_liberties(new_board, nb)
            checked |= grp
            if len(libs) == 0:
                captured += len(grp)
                for s in grp:
                    del new_board[s]

    my_grp, my_libs = group_and_liberties(new_board, move)
    if len(my_libs) == 0:
        return board, False, 0

    return new_board, True, captured


def board_hash(board: Dict[Tuple[int, int], int]) -> Tuple[Tuple[int, int, int], ...]:
    return tuple(sorted((r, c, v) for (r, c), v in board.items()))


def candidate_moves(board: Dict[Tuple[int, int], int]):
    occupied = set(board.keys())
    if not occupied:
        return [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]

    cand = set()
    for p in occupied:
        r, c = p
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                q = (nr, nc)
                if inside(nr, nc) and q not in occupied:
                    cand.add(q)

    if len(cand) < 20:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if (r, c) not in occupied:
                    cand.add((r, c))
    return list(cand)


def count_adjacent(board, move, color):
    s = 0
    for nb in neighbors(move):
        if board.get(nb) == color:
            s += 1
    return s


def min_neighbor_group_libs(board, move, color):
    vals = []
    seen = set()
    for nb in neighbors(move):
        if board.get(nb) == color and nb not in seen:
            grp, libs = group_and_liberties(board, nb)
            seen |= grp
            vals.append(len(libs))
    if not vals:
        return None
    return min(vals)


def score_move(board: Dict[Tuple[int, int], int], move: Tuple[int, int], prev_hashes: Set[Tuple]):
    new_board, legal, captured = play_move(board, move, 1)
    if not legal:
        return -10**18, None
    h = board_hash(new_board)
    if h in prev_hashes:
        return -10**12, None

    score = 0.0
    score += 1000.0 * captured

    my_grp, my_libs = group_and_liberties(new_board, move)
    score += 12.0 * len(my_libs)
    score += 5.0 * len(my_grp)

    # Connection value
    my_adj = count_adjacent(board, move, 1)
    opp_adj = count_adjacent(board, move, 2)
    score += 18.0 * my_adj
    score += 6.0 * opp_adj

    # Save own atari groups / attack enemy atari groups
    seen = set()
    for nb in neighbors(move):
        if board.get(nb) == 1 and nb not in seen:
            grp, libs = group_and_liberties(board, nb)
            seen |= grp
            if len(libs) == 1 and move in libs:
                score += 140.0 + 8.0 * len(grp)

    seen = set()
    for nb in neighbors(move):
        if board.get(nb) == 2 and nb not in seen:
            grp, libs = group_and_liberties(board, nb)
            seen |= grp
            if len(libs) == 1 and move in libs:
                score += 180.0 + 10.0 * len(grp)
            else:
                before = len(libs)
                _, libs_after = group_and_liberties(new_board, nb) if nb in new_board and new_board.get(nb) == 2 else (set(), set())
                after = len(libs_after) if nb in new_board and new_board.get(nb) == 2 else 0
                score += 4.0 * max(0, before - after)

    # Penalize self-atari-ish outcomes
    if len(my_libs) == 1 and captured == 0:
        score -= 220.0
    elif len(my_libs) == 2:
        score -= 20.0

    # Shape / locality
    r, c = move
    center_dist = abs(r - 10) + abs(c - 10)
    score -= 1.2 * center_dist

    # Prefer not too close to edge unless tactical
    edge_dist = min(r - 1, c - 1, BOARD_SIZE - r, BOARD_SIZE - c)
    score += 1.5 * min(edge_dist, 4)

    # Influence near stones
    local = 0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if inside(nr, nc):
                v = board.get((nr, nc), 0)
                if v == 1:
                    local += 2
                elif v == 2:
                    local += 1
    score += 1.2 * local

    # Slight preference for star points on sparse boards
    if move in {(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)}:
        score += 8.0

    return score, new_board


def all_legal_moves(board: Dict[Tuple[int, int], int], prev_hashes: Set[Tuple]):
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) in board:
                continue
            nb, legal, _ = play_move(board, (r, c), 1)
            if legal and board_hash(nb) not in prev_hashes:
                moves.append((r, c))
    return moves


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if memory is None or not isinstance(memory, dict):
        memory = {}

    board = board_from_lists(me, opponent)

    prev_hashes_list = memory.get("prev_hashes", [])
    if not isinstance(prev_hashes_list, list):
        prev_hashes_list = []
    prev_hashes = set()
    for x in prev_hashes_list[-4:]:
        try:
            prev_hashes.add(tuple(x))
        except Exception:
            pass

    current_hash = board_hash(board)
    prev_hashes.add(current_hash)

    best_move = None
    best_score = -10**30
    best_board = None

    cand = candidate_moves(board)

    # Fast tactical scan first: immediate captures / saves get priority naturally via scoring.
    for mv in cand:
        sc, nb = score_move(board, mv, prev_hashes)
        if sc > best_score:
            best_score = sc
            best_move = mv
            best_board = nb

    if best_move is None:
        legal = all_legal_moves(board, prev_hashes)
        if legal:
            best_move = legal[0]
            best_board, _, _ = play_move(board, best_move, 1)
        else:
            return (0, 0), {"prev_hashes": prev_hashes_list[-3:] + [current_hash]}

    new_hist = prev_hashes_list[-3:] + [current_hash]
    if best_board is not None:
        new_hist.append(board_hash(best_board))
        new_hist = new_hist[-6:]

    return best_move, {"prev_hashes": new_hist}
