
import math
from typing import List, Tuple, Dict, Set

BOARD_SIZE = 19
CENTER = (10, 10)

STAR_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)
]

def neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    r, c = pos
    nbs = []
    if r > 1: nbs.append((r - 1, c))
    if r < BOARD_SIZE: nbs.append((r + 1, c))
    if c > 1: nbs.append((r, c - 1))
    if c < BOARD_SIZE: nbs.append((r, c + 1))
    return nbs

def compute_groups(stones_set: Set[Tuple[int, int]], all_occ: Set[Tuple[int, int]]):
    groups = []
    stone_to_group = {}
    visited = set()
    for stone in stones_set:
        if stone in visited:
            continue
        stack = [stone]
        visited.add(stone)
        group_stones = set()
        liberties = set()
        while stack:
            p = stack.pop()
            group_stones.add(p)
            for n in neighbors(p):
                if n in stones_set and n not in visited:
                    visited.add(n)
                    stack.append(n)
                elif n not in all_occ:
                    liberties.add(n)
        gid = len(groups)
        for s in group_stones:
            stone_to_group[s] = gid
        groups.append({"stones": group_stones, "liberties": liberties})
    return groups, stone_to_group

def group_liberties(start: Tuple[int, int], me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]):
    visited = set([start])
    stack = [start]
    liberties = set()
    while stack:
        p = stack.pop()
        for n in neighbors(p):
            if n in me_set:
                if n not in visited:
                    visited.add(n)
                    stack.append(n)
            elif n in opp_set:
                continue
            else:
                liberties.add(n)
    return liberties

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict):
    me_set = set(me)
    opp_set = set(opponent)
    all_occ = me_set | opp_set

    # Precompute groups and liberties
    my_groups, my_map = compute_groups(me_set, all_occ)
    opp_groups, opp_map = compute_groups(opp_set, all_occ)

    # 1. Capture if possible
    capture_moves = []
    for gid, grp in enumerate(opp_groups):
        libs = grp["liberties"]
        if len(libs) == 1:
            move = next(iter(libs))
            if move not in all_occ:
                capture_moves.append((len(grp["stones"]), move))
    if capture_moves:
        capture_moves.sort(reverse=True)
        move = capture_moves[0][1]
        return move, memory

    # 2. Defend groups in atari
    defend_moves = []
    for gid, grp in enumerate(my_groups):
        libs = grp["liberties"]
        if len(libs) == 1:
            move = next(iter(libs))
            if move in all_occ:
                continue
            # Check legality by simple simulation
            captured = set()
            for n in neighbors(move):
                if n in opp_set:
                    ogid = opp_map[n]
                    if len(opp_groups[ogid]["liberties"]) == 1 and move in opp_groups[ogid]["liberties"]:
                        captured |= opp_groups[ogid]["stones"]
            new_opp = opp_set - captured if captured else opp_set
            new_me = me_set | {move}
            libs_new = group_liberties(move, new_me, new_opp)
            legal = bool(captured) or len(libs_new) > 0
            if legal:
                defend_moves.append((len(grp["stones"]), move))
    if defend_moves:
        defend_moves.sort(reverse=True)
        move = defend_moves[0][1]
        return move, memory

    # 3. Opening star points
    total_stones = len(me_set) + len(opp_set)
    if total_stones < 8:
        for sp in STAR_POINTS:
            if sp not in all_occ:
                return sp, memory

    # Helper for simulation
    def simulate_move(pos: Tuple[int, int]):
        if pos in all_occ:
            return None
        captured = set()
        for n in neighbors(pos):
            if n in opp_set:
                gid = opp_map[n]
                libs = opp_groups[gid]["liberties"]
                if len(libs) == 1 and pos in libs:
                    captured |= opp_groups[gid]["stones"]
        new_opp = opp_set - captured if captured else opp_set
        new_me = me_set | {pos}
        libs_new = group_liberties(pos, new_me, new_opp)
        legal = bool(captured) or len(libs_new) > 0
        if not legal:
            return None
        return captured, libs_new

    # 4. Evaluate all legal moves
    best_move = None
    best_score = -1e9
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            pos = (r, c)
            if pos in all_occ:
                continue
            sim = simulate_move(pos)
            if sim is None:
                continue
            captured, libs_new = sim
            captured_count = len(captured)

            adj_friend = sum((n in me_set) for n in neighbors(pos))
            adj_opp = sum((n in opp_set) for n in neighbors(pos))

            atari = 0
            for n in neighbors(pos):
                if n in opp_set:
                    gid = opp_map[n]
                    libs = opp_groups[gid]["liberties"]
                    if len(libs) == 2 and pos in libs:
                        atari += 1

            dist = abs(r - CENTER[0]) + abs(c - CENTER[1])
            centrality = 20 - dist

            score = 0
            score += 100 * captured_count
            score += 2 * adj_friend + 1 * adj_opp
            score += 5 * atari
            score += centrality
            score += 0.5 * len(libs_new)
            if captured_count == 0 and len(libs_new) == 1:
                score -= 8  # self-atari penalty

            if score > best_score:
                best_score = score
                best_move = pos

    if best_move is None:
        return (0, 0), memory
    return best_move, memory
