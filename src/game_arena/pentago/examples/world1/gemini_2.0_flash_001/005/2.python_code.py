
import random
import numpy as np

def check_win(board):
    """Checks for 5-in-a-row (win) on the board."""
    n = 6
    # Check horizontal
    for r in range(n):
        for c in range(n - 4):
            if board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3] == board[r][c+4] and board[r][c] != 0:
                return True

    # Check vertical
    for r in range(n - 4):
        for c in range(n):
            if board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c] == board[r+4][c] and board[r][c] != 0:
                return True

    # Check diagonals (top-left to bottom-right)
    for r in range(n - 4):
        for c in range(n - 4):
            if board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3] == board[r+4][c+4] and board[r][c] != 0:
                return True

    # Check diagonals (top-right to bottom-left)
    for r in range(n - 4):
        for c in range(4, n):
            if board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3] == board[r+4][c-4] and board[r][c] != 0:
                return True

    return False

def rotate_quadrant(board, quad, direction):
    """Rotates the specified quadrant in the given direction."""
    new_board = np.copy(board)
    if quad == 0:
        subgrid = board[0:3, 0:3]
        if direction == 'R':
            rotated_subgrid = np.rot90(subgrid, k=-1)  # Clockwise
        else:
            rotated_subgrid = np.rot90(subgrid, k=1)  # Anticlockwise
        new_board[0:3, 0:3] = rotated_subgrid
    elif quad == 1:
        subgrid = board[0:3, 3:6]
        if direction == 'R':
            rotated_subgrid = np.rot90(subgrid, k=-1)
        else:
            rotated_subgrid = np.rot90(subgrid, k=1)
        new_board[0:3, 3:6] = rotated_subgrid
    elif quad == 2:
        subgrid = board[3:6, 0:3]
        if direction == 'R':
            rotated_subgrid = np.rot90(subgrid, k=-1)
        else:
            rotated_subgrid = np.rot90(subgrid, k=1)
        new_board[3:6, 0:3] = rotated_subgrid
    elif quad == 3:
        subgrid = board[3:6, 3:6]
        if direction == 'R':
            rotated_subgrid = np.rot90(subgrid, k=-1)
        else:
            rotated_subgrid = np.rot90(subgrid, k=1)
        new_board[3:6, 3:6] = rotated_subgrid
    return new_board

def evaluate_board(you, opponent):
    """Evaluates the board state based on potential lines."""
    score = 0
    my_board = np.copy(you)
    opponent_board = np.copy(opponent)

    # Combine for easier checking
    combined_board = np.zeros((6, 6))
    combined_board[my_board == 1] = 1
    combined_board[opponent_board == 1] = -1

    # Evaluate horizontal lines
    for r in range(6):
        for c in range(2):
            line = combined_board[r, c:c+5]
            score += evaluate_line(line)

    # Evaluate vertical lines
    for c in range(6):
        for r in range(2):
            line = combined_board[r:r+5, c]
            score += evaluate_line(line)

    # Evaluate diagonals (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            line = np.diag(combined_board[r:r+5, c:c+5])
            score += evaluate_line(line)

    # Evaluate diagonals (top-right to bottom-left)
    for r in range(2):
        for c in range(4, 6):
            line = np.diag(np.fliplr(combined_board[r:r+5, c-4:c+1]))
            score += evaluate_line(line)

    return score

def evaluate_line(line):
    """Helper function to evaluate a single line of 5."""
    my_count = np.sum(line == 1)
    opponent_count = np.sum(line == -1)

    if my_count == 4 and opponent_count == 0:
        return 100  # Near win
    elif my_count == 3 and opponent_count == 0:
        return 10 # Potential
    elif opponent_count == 4 and my_count == 0:
        return -100  # Near loss
    elif opponent_count == 3 and my_count == 0:
        return -10
    return 0

def policy(you, opponent) -> str:
    """Chooses the next move."""
    my_board = np.array(you)
    opponent_board = np.array(opponent)
    empty_cells = np.where((my_board == 0) & (opponent_board == 0))
    empty_cells = list(zip(empty_cells[0], empty_cells[1]))

    best_move = None
    best_score = float('-inf')

    for row, col in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Create a hypothetical board state
                temp_my_board = np.copy(my_board)
                temp_my_board[row, col] = 1
                temp_opponent_board = np.copy(opponent_board)

                rotated_my_board = rotate_quadrant(temp_my_board, quad, direction)
                rotated_opponent_board = rotate_quadrant(temp_opponent_board, quad, direction)

                # Check if the move results in a win
                combined_board = np.zeros((6,6))
                combined_board[rotated_my_board == 1] = 1
                combined_board[rotated_opponent_board == 1] = -1

                if check_win(combined_board == 1):
                    return f"{row+1},{col+1},{quad},{direction}" # Immediately return the winning move

                # Evaluate the move
                score = evaluate_board(rotated_my_board, rotated_opponent_board)


                if score > best_score:
                    best_score = score
                    best_move = f"{row+1},{col+1},{quad},{direction}"

    #If no winning move, return best move
    if best_move is not None:
        return best_move

    #If no best move, make a random legal move:
    row, col = random.choice(empty_cells)
    quad = random.randint(0, 3)
    direction = random.choice(['L', 'R'])
    return f"{row+1},{col+1},{quad},{direction}"
