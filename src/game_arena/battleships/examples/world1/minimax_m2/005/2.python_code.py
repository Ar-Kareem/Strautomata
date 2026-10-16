
import random

# Precompute the hunt sequence: all cells ordered by increasing row+col, then by row.
hunt_sequence = []
for s in range(0, 19):  # s is row+col, from 0 to 18 for 10x10 grid
    for r in range(10):
        c = s - r
        if 0 <= c < 10:
            hunt_sequence.append((r, c))

def policy(board):
    # Find all cells that have not been fired (value 0) and hit cells (value 1)
    not_fired = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
    hit_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]
    
    # If there are hit cells, find connected components using 4-adjacency
    if hit_cells:
        components = find_hit_components(board)
        targets = []
        for component in components:
            # Generate targets for this component
            if len(component) == 1:
                # Single hit: target all four adjacent cells
                r, c = list(component)[0]
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        targets.append((nr, nc))
            else:
                # Multiple hits: determine orientation
                rows = {r for r, c in component}
                cols = {c for r, c in component}
                if len(rows) == 1:  # Horizontal
                    row = rows.pop()
                    cols_list = sorted([c for r, c in component])
                    min_col, max_col = cols_list[0], cols_list[-1]
                    # Extend left
                    if min_col > 0 and board[row][min_col-1] == 0:
                        targets.append((row, min_col-1))
                    # Extend right
                    if max_col < 9 and board[row][max_col+1] == 0:
                        targets.append((row, max_col+1))
                else:  # Vertical
                    col = cols.pop()
                    rows_list = sorted([r for r, c in component])
                    min_row, max_row = rows_list[0], rows_list[-1]
                    # Extend up
                    if min_row > 0 and board[min_row-1][col] == 0:
                        targets.append((min_row-1, col))
                    # Extend down
                    if max_row < 9 and board[max_row+1][col] == 0:
                        targets.append((max_row+1, col))
        
        # If there are targets, choose one randomly
        if targets:
            return random.choice(targets)
    
    # No targets from hits, so use hunt sequence
    for cell in hunt_sequence:
        if board[cell[0]][cell[1]] == 0:
            return cell
    # If no cell found in hunt sequence (shouldn't happen), choose randomly from not fired
    return random.choice(not_fired)

def find_hit_components(board):
    # Find all hit cells
    hit_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]
    visited = set()
    components = []
    for cell in hit_cells:
        if cell not in visited:
            # BFS to find connected component
            component = set()
            queue = [cell]
            while queue:
                current = queue.pop(0)
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    r, c = current
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and (nr, nc) not in visited:
                            queue.append((nr, nc))
            components.append(component)
    return components
