
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing my mark here
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's mark here
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Use minimax to find best move
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False)
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # If all positions have equal value, prefer center, then corners, then edges
    if best_move is None:
        # Find all empty spots
        empty_spots = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    empty_spots.append((i, j))
        
        # Prefer center
        if (1, 1) in empty_spots:
            return (1, 1)
        
        # Prefer corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        for corner in corners:
            if corner in empty_spots:
                return corner
        
        # Take any remaining spot
        return empty_spots[0]
    
    return best_move

def minimax(board, depth, is_maximizing):
    winner = check_winner(board)
    
    # Base cases
    if winner == 1:  # I win
        return 10 - depth
    elif winner == -1:  # Opponent wins
        return depth - 10
    elif is_board_full(board):  # Tie
        return 0
    
    if is_maximizing:
        # My turn - maximize score
        best_score = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, depth + 1, False)
                    board[i][j] = 0
                    best_score = max(score, best_score)
        return best_score
    else:
        # Opponent's turn - minimize score
        best_score = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, depth + 1, True)
                    board[i][j] = 0
                    best_score = min(score, best_score)
        return best_score

def check_winner(board):
    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    
    # Check columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    return 0  # No winner

def is_board_full(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True
