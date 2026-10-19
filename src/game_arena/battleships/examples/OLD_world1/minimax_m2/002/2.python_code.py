
from collections import deque

def policy(board):
    center_r, center_c = 4.5, 4.5
    has_hit = False
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                has_hit = True
                break
        if has_hit:
            break
            
    if has_hit:
        visited = [[False] * 10 for _ in range(10)]
        components = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 1 and not visited[r][c]:
                    component = []
                    queue = deque([(r, c)])
                    visited[r][c] = True
                    while queue:
                        x, y = queue.popleft()
                        component.append((x, y))
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 10 and 0 <= ny < 10 and not visited[nx][ny] and board[nx][ny] == 1:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                    components.append(component)
                    
        best_component = None
        best_candidates = []
        best_score = -1
        
        for comp in components:
            if len(comp) == 1:
                r, c = comp[0]
                candidate_cells = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        candidate_cells.append((nr, nc))
                if candidate_cells:
                    score = len(comp)
                    if score > best_score:
                        best_score = score
                        best_component = comp
                        best_candidates = candidate_cells
            else:
                rows = [r for r, c in comp]
                cols = [c for r, c in comp]
                if len(set(rows)) == 1:
                    r_val = rows[0]
                    c1 = min(cols)
                    c2 = max(cols)
                    candidate_cells = []
                    if c1 > 0 and board[r_val][c1 - 1] == 0:
                        candidate_cells.append((r_val, c1 - 1))
                    if c2 < 9 and board[r_val][c2 + 1] == 0:
                        candidate_cells.append((r_val, c2 + 1))
                    if candidate_cells:
                        score = len(comp)
                        if score > best_score:
                            best_score = score
                            best_component = comp
                            best_candidates = candidate_cells
                elif len(set(cols)) == 1:
                    c_val = cols[0]
                    r1 = min(rows)
                    r2 = max(rows)
                    candidate_cells = []
                    if r1 > 0 and board[r1 - 1][c_val] == 0:
                        candidate_cells.append((r1 - 1, c_val))
                    if r2 < 9 and board[r2 + 1][c_val] == 0:
                        candidate_cells.append((r2 + 1, c_val))
                    if candidate_cells:
                        score = len(comp)
                        if score > best_score:
                            best_score = score
                            best_component = comp
                            best_candidates = candidate_cells
                            
        if best_component is not None:
            best_target = None
            best_dist = float('inf')
            for (r, c) in best_candidates:
                dist = (r - center_r)**2 + (c - center_c)**2
                if dist < best_dist:
                    best_dist = dist
                    best_target = (r, c)
            if best_target is not None:
                return best_target
                
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0 and (r + c) % 2 == 0:
                return (r, c)
                
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
                
    return (0, 0)
