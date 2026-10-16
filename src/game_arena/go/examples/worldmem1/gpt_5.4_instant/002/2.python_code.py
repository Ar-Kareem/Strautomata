
from __future__ import annotations

from typing import List, Tuple, Dict, Set

BOARD_SIZE = 19
PASS_MOVE = (0, 0)


def neighbors(r: int, c: int):
    if r > 1:
        yield (r - 1, c)
    if r < BOARD_SIZE:
        yield (r + 1, c)
    if c > 1:
        yield (r, c - 1)
    if c < BOARD_SIZE:
        yield (r, c + 1)


def board_from_lists(me, opponent):
    board = {}
    for p in me:
        board[p] = 1
    for p in opponent:
        board[p] = -1
    return board


def get_group_and_liberties(board: Dict[Tuple[int, int], int], start: Tuple[int, int]):
    color = board.get(start, 0)
    if color == 0:
        return set(), set()
    stack = [start]
    group = set([start])
    liberties = set()
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


def remove_group(board: Dict[Tuple[int, int], int], group: Set[Tuple[int, int]]):
    for p in group:
        if p in board:
            del board[p]


def simulate_move(board: Dict[Tuple[int, int], int], move: Tuple[int, int], color: int):
    if move == PASS_MOVE:
        return dict(board), 0, True
    if move in board:
        return None, 0, False

    new_board = dict(board)
    new_board[move] = color
    captured = 0
    opp = -color

    checked = set()
    for nb in neighbors(*move):
        if new_board.get(nb, 0) == opp and nb not in checked:
            grp, libs = get_group_and_liberties(new_board, nb)
            checked |= grp
            if len(libs) == 0:
                captured += len(grp)
                remove_group(new_board, grp)

    my_group, my_libs = get_group_and_liberties(new_board, move)
    if len(my_libs) == 0:
        return None, 0, False

    return new_board, captured, True


def board_hash(board: Dict[Tuple[int, int], int]):
    return tuple(sorted(board.items()))


def legal_moves(me, opponent, memory):
    board = board_from_lists(me, opponent)
    seen = set(memory.get("seen_hashes", []))
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            mv = (r, c)
            if mv in board:
                continue
            new_board, _, ok = simulate_move(board, mv, 1)
            if not ok:
                continue
            h = board_hash(new_board)
            if h in seen:
                continue
            moves.append(mv)
    if not moves:
        return [PASS_MOVE]
    return moves


def count_adjacent_allies(board, move, color=1):
    s = 0
    for nb in neighbors(*move):
        if board.get(nb, 0) == color:
            s += 1
    return s


def count_adjacent_enemies(board, move, color=1):
    s = 0
    opp = -color
    for nb in neighbors(*move):
        if board.get(nb, 0) == opp:
            s += 1
    return s


def local_density(board, move, dist=2):
    r0, c0 = move
    allies = enemies = 0
    for (r, c), v in board.items():
        if abs(r - r0) + abs(c - c0) <= dist:
            if v == 1:
                allies += 1
            else:
                enemies += 1
    return allies, enemies


def center_bonus(move):
    r, c = move
    return -((r - 10) ** 2 + (c - 10) ** 2) / 20.0


def evaluate_move(me, opponent, move):
    board = board_from_lists(me, opponent)
    new_board, captured, ok = simulate_move(board, move, 1)
    if not ok:
        return -10**18
    if move == PASS_MOVE:
        return -999999

    score = 0.0
    score += captured * 1000.0

    my_group, my_libs = get_group_and_liberties(new_board, move)
    score += len(my_libs) * 12.0
    score += len(my_group) * 2.0

    adj_allies = count_adjacent_allies(board, move, 1)
    adj_enemies = count_adjacent_enemies(board, move, 1)
    score += adj_allies * 18.0
    score += adj_enemies * 8.0

    connected_groups = set()
    for nb in neighbors(*move):
        if board.get(nb, 0) == 1:
            grp, _ = get_group_and_liberties(board, nb)
            connected_groups.add(min(grp))
    score += max(0, len(connected_groups) - 1) * 25.0

    # Save own groups in atari
    saved = 0
    checked = set()
    for p in me:
        if p in checked:
            continue
        grp, libs = get_group_and_liberties(board, p)
        checked |= grp
        if len(libs) == 1 and move in libs:
            saved += len(grp)
    score += saved * 180.0

    # Put opponent groups into atari / pressure
    pressured = 0
    checked = set()
    for p in opponent:
        if p in checked:
            continue
        grp, libs = get_group_and_liberties(board, p)
        checked |= grp
        if move in libs:
            _, libs_after = get_group_and_liberties(new_board, p) if p in new_board else (set(), set())
            if p in new_board:
                if len(libs_after) == 1:
                    pressured += len(grp) * 1.5
                elif len(libs_after) == 2:
                    pressured += len(grp) * 0.5
    score += pressured * 40.0

    allies, enemies = local_density(board, move, dist=2)
    if allies + enemies == 0:
        score += center_bonus(move)
    else:
        score += allies * 4.0 + enemies * 2.5

    # Avoid filling own eyes-ish
    eye_like = True
    for nb in neighbors(*move):
        if board.get(nb, 0) != 1:
            eye_like = False
            break
    if eye_like:
        score -= 120.0

    score += center_bonus(move) * 0.7
    return score


def update_memory(me, opponent, memory):
    board = board_from_lists(me, opponent)
    h = board_hash(board)
    seen = list(memory.get("seen_hashes", []))
    if not seen or seen[-1] != h:
        seen.append(h)
    if len(seen) > 12:
        seen = seen[-12:]
    memory["seen_hashes"] = seen
    return memory


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if memory is None:
        memory = {}
    else:
        memory = dict(memory)

    memory = update_memory(me, opponent, memory)

    board = board_from_lists(me, opponent)
    moves = legal_moves(me, opponent, memory)

    if moves == [PASS_MOVE]:
        return PASS_MOVE, memory

    # Fast tactical pre-check: immediate captures or urgent saves
    best_move = None
    best_score = -10**18

    for mv in moves:
        score = evaluate_move(me, opponent, mv)
        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is None:
        return PASS_MOVE, memory

    # Record resulting board hash to help avoid simple cycles
    new_board, _, ok = simulate_move(board, best_move, 1)
    if ok and new_board is not None:
        seen = list(memory.get("seen_hashes", []))
        seen.append(board_hash(new_board))
        if len(seen) > 12:
            seen = seen[-12:]
        memory["seen_hashes"] = seen

    return best_move, memory
