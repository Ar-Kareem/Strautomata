
import random
from collections import deque

def policy(board) -> str:
    def get_line_cells(x, y, dx, dy):
        cells = []
        i, j = x, y
        while 0 <= i < 8 and 0 <= j < 8:
            cells.append( (i,j) )
            i += dx
            j += dy
        i, j = x - dx, y - dy
        while 0 <= i < 8 and 0 <= j < 8:
            cells.insert(0, (i,j))
            i -= dx
            j -= dy
        return cells

    def count_connected_components(b, player):
        visited = set()
        count = 0
        for i in range(8):
            for j in range(8):
                if b[i][j] == player and (i,j) not in visited:
                    queue = deque()
                    queue.append( (i,j) )
                    visited.add( (i,j) )
                    while queue:
                        x, y = queue.popleft()
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1):
                                if dx == 0 and dy == 0:
                                    continue
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < 8 and 0 <= ny < 8:
                                    if b[nx][ny] == player and (nx, ny) not in visited:
                                        visited.add( (nx, ny) )
                                        queue.append( (nx, ny) )
                    count += 1
        return count

    moves = []
    directions = [ (0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1) ]
    for x in range(8):
        for y in range(8):
            if board[x][y] != 1:
                continue
            for dx, dy in directions:
                line_cells = get_line_cells(x, y, dx, dy)
                count = sum(1 for (i,j) in line_cells if board[i][j] != 0)
                if count == 0:
                    continue
                tx = x + dx * count
                ty = y + dy * count
                if not (0 <= tx < 8 and 0 <= ty < 8):
                    continue
                blocked = False
                for step in range(1, count):
                    cx = x + dx * step
                    cy = y + dy * step
                    if board[cx][cy] == -1:
                        blocked = True
                        break
                if blocked or board[tx][ty] == 1:
                    continue
                moves.append( (x, y, tx, ty) )

    if not moves:
        return ""
    
    best_score = -float('inf')
    best_moves = []
    for (fx, fy, tx, ty) in moves:
        new_board = [row[:] for row in board]
        new_board[fx][fy] = 0
        capture = new_board[tx][ty] == -1
        new_board[tx][ty] = 1
        
        my_cc = count_connected_components(new_board, 1)
        if my_cc == 1:
            return f"{fx},{fy}:{tx},{ty}"
        
        opp_cc = count_connected_components(new_board, -1)
        score = 1000//my_cc + 100*opp_cc + 200*capture
        
        if score > best_score:
            best_score = score
            best_moves = [(fx, fy, tx, ty)]
        elif score == best_score:
            best_moves.append( (fx, fy, tx, ty) )
    
    chosen = random.choice(best_moves)
    return f"{chosen[0]},{chosen[1]}:{chosen[2]},{chosen[3]}"
