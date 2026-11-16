
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert lists to sets for efficient lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Define hexagonal adjacency (6 neighbors per cell)
    def get_neighbors(i, j):
        neighbors = []
        # Hex grid adjacency: 6 directions
        dirs = [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1), (0, -1)]
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < 11 and 0 <= nj < 11:
                neighbors.append((ni, nj))
        return neighbors

    # Find connected components using BFS
    def find_components(stones):
        visited = set()
        components = []
        for stone in stones:
            if stone not in visited:
                comp = []
                stack = [stone]
                visited.add(stone)
                while stack:
                    cell = stack.pop()
                    comp.append(cell)
                    for neighbor in get_neighbors(*cell):
                        if neighbor in stones and neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
                components.append(comp)
        return components

    # Check if a component touches goal lines
    def touches_goal(comp):
        if color == 'b':  # Black connects top/bottom
            return any(cell[0] == 0 for cell in comp) and any(cell[0] == 10 for cell in comp)
        else:  # White connects left/right
            return any(cell[1] == 0 for cell in comp) and any(cell[1] == 10 for cell in comp)

    # Generate all empty cells
    empty_cells = [(i, j) for i in range(11) for j in range(11) 
                  if (i, j) not in me_set and (i, j) not in opp_set]
    
    best_move = None
    best_score = -float('inf')
    
    for move in empty_cells:
        # Simulate placing the stone
        new_me = me_set | {move}
        
        # Check for immediate win
        if touches_goal(find_components(new_me)[0]):
            return move
        
        # Calculate heuristic score
        components = find_components(new_me)
        score = 0
        for comp in components:
            if touches_goal(comp):
                score += 2  # Bonus for connecting goal lines
            else:
                # Count stones touching goal lines
                top_bottom = any(cell[0] == 0 or cell[0] == 10 for cell in comp)
                left_right = any(cell[1] == 0 or cell[1] == 10 for cell in comp)
                score += top_bottom + left_right
        
        # Prefer moves that block opponent's threats
        opp_components = find_components(opp_set)
        for comp in opp_components:
            if touches_goal(comp):
                score -= 1  # Penalty for opponent's winning threat
        
        # Select best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
