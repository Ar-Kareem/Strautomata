
def is_win(board, player):
    """Check if specified player has a winning position"""
    # Check rows and columns
    for i in range(4):
        if all(board[i][j] == player for j in range(4)) or \
           all(board[j][i] == player for j in range(4)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(4)) or \
       all(board[i][3-i] == player for i in range(4)):
        return True
    return False

def policy(board):
    """Determine optimal move for 4x4 Tic Tac Toe"""
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    # Attempt immediate win
    for i, j in empty_cells:
        board[i][j] = 1
        if is_win(board, 1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Block opponent win
    for i, j in empty_cells:
        board[i][j] = -1
        if is_win(board, -1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Heuristic scoring system
    best_score = -1
    best_move = empty_cells[0]
    for i, j in empty_cells:
        # Line analysis
        row = board[i]
        col = [board[x][j] for x in range(4)]
        lines = [row, col]
        
        # Diagonal checks
        if i == j:
            lines.append([board[x][x] for x in range(4)])
        if i + j == 3:
            lines.append([board[x][3-x] for x in range(4)])
        
        # Calculate score
        score = 0
        for line in lines:
            if -1 not in line:  # Unblocked line
                score += sum(1 for x in line if x == 1)
        
        # Center bonus (2x2 center area)
        if 1 <= i <= 2 and 1 <= j <= 2:
            score += 0.1
        
        # Update best move
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = (i, j)
    
    return best_move
