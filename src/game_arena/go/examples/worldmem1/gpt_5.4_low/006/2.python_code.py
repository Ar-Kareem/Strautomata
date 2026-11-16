
from typing import List, Tuple, Dict, Set
import math

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    my_set = set(me)
    opp_set = set(opponent)
    current_board_key = board_key(my_set, opp_set)

    prev_my_board = memory.get("prev_my_board")  # board after my previous move, for simple ko

    empties = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1)
               if (r, c) not in my_set and (r, c) not in opp_set]

    # Opening preference if board is empty or nearly empty
    total_stones = len(my_set) + len(opp_set)
    opening_points = [
        (4, 4), (4, 16), (16, 4), (16, 16),
        (10, 10), (4, 10), (10, 4), (10, 16), (16, 10),
        (7, 7), (7, 13), (13, 7), (13, 13),
    ]

    legal_moves = []
    candidate_moves = set()

    # Tactical/local candidates near stones
    stones = my_set | opp_set
    for s in stones:
        for nb in neighbors(s):
            if nb not in my_set and nb not in opp_set:
                candidate_moves.add(nb)
        # small radius-2 local expansion
        r, c = s
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                if abs(dr) + abs(dc) <= 2:
                    p = (r + dr, c + dc)
                    if on_board(p) and p not in my_set and p not in opp_set:
                        candidate_moves.add(p)

    # Add opening/global candidates
    for p in opening_points:
        if p not in my_set and p not in opp_set:
            candidate_moves.add(p)

    # Fallback: if somehow candidate set is too small, add all empties
    if len(candidate_moves) < 40:
        candidate_moves.update(empties)

    # Precompute groups/liberties on current board
    my_groups = all_groups(my_set, opp_set)
    opp_groups = all_groups(opp_set, my_set)

    my_group_by_stone = {}
    for g, libs in my_groups:
        for s in g:
            my_group_by_stone[s] = (g, libs)

    opp_group_by_stone = {}
    for g, libs in opp_groups:
        for s in g:
            opp_group_by_stone[s] = (g, libs)

    best_move = (0, 0)
    best_score = -10**18
    best_result_board = None

    for move in candidate_moves:
        if not is_legal(move, my_set, opp_set, prev_my_board):
            continue

        new_my, new_opp, captured = play_move(move, my_set, opp_set)
        score = 0.0

        # Immediate tactical value: captures
        score += 1000 * captured

        # Prefer saving adjacent friendly groups in atari
        saved = 0
        for nb in neighbors(move):
            if nb in my_set:
                g, libs = my_group_by_stone[nb]
                if len(libs) == 1 and move in libs:
                    saved += len(g)
        score += 220 * saved

        # Prefer moves that put enemy groups in atari / reduce liberties
        attack_value = 0
        for nb in neighbors(move):
            if nb in opp_set:
                g, old_libs = opp_group_by_stone[nb]
                if move in old_libs:
                    new_libs = liberties_of_group(g, new_opp, new_my)
                    if len(new_libs) == 1:
                        attack_value += 70 * len(g)
                    elif len(new_libs) == 2:
                        attack_value += 22 * len(g)
                    attack_value += max(0, (len(old_libs) - len(new_libs))) * 10
        score += attack_value

        # Shape/connectivity
        friendly_neighbors = sum((nb in my_set) for nb in neighbors(move))
        enemy_neighbors = sum((nb in opp_set) for nb in neighbors(move))
        score += 14 * friendly_neighbors
        score += 6 * enemy_neighbors

        # Prefer making groups with liberties
        my_new_group = group_at(move, new_my, new_opp)
        new_libs = liberties_of_group(my_new_group, new_my, new_opp)
        score += 8 * len(new_libs)

        # Slight preference for connecting distinct friendly groups
        adjacent_groups = set()
        for nb in neighbors(move):
            if nb in my_set:
                adjacent_groups.add(frozenset(my_group_by_stone[nb][0]))
        if len(adjacent_groups) >= 2:
            score += 45 * (len(adjacent_groups) - 1)

        # Avoid filling your own eye unless tactical
        if looks_like_own_eye(move, my_set, opp_set) and captured == 0 and saved == 0:
            score -= 120

        # Positional preferences
        score += position_bonus(move, total_stones)

        # Prefer locality in middlegame but not pure tenuki spam
        if total_stones >= 6:
            min_dist = min(manhattan(move, s) for s in stones) if stones else 0
            score -= 2.0 * max(0, min_dist - 2)

        # Tiny deterministic tie-break
        score += 0.001 * (move[0] * 19 + move[1])

        if score > best_score:
            best_score = score
            best_move = move
            best_result_board = (new_my, new_opp)

    # If no legal move among candidates, search all empties
    if best_move == (0, 0):
        for move in empties:
            if is_legal(move, my_set, opp_set, prev_my_board):
                new_my, new_opp, _ = play_move(move, my_set, opp_set)
                best_move = move
                best_result_board = (new_my, new_opp)
                break

    new_memory = dict(memory)

    if best_move == (0, 0):
        # Pass only if truly no legal move found
        new_memory["prev_my_board"] = current_board_key
        return (0, 0), new_memory

    # Store board after my move for simple ko next turn
    new_memory["prev_my_board"] = board_key(best_result_board[0], best_result_board[1])
    return best_move, new_memory


