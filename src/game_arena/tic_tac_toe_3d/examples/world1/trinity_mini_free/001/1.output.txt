import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all 49 winning lines in 3x3x3 Tic Tac Toe
    lines = []
    # Rows (x varies, y and z fixed)
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    # Columns (y varies, x and z fixed)
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    # Pillars (z varies, x and y fixed)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    # Diagonals in xy-plane (fixed z)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    # Diagonals in xz-plane (fixed y)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    # Diagonals in yz-plane (fixed x)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # Find all empty cells
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    
    # Check for winning moves
    for cell in empty_cells:
        x, y, z = cell
        for line in lines:
            if cell in line:
                # Check if placing '1' here completes a winning line
                other_cells = [c for c in line if c != cell]
                if board[other_cells[0][0]][other_cells[0][1]][other_cells[0][2]] == 1 and \
                   board[other_cells[1][0]][other_cells[1][1]][other_cells[1][2]] == 1:
                    return (x, y, z)
    
    # Check for opponent's winning moves
    for cell in empty_cells:
        x, y, z = cell
        for line in lines:
            if cell in line:
                # Check if opponent can win by placing '-1' here
                other_cells = [c for c in line if c != cell]
                if board[other_cells[0][0]][other_cells[0][1]][other_cells[0][2]] == -1 and \
                   board[other_cells[1][0]][other_cells[1][1]][other_cells[1][2]] == -1:
                    return (x, y, z)
    
    # Choose a random empty cell if no immediate threats
    return random.choice(empty_cells)