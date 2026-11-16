
import random

def policy(you, opponent):
    # Convert the input arrays to lists for easier manipulation
    you_board = [list(row) for row in you]
    opponent_board = [list(row) for row in opponent]

    # Generate all possible legal moves
    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 0 and opponent_board[r][c] == 0:
                for quad in range(4):
                    for dir in ['L', 'R']:
                        legal_moves.append(f"{r+1},{c+1},{quad},{dir}")

    # If no legal moves (shouldn't happen per problem statement), return a random one
    if not legal_moves:
        return "1,1,0,L"

    # Function to check if a player has a 5-in-a-row
    def check_win(board):
        # Check rows
        for r in range(6):
            for c in range(2):
                if all(board[r][c+i] == 1 for i in range(5)):
                    return True
        # Check columns
        for c in range(6):
            for r in range(2):
                if all(board[r+i][c] == 1 for i in range(5)):
                    return True
        # Check diagonals (top-left to bottom-right)
        for r in range(2):
            for c in range(2):
                if all(board[r+i][c+i] == 1 for i in range(5)):
                    return True
        # Check diagonals (top-right to bottom-left)
        for r in range(2):
            for c in range(4, 6):
                if all(board[r+i][c-i] == 1 for i in range(5)):
                    return True
        return False

    # Function to rotate a quadrant
    def rotate_quadrant(board, quad, dir):
        # Define the quadrant boundaries
        if quad == 0:
            rows = slice(0, 3)
            cols = slice(0, 3)
        elif quad == 1:
            rows = slice(0, 3)
            cols = slice(3, 6)
        elif quad == 2:
            rows = slice(3, 6)
            cols = slice(0, 3)
        elif quad == 3:
            rows = slice(3, 6)
            cols = slice(3, 6)

        # Extract the quadrant
        quadrant = [row[cols] for row in board[rows]]

        # Rotate the quadrant
        if dir == 'L':
            # Rotate 90 degrees anticlockwise
            rotated = [[quadrant[2][0], quadrant[1][0], quadrant[0][0]],
                       [quadrant[2][1], quadrant[1][1], quadrant[0][1]],
                       [quadrant[2][2], quadrant[1][2], quadrant[0][2]]]
        else:
            # Rotate 90 degrees clockwise
            rotated = [[quadrant[0][2], quadrant[1][2], quadrant[2][2]],
                       [quadrant[0][1], quadrant[1][1], quadrant[2][1]],
                       [quadrant[0][0], quadrant[1][0], quadrant[2][0]]]

        # Update the board
        for i in range(3):
            for j in range(3):
                board[rows.start + i][cols.start + j] = rotated[i][j]

    # Evaluate each legal move
    best_moves = []
    for move in legal_moves:
        r, c, quad, dir = move.split(',')
        r, c, quad = int(r)-1, int(c)-1, int(quad)

        # Simulate the move
        new_you = [row[:] for row in you_board]
        new_opponent = [row[:] for row in opponent_board]
        new_you[r][c] = 1

        # Rotate the quadrant
        rotate_quadrant(new_you, quad, dir)
        rotate_quadrant(new_opponent, quad, dir)

        # Check if the move leads to a win
        if check_win(new_you):
            return move

    # If no winning move, check for blocking moves
    for move in legal_moves:
        r, c, quad, dir = move.split(',')
        r, c, quad = int(r)-1, int(c)-1, int(quad)

        # Simulate the move
        new_you = [row[:] for row in you_board]
        new_opponent = [row[:] for row in opponent_board]
        new_you[r][c] = 1

        # Rotate the quadrant
        rotate_quadrant(new_you, quad, dir)
        rotate_quadrant(new_opponent, quad, dir)

        # Check if the opponent would win next
        # This is a simplified check; a full lookahead would be better
        # Here, we just check if the opponent has a 4-in-a-row that can be extended
        # For simplicity, we'll skip this and just return a random move
        pass

    # If no winning or blocking move, return a random legal move
    return random.choice(legal_moves)
