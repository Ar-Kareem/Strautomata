
from collections import defaultdict

def generate_lines():
    lines = []

    # Axis-aligned lines
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])

    # Face diagonals (xy, xz, yz planes)
    for z in range(3):
        lines.append([(x, x, z) for x in range(3)])
        lines.append([(x, 2 - x, z) for x in range(3)])
    for y in range(3):
        lines.append([(x, y, x) for x in range(3)])
        lines.append([(x, y, 2 - x) for x in range(3)])
    for x in range(3):
        lines.append([(x, y, y) for y in range(3)])
        lines.append([(x, y, 2 - y) for y in range(3)])

    # Space diagonals
    lines.append([(x, x, x) for x in range(3)])
    lines.append([(x, x, 2 - x) for x in range(3)])
    lines.append([(x, 2 - x, x) for x in range(3)])
    lines.append([(x, 2 - x, 2 - x) for x in range(3)])

    return lines

all_lines = generate_lines()
cell_to_lines = defaultdict(list)
for line in all_lines:
    for cell in line:
        cell_to_lines[cell].append(line)

def policy(board):
    # Step 1: Check for immediate win
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    for line in cell_to_lines[(i, j, k)]:
                        count = 0
                        for (x, y, z) in line:
                            if (x, y, z) == (i, j, k):
                                continue
                            if board[x][y][z] == 1:
                                count += 1
                        if count == 2:
                            return (i, j, k)

    # Step 2: Block opponent's winning move
    threats = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    for line in cell_to_lines[(i, j, k)]:
                        count = 0
                        for (x, y, z) in line:
                            if (x, y, z) == (i, j, k):
                                continue
                            if board[x][y][z] == -1:
                                count += 1
                        if count == 2:
                            threats.append((i, j, k))
                            break

    if threats:
        best_cell = None
        best_score = -1
        for cell in threats:
            score = len(cell_to_lines[cell])
            if score > best_score or (score == best_score and best_cell is None):
                best_score = score
                best_cell = cell
        return best_cell

    # Step 3: Choose best move based on line count
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    best_move = None
    best_score = -1
    for cell in empty_cells:
        score = len(cell_to_lines[cell])
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = cell
    return best_move
