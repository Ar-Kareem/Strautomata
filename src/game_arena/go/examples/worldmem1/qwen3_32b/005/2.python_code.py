
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Generate all empty positions
    empty_positions = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opponent_set:
                empty_positions.append((r, c))
    
    # Check validity of each empty position and collect valid moves
    valid_moves = []
    for (r, c) in empty_positions:
        # Check if the move has liberties
        has_liberties = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            x, y = r + dx, c + dy
            if (x, y) not in me_set and (x, y) not in opponent_set:
                has_liberties = True
                break
        if has_liberties:
            valid_moves.append((r, c))
        else:
            # Check if the move captures any stones
            captured = 0
            visited = set()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                x_adj, y_adj = r + dx, c + dy
                adj_pos = (x_adj, y_adj)
                if adj_pos in opponent_set and adj_pos not in visited:
                    # Find the entire group
                    group = set()
                    queue = [adj_pos]
                    group.add(adj_pos)
                    visited.add(adj_pos)
                    while queue:
                        cell = queue.pop(0)
                        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            new_cell = (cell[0] + ddx, cell[1] + ddy)
                            if new_cell in opponent_set and new_cell not in group:
                                group.add(new_cell)
                                queue.append(new_cell)
                                visited.add(new_cell)
                    # Find group's liberties
                    group_liberties = set()
                    for (gr, gc) in group:
                        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            lib = (gr + ddx, gc + ddy)
                            if lib not in me_set and lib not in opponent_set:
                                group_liberties.add(lib)
                    # Check if placing this move captures the group
                    if (r, c) in group_liberties:
                        new_liberties = group_liberties - {(r, c)}
                        if not new_liberties:
                            captured += len(group)
            if captured > 0:
                valid_moves.append((r, c))
    
    if not valid_moves:
        return ((0, 0), memory)
    
    # Evaluate each valid move and compute scores
    best_score = float('-inf')
    best_move = (0, 0)
    for (r, c) in valid_moves:
        # Calculate score
        score = 0
        
        # Check captures
        captured = 0
        visited = set()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            x_adj, y_adj = r + dx, c + dy
            adj_pos = (x_adj, y_adj)
            if adj_pos in opponent_set and adj_pos not in visited:
                # Find the entire group
                group = set()
                queue = [adj_pos]
                group.add(adj_pos)
                visited.add(adj_pos)
                while queue:
                    cell = queue.pop(0)
                    for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        new_cell = (cell[0] + ddx, cell[1] + ddy)
                        if new_cell in opponent_set and new_cell not in group:
                            group.add(new_cell)
                            queue.append(new_cell)
                            visited.add(new_cell)
                # Find group's liberties
                group_liberties = set()
                for (gr, gc) in group:
                    for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        lib = (gr + ddx, gc + ddy)
                        if lib not in me_set and lib not in opponent_set:
                            group_liberties.add(lib)
                # Check if placing this move captures the group
                if (r, c) in group_liberties:
                    new_liberties = group_liberties - {(r, c)}
                    if not new_liberties:
                        captured += len(group)
        score += captured * 100
        
        # Count adjacent empty positions (liberties for the new stone)
        liberties_count = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            x, y = r + dx, c + dy
            if (x, y) not in me_set and (x, y) not in opponent_set:
                liberties_count += 1
        score += liberties_count * 10
        
        # Check if adjacent to opponent stones
        adjacent_opponent = any((r + dx, c + dy) in opponent_set for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
        if adjacent_opponent:
            score += 5
        
        # Check if adjacent to own stones
        adjacent_me = any((r + dx, c + dy) in me_set for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
        if adjacent_me:
            score += 5
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return (best_move, memory)
