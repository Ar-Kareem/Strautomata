
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_empty_cells(board):
        empty = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        empty.append((i, j, k))
        return empty
    
    def check_winner(board):
        # Check all possible lines in 3D space
        lines = []
        
        # Lines parallel to x-axis
        for j in range(3):
            for k in range(3):
                lines.append([(i, j, k) for i in range(3)])
        
        # Lines parallel to y-axis
        for i in range(3):
            for k in range(3):
                lines.append([(i, j, k) for j in range(3)])
        
        # Lines parallel to z-axis
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)])
        
        # Face diagonals in xy planes
        for k in range(3):
            lines.append([(i, i, k) for i in range(3)])  # main diagonal
            lines.append([(i, 2-i, k) for i in range(3)])  # anti diagonal
        
        # Face diagonals in xz planes
        for j in range(3):
            lines.append([(i, j, i) for i in range(3)])  # main diagonal
            lines.append([(i, j, 2-i) for i in range(3)])  # anti diagonal
        
        # Face diagonals in yz planes
        for i in range(3):
            lines.append([(i, j, j) for j in range(3)])  # main diagonal
            lines.append([(i, j, 2-j) for j in range(3)])  # anti diagonal
        
        # Space diagonals (4 total)
        lines.append([(i, i, i) for i in range(3)])  # main space diagonal
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        for line in lines:
            values = [board[pos[0]][pos[1]][pos[2]] for pos in line]
            if all(v == 1 for v in values):
                return 1
            elif all(v == -1 for v in values):
                return -1
        
        return 0
    
    def evaluate_board(board):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        # Evaluate based on potential lines
        score = 0
        lines = []
        
        # Same line definitions as in check_winner
        for j in range(3):
            for k in range(3):
                lines.append([(i, j, k) for i in range(3)])
        for i in range(3):
            for k in range(3):
                lines.append([(i, j, k) for j in range(3)])
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)])
        for k in range(3):
            lines.append([(i, i, k) for i in range(3)])
            lines.append([(i, 2-i, k) for i in range(3)])
        for j in range(3):
            lines.append([(i, j, i) for i in range(3)])
            lines.append([(i, j, 2-i) for i in range(3)])
        for i in range(3):
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        for line in lines:
            values = [board[pos[0]][pos[1]][pos[2]] for pos in line]
            player_count = values.count(1)
            opponent_count = values.count(-1)
            
            if opponent_count == 0:
                score += player_count ** 2
            elif player_count == 0:
                score -= opponent_count ** 2
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0 or depth == 0:
            return evaluate_board(board)
        
        empty_cells = get_empty_cells(board)
        if not empty_cells:
            return 0
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in empty_cells:
                i, j, k = move
                board[i][j][k] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[i][j][k] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in empty_cells:
                i, j, k = move
                board[i][j][k] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[i][j][k] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    empty_cells = get_empty_cells(board)
    if not empty_cells:
        return (0, 0, 0)
    
    # Check for immediate win
    for move in empty_cells:
        i, j, k = move
        board[i][j][k] = 1
        if check_winner(board) == 1:
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0
    
    # Check for blocking opponent win
    for move in empty_cells:
        i, j, k = move
        board[i][j][k] = -1
        if check_winner(board) == -1:
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0
    
    # Use minimax for best move
    best_move = empty_cells[0]
    best_score = float('-inf')
    depth = min(6, len(empty_cells))
    
    for move in empty_cells:
        i, j, k = move
        board[i][j][k] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[i][j][k] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
