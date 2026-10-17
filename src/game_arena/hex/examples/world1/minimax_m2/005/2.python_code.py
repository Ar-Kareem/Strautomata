
# Precompute the neighbors for the 11x11 hex grid
neighbors = {}
for i in range(11):
    for j in range(11):
        n = []
        if j-1 >= 0:
            n.append((i, j-1))
        if j+1 <= 10:
            n.append((i, j+1))
        if i-1 >= 0:
            n.append((i-1, j))
            if j+1 <= 10:
                n.append((i-1, j+1))
        if i+1 <= 10:
            n.append((i+1, j))
            if j-1 >= 0:
                n.append((i+1, j-1))
        neighbors[(i, j)] = n

def check_win(stones, color):
    if color == 'b':
        visited = set()
        queue = []
        for stone in stones:
            if stone[0] == 0:
                queue.append(stone)
                visited.add(stone)
        if not queue:
            return False
        while queue:
            node = queue.pop(0)
            if node[0] == 10:
                return True
            for neighbor in neighbors[node]:
                if neighbor in stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False
    else:
        visited = set()
        queue = []
        for stone in stones:
            if stone[1] == 0:
                queue.append(stone)
                visited.add(stone)
        if not queue:
            return False
        while queue:
            node = queue.pop(0)
            if node[1] == 10:
                return True
            for neighbor in neighbors[node]:
                if neighbor in stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'
    
    for i in range(11):
        for j in range(11):
            candidate = (i, j)
            if candidate in me_set or candidate in opp_set:
                continue
            new_me = me_set | {candidate}
            if check_win(new_me, color):
                return candidate
            
    for i in range(11):
        for j in range(11):
            candidate = (i, j)
            if candidate in me_set or candidate in opp_set:
                continue
            new_opp = opp_set | {candidate}
            if check_win(new_opp, opp_color):
                return candidate
                
    parent = {}
    rank = {}
    for stone in me:
        parent[stone] = stone
        rank[stone] = 0
        
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
        
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
            
    for stone in me:
        for neighbor in neighbors[stone]:
            if neighbor in me_set:
                union(stone, neighbor)
                
    components = {}
    for stone in me:
        root = find(stone)
        if root not in components:
            components[root] = {
                'stones': set(),
                'touches_top': False,
                'touches_bottom': False,
                'touches_left': False,
                'touches_right': False,
            }
        comp = components[root]
        comp['stones'].add(stone)
        if stone[0] == 0:
            comp['touches_top'] = True
        if stone[0] == 10:
            comp['touches_bottom'] = True
        if stone[1] == 0:
            comp['touches_left'] = True
        if stone[1] == 10:
            comp['touches_right'] = True
            
    candidate_moves = []
    for i in range(11):
        for j in range(11):
            candidate = (i, j)
            if candidate in me_set or candidate in opp_set:
                continue
            adjacent_roots = set()
            for neighbor in neighbors[candidate]:
                if neighbor in me_set:
                    adjacent_roots.add(find(neighbor))
                    
            new_touches_top = (i == 0)
            new_touches_bottom = (i == 10)
            new_touches_left = (j == 0)
            new_touches_right = (j == 10)
            
            for root in adjacent_roots:
                comp = components[root]
                new_touches_top = new_touches_top or comp['touches_top']
                new_touches_bottom = new_touches_bottom or comp['touches_bottom']
                new_touches_left = new_touches_left or comp['touches_left']
                new_touches_right = new_touches_right or comp['touches_right']
                
            if color == 'b':
                score = 0
                if not new_touches_top:
                    score += i
                if not new_touches_bottom:
                    score += (10 - i)
            else:
                score = 0
                if not new_touches_left:
                    score += j
                if not new_touches_right:
                    score += (10 - j)
                    
            total_size = 1
            for root in adjacent_roots:
                total_size += len(components[root]['stones'])
                
            dist_center = abs(i - 5) + abs(j - 5)
            candidate_moves.append((score, total_size, dist_center, candidate))
            
    candidate_moves.sort(key=lambda x: (x[0], -x[1], x[2]))
    
    if candidate_moves:
        return candidate_moves[0][3]
    else:
        for i in range(11):
            for j in range(11):
                if (i, j) not in me_set and (i, j) not in opp_set:
                    return (i, j)
        return (5, 5)
