
import collections

DIR = [(-1, 0), (0, -1), (-1, -1), (0, 1), (1, 0), (-1, 1)]

def check_winning(me_set, opp_set, valid_mask, candidate, DIR):
    """Check if placing candidate completes a winning structure."""
    new_me = me_set | {candidate}
    adj = {}
    for node in new_me:
        adj[node] = []
        r, c = node
        for dr, dc in DIR:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if (nr, nc) in new_me:
                    adj[node].append((nr, nc))
    
    visited = set()
    components = []
    for node in new_me:
        if node not in visited:
            comp = []
            stack = [node]
            visited.add(node)
            while stack:
                n = stack.pop()
                comp.append(n)
                for nb in adj.get(n, []):
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            components.append(comp)
    
    for comp in components:
        n = len(comp)
        edges = 0
        for node in comp:
            edges += len(adj[node])
        edges //= 2
        if edges >= n:
            return True
            
        corners = {(0, 0), (0, 14), (14, 0), (14, 14)}
        if len([c for c in corners if c in comp]) >= 2:
            return True
            
        edge_types = set()
        for (r_node, c_node) in comp:
            if r_node == 0 and 1 <= c_node <= 13:
                edge_types.add('top')
            elif r_node == 14 and 1 <= c_node <= 13:
                edge_types.add('bottom')
            elif c_node == 0 and 1 <= r_node <= 13:
                edge_types.add('left')
            elif c_node == 14 and 1 <= r_node <= 13:
                edge_types.add('right')
        if len(edge_types) >= 3:
            return True
            
    return False

def heuristic(me_set, opp_set, comp_map, corners, move, DIR):
    """Evaluate move's immediate connectivity benefits."""
    r, c = move
    new_degree = 0
    comp_ids = set()
    corner_adj = False
    for dr, dc in DIR:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 15 and 0 <= nc < 15:
            neighbor = (nr, nc)
            if neighbor in me_set:
                new_degree += 1
                comp_ids.add(comp_map[neighbor])
            elif neighbor in corners and neighbor in me_set:
                corner_adj = True
                
    bonus = len(comp_ids) - 1 if comp_ids else -1
    return new_degree + bonus + (1 if corner_adj else 0)

def policy(me, opp, valid_mask):
    me_set = set(me)
    opp_set = set(opp)
    corners = {(0, 0), (0, 14), (14, 0), (14, 14)}
    
    # Precompute current components
    current_components = []
    visited = set()
    comp_map = {}
    for node in me_set:
        if node not in visited:
            comp = []
            stack = [node]
            visited.add(node)
            while stack:
                n = stack.pop()
                comp.append(n)
                for dr, dc in DIR:
                    nr = n[0] + dr
                    nc = n[1] + dc
                    if 0 <= nr < 15 and 0 <= nc < 15:
                        neighbor = (nr, nc)
                        if neighbor in me_set and neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
            current_components.append(comp)
            
    comp_map = {node: idx for idx, comp in enumerate(current_components)}
    
    # Generate valid moves
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                cell = (r, c)
                if cell not in me_set and cell not in opp_set:
                    valid_moves.append(cell)
                    
    if not valid_moves:
        # Fallback: return first valid cell (shouldn't happen)
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c]:
                    return (r, c)
        return (0, 0)
                    
    winning_moves = []
    for move in valid_moves:
        if check_winning(me_set, opp_set, valid_mask, move, DIR):
            winning_moves.append(move)
            
    if winning_moves:
        best_winning = None
        best_score = -float('inf')
        for move in winning_moves:
            score = heuristic(me_set, opp_set, comp_map, corners, move, DIR)
            if score > best_score:
                best_score = score
                best_winning = move
        return best_winning
        
    best_move = None
    best_score = -float('inf')
    for move in valid_moves:
        score = heuristic(me_set, opp_set, comp_map, corners, move, DIR)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
