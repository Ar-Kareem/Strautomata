
from collections import deque

SIZE = 19
CENTER = (10, 10)

def neighbors(r, c):
    if r > 1: yield (r-1, c)
    if r < SIZE: yield (r+1, c)
    if c > 1: yield (r, c-1)
    if c < SIZE: yield (r, c+1)

def group_and_liberties(start, own_set, opp_set):
    # BFS to collect group and its liberties
    q = deque([start])
    visited = {start}
    group = {start}
    liberties = set()
    while q:
        r, c = q.popleft()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in own_set and (nr, nc) not in visited:
                visited.add((nr, nc))
                group.add((nr, nc))
                q.append((nr, nc))
            elif (nr, nc) not in own_set and (nr, nc) not in opp_set:
                liberties.add((nr, nc))
    return group, liberties

def policy(me, opponent):
    me_set = set(me)
    opp_set = set(opponent)

    # Opening: play center if empty
    if not me_set and not opp_set and (10, 10) not in me_set and (10, 10) not in opp_set:
        return (10, 10)

    best_move = None
    best_score = -10**9

    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            p = (r, c)
            if p in me_set or p in opp_set:
                continue

            captured = set()
            # Track atari threats
            atari_threats = 0
            visited_opp = set()
            for n in neighbors(r, c):
                if n in opp_set and n not in visited_opp:
                    grp, libs = group_and_liberties(n, opp_set, me_set)
                    visited_opp |= grp
                    if p in libs and len(libs) == 1:
                        captured |= grp
                    elif p in libs and len(libs) == 2:
                        atari_threats += 1

            new_opp = opp_set - captured
            new_me = me_set | {p}

            # Check legality: our group must have liberties after move
            grp, libs = group_and_liberties(p, new_me, new_opp)
            if len(libs) == 0:
                continue  # illegal (suicide)

            # Scoring heuristic
            score = 0
            cap_count = len(captured)
            if cap_count > 0:
                score += 1000 * cap_count + 50 * cap_count

            # Saving own groups in atari
            visited_own = set()
            saved_groups = 0
            for n in neighbors(r, c):
                if n in me_set and n not in visited_own:
                    g, l = group_and_liberties(n, me_set, opp_set)
                    visited_own |= g
                    if p in l and len(l) == 1:
                        saved_groups += 1
            score += 200 * saved_groups

            # Atari threats
            score += 50 * atari_threats

            # Connection bonus
            adj_own = sum(1 for n in neighbors(r, c) if n in me_set)
            score += 5 * adj_own

            # Liberties of new group
            score += 2 * len(libs)

            # Centrality
            dist = abs(r - CENTER[0]) + abs(c - CENTER[1])
            score += (10 - dist)

            # Self-atari penalty (unless capture)
            if len(libs) == 1 and cap_count == 0:
                score -= 100

            if score > best_score:
                best_score = score
                best_move = p

    if best_move is None:
        return (0, 0)
    return best_move
