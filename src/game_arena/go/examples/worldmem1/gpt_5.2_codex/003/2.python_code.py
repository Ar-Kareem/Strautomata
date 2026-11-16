
import math

BOARD_SIZE = 19

def neighbors(pt):
    r, c = pt
    for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield (nr, nc)

def get_group(start, stones_set):
    group = set()
    stack = [start]
    while stack:
        p = stack.pop()
        if p in group:
            continue
        group.add(p)
        for n in neighbors(p):
            if n in stones_set and n not in group:
                stack.append(n)
    return group

def count_liberties(group, me_set, opp_set):
    libs = set()
    occupied = me_set | opp_set
    for p in group:
        for n in neighbors(p):
            if n not in occupied:
                libs.add(n)
    return len(libs)

def simulate_move(move, me_set, opp_set):
    # returns (legal, captured_set)
    if move in me_set or move in opp_set:
        return False, set()
    new_me = set(me_set)
    new_me.add(move)
    captured = set()
    # check opponent groups for capture
    for n in neighbors(move):
        if n in opp_set:
            grp = get_group(n, opp_set)
            libs = count_liberties(grp, new_me, opp_set)
            if libs == 0:
                captured |= grp
    # remove captured stones
    new_opp = set(opp_set) - captured
    # check own liberties
    my_group = get_group(move, new_me)
    my_libs = count_liberties(my_group, new_me, new_opp)
    if my_libs == 0:
        return False, set()
    return True, captured

def policy(me, opponent, memory):
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    # Opening: if board empty, play center
    if not occupied:
        return (10, 10), memory

    legal_moves = []
    best_move = (0, 0)
    best_score = -1e9

    # precompute opponent groups in atari
    opp_in_atari = set()
    for s in opp_set:
        grp = get_group(s, opp_set)
        libs = count_liberties(grp, me_set, opp_set)
        if libs == 1:
            opp_in_atari |= grp

    # precompute my groups in atari
    my_in_atari_libs = set()
    visited = set()
    for s in me_set:
        if s in visited: 
            continue
        grp = get_group(s, me_set)
        visited |= grp
        libs = []
        occupied = me_set | opp_set
        for p in grp:
            for n in neighbors(p):
                if n not in occupied:
                    libs.append(n)
        if len(set(libs)) == 1:
            my_in_atari_libs |= set(libs)

    # evaluate all points
    for r in range(1, BOARD_SIZE+1):
        for c in range(1, BOARD_SIZE+1):
            move = (r, c)
            if move in occupied:
                continue
            legal, captured = simulate_move(move, me_set, opp_set)
            if not legal:
                continue

            # scoring
            score = 0
            if captured:
                score += 1000 * len(captured)
            # save own stones in atari
            if move in my_in_atari_libs:
                score += 500
            # attack/pressure: adjacent to opponent
            adj_opp = sum((1 for n in neighbors(move) if n in opp_set))
            score += 10 * adj_opp
            # play on liberties of atari opponent groups
            if move in opp_in_atari:
                score += 200
            # centrality
            center = (10, 10)
            dist = abs(move[0] - center[0]) + abs(move[1] - center[1])
            score += max(0, 20 - dist)

            if score > best_score:
                best_score = score
                best_move = move

    if best_score == -1e9:
        return (0, 0), memory
    return best_move, memory
