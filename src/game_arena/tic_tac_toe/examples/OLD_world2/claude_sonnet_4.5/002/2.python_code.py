
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy using minimax with alpha-beta pruning.
    Returns the best move as (row, col).
    """
    
    def check_winner(b):
        """Check if there's a winner. Returns 1, -1, or 0."""
        # Check rows
        for row in b:
            if all(cell == 1 for cell in row):
                return 1
            if all(cell == -1 for cell in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(b[row][col] == 1 for row in range(4)):
                return 1
            if all(b[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(b[i][i] == 1 for i in range(4)):
            return 1
        if all(b[i][i] == -1 for i in range(4)):
            return -1
        if all(b[i][3-i] == 1 for i in range(4)):
            return 1
        if all(b[i][3-i] == -1 for i in range(4)):
            return -1
        
        return 0
    
    def is_full(b):
        """Check if board is full."""
        return all(b[i][j] != 0 for i in range(4) for j in range(4))
    
    def evaluate(b):
        """Evaluate board state with heuristics."""
        winner = check_winner(b)
        if winner != 0:
            return winner * 1000
        
        score = 0
        # Check all lines for threats and opportunities
        lines = []
        
        # Rows and columns
        for i in range(4):
            lines.append([b[i][j] for j in range(4)])
            lines.append([b[j][i] for j in range(4)])
        
        # Diagonals
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        
        for line in lines:
            ones = line.count(1)
            negs = line.count(-1)
            if negs == 0:
                score += ones ** 2
            if ones == 0:
                score -= negs ** 2
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        winner = check_winner(b)
        if winner != 0:
            return winner * 1000
        
        if is_full(b) or depth == 0:
            return evaluate(b)
        
        if maximizing:
            max_eval = float('-inf')
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval_score = minimax(b, depth - 1, alpha, beta, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval_score = minimax(b, depth - 1, alpha, beta, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Count empty cells to determine search depth
    empty_count = sum(1 for i in range(4) for j in range(4) if board[i][j] == 0)
    
    # Adjust depth based on game state
    if empty_count > 12:
        depth = 4
    elif empty_count > 8:
        depth = 6
    else:
        depth = 8
    
    best_move = None
    best_score = float('-inf')
    
    # Try all possible moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, depth, float('-inf'), float('inf'), False)
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move if best_move else (0, 0)
