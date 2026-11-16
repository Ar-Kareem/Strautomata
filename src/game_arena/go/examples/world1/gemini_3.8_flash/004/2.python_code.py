
from typing import List, Tuple, Set, Dict
import random

BOARD_SIZE = 19

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def neighbors(r: int, c: int):
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield nr, nc

def diagonals(r: int, c: int):
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield nr, nc

def get_chains(stones: Set[Tuple[int, int]], occupied: Set[Tuple[int, int]]) -> Tuple[Dict[Tuple[int, int], Set[Tuple[int, int]]], Dict[Tuple[int, int], Set[Tuple[int, int]]]]:
    """
    Returns:
      stone_to_chain: mapping from stone (r, c) -> set of stones in chain
      chain_to_liberties: mapping from chain representative stone -> set of empty neighbor positions
    """
    stone_to_chain = {}
    chain_to_liberties = {}
    visited = set()

    for stone in stones:
        if stone in visited:
            continue
        chain = set()
        queue = [stone]
        visited.add(stone)
        liberties = set()

        while queue:
            curr = queue.pop()
            chain.add(curr)
            for nr, nc in neighbors(curr[0], curr[1]):
                nbr = (nr, nc)
                if nbr in stones and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
                elif nbr not in occupied:
                    liberties.add(nbr)

        rep = stone
        chain_to_liberties[rep] = liberties
        for s in chain:
            stone_to_chain[s] = chain

    return stone_to_chain, chain_to_liberties

def is_legal(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]],
             opp_chains: Dict[Tuple[int, int], Set[Tuple[int, int]]]) -> bool:
    r, c = move
    if not in_bounds(r, c):
        return False
    if move in my_set or move in opp_set:
        return False

    occupied = my_set | opp_set

    # 1. Does it have an immediate empty neighbor?
    has_empty = False
    for nbr in neighbors(r, c):
        if nbr not in occupied:
            has_empty = True
            break
    if has_empty:
        return True

    # 2. Does it capture any adjacent opponent chain that has only this liberty?
    for nbr in neighbors(r, c):
        if nbr in opp_set:
            chain = opp_chains.get(nbr)
            if chain is not None:
                # Count liberties of this chain
                chain_libs = set()
                for s in chain:
                    for sn in neighbors(s[0], s[1]):
                        if sn not in occupied:
                            chain_libs.add(sn)
                if chain_libs == {move}:
                    return True

    # 3. Does it connect to a friendly group that has at least one other liberty?
    for nbr in neighbors(r, c):
        if nbr in my_set:
            # Check if this friendly group has other liberties
            chain = set()
            queue = [nbr]
            vis = {nbr}
            other_lib_found = False
            while queue and not other_lib_found:
                curr = queue.pop()
                chain.add(curr)
                for sn in neighbors(curr[0], curr[1]):
                    if sn == move:
                        continue
                    if sn not in occupied:
                        other_lib_found = True
                        break
                    elif sn in my_set and sn not in vis:
                        vis.add(sn)
                        queue.append(sn)
            if other_lib_found:
                return True

    return False

