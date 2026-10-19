
import numpy as np
import random

def policy(you, opponent) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you)
    opponent_board = np.array(opponent)

    # Check for immediate winning move
    winning_move = find_winning_move(you_board, opponent_board)
    if winning_move:
        return winning_move

    # Check for opponent's near-win (4 in a row with empty space)
    opponent_near_win = find_opponent_near_win(you_board, opponent_board)
    if opponent_near_win:
        return opponent_near_win

    # Find the best move using a combination of placement and rotation
    best_move = None
    best_score = -float('inf')

    # Iterate over all empty positions
    for row in range(6):
        for col in range(6):
            if you_board[row][col] == 0 and opponent_board[row][col] == 0:
                # Try placing a marble here
                temp_you = you_board.copy()
                temp_you[row][col] = 1

                # Try all possible rotations for each quadrant
                for quad in range(4):
                    for direction in ['L', 'R']:
                        # Rotate the quadrant
                        rotated_you = rotate_quadrant(temp_you, quad, direction)
                        rotated_opponent = rotate_quadrant(opponent_board, quad, direction)

                        # Evaluate the new board state
                        score = evaluate_board(rotated_you, rotated_opponent)

                        # Update best move if this is better
                        if score > best_score:
                            best_score = score
                            best_move = f"{row+1},{col+1},{quad},{direction}"

    # If no strategic move found, place in a random empty position and rotate a random quadrant
    if not best_move:
        empty_positions = [(r, c) for r in range(6) for c in range(6) if you_board[r][c] == 0 and opponent_board[r][c] == 0]
        row, col = random.choice(empty_positions)
        quad = random.randint(0, 3)
        direction = random.choice(['L', 'R'])
        best_move = f"{row+1},{col+1},{quad},{direction}"

    return best_move

def find_winning_move(you_board, opponent_board):
    # Check all empty positions to see if placing a marble creates a 5-in-a-row
    for row in range(6):
        for col in range(6):
            if you_board[row][col] == 0 and opponent_board[row][col] == 0:
                temp_you = you_board.copy()
                temp_you[row][col] = 1

                # Check all possible rotations for each quadrant
                for quad in range(4):
                    for direction in ['L', 'R']:
                        rotated_you = rotate_quadrant(temp_you, quad, direction)
                        if has_five_in_a_row(rotated_you):
                            return f"{row+1},{col+1},{quad},{direction}"
    return None

def find_opponent_near_win(you_board, opponent_board):
    # Check for opponent's near-win (4 in a row with empty space)
    for row in range(6):
        for col in range(6):
            if opponent_board[row][col] == 0 and you_board[row][col] == 0:
                # Check horizontal
                if col >= 4:
                    if sum(opponent_board[row][col-4:col+1]) == 4:
                        temp_you = you_board.copy()
                        temp_you[row][col] = 1
                        for quad in range(4):
                            for direction in ['L', 'R']:
                                rotated_you = rotate_quadrant(temp_you, quad, direction)
                                return f"{row+1},{col+1},{quad},{direction}"
                # Check vertical
                if row >= 4:
                    if sum(opponent_board[row-4:row+1][col]) == 4:
                        temp_you = you_board.copy()
                        temp_you[row][col] = 1
                        for quad in range(4):
                            for direction in ['L', 'R']:
                                rotated_you = rotate_quadrant(temp_you, quad, direction)
                                return f"{row+1},{col+1},{quad},{direction}"
                # Check diagonal (top-left to bottom-right)
                if row >= 4 and col >= 4:
                    if sum(opponent_board[row-4:row+1][col-4:col+1].diagonal()) == 4:
                        temp_you = you_board.copy()
                        temp_you[row][col] = 1
                        for quad in range(4):
                            for direction in ['L', 'R']:
                                rotated_you = rotate_quadrant(temp_you, quad, direction)
                                return f"{row+1},{col+1},{quad},{direction}"
                # Check diagonal (top-right to bottom-left)
                if row >= 4 and col <= 1:
                    if sum(opponent_board[row-4:row+1][col:col+5][::-1].diagonal()) == 4:
                        temp_you = you_board.copy()
                        temp_you[row][col] = 1
                        for quad in range(4):
                            for direction in ['L', 'R']:
                                rotated_you = rotate_quadrant(temp_you, quad, direction)
                                return f"{row+1},{col+1},{quad},{direction}"
    return None

def rotate_quadrant(board, quad, direction):
    # Rotate the specified quadrant 90 degrees in the given direction
    rotated_board = board.copy()
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

    quadrant = rotated_board[rows, cols]
    if direction == 'L':
        quadrant = np.rot90(quadrant, k=-1)
    else:
        quadrant = np.rot90(quadrant, k=1)
    rotated_board[rows, cols] = quadrant
    return rotated_board

def has_five_in_a_row(board):
    # Check horizontal
    for row in range(6):
        for col in range(2):
            if sum(board[row, col:col+5]) == 5:
                return True
    # Check vertical
    for col in range(6):
        for row in range(2):
            if sum(board[row:row+5, col]) == 5:
                return True
    # Check diagonal (top-left to bottom-right)
    for row in range(2):
        for col in range(2):
            if sum(board.diagonal(row, col)[:5]) == 5:
                return True
    # Check diagonal (top-right to bottom-left)
    for row in range(2):
        for col in range(4, 6):
            if sum(board[row:row+5, col][::-1]) == 5:
                return True
    return False

def evaluate_board(you_board, opponent_board):
    # Evaluate the board state by counting potential lines
    score = 0

    # Count potential lines for you
    for row in range(6):
        for col in range(2):
            line = you_board[row, col:col+5]
            score += count_potential_lines(line)

    for col in range(6):
        for row in range(2):
            line = you_board[row:row+5, col]
            score += count_potential_lines(line)

    for row in range(2):
        for col in range(2):
            line = you_board.diagonal(row, col)[:5]
            score += count_potential_lines(line)

    for row in range(2):
        for col in range(4, 6):
            line = you_board[row:row+5, col][::-1]
            score += count_potential_lines(line)

    # Subtract opponent's potential lines
    for row in range(6):
        for col in range(2):
            line = opponent_board[row, col:col+5]
            score -= count_potential_lines(line)

    for col in range(6):
        for row in range(2):
            line = opponent_board[row:row+5, col]
            score -= count_potential_lines(line)

    for row in range(2):
        for col in range(2):
            line = opponent_board.diagonal(row, col)[:5]
            score -= count_potential_lines(line)

    for row in range(2):
        for col in range(4, 6):
            line = opponent_board[row:row+5, col][::-1]
            score -= count_potential_lines(line)

    return score

def count_potential_lines(line):
    # Count potential lines based on consecutive marbles
    count = 0
    consecutive = 0
    for marble in line:
        if marble == 1:
            consecutive += 1
            count += consecutive
        else:
            consecutive = 0
    return count
