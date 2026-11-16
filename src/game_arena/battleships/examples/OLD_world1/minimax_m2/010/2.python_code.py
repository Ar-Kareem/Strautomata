
# Precomputed hunt pattern and total order for firing
HUNT_PATTERN = [
    (0,0), (0,3), (0,6), (0,9),
    (1,1), (1,4), (1,7),
    (2,2), (2,5), (2,8),
    (3,0), (3,3), (3,6), (3,9),
    (4,1), (4,4), (4,7),
    (5,2), (5,5), (5,8),
    (6,0), (6,3), (6,6), (6,9),
    (7,1), (7,4), (7,7),
    (8,2), (8,5), (8,8),
    (9,0), (9,3), (9,6), (9,9)
]

ALL_CELLS = [(r, c) for r in range(10) for c in range(10)]
HUNT_PATTERN_SET = set(HUNT_PATTERN)
TOTAL_ORDER = HUNT_PATTERN + [cell for cell in ALL_CELLS if cell not in HUNT_PATTERN_SET]

def policy(board: list[list[int]]) -> tuple[int, int]:
    visited = [[False]*10 for _ in range(10)]
    ships = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and not visited[r][c]:
                queue = [(r, c)]
                visited[r][c] = True
                ship = [(r, c)]
                orientation = None
                
                while queue:
                    x, y = queue.pop()
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 10 and 0 <= ny < 10 and not visited[nx][ny] and board[nx][ny] == 1:
                            if orientation is None:
                                if nx == x or ny == y:
                                    orientation = 'horizontal' if nx == x else 'vertical'
                                    visited[nx][ny] = True
                                    ship.append((nx, ny))
                                    queue.append((nx, ny))
                            else:
                                if orientation == 'horizontal' and nx == x:
                                    visited[nx][ny] = True
                                    ship.append((nx, ny))
                                    queue.append((nx, ny))
                                elif orientation == 'vertical' and ny == y:
                                    visited[nx][ny] = True
                                    ship.append((nx, ny))
                                    queue.append((nx, ny))
                
                ships.append(ship)
    
    candidate_list = []
    for ship in ships:
        if len(ship) == 5:
            continue
        if len(ship) == 1:
            r0, c0 = ship[0]
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r0+dr, c0+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidate_list.append((len(ship), (nr, nc)))
        else:
            rows = [cell[0] for cell in ship]
            cols = [cell[1] for cell in ship]
            if all(x == rows[0] for x in rows):
                r = rows[0]
                min_c = min(cols)
                max_c = max(cols)
                if min_c - 1 >= 0 and board[r][min_c-1] == 0:
                    candidate_list.append((len(ship), (r, min_c-1)))
                if max_c + 1 < 10 and board[r][max_c+1] == 0:
                    candidate_list.append((len(ship), (r, max_c+1)))
            elif all(x == cols[0] for x in cols):
                c = cols[0]
                min_r = min(rows)
                max_r = max(rows)
                if min_r - 1 >= 0 and board[min_r-1][c] == 0:
                    candidate_list.append((len(ship), (min_r-1, c)))
                if max_r + 1 < 10 and board[max_r+1][c] == 0:
                    candidate_list.append((len(ship), (max_r+1, c)))
    
    if candidate_list:
        candidate_list.sort(key=lambda x: x[0], reverse=True)
        return candidate_list[0][1]
    
    fired_cells = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:
                fired_cells.add((r, c))
    
    for cell in TOTAL_ORDER:
        if cell not in fired_cells:
            return cell
    
    return (0, 0)
