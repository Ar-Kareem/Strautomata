
import random
import time
from collections import defaultdict

# Global neighbor map for an 11x11 hex board
N = 11
NEIGHBORS = {}
for r in range(N):
    for c in range(N):
        neigh = []
        # left and right
        if c - 1 >= 0:
            neigh.append((r, c - 1))
        if c + 1 < N:
            neigh.append((r, c + 1))
        # top-left and top-right
        if r - 1 >= 0 and c - 1 >= 0:
            neigh.append((r - 1, c - 1))
        if r - 1 >= 0 and c < N - 1:
            neigh.append((r - 1, c))
        # bottom-left and bottom-right
        if r + 1 < N and c - 1 >= 0:
            neigh.append((r + 1, c - 1))
        if r + 1 < N and c < N:
            neigh.append((r + 1, c))
        NEIGHBORS[(r, c)] = tuple(neigh)

def edges_for(color):
    # Returns the two goal edges for the player color
    # 'b' connects top (row 0) to bottom (row N-1)
    # 'w' connects left (col 0) to right (col N-1)
    if color == 'b':
        return (0, N - 1)  # (top row, bottom row)
    else:
        return (0, N - 1)  # (left col, right col)

class UnionFind:
    __slots__ = ('parent', 'rank', 'edges')
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.edges = defaultdict(set)  # node -> set of 'top','bottom','left','right' flags
    def make_set(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.edges[x] = set()
    def find(self, x):
        # Path compression
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(self, x, y):
        # Merge sets of x and y
        rx = self.find(x)
        ry = self.find(y)
        if rx == ry:
            return
        rrank = self.rank
        rparent = self.parent
        redges = self.edges
        if rrank[rx] < rrank[ry]:
            rx, ry = ry, rx
        rparent[ry] = rx
        if rrank[rx] == rrank[ry]:
            rrank[rx] += 1
        redges[rx].update(redges[ry])
        del redges[ry]
    def add_node_and_union_all(self, x, stones_set):
        self.make_set(x)
        for nb in NEIGHBORS[x]:
            if nb in stones_set:
                self.union(x, nb)
    def touches_both_sides(self, color):
        goal_a, goal_b = edges_for(color)
        if color == 'b':
            # top/bottom rows
            return any(('top' in self.edges[self.find(x)]) and ('bottom' in self.edges[self.find(x)]) for x in self.parent if x[0] in (0, N - 1) and 'top' in self.edges[self.find(x)])
        else:
            # left/right cols
            return any(('left' in self.edges[self.find(x)]) and ('right' in self.edges[self.find(x)]) for x in self.parent if x[1] in (0, N - 1) and 'left' in self.edges[self.find(x)])

def add_edge_flags(uf, stones_set, color):
    # Set edge flags for nodes on edges
    for (r, c) in stones_set:
        if r == 0:
            uf.edges[uf.find((r, c))].add('top')
        if r == N - 1:
            uf.edges[uf.find((r, c))].add('bottom')
        if c == 0:
            uf.edges[uf.find((r, c))].add('left')
        if c == N - 1:
            uf.edges[uf.find((r, c))].add('right')

def evaluate_board(me_set, opp_set, color):
    # Heuristic: longest connected path to each goal side for 'me' minus 'opp'
    my_uf = UnionFind()
    for s in me_set:
        my_uf.add_node_and_union_all(s, me_set)
    add_edge_flags(my_uf, me_set, color)

    opp_color = 'w' if color == 'b' else 'b'
    op_uf = UnionFind()
    for s in opp_set:
        op_uf.add_node_and_union_all(s, opp_set)
    add_edge_flags(op_uf, opp_set, opp_color)

    def longest_chain(uf, color):
        best = 0
        goal_a, goal_b = edges_for(color)
        if color == 'b':
            # distance from top row (0) to bottom (N-1)
            for root in set(uf.find(x) for x in uf.parent):
                has_top = 'top' in uf.edges[root]
                has_bot = 'bottom' in uf.edges[root]
                if has_top and has_bot:
                    # connected: treat as strong
                    return N + 5
            # use BFS-ish from top-edge components
            top_nodes = [x for x in uf.parent if x[0] == 0]
            dist = {}
        else:
            # distance from left col (0) to right col (N-1)
            for root in set(uf.find(x) for x in uf.parent):
                has_left = 'left' in uf.edges[root]
                has_right = 'right' in uf.edges[root]
                if has_left and has_right:
                    return N + 5
            top_nodes = [x for x in uf.parent if x[1] == 0]
            dist = {}
        # Multi-source BFS from goal edge nodes
        from collections import deque
        q = deque()
        visited = set()
        for s in top_nodes:
            r, c = s
            root = uf.find(s)
            if root not in visited:
                visited.add(root)
                q.append((s, 0))
                if color == 'b':
                    if r == 0:
                        dist[root] = 0
                else:
                    if c == 0:
                        dist[root] = 0
        best = 0
        while q:
            (r, c), d = q.popleft()
            if color == 'b':
                if r == N - 1:
                    best = max(best, d)
            else:
                if c == N - 1:
                    best = max(best, d)
            for nb in NEIGHBORS[(r, c)]:
                if nb not in uf.parent:
                    continue
                root_nb = uf.find(nb)
                if root_nb not in visited:
                    visited.add(root_nb)
                    q.append((nb, d + 1))
        return best

    my_score = longest_chain(my_uf, color)
    opp_score = longest_chain(op_uf, opp_color)
    return my_score - opp_score

def check_winner(me_set, opp_set, color):
    my_uf = UnionFind()
    for s in me_set:
        my_uf.add_node_and_union_all(s, me_set)
    add_edge_flags(my_uf, me_set, color)
    if my_uf.touches_both_sides(color):
        return color

    opp_color = 'w' if color == 'b' else 'b'
    op_uf = UnionFind()
    for s in opp_set:
        op_uf.add_node_and_union_all(s, opp_set)
    add_edge_flags(op_uf, opp_set, opp_color)
    if op_uf.touches_both_sides(opp_color):
        return opp_color
    return None

def generate_candidates(me_set, opp_set, color):
    occupied = set(me_set) | set(opp_set)
    frontier = set()
    for s in occupied:
        for nb in NEIGHBORS[s]:
            if nb not in occupied:
                frontier.add(nb)
    # If board is empty, start near the center
    if not occupied:
        center = (N // 2, N // 2)
        return [center]
    candidates = list(frontier)
    if len(candidates) > 50:
        # keep closest to center among frontier to reduce branching
        cx = cy = N // 2
        candidates.sort(key=lambda rc: abs(rc[0] - cx) + abs(rc[1] - cy))
        candidates = candidates[:50]
    if len(candidates) < 10:
        # add a few random empties to explore
        all_cells = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
        candidates.extend(random.sample(all_cells, min(10 - len(candidates), len(all_cells))))
    return candidates

def random_winner_from(me_set, opp_set, to_move_color):
    # Simulate a random game from the current position. Return winner color.
    me = set(me_set)
    opp = set(opp_set)
    color = to_move_color
    empty = {(r, c) for r in range(N) for c in range(N)} - me - opp
    # If someone already won, return that
    w = check_winner(me, opp, 'b')
    if w is None:
        w = check_winner(me, opp, 'w')
    if w:
        return w
    # Random shuffle of empties to make playouts cheap
    empties = list(empty)
    random.shuffle(empties)
    # alternate turns deterministically by parity of length difference if needed, but here we respect 'color' for first move
    turn = color
    idx = 0
    while True:
        if idx >= len(empties):
            break
        move = empties[idx]
        idx += 1
        if turn == 'b':
            me.add(move)
        else:
            opp.add(move)
        # Check winner
        w = check_winner(me, opp, 'b')
        if w is None:
            w = check_winner(me, opp, 'w')
        if w:
            return w
        turn = 'w' if turn == 'b' else 'b'
    # Fallback draw shouldn't happen in Hex; return random
    return random.choice(['b', 'w'])

def policy(me, opp, color):
    # Build sets
    me_set = set(me)
    opp_set = set(opp)

    # Immediate win check for me
    for rc in generate_candidates(me_set, opp_set, color):
        new_me = me_set | {rc}
        if check_winner(new_me, opp_set, color) == color:
            return rc

    opp_color = 'w' if color == 'b' else 'b'
    # Immediate block: if opponent can win next, play that cell
    for rc in generate_candidates(opp_set, me_set, opp_color):
        new_opp = opp_set | {rc}
        if check_winner(me_set, new_opp, opp_color) == opp_color:
            # prefer block that also maximizes my heuristic score
            # ensure rc is empty and not occupied by me
            if rc not in me_set and rc not in opp_set:
                return rc

    # Candidate moves for me
    candidates = generate_candidates(me_set, opp_set, color)

    # Small move ordering: sort by heuristic (defense/offense)
    def heuristic_score(rc):
        new_me = me_set | {rc}
        new_opp = opp_set
        return evaluate_board(new_me, new_opp, color)
    candidates.sort(key=heuristic_score, reverse=True)

    start_time = time.time()
    time_limit = 0.95  # seconds
    best_move = candidates[0] if candidates else (N // 2, N // 2)
    best_rate = -1.0
    played = 0

    for mv in candidates:
        if time.time() - start_time > time_limit:
            break
        wins = 0
        trials = 0
        # Simulate multiple playouts from after playing mv
        while trials < 40:
            if time.time() - start_time > time_limit:
                break
            trials += 1
            new_me = me_set | {mv}
            new_opp = set(opp_set)
            winner = random_winner_from(new_me, new_opp, opp_color)
            if winner == color:
                wins += 1
        if trials > 0:
            rate = wins / trials
            if rate > best_rate:
                best_rate = rate
                best_move = mv
        played += 1

    # Fallback: if no simulation finished, choose best heuristic
    return best_move
