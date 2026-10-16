
import numpy as np

def has_winning_line(board, player):
    # Check all rows, columns, and diagonals for a winning line
    for i in range(6):
        for j in range(2):
            # Check rows
            if np.sum(board[i, j:j+5]) == player * 5:
                return True
            # Check columns
            if np.sum(board[j:j+5, i]) == player * 5:
                return True
            
    # Check diagonals
    for i in range(3):
        for j in range(3):
            if np.sum(board[i:i+5, j:j+5].diagonal()) == player * 5 or\
               np.sum(np.fliplr(board[i:i+5, j:j+5]).diagonal()) == player * 5:
                return True
    return False

def simulate_move(board, marble_position, quadrant, direction):
    # Simulate placing a marble and rotating a quadrant
    new_board = board.copy()
    r, c = marble_position
    new_board[r, c] = 1  # Place our marble
    
    # Rotate the specified quadrant
    if direction == 'L':
        # Rotate left (90 degrees anticlockwise)
        new_board[quadrant*3:quadrant*3+3, :] = np.rot90(new_board[quadrant*3:quadrant*3+3, :])
    elif direction == 'R':
        # Rotate right (90 degrees clockwise)
        new_board[quadrant*3:quadrant*3+3, :] = np.rot90(new_board[quadrant*3:quadrant*3+3, :], -1)

    return new_board

def get_empty_positions(board):
    positions = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # Empty cell
                positions.append((r, c))
    return positions

def policy(you, opponent) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    board = you + opponent  # Combine the boards to evaluate
    
    # Check for winning moves
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # For each empty cell, check winning move
                # Try placing my marble
                new_board = simulate_move(board, (r, c), 0, 'L')  # Placeholder for quadrant and direction
                if has_winning_line(new_board, 1):  # 1 represents us
                    return f"{r+1},{c+1},0,L"  # Return a winning move (placeholder quadrant & direction)

    # If no winning move, look for blocking moves
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # Check empty cells
                new_board = simulate_move(board, (r, c), 0, 'L')  # Placeholder for quadrant and direction
                if has_winning_line(new_board, 2):  # 2 represents opponent
                    return f"{r+1},{c+1},0,L"  # Block winning move (placeholder quadrant & direction)

    # If no immediate moves, select a random valid move (you can enhance this logic as need)
    empty_positions = get_empty_positions(board)
    if empty_positions:
        r, c = empty_positions[0]  # Take first available place (expanded logic needed for quadrant & rotation)
        return f"{r+1},{c+1},0,L"  # also placeholder quadrant & direction
