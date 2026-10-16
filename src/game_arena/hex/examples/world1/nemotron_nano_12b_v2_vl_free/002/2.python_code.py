
def policy(me, opp, color):
    me = set((r, c) for (r, c) in me)
    opp = set((r, c) for (r, c) in opp)
    directions = [
        (-1, 0),   # Up (north)
        (-1, 1),   # Up-right
        (0, -1),   # Left
        (0, 1),    # Right
        (1, -1),   # Down-left
        (1, 0)     # Down
    ]
    
    # Generate all possible empty cells
    empty = [
        (r, c)
        for r in range(11)
        for c in range(11)
        if (r, c) not in me and (r, c) not in opp
    ]
    
    if not empty:
        return None  # This should never happen in a real game

    # Helper function to find root with path compression
    def find(parent, node):
        while parent[node] != node:
            parent[node] = parent.get(parent[node], node)
            node = parent[node]
        return node

    # Step 1: Check all empty cells for an immediate win
    winning_moves = []
    for cell in empty:
        temp_me = me.copy()
        temp_me.add(cell)
        stones = list(temp_me)
        
        parent = {s: s for s in stones}
        
        # Build adjacency graph
        for stone in stones:
            r, c = stone
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                neighbor = (nr, nc)
                if 0 <= nr < 11 and 0 <= nc < 11 and neighbor in parent:
                    root_s = find(stone, parent)
                    root_n = find(neighbor, parent)
                    if root_s != root_n:
                        parent[root_n] = root_s
        
        # Evaluate if the move creates a connection between sides
        connected = False
        if color == 'b':
            top_nodes = [s for s in stones if s[0] == 0]
            bottom_nodes = [s for s in stones if s[0] == 10]
            if not top_nodes or not bottom_nodes:
                continue
            top_roots = {find(s, parent) for s in top_nodes}
            bottom_roots = {find(s, parent) for s in bottom_nodes}
            if top_roots & bottom_roots:
                connected = True
        elif color == 'w':
            left_nodes = [s for s in stones if s[1] == 0]
            right_nodes = [s for s in stones if s[1] == 10]
            if not left_nodes or not right_nodes:
                continue
            left_roots = {find(s, parent) for s in left_nodes}
            right_roots = {find(s, parent) for s in right_nodes}
            if left_roots & right_roots:
                connected = True
        
        if connected:
            return cell

    # If no immediate win found, proceed with heuristic
    def adj_count(cell):
        r, c = cell
        return sum(1 for dr, dc in directions if (r + dr, c + dc) in me)

    # Evaluate each empty cell by adjacency and proximity
    def evaluate(cell):
        r, c = cell
        adj = adj_count(cell)
        if color == 'b':
            proximity = r * (10 - r)  # Maximize for center row
        else:
            proximity = c * (10 - c)  # Maximize for center column
        return adj, proximity

    best_cell = None
    best_score = (-1, -1)  # (adj, proximity)

    for cell in empty:
        adj, proximity = evaluate(cell)
        if (adj, proximity) > best_score:
            best_cell = cell
            best_score = (adj, proximity)

    return best_cell
