
# Precompute the winning lines for 3x3x3 Tic Tac Toe
directions = [
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, -1, 0),
    (1, 0, 1), (1, 0, -1),
    (0, 1, 1), (0, 1, -1),
    (1, 1, 1), (1, 1, -1),
    (1, -1, 1), (1, -1, -1)
]

WIN_LINES = []

for dx, dy, dz in directions:
    for x0 in range(3):
        for y0 in range(3):
            for z0 in range(3):
                if (x0 - dx < 0) or (x0 - dx >= 3) or (y0 - dy < 0) or (y0 - dy >= 3) or (z0 - dz < 0) or (z0 - dz >= 3):
                    line = []
                    for t in range(3):
                        x = x0 + t * dx
                        y = y0 + t * dy
                        z = z0 + t * dz
                        if x < 0 or x >= 3 or y < 0 or y >= 3 or z < 0 or z >= 3:
                            break
                        line.append((x, y, z))
                    if len(line) == 3:
                        converted_line = [(z, x, y) for (x, y, z) in line]
                        WIN_LINES.append(tuple(converted_line))

corners = [
    (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
    (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
]

priority_cells = []
priority_cells.append((1, 1, 1))
priority_cells.extend(corners)

for z in range(3):
    for x in range(3):
        for y in range(3):
            cell = (z, x, y)
            if cell not in priority_cells:
                priority_cells.append(cell)

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    total_zeros = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    total_zeros += 1
    
    if total_zeros == 0:
        return (0, 0, 0)
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1
                    win = False
                    for line in WIN_LINES:
                        a, b, c = line
                        if board[a[0]][a[1]][a[2]] == board[b[0]][b[1]][b[2]] == board[c[0]][c[1]][c[2]] == 1:
                            win = True
                            break
                    if win:
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = -1
                    win = False
                    for line in WIN_LINES:
                        a, b, c = line
                        if board[a[0]][a[1]][a[2]] == board[b[0]][b[1]][b[2]] == board[c[0]][c[1]][c[2]] == -1:
                            win = True
                            break
                    if win:
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0
    
    for cell in priority_cells:
        z, x, y = cell
        if board[z][x][y] == 0:
            return cell
    
    return (0, 0, 0)
