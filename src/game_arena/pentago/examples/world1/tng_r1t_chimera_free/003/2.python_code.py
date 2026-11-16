
import copy

def has_five(board):
    """Check if the board has five consecutive 1's in any line."""
    # Check rows
    for row in range(6):
        for col in range(2):
            if all(board[row][col + i] for i in range(5)):
                return True
    # Check columns
    for col in range(6):
        for row in range(2):
            if all(board[row + i][col] for i in range(5)):
                return True
    # Check diagonals (top-left to bottom-right)
    for row in range(2):
        for col in range(2):
            if all(board[row + i][col + i] for i in range(5)):
                return True
    # Check diagonals (top-right to bottom-left)
    for row in range(2):
        for col in range(4, 6):
            if all(board[row + i][col - i] for i in range(5)):
                return True
    return False

def rotate_quadrant(board, quad, direction):
    """Rotate the specified quadrant of the board in-place."""
    top = 0 if quad in (0, 1) else 3
    left = 0 if quad in (0, 2) else 3
    q = [[board[top + i][left + j] for j in range(3)] for i in range(3)]
    if direction == 'R':
        rotated = list(zip(*q[::-1]))  # Clockwise
    else:
        rotated = list(zip(*q))[::-1]  # Anticlockwise
    for i in range(3):
        for j in range(3):
            board[top + i][left + j] = rotated[i][j]

def policy(you, opponent):
    # Check all possible moves for a winning play
    for r in range(6):
        for c in range(6):
            if you[r][c] or opponent[r][c]:
                continue
            # Simulate placing a marble at (r, c)
            new_you = [row.copy() for row in you]
            new_you[r][c] = 1
            for quad in range(4):
                for direction in ['L', 'R']:
                    temp_you = [row.copy() for row in new_you]
                    temp_opponent = [row.copy() for row in opponent]
                    rotate_quadrant(temp_you, quad, direction)
                    rotate_quadrant(temp_opponent, quad, direction)
                    if has_five(temp_you):
                        return f"{r+1},{c+1},{quad},{direction}"
    
    # No winning move found; select the most central empty cell
    empty = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                dist = (r - 2.5)**2 + (c - 2.5)**2  # Distance from center
                empty.append( (dist, r, c) )
    empty.sort()
    best_r, best_c = empty[0][1], empty[0][2]
    
    # Determine quadrant of the chosen cell
    quad = 0
    if best_r >= 3:
        quad += 2
    if best_c >= 3:
        quad += 1
    
    return f"{best_r+1},{best_c+1},{quad},R"
