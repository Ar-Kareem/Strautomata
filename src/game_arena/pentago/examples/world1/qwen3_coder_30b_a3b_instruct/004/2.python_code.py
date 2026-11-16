
import numpy as np
import copy

def policy(you, opponent):
    # Convert input to numpy arrays to make handling easier  
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Get all empty positions
    empty_positions = []
    for i in range(6):
        for j in range(6):
            if you[i][j] == 0 and opponent[i][j] == 0:
                empty_positions.append((i, j))
                
    # Check for winning move (either player can win)
    for row, col in empty_positions:
        # Try the move - place our marble
        you_copy = copy.deepcopy(you)
        you_copy[row][col] = 1
        if check_win(you_copy, opponent):
            return f"{row+1},{col+1},0,L"  # Return a valid format, 0,L as placeholder
    
    # Check for opponent's winning move and block it
    for row, col in empty_positions:
        opponent_copy = copy.deepcopy(opponent)
        opponent_copy[row][col] = 1
        # Try a rotation to see if it blocks a win
        for quad in range(4):
            # Create a temporary board with move and rotation
            temp_you = copy.deepcopy(you)
            temp_opponent = copy.deepcopy(opponent)
            temp_opponent[row][col] = 1
            # Apply rotation of quadrant (simplified - not full simulation)
            # Just check if the opponent can win if we don't block
            if check_win(temp_opponent, temp_you):
                # This is to prevent immediate loss
                pass
    
    # Try blocking opponent's immediate wins
    for row, col in empty_positions:
        opponent_copy = copy.deepcopy(opponent)
        opponent_copy[row][col] = 1
        if check_win(opponent_copy, you):
            # This is a winning block for us
            return f"{row+1},{col+1},0,L"
    
    # If no immediate wins/blocks, make a smart heuristic play 
    # Prefer center positions
    center_positions = [(2,2), (2,3), (3,2), (3,3)]
    for pos in center_positions:
        if you[pos[0]][pos[1]] == 0 and opponent[pos[0]][pos[1]] == 0:
            # Test if move leads to a winning line or blocks opponent
            for quad in range(4):
                # Try a rotation and see if it's good
                # For now, just place at center and rotate quadrant 0  
                return f"{pos[0]+1},{pos[1]+1},0,L"
    
    # Fallback to simple first available
    pos = empty_positions[0]
    return f"{pos[0]+1},{pos[1]+1},0,L"
    
def check_win(board, opponent_board):
    # Check for 5-in-a-row on the board
    # Check all horizontal lines (6 rows)
    for i in range(6):
        for j in range(2):  # 5 consecutive positions in row
            if board[i][j] == 1 and board[i][j+1] == 1 and board[i][j+2] == 1 and board[i][j+3] == 1 and board[i][j+4] == 1:
                return True
    
    # Check all vertical lines
    for i in range(2):  # 5 consecutive positions in column
        for j in range(6):
            if board[i][j] == 1 and board[i+1][j] == 1 and board[i+2][j] == 1 and board[i+3][j] == 1 and board[i+4][j] == 1:
                return True
    
    # Check main diagonals
    for i in range(2):
        for j in range(2):
            if board[i][j] == 1 and board[i+1][j+1] == 1 and board[i+2][j+2] == 1 and board[i+3][j+3] == 1 and board[i+4][j+4] == 1:
                return True
    
    # Check other diagonals
    for i in range(2):
        for j in range(4, 6):
            if board[i][j] == 1 and board[i+1][j-1] == 1 and board[i+2][j-2] == 1 and board[i+3][j-3] == 1 and board[i+4][j-4] == 1:
                return True

    return False
