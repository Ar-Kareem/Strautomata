
import sys
from collections import deque

def get_neighbors(point):
    r, c = point
    neighbors = []
    if r > 1: neighbors.append((r-1, c))
    if r < 19: neighbors.append((r+1, c))
    if c > 1: neighbors.append((r, c-1))
    if c < 19: neighbors.append((r, c+1))
    return neighbors

def find_groups(color_stones, occupied_set):
    groups = []
    visited = set()
    for stone in color_stones:
        if stone not in visited:
            group = set([stone])
            queue = deque([stone])
            visited.add(stone)
            while queue:
                current = queue.popleft()
                for neighbor in get_neighbors(current):
                    if neighbor in color_stones and neighbor not in visited:
                        visited.add(neighbor)
                        group.add(neighbor)
                        queue.append(neighbor)
            # Find liberties for the group
            liberties = set()
            for s in group:
                for n in get_neighbors(s):
                    if n not in occupied_set:
                        liberties.add(n)
            groups.append( (group, liberties, len(group)) )
    return groups

def check_legal_move(p, me_set, opp_set, occ):
    # Simulate the move
    new_occ = set(occ)
    new_occ.add(p)
    # Check for captured opponent groups
    new_opp_groups = find_groups(opp_set, new_occ)
    captured = []
    for group in new_opp_groups:
        if len(group[1]) == 0:  # no liberties
            captured.append(group)
    # Remove captured stones
    for group in captured:
        new_occ -= group[0]
    # Now, check if the stone at p has liberties
    # Find the group containing p in the new my stones
    my_stones_new = me_set | {p}
    # But new_occ has my stones and opponent stones after capture, so the my stones are my_stones_new, because I added p, and I didn't remove any of my stones.
    # So, to find the group of p, I can do a BFS from p using the new my stones.
    visited = set()
    group = set([p])
    queue = deque([p])
    visited.add(p)
    # Now, find all connected my stones from p
    while queue:
        current = queue.popleft()
        for neighbor in get_neighbors(current):
            if neighbor in my_stones_new and neighbor not in visited:
                visited.add(neighbor)
                group.add(neighbor)
                queue.append(neighbor)
    # Now, group is the set of my stones connected to p.
    # Liberties: empty points adjacent to the group
    liberties = set()
    for s in group:
        for n in get_neighbors(s):
            if n not in new_occ:
                liberties.add(n)
    return len(liberties) > 0

def policy(me, opponent, memory):
    me_set = set(me)
    opp_set = set(opponent)
    occ = me_set | opp_set

    opp_groups = find_groups(opp_set, occ)
    my_groups = find_groups(me_set, occ)

    capture_moves = []
    for group in opp_groups:
        if len(group[1]) == 1:
            l = list(group[1])[0]
            capture_moves.append( (l, group[2]) )

    defense_moves = []
    for group in my_groups:
        if len(group[1]) == 1:
            l = list(group[1])[0]
            defense_moves.append( (l, group[2]) )

    if capture_moves:
        best_move = max(capture_moves, key=lambda x: x[1])
        action = best_move[0]
    elif defense_moves:
        best_move = max(defense_moves, key=lambda x: x[1])
        action = best_move[0]
    else:
        # Generate potential moves
        all_points = [(r, c) for r in range(1, 20) for c in range(1, 20)]
        empty_points = [p for p in all_points if p not in occ]
        potential_moves = []
        for p in empty_points:
            for n in get_neighbors(p):
                if n in occ:
                    potential_moves.append(p)
                    break  # since it has at least one neighbor in occ
        # If no potential moves, but occ might be empty
        if not potential_moves:
            if not occ:
                action = (10, 10)
            else:
                action = (0, 0)
        else:
            # Sort potential_moves by distance to center
            center = (10, 10)
            potential_moves.sort(key=lambda p: abs(p[0]-10) + abs(p[1]-10))
            for p in potential_moves:
                if check_legal_move(p, me_set, opp_set, occ):
                    action = p
                    break
            else:
                action = (0, 0)

    return action, {}
