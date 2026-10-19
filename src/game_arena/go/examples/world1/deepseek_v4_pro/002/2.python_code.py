
def neighbors(pos):
    r, c = pos
    nbrs = []
    if r > 1: nbrs.append((r-1, c))
    if r < 19: nbrs.append((r+1, c))
    if c > 1: nbrs.append((r, c-1))
    if c < 19: nbrs.append((r, c+1))
    return nbrs

def get_group(start, stones, other_stones):
    group = set()
    liberties = set()
    queue = [start]
    visited = set([start])
    while queue:
        p = queue.pop()
        group.add(p)
        for nbr in neighbors(p):
            if nbr in stones and nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)
            elif nbr not in stones and nbr not in other_stones:
                liberties.add(nbr)
    return group, liberties

class BoardAnalysis:
    def __init__(self, me, opp):
        self.me = set(me)
        self.opp = set(opp)
        self.me_groups = {}
        self.opp_groups = {}
        self.me_stone_to_group = {}
        self.opp_stone_to_group = {}
        self._compute_groups(self.me, self.opp, self.me_groups, self.me_stone_to_group)
        self._compute_groups(self.opp, self.me, self.opp_groups, self.opp_stone_to_group)

    def _compute_groups(self, stones, other_stones, groups_dict, stone_to_group):
        visited = set()
        gid = 0
        for stone in stones:
            if stone in visited: continue
            gid += 1
            group = set()
            liberties = set()
            queue = [stone]
            visited.add(stone)
            while queue:
                p = queue.pop()
                group.add(p)
                for nbr in neighbors(p):
                    if nbr in stones and nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
                    elif nbr not in stones and nbr not in other_stones:
                        liberties.add(nbr)
            groups_dict[gid] = {'stones': group, 'liberties': liberties}
            for s in group:
                stone_to_group[s] = gid

def compute_contested(me, opp):
    empty = set()
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me and (r, c) not in opp:
                empty.add((r, c))
    queue = []
    visited = set()
    for stone in opp:
        for nbr in neighbors(stone):
            if nbr in empty and nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)
    while queue:
        p = queue.pop()
        for nbr in neighbors(p):
            if nbr in empty and nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)
    contested = visited
    safe = empty - contested
    return contested, safe

def simulate_move(move, me, opp):
    if move in me or move in opp:
        return None
    new_me = set(me)
    new_opp = set(opp)
    new_me.add(move)
    captured_opp = set()
    for nbr in neighbors(move):
        if nbr in new_opp:
            group, liberties = get_group(nbr, new_opp, new_me)
            if len(liberties) == 0:
                captured_opp.update(group)
    for s in captured_opp:
        new_opp.remove(s)
    our_group, our_liberties = get_group(move, new_me, new_opp)
    if len(our_liberties) == 0:
        return None
    return new_me, new_opp, captured_opp, our_group, our_liberties

def evaluate_move(move, me, opp, analysis, contested, safe,
                  new_me, new_opp, captured_opp, our_group, our_liberties):
    score = 0.0
    if captured_opp:
        score += len(captured_opp) * 10.0
    for gid, info in analysis.me_groups.items():
        if len(info['liberties']) == 1:
            liberty = next(iter(info['liberties']))
            if move == liberty:
                score += len(info['stones']) * 8.0
    adjacent_me_groups = set()
    for nbr in neighbors(move):
        if nbr in me:
            gid = analysis.me_stone_to_group.get(nbr)
            if gid is not None:
                adjacent_me_groups.add(gid)
    if len(adjacent_me_groups) >= 2:
        score += 5.0 * (len(adjacent_me_groups) - 1)
    for nbr in neighbors(move):
        if nbr in new_opp:
            opp_group, opp_liberties = get_group(nbr, new_opp, new_me)
            if len(opp_liberties) == 1:
                score += 3.0
            elif len(opp_liberties) == 2:
                score += 0.5
    score += len(our_liberties) * 0.2
    dist = abs(move[0] - 10) + abs(move[1] - 10)
    score += (20 - dist) * 0.01
    if move in safe:
        score -= 5.0
    elif move in contested:
        score += 0.5
    return score

def policy(me, opponent):
    me_set = set(me)
    opp_set = set(opponent)

    if not me_set and not opp_set:
        return (4, 4)

    analysis = BoardAnalysis(me_set, opp_set)
    contested, safe = compute_contested(me_set, opp_set)

    empty = set()
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opp_set:
                empty.add((r, c))

    best_move = (0, 0)
    best_score = -1e9
    pass_score = 0.0

    for move in empty:
        result = simulate_move(move, me_set, opp_set)
        if result is None:
            continue
        new_me, new_opp, captured_opp, our_group, our_liberties = result
        score = evaluate_move(move, me_set, opp_set, analysis, contested, safe,
                              new_me, new_opp, captured_opp, our_group, our_liberties)
        if score > best_score:
            best_score = score
            best_move = move

    if pass_score >= best_score:
        return (0, 0)
    return best_move
