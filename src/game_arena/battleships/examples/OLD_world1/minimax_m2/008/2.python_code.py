
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Precompute pattern for hunt mode: checkerboard pattern
    pattern = []
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 0:
                pattern.append((r, c))
    
    # Build connected components of hits (using 4-connectivity)
    visited = set()
    components = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and (r, c) not in visited:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    comp.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and (nr, nc) not in visited:
                            stack.append((nr, nc))
                components.append(comp)
    
    # Sort components by size (descending)
    components.sort(key=len, reverse=True)
    
    # Target mode: process each component
    for comp in components:
        if len(comp) >= 2:
            rows = [r for r, c in comp]
            cols = [c for r, c in comp]
            if all(r == rows[0] for r in rows):
                row = rows[0]
                min_col = min(cols)
                max_col = max(cols)
                for delta in range(1, 10):
                    new_col = min_col - delta
                    if new_col < 0:
                        break
                    if board[row][new_col] == 0:
                        return (row, new_col)
                    else:
                        break
                for delta in range(1, 10):
                    new_col = max_col + delta
                    if new_col >= 10:
                        break
                    if board[row][new_col] == 0:
                        return (row, new_col)
                    else:
                        break
            elif all(c == cols[0] for c in cols):
                col = cols[0]
                min_row = min(rows)
                max_row = max(rows)
                for delta in range(1, 10):
                    new_row = min_row - delta
                    if new_row < 0:
                        break
                    if board[new_row][col] == 0:
                        return (new_row, col)
                    else:
                        break
                for delta in range(1, 10):
                    new_row = max_row + delta
                    if new_row >= 10:
                        break
                    if board[new_row][col] == 0:
                        return (new_row, col)
                    else:
                        break
            else:
                continue
        else:
            r, c = comp[0]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Hunt mode: use pattern
    for (r, c) in pattern:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback: scan grid for first 0
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
