
import random
import numpy as np

def policy(you, opponent) -> str:
    # Convert inputs to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)

    # Get all empty cells
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 0 and opp_board[r][c] == 0:
                empty_cells.append((r+1, c+1))

    # Check for immediate winning move
    for r, c in empty_cells:
        # Try placing our marble
        temp_you = you_board.copy()
        temp_you[r-1][c-1] = 1

        # Check all possible rotations
        for quad in range(4):
            for dir in ['L', 'R']:
                # Apply rotation
                rotated_you = rotate_board(temp_you, quad, dir)
                rotated_opp = rotate_board(opp_board, quad, dir)

                # Check if we win
                if check_win(rotated_you):
                    return f"{r},{c},{quad},{dir}"

    # Check for opponent's potential winning moves to block
    for r, c in empty_cells:
        # Try placing opponent's marble (simulate their move)
        temp_opp = opp_board.copy()
        temp_opp[r-1][c-1] = 1

        # Check all possible rotations
        for quad in range(4):
            for dir in ['L', 'R']:
                # Apply rotation
                rotated_you = rotate_board(you_board, quad, dir)
                rotated_opp = rotate_board(temp_opp, quad, dir)

                # Check if opponent would win
                if check_win(rotated_opp):
                    # Block by placing our marble here
                    # Now find best rotation to prevent opponent's win
                    for quad2 in range(4):
                        for dir2 in ['L', 'R']:
                            # Apply our rotation
                            rotated_you2 = rotate_board(you_board, quad2, dir2)
                            rotated_opp2 = rotate_board(opp_board, quad2, dir2)
                            rotated_opp2[r-1][c-1] = 1  # Place our marble

                            # Check if opponent still wins
                            if not check_win(rotated_opp2):
                                return f"{r},{c},{quad2},{dir2}"

    # If no immediate threats, play strategically
    # First try to place in center of quadrants
    center_moves = [(2,2), (2,5), (5,2), (5,5)]
    for r, c in center_moves:
        if (r, c) in empty_cells:
            # Try all rotations for this position
            for quad in range(4):
                for dir in ['L', 'R']:
                    # Apply rotation
                    rotated_you = rotate_board(you_board, quad, dir)
                    rotated_opp = rotate_board(opp_board, quad, dir)

                    # Check if we create a good position
                    if is_good_position(rotated_you, rotated_opp):
                        return f"{r},{c},{quad},{dir}"

    # If no center moves available, try to create lines of 4
    for r, c in empty_cells:
        # Try placing our marble
        temp_you = you_board.copy()
        temp_you[r-1][c-1] = 1

        # Check all possible rotations
        for quad in range(4):
            for dir in ['L', 'R']:
                # Apply rotation
                rotated_you = rotate_board(temp_you, quad, dir)
                rotated_opp = rotate_board(opp_board, quad, dir)

                # Check if we create a line of 4
                if has_line_of_4(rotated_you):
                    return f"{r},{c},{quad},{dir}"

    # If no good strategic moves, play randomly
    r, c = random.choice(empty_cells)
    quad = random.randint(0, 3)
    dir = random.choice(['L', 'R'])
    return f"{r},{c},{quad},{dir}"

def rotate_board(board, quad, direction):
    # Create a copy of the board
    rotated = board.copy()

    # Determine the quadrant boundaries
    if quad == 0:  # top-left
        rows = slice(0, 3)
        cols = slice(0, 3)
    elif quad == 1:  # top-right
        rows = slice(0, 3)
        cols = slice(3, 6)
    elif quad == 2:  # bottom-left
        rows = slice(3, 6)
        cols = slice(0, 3)
    else:  # bottom-right
        rows = slice(3, 6)
        cols = slice(3, 6)

    # Extract the quadrant
    quadrant = board[rows, cols]

    # Rotate the quadrant
    if direction == 'L':  # 90 degrees anticlockwise
        rotated_quad = np.rot90(quadrant, k=1)
    else:  # 90 degrees clockwise
        rotated_quad = np.rot90(quadrant, k=-1)

    # Put the rotated quadrant back
    rotated[rows, cols] = rotated_quad

    return rotated

def check_win(board):
    # Check rows
    for row in board:
        if np.sum(row) >= 5:
            return True

    # Check columns
    for col in range(6):
        if np.sum(board[:, col]) >= 5:
            return True

    # Check diagonals (top-left to bottom-right)
    for i in range(2):
        for j in range(2):
            if np.sum([board[i+k][j+k] for k in range(5) if i+k < 6 and j+k < 6]) >= 5:
                return True

    # Check diagonals (top-right to bottom-left)
    for i in range(2):
        for j in range(4, 6):
            if np.sum([board[i+k][j-k] for k in range(5) if i+k < 6 and j-k >= 0]) >= 5:
                return True

    return False

def has_line_of_4(board):
    # Check for lines of 4 (potential to become 5)
    # Check rows
    for row in board:
        for i in range(3):
            if np.sum(row[i:i+4]) == 4:
                return True

    # Check columns
    for col in range(6):
        for i in range(3):
            if np.sum(board[i:i+4, col]) == 4:
                return True

    # Check diagonals (top-left to bottom-right)
    for i in range(3):
        for j in range(3):
            if np.sum([board[i+k][j+k] for k in range(4)]) == 4:
                return True

    # Check diagonals (top-right to bottom-left)
    for i in range(3):
        for j in range(3, 6):
            if np.sum([board[i+k][j-k] for k in range(4)]) == 4:
                return True

    return False

def is_good_position(you_board, opp_board):
    # Simple heuristic: count potential lines of 3 or 4
    you_score = 0
    opp_score = 0

    # Check rows for you
    for row in you_board:
        for i in range(4):
            if np.sum(row[i:i+4]) >= 3:
                you_score += 1

    # Check rows for opponent
    for row in opp_board:
        for i in range(4):
            if np.sum(row[i:i+4]) >= 3:
                opp_score += 1

    # Check columns for you
    for col in range(6):
        for i in range(4):
            if np.sum(you_board[i:i+4, col]) >= 3:
                you_score += 1

    # Check columns for opponent
    for col in range(6):
        for i in range(4):
            if np.sum(opp_board[i:i+4, col]) >= 3:
                opp_score += 1

    # Check diagonals for you (top-left to bottom-right)
    for i in range(3):
        for j in range(3):
            if np.sum([you_board[i+k][j+k] for k in range(4)]) >= 3:
                you_score += 1

    # Check diagonals for opponent (top-left to bottom-right)
    for i in range(3):
        for j in range(3):
            if np.sum([opp_board[i+k][j+k] for k in range(4)]) >= 3:
                opp_score += 1

    # Check diagonals for you (top-right to bottom-left)
    for i in range(3):
        for j in range(3, 6):
            if np.sum([you_board[i+k][j-k] for k in range(4)]) >= 3:
                you_score += 1

    # Check diagonals for opponent (top-right to bottom-left)
    for i in range(3):
        for j in range(3, 6):
            if np.sum([opp_board[i+k][j-k] for k in range(4)]) >= 3:
                opp_score += 1

    return you_score > opp_score