def count_move_liberties(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]) -> int:
    """Estimates the liberties of the newly formed chain if move is played."""
    r, c = move
    sim_my = my_set | {move}
    occupied = sim_my | opp_set

    # Simple check for captures
    captured = set()
    for nbr in neighbors(r, c):
        if nbr in opp_set and nbr not in captured:
            # Check if this opp chain is dead
            chain = set()
            q = [nbr]
            vis = {nbr}
            dead = True
            while q:
                curr = q.pop()
                chain.add(curr)
                for sn in neighbors(curr[0], curr[1]):
                    if sn == move:
                        continue
                    if sn not in occupied:
                        dead = False
                        break
                    if sn in opp_set and sn not in vis:
                        vis.add(sn)
                        q.append(sn)
                if not dead:
                    break
            if dead:
                captured.update(chain)

    sim_opp = opp_set - captured
    sim_occupied = sim_my | sim_opp

    # Flood fill friendly group
    chain = set()
    q = [move]
    vis = {move}
    libs = set()
    while q:
        curr = q.pop()
        chain.add(curr)
        for sn in neighbors(curr[0], curr[1]):
            if sn not in sim_occupied:
                libs.add(sn)
            elif sn in sim_my and sn not in vis:
                vis.add(sn)
                q.append(sn)

    return len(libs)

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    my_set = set(me)
    opp_set = set(opponent)
    occupied = my_set | opp_set

    my_chains, _ = get_chains(my_set, occupied)
    opp_chains, _ = get_chains(opp_set, occupied)

    # 1. Opening book / Corner & Side anchor points
    total_stones = len(me) + len(opponent)
    opening_points = [
        # 4 corners star points & 3-4 points
        (4, 4), (16, 16), (4, 16), (16, 4),
        (3, 4), (4, 3), (17, 4), (16, 3), (3, 16), (4, 17), (17, 16), (16, 17),
        (3, 3), (17, 17), (3, 17), (17, 3),
        # Side star points
        (4, 10), (16, 10), (10, 4), (10, 16),
        # Tengen
        (10, 10)
    ]

    if total_stones < 8:
        for pt in opening_points:
            if pt not in occupied and is_legal(pt, my_set, opp_set, opp_chains):
                return pt

    # Tactical analysis: Identify chains in atari
    # Opponent chains in atari (Attack / Capture)
    opp_atari_targets = []
    seen_opp_chains = set()
    for stone, chain in opp_chains.items():
        rep = min(chain)
        if rep in seen_opp_chains:
            continue
        seen_opp_chains.add(rep)

        libs = set()
        for s in chain:
            for nbr in neighbors(s[0], s[1]):
                if nbr not in occupied:
                    libs.add(nbr)
        if len(libs) == 1:
            target_move = next(iter(libs))
            if is_legal(target_move, my_set, opp_set, opp_chains):
                opp_atari_targets.append((len(chain), target_move))

    if opp_atari_targets:
        opp_atari_targets.sort(key=lambda x: x[0], reverse=True)
        return opp_atari_targets[0][1]

    # Friendly chains in atari (Defense / Escape)
    my_atari_defenses = []
    seen_my_chains = set()
    for stone, chain in my_chains.items():
        rep = min(chain)
        if rep in seen_my_chains:
            continue
        seen_my_chains.add(rep)

        libs = set()
        for s in chain:
            for nbr in neighbors(s[0], s[1]):
                if nbr not in occupied:
                    libs.add(nbr)
        if len(libs) == 1:
            escape_move = next(iter(libs))
            if is_legal(escape_move, my_set, opp_set, opp_chains):
                new_libs = count_move_liberties(escape_move, my_set, opp_set)
                if new_libs > 1:
                    my_atari_defenses.append((len(chain), escape_move))

    if my_atari_defenses:
        my_atari_defenses.sort(key=lambda x: x[0], reverse=True)
        return my_atari_defenses[0][1]

    # Candidate move generation based on adjacency to stones
    candidate_moves = set()

    # Generate moves within 1-2 distance of existing stones
    for s in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = s[0] + dr, s[1] + dc
                if in_bounds(nr, nc) and (nr, nc) not in occupied:
                    candidate_moves.add((nr, nc))

    # Add standard opening points if still empty
    for pt in opening_points:
        if pt not in occupied:
            candidate_moves.add(pt)

    # Move Evaluation Heuristic
    best_move = (0, 0)
    best_score = -1e9

    for move in candidate_moves:
        if not is_legal(move, my_set, opp_set, opp_chains):
            continue

        r, c = move
        score = 0.0

        # Avoid 1st line unless necessary
        dist_edge = min(r, BOARD_SIZE - r + 1, c, BOARD_SIZE - c + 1)
        if dist_edge == 1:
            score -= 15.0
        elif dist_edge == 2:
            score -= 4.0
        elif dist_edge in (3, 4):
            score += 4.0  # 3rd and 4th lines are optimal for territory/influence

        # Check liberties after playing
        libs = count_move_liberties(move, my_set, opp_set)
        if libs <= 1:
            # Self-atari is almost always bad
            score -= 30.0
        else:
            score += libs * 2.0

        # Shape & connectivity bonuses
        nbr_opp = 0
        nbr_my = 0
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                nbr_opp += 1
            elif (nr, nc) in my_set:
                nbr_my += 1

        diag_opp = 0
        diag_my = 0
        for nr, nc in diagonals(r, c):
            if (nr, nc) in opp_set:
                diag_opp += 1
            elif (nr, nc) in my_set:
                diag_my += 1

        # Hane / contact attack or defense
        if nbr_opp > 0:
            score += 2.5 * nbr_opp
        if nbr_my > 0:
            score += 3.0 * nbr_my
        if diag_my > 0:
            score += 1.5 * diag_my

        # Slight preference toward center control
        center_dist = abs(r - 10) + abs(c - 10)
        score -= center_dist * 0.1

        # Add small jitter to avoid determinism loops
        score += random.uniform(0.0, 0.5)

        if score > best_score:
            best_score = score
            best_move = move

    if best_move != (0, 0):
        return best_move

    # Fallback to any valid open point
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in occupied and is_legal((r, c), my_set, opp_set, opp_chains):
                return (r, c)

    return (0, 0)
