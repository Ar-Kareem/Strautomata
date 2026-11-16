
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy using minimax with alpha-beta pruning
    """
    
    def check_winner(b):
        """Check if there's a winner. Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise"""
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
    
    def count_threats(b, player):
        """Count potential winning lines for a player"""
        score = 0
        
        # Check rows
        for row in b:
            if row.count(player) == 3 and row.count(0) == 1:
                score += 50
            elif row.count(player) == 2 and row.count(0) == 2:
                score += 10
            elif row.count(player) == 1 and row.count(0) == 3:
                score += 1
        
        # Check columns
        for col in range(4):
            col_vals = [b[row][col] for row in range(4)]
            if col_vals.count(player) == 3 and col_vals.count(0) == 1:
                score += 50
            elif col_vals.count(player) == 2 and col_vals.count(0) == 2:
                score += 10
            elif col_vals.count(player) == 1 and col_vals.count(0) == 3:
                score += 1
        
        # Check diagonals
        diag1 = [b[i][i] for i in range(4)]
        diag2 = [b[i][3-i] for i in range(4)]
        
        for diag in [diag1, diag2]:
            if diag.count(player) == 3 and diag.count(0) == 1:
                score += 50
            elif diag.count(player) == 2 and diag.count(0) == 2:
                score += 10
            elif diag.count(player) == 1 and diag.count(0) == 3:
                score += 1
        
        return score
    
    def evaluate(b):
        """Evaluate board position"""
        winner = check_winner(b)
        if winner == 1:
            return 10000
        elif winner == -1:
            return -10000
        
        # Heuristic evaluation
        my_threats = count_threats(b, 1)
        opp_threats = count_threats(b, -1)
        
        return my_threats - opp_threats
    
    def get_moves(b):
        """Get all available moves"""
        moves = []
        for i in range(4):
            for j in range(4):
                if b[i][j] == 0:
                    moves.append((i, j))
        return moves
    
    def minimax(b, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        winner = check_winner(b)
        if winner != 0:
            return winner * 10000
        
        moves = get_moves(b)
        if not moves or depth == 0:
            return evaluate(b)
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                i, j = move
                b[i][j] = 1
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                i, j = move
                b[i][j] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    moves = get_moves(board)
    
    if not moves:
        return (0, 0)
    
    # Determine search depth based on number of empty cells
    num_empty = len(moves)
    if num_empty <= 6:
        depth = 10
    elif num_empty <= 10:
        depth = 6
    else:
        depth = 4
    
    best_move = moves[0]
    best_score = float('-inf')
    
    for move in moves:
        i, j = move
        board[i][j] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
