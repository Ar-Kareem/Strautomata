
def rotate_quadrant(board, quad, direction):
    """ Rotates the specified 3x3 quadrant in the given direction. """
    if direction == 'L':  # clockwise
        if quad == 0:
            temp = [board[0][0:3], board[1][0:3], board[2][0:3]]
            board[0][0:3] = [temp[2][0], temp[1][0], temp[0][0]]
            board[1][0:3] = [temp[2][1], temp[1][1], temp[0][1]]
            board[2][0:3] = [temp[2][2], temp[1][2], temp[0][2]]
        elif quad == 1:
            temp = [board[0][3:6], board[1][3:6], board[2][3:6]]
            board[0][3:6] = [temp[2][0], temp[1][0], temp[0][0]]
            board[1][3:6] = [temp[2][1], temp[1][1], temp[0][1]]
            board[2][3:6] = [temp[2][2], temp[1][2], temp[0][2]]
        elif quad == 2:
            temp = [board[3][0:3], board[4][0:3], board[5][0:3]]
            board[3][0:3] = [temp[2][0], temp[1][0], temp[0][0]]
            board[4][0:3] = [temp[2][1], temp[1][1], temp[0][1]]
            board[5][0:3] = [temp[2][2], temp[1][2], temp[0][2]]
        elif quad == 3:
            temp = [board[3][3:6], board[4][3:6], board[5][3:6]]
            board[3][3:6] = [temp[2][0], temp[1][0], temp[0][0]]
            board[4][3:6] = [temp[2][1], temp[1][1], temp[0][1]]
            board[5][3:6] = [temp[2][2], temp[1][2], temp[0][2]]

    elif direction == 'R':  # anticlockwise
        rotate_quadrant(board, quad, 'L')
        rotate_quadrant(board, quad, 'L')
        rotate_quadrant(board, quad, 'L')

def check_win(board):
    for r in range(6):
        for c in range(6):
            if board[r][c] == 1:
                # Check horizontal
                if c <= 1 and all(board[r][c + i] == 1 for i in range(5)):
                    return True
                # Check vertical
                if r <= 1 and all(board[r + i][c] == 1 for i in range(5)):
                    return True
                # Check diagonal \
                if r <= 1 and c <= 1 and all(board[r + i][c + i] == 1 for i in range(5)):
                    return True
                # Check diagonal /
                if r <= 1 and c >= 4 and all(board[r + i][c - i] == 1 for i in range(5)):
                    return True
    return False

def policy(you, opponent) -> str:
    empty_positions = [
        (r, c) 
        for r in range(6) 
        for c in range(6) 
        if you[r][c] == 0 and opponent[r][c] == 0
    ]
    
    for row, col in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate the move
                test_you = [row[:] for row in you]
                test_opponent = [row[:] for row in opponent]
                test_you[row][col] = 1
                
                # Test rotation
                board_after_rotation = [row[:] for row in test_you]
                rotate_quadrant(board_after_rotation, quad, direction)

                # Check if this move results in a win
                if check_win(board_after_rotation):
                    return f"{row + 1},{col + 1},{quad},{direction}"

    # If we can't win immediately, pick random placement and random quadrant/direction
    from random import choice
    row, col = choice(empty_positions)
    quad = choice(range(4))
    direction = choice(['L', 'R'])
    
    return f"{row + 1},{col + 1},{quad},{direction}"
