
import copy

class UnionFind:
    def __init__(self, size=123):
        self.parent = list(range(size))

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[px] = py

def get_neighbors(r, c):
    candidates = [(r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)]
    return [(rr, cc) for rr, cc in candidates if 0 <= rr < 11 and 0 <= cc < 11]

def get_special_sides(col):
    if col == 'b':
        s1_ids = {i for i in range(121) if i // 11 == 0}  # row 0
        s2_ids = {i for i in range(121) if i // 11 == 10}  # row 10
    else:
        s1_ids = {i for i in range(121) if i % 11 == 0}   # col 0
        s2_ids = {i for i in range(121) if i % 11 == 10}  # col 10
    return s1_ids, s2_ids

def build_uf(stones_set, s1_ids, s2_ids, sp1_id=121, sp2_id=122):
    uf = UnionFind()
    for stone_id in stones_set:
        # Union with its neighbors
        for nr, nc in get_neighbors(stone_id // 11, stone_id % 11):
            n_id = nr * 11 + nc
            if n_id in stones_set:
                uf.union(stone_id, n_id)
        # Union with sides
        if stone_id in s1_ids:
            uf.union(stone_id, sp1_id)
        if stone_id in s2_ids:
            uf.union(stone_id, sp2_id)
    return uf

def simulate_add(uf, new_id, stones_set, s1_ids, s2_ids, sp1_id=121, sp2_id=122):
    uf_copy = UnionFind()
    uf_copy.parent = uf.parent[:]
    uf_copy.parent[new_id] = new_id
    # Union with existing neighbors
    for nr, nc in get_neighbors(new_id // 11, new_id % 11):
        n_id = nr * 11 + nc
        if n_id in stones_set:
            uf_copy.union(new_id, n_id)
    # Union with sides
    if new_id in s1_ids:
        uf_copy.union(new_id, sp1_id)
    if new_id in s2_ids:
        uf_copy.union(new_id, sp2_id)
    return uf_copy.find(sp1_id) == uf_copy.find(sp2_id)

def policy(me, opp, color):
    all_occupied = set((r * 11 + c) for r, c in me) | set((r * 11 + c) for r, c in opp)
    empty_cells = [(i // 11, i % 11) for i in range(121) if i not in all_occupied]
    
    me_stones = set((r * 11 + c) for r, c in me)
    opp_stones = set((r * 11 + c) for r, c in opp)
    
    my_s1, my_s2 = get_special_sides(color)
    opp_s1, opp_s2 = get_special_sides('w' if color == 'b' else 'b')
    
    my_uf = build_uf(me_stones, my_s1, my_s2)
    opp_uf = build_uf(opp_stones, opp_s1, opp_s2)
    
    # Check for immediate win
    for r, c in empty_cells:
        move_id = r * 11 + c
        if simulate_add(my_uf, move_id, me_stones, my_s1, my_s2):
            return (r, c)
    
    # Check for threats from opponent
    threatening_moves = []
    for r, c in empty_cells:
        move_id = r * 11 + c
        if simulate_add(opp_uf, move_id, opp_stones, opp_s1, opp_s2):
            threatening_moves.append((r, c))
    
    if threatening_moves:
        return threatening_moves[0]  # Block the first threat
    
    # Heuristic: Max friendly neighbors
    best_moves = []
    max_score = -1
    for r, c in empty_cells:
        score = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me:
                score += 1
        if score > max_score:
            max_score = score
            best_moves = [(r, c)]
        elif score == max_score:
            best_moves.append((r, c))
    
    return best_moves[0] if best_moves else empty_cells[0]  # Fallback, though shouldn't happen
