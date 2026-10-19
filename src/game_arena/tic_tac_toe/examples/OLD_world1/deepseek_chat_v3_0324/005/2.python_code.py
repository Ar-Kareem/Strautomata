
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to a simpler format for processing
    converted_board = [[cell for cell in row] for row in board]
    
    # Check for immediate winning moves or blocks
    best_move = find_immediate_move(converted_board)
    if best_move:
        return best_move
    
    # Use minimax for optimal play
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if converted_board[i][j] == 0:
                converted_board[i][j] = 1
                score = minimax(converted_board, False, -float('inf'), float('inf'))
                converted_board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                elif score == best_score:
                    # Randomize between equally good moves to avoid predictable patterns
                    if random.random() < 0.5:
                        best_move = (i, j)
    
    # If no move found (shouldn't happen in valid game states), pick first available
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if converted_board[i][j] == 0:
                    return (i, j)
    
    return best_move

def find_immediate_move(board):
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check for opponent's winning move to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Try to take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take corners if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)  # Randomize corner selection
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)
    
    return None

def minimax(board, is_maximizing, alpha, beta):
    result = check_winner(board)
    if result is not None:
        return result
    
    if is_maximizing:
        best_score = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, False, alpha, beta)
                    board[i][j] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, True, alpha, beta)
                    board[i][j] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    # Check for draw
    if all(cell != 0 for row in board for cell in row):
        return 0
    
    # Game not finished
    return None
