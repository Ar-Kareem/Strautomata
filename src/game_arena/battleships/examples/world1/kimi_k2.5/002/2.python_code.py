
def policy(board):
    rows, cols = 10, 10
    # Standard ship set
    remaining_ships = [5, 4, 3, 3, 2]
    
    # --- 1. Detect Sunk Ships to update remaining_ships ---
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1 and not visited[r][c]:
                # Find connected component of hits
                stack = [(r, c)]
                visited[r][c] = True
                component = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                            component.append((nr, nc))
                
                n = len(component)
                if n > 1:
                    rs = [cell[0] for cell in component]
                    cs = [cell[1] for cell in component]
                    # Check if horizontal and bounded
                    if len(set(rs)) == 1:
                        row = rs[0]
                        min_c, max_c = min(cs), max(cs)
                        left_blocked = (min_c == 0) or (board[row][min_c - 1] == -1)
                        right_blocked = (max_c == 9) or (board[row][max_c + 1] == -1)
                        if left_blocked and right_blocked and n in remaining_ships:
                            remaining_ships.remove(n)
                    # Check if vertical and bounded
                    elif len(set(cs)) == 1:
                        col = cs[0]
                        min_r, max_r = min(rs), max(rs)
                        top_blocked = (min_r == 0) or (board[min_r - 1][col] == -1)
                        bottom_blocked = (max_r == 9) or (board[max_r + 1][col] == -1)
                        if top_blocked and bottom_blocked and n in remaining_ships:
                            remaining_ships.remove(n)
                # Note: Single-cell components cannot be confirmed sunk (min ship len is 2)
    
    # --- 2. Calculate Targeting Bonuses ---
    bonus = [[0 for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1:
                # Check if part of horizontal line
                is_horizontal = False
                if c > 0 and board[r][c-1] == 1:
                    is_horizontal = True
                if c < 9 and board[r][c+1] == 1:
                    is_horizontal = True
                
                if is_horizontal:
                    # Extend left
                    if c > 0 and board[r][c-1] == 0:
                        bonus[r][c-1] += 1000
                    # Extend right
                    if c < 9 and board[r][c+1] == 0:
                        bonus[r][c+1] += 1000
                else:
                    # Check if part of vertical line
                    is_vertical = False
                    if r > 0 and board[r-1][c] == 1:
                        is_vertical = True
                    if r < 9 and board[r+1][c] == 1:
                        is_vertical = True
                    
                    if is_vertical:
                        # Extend up
                        if r > 0 and board[r-1][c] == 0:
                            bonus[r-1][c] += 1000
                        # Extend down
                        if r < 9 and board[r+1][c] == 0:
                            bonus[r+1][c] += 1000
                    else:
                        # Isolated hit - explore all 4 directions
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 0:
                                bonus[nr][nc] += 100
    
    # --- 3. Calculate Hunt Scores and select best move ---
    best_score = -1
    best_moves = []
    
    for r in range(rows):
        for c in range(cols):
            if board[r][c] != 0:
                continue
            
            score = bonus[r][c]
            
            # Count valid horizontal placements covering (r,c)
            for L in remaining_ships:
                count = 0
                min_c0 = max(0, c - L + 1)
                max_c0 = min(c, cols - L)
                for c0 in range(min_c0, max_c0 + 1):
                    valid = True
                    for k in range(c0, c0 + L):
                        if board[r][k] == -1:
                            valid = False
                            break
                    if valid:
                        count += 1
                score += count
            
            # Count valid vertical placements covering (r,c)
            for L in remaining_ships:
                count = 0
                min_r0 = max(0, r - L + 1)
                max_r0 = min(r, rows - L)
                for r0 in range(min_r0, max_r0 + 1):
                    valid = True
                    for k in range(r0, r0 + L):
                        if board[k][c] == -1:
                            valid = False
                            break
                    if valid:
                        count += 1
                score += count
            
            # Parity preference (checkerboard)
            if (r + c) % 2 == 0:
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif abs(score - best_score) < 1e-6:
                best_moves.append((r, c))
    
    if best_moves:
        return best_moves[0]
    
    # Fallback (should not happen)
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
