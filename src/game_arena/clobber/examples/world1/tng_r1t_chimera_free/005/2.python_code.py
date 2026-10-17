
def policy(you: list[int], opponent: list[int]) -> str:
    moves = []
    rows = 5
    cols = 6
    directions = [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]
    
    for row in range(rows):
        for col in range(cols):
            if you[row][col] != 1:
                continue
            for dir_label, dr, dc in directions:
                new_row = row + dr
                new_col = col + dc
                if 0 <= new_row < rows and 0 <= new_col < cols:
                    if opponent[new_row][new_col] == 1:
                        moves.append((row, col, dir_label, new_row, new_col))
    
    scored_moves = []
    for move in moves:
        s_row, s_col, dir_label, t_row, t_col = move
        # Calculate position score
        is_corner = (t_row in (0, rows-1)) and (t_col in (0, cols-1))
        is_edge = not is_corner and (t_row in (0, rows-1) or t_col in (0, cols-1))
        pos_score = 3 if is_corner else 2 if is_edge else 1
        
        # Count adjacent opponent pieces
        adj_count = 0
        for _, dr, dc in directions:
            adj_r = t_row + dr
            adj_c = t_col + dc
            if 0 <= adj_r < rows and 0 <= adj_c < cols:
                adj_count += opponent[adj_r][adj_c]
        
        score = pos_score * 10 + (4 - adj_count)
        scored_moves.append((score, move))
    
    # Sort by descending score, then row, column, direction
    scored_moves.sort(key=lambda x: (-x[0], x[1][0], x[1][1], x[1][2]))
    best = scored_moves[0][1]
    return f"{best[0]},{best[1]},{best[2]}"
