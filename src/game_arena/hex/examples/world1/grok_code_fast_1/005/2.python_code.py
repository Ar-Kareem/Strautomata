
import random

def get_neighbors(r, c):
    dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]
    neighbors = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr <= 10 and 0 <= nc <= 10:
            neighbors.append((nr, nc))
    return neighbors

def is_win(my_stones, my_color):
    stone_set = set(my_stones)
    if my_color == 'b':
        visited = set()
        queue = [(r, c) for r, c in my_stones if r == 0 and (r, c) in stone_set]
        if not queue:
            return False
        visited.update(set(queue))
        while queue:
            cr, cc = queue.pop(0)
            if cr == 10:
                return True
            for nr, nc in get_neighbors(cr, cc):
                if (nr, nc) in stone_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False
    else:  # 'w'
        visited = set()
        queue = [(r, c) for r, c in my_stones if c == 0 and (r, c) in stone_set]
        if not queue:
            return False
        visited.update(set(queue))
        while queue:
            cr, cc = queue.pop(0)
            if cc == 10:
                return True
            for nr, nc in get_neighbors(cr, cc):
                if (nr, nc) in stone_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

def policy(me, opp, color):
    all_stones = set(me).union(set(opp))
    legal = [(r, c) for r in range(11) for c in range(11) if (r, c) not in all_stones]
    if not legal:
        return None  # Though unlikely
    
    # 1. Check for a winning move
    for move in legal:
        new_me = me + [move]
        if is_win(new_me, color):
            return move
    
    # 2. Check for a blocking move (prevent opponent win)
    opp_color = 'w' if color == 'b' else 'b'
    for move in legal:
        new_opp = opp + [move]
        if is_win(new_opp, opp_color):
            return move
    
    # 3. Otherwise, greedy: closest to center
    def dist_to_center(move):
        r, c = move
        return abs(r - 5) + abs(c - 5)
    
    return min(legal, key=dist_to_center)
