
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    size = len(valid_mask)
    valid_moves = []
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                valid_moves.append((r, c))
    if not valid_moves:
        return (0, 0)  # fallback, though per problem, valid moves exist
    
    corners = {(0,0), (0,14), (14,0), (14,14), (7,0), (7,14)}
    
    def get_connected_component(stones, move):
        from collections import deque
        component = set()
        if move not in stones:
            return component
        visited = set()
        queue = deque([move])
        deltas = [(-1,0), (-1,1), (0,1), (1,0), (1,-1), (0,-1)]
        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            component.add((r, c))
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size:
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        queue.append((nr, nc))
        return component
    
    def is_bridge(component):
        count = 0
        for corner in corners:
            if corner in component:
                count += 1
        return count >= 2
    
    def get_edges(component):
        edges = set()
        for r, c in component:
            if r == 0:
                edges.add('top')
            elif r == size - 1:
                edges.add('bottom')
            if c == 0:
                edges.add('left')
            elif c == size - 1:
                edges.add('right')
        return edges
    
    def is_fork(component):
        return len(get_edges(component)) >= 3
    
    # Check for immediate win
    for move in valid_moves:
        temp_me = me + [move]
        component = get_connected_component(temp_me, move)
        if is_bridge(component) or is_fork(component):
            return move
    
    # Check opponent's winning moves to block
    blocks = []
    for move in valid_moves:
        temp_opp = opp + [move]
        component = get_connected_component(temp_opp, move)
        if is_bridge(component) or is_fork(component):
            blocks.append(move)
    if blocks:
        return blocks[0]
    
    # Heuristic evaluation
    phase = len(me) + len(opp)
    best_score = -np.inf
    best_move = valid_moves[0]
    deltas = [(-1,0), (-1,1), (0,1), (1,0), (1,-1), (0,-1)]
    center = (size // 2, size // 2)
    
    for move in valid_moves:
        r, c = move
        score = 0
        
        # Adjacency bonuses
        friendly = 0
        enemy = 0
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                if (nr, nc) in me:
                    friendly += 1
                elif (nr, nc) in opp:
                    enemy += 1
        score += 2 * friendly + 1 * enemy
        
        # Position bonuses
        if (r, c) in corners:
            score += 5  # big bonus for corners (bridge potential)
        elif r == 0 or r == size-1 or c == 0 or c == size-1:
            score += 2  # edge bonus (fork potential)
        
        # Phase-based center weighting
        if phase < 10:  # early game
            dist = abs(r - center[0]) + abs(c - center[1])
            score += (20 - dist)  # prefer center
        else:
            # Connect to existing stones
            if me:
                min_dist = min(abs(r - mr) + abs(c - mc) for mr, mc in me)
                score += (10 - min_dist)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
