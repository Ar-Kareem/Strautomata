
import random

# Define all winning sets for 3x3x3 Tic Tac Toe
win_sets = []

# Straight lines in x-direction (fixed y, z, vary x)
for y in range(3):
    for z in range(3):
        win_sets.append([(x, y, z) for x in range(3)])

# Straight lines in y-direction (fixed x, z, vary y)
for x in range(3):
    for z in range(3):
        win_sets.append([(x, y, z) for y in range(3)])

# Straight lines in z-direction (fixed x, y, vary z)
for x in range(3):
    for y in range(3):
        win_sets.append([(x, y, z) for z in range(3)])

# Diagonals in XY planes (fixed z)
for z in range(3):
    win_sets.append([(i, i, z) for i in range(3)])  # Major diagonal (x=y)
    win_sets.append([(i, 2 - i, z) for i in range(3)])  # Other diagonal (x+y=2)

# Diagonals in XZ planes (fixed y)
for y in range(3):
    win_sets.append([(i, y, i) for i in range(3)])  # Major (x=z)
    win_sets.append([(i, y, 2 - i) for i in range(3)])  # Other (x+z=2)

# Diagonals in YZ planes (fixed x)
for x in range(3):
    win_sets.append([(x, i, i) for i in range(3)])  # Major (y=z)
    win_sets.append([(x, i, 2 - i) for i in range(3)])  # Other (y+z=2)

# Space diagonals
win_sets.append([(i, i, i) for i in range(3)])  # x=y=z
win_sets.append([(i, i, 2 - i) for i in range(3)])  # x=y, z=2-i
win_sets.append([(i, 2 - i, i) for i in range(3)])  # x=z, y=2-i
win_sets.append([(2 - i, i, i) for i in range(3)])  # y=z, x=2-i

def is_win(board, p):
    return any(sum(board[x][y][z] for x, y, z in line) == 3 * p for line in win_sets)

def policy(board):
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    
    if not empty_cells:
        return None  # Though should not happen
    
    def check_win_after_place(x, y, z, p):
        board[x][y][z] = p
        win = is_win(board, p)
        board[x][y][z] = 0
        return win
    
    # Check for winning move
    for x, y, z in empty_cells:
        if check_win_after_place(x, y, z, 1):
            return (x, y, z)
    
    # Check for blocking move
    for x, y, z in empty_cells:
        if check_win_after_place(x, y, z, -1):
            return (x, y, z)
    
    # Prefer center if available
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)
    
    # Otherwise, random choice
    return random.choice(empty_cells)
