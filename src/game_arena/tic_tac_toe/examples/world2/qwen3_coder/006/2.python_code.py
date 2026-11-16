
import itertools

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to more convenient format
    # 1 is me, -1 is opponent, 0 is empty
    
    # Check for immediate win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # empty spot
                # Try placing my piece here
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # reset
                    return (i, j)
                board[i][j] = 0  # reset
    
    # Check for opponent immediate win to block
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # empty spot
                # Try placing opponent piece here
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # reset
                    return (i, j)
                board[i][j] = 0  # reset
    
    # No immediate threats, use heuristic evaluation
    # Evaluate each empty position
    best_move = None
    best_score = float('-inf')
    
    # Preferred positions (center, corners, edges)
    position_preference = [
        (1, 1), (1, 2), (2, 1), (2, 2),  # center
        (0, 0), (0, 3), (3, 0), (3, 3),  # corners
        (0, 1), (0, 2), (1, 0), (1, 3),  # edges
        (2, 0), (2, 3), (3, 1), (3, 2)
    ]
    
    for i, j in position_preference:
        if board[i][j] == 0:  # empty
            score = evaluate_move(board, i, j)
            if score > best_score:
                best_score = score
                best_move = (i, j)
    
    # Fallback: first empty spot
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move

def check_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    
    # Check anti-diagonal
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False

def evaluate_move(board, row, col):
    # Evaluate how good a move is by counting potential lines
    score = 0
    
    # Temporarily place my piece
    board[row][col] = 1
    
    # Count how many lines I'm contributing to
    # Rows
    my_count = sum(1 for j in range(4) if board[row][j] == 1)
    empty_count = sum(1 for j in range(4) if board[row][j] == 0)
    opponent_count = sum(1 for j in range(4) if board[row][j] == -1)
    
    if opponent_count == 0 and my_count > 0:
        score += my_count * 10
    
    # Columns
    my_count = sum(1 for i in range(4) if board[i][col] == 1)
    empty_count = sum(1 for i in range(4) if board[i][col] == 0)
    opponent_count = sum(1 for i in range(4) if board[i][col] == -1)
    
    if opponent_count == 0 and my_count > 0:
        score += my_count * 10
    
    # Main diagonal (if applicable)
    if row == col:
        my_count = sum(1 for i in range(4) if board[i][i] == 1)
        empty_count = sum(1 for i in range(4) if board[i][i] == 0)
        opponent_count = sum(1 for i in range(4) if board[i][i] == -1)
        
        if opponent_count == 0 and my_count > 0:
            score += my_count * 10
    
    # Anti-diagonal (if applicable)
    if row + col == 3:
        my_count = sum(1 for i in range(4) if board[i][3-i] == 1)
        empty_count = sum(1 for i in range(4) if board[i][3-i] == 0)
        opponent_count = sum(1 for i in range(4) if board[i][3-i] == -1)
        
        if opponent_count == 0 and my_count > 0:
            score += my_count * 10
    
    # Block opponent potential
    # Rows
    board[row][col] = -1  # pretend opponent is here
    opponent_count = sum(1 for j in range(4) if board[row][j] == -1)
    empty_count = sum(1 for j in range(4) if board[row][j] == 0)
    my_count = sum(1 for j in range(4) if board[row][j] == 1)
    
    if my_count == 0 and opponent_count > 0:
        score += opponent_count * 5  # blocking value
    
    # Columns
    opponent_count = sum(1 for i in range(4) if board[i][col] == -1)
    empty_count = sum(1 for i in range(4) if board[i][col] == 0)
    my_count = sum(1 for i in range(4) if board[i][col] == 1)
    
    if my_count == 0 and opponent_count > 0:
        score += opponent_count * 5
    
    # Reset
    board[row][col] = 1
    
    # Position preference bonus
    center_positions = {(1,1), (1,2), (2,1), (2,2)}
    corner_positions = {(0,0), (0,3), (3,0), (3,3)}
    
    if (row, col) in center_positions:
        score += 3
    elif (row, col) in corner_positions:
        score += 2
    else:
        score += 1
    
    board[row][col] = 0  # reset board
    return score