def on_board(p: Tuple[int, int]) -> bool:
    r, c = p
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def neighbors(p: Tuple[int, int]):
    r, c = p
    for dr, dc in DIRS:
        q = (r + dr, c + dc)
        if on_board(q):
            yield q


def board_key(my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]):
    return (tuple(sorted(my_set)), tuple(sorted(opp_set)))


def group_at(start: Tuple[int, int], own: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    stack = [start]
    seen = {start}
    while stack:
        p = stack.pop()
        for nb in neighbors(p):
            if nb in own and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen


def liberties_of_group(group: Set[Tuple[int, int]], own: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    libs = set()
    occupied = own | opp
    for s in group:
        for nb in neighbors(s):
            if nb not in occupied:
                libs.add(nb)
    return libs


def all_groups(own: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]):
    rem = set(own)
    out = []
    while rem:
        s = next(iter(rem))
        g = group_at(s, own, opp)
        libs = liberties_of_group(g, own, opp)
        out.append((g, libs))
        rem -= g
    return out


def play_move(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]):
    new_my = set(my_set)
    new_opp = set(opp_set)
    new_my.add(move)

    captured = 0
    checked = set()
    for nb in neighbors(move):
        if nb in new_opp and nb not in checked:
            g = group_at(nb, new_opp, new_my)
            checked |= g
            libs = liberties_of_group(g, new_opp, new_my)
            if not libs:
                captured += len(g)
                new_opp -= g

    return new_my, new_opp, captured


def is_legal(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]], prev_my_board):
    if move == (0, 0):
        return True
    if move in my_set or move in opp_set:
        return False

    new_my, new_opp, _ = play_move(move, my_set, opp_set)

    # Suicide check
    my_group = group_at(move, new_my, new_opp)
    libs = liberties_of_group(my_group, new_my, new_opp)
    if not libs:
        return False

    # Simple ko: don't recreate board after my previous move
    if prev_my_board is not None and board_key(new_my, new_opp) == prev_my_board:
        return False

    return True


def looks_like_own_eye(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]) -> bool:
    # Approximate eye test
    for nb in neighbors(move):
        if nb not in my_set:
            return False

    r, c = move
    diags = []
    for dr in (-1, 1):
        for dc in (-1, 1):
            p = (r + dr, c + dc)
            if on_board(p):
                diags.append(p)

    enemy_diags = sum((d in opp_set) for d in diags)
    # edge/corner eyes tolerate fewer diagonals
    edge_count = int(r in (1, BOARD_SIZE)) + int(c in (1, BOARD_SIZE))
    allowed_enemy_diags = 0 if edge_count == 0 else 1
    return enemy_diags <= allowed_enemy_diags


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def position_bonus(move: Tuple[int, int], total_stones: int) -> float:
    r, c = move
    center_dist = abs(r - 10) + abs(c - 10)

    # Opening: favor star points and center-ish development, not too close to edges
    stars = {(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)}
    bonus = 0.0

    if total_stones < 8:
        if move in stars:
            bonus += 20
        bonus += max(0, 12 - center_dist)
        if r in (1, 2, 18, 19) or c in (1, 2, 18, 19):
            bonus -= 8
    elif total_stones < 30:
        bonus += max(0, 8 - 0.5 * center_dist)
    else:
        bonus += max(0, 4 - 0.2 * center_dist)

    return bonus
