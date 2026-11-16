
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows
        for row in board:
            if all(cell == 1 for cell in row):
                return 1
            elif all(cell == -1 for cell in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(board[row][col] == 1 for row in range(4)):
                return 1
            elif all(board[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(board[i][i] == 1 for i in range(4)):
            return 1
        elif all(board[i][i] == -1 for i in range(4)):
            return -1
        
        if all(board[i][3-i] == 1 for i in range(4)):
            return 1
        elif all(board[i][3-i] == -1 for i in range(4)):
            return -1
        
        return 0
    
    def get_empty_cells(board):
        return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def evaluate_position(board):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        score = 0
        
        # Evaluate all lines (rows, columns, diagonals)
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([board[i][j] for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([board[i][j] for i in range(4)])
        
        # Diagonals
        lines.append([board[i][i] for i in range(4)])
        lines.append([board[i][3-i] for i in range(4)])
        
        for line in lines:
            my_count = line.count(1)
            opp_count = line.count(-1)
            
            if opp_count == 0:  # No opponent pieces
                if my_count == 3:
                    score += 50
                elif my_count == 2:
                    score += 10
                elif my_count == 1:
                    score += 2
            elif my_count == 0:  # No my pieces
                if opp_count == 3:
                    score -= 50
                elif opp_count == 2:
                    score -= 10
                elif opp_count == 1:
                    score -= 2
        
        # Center control bonus
        center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for r, c in center_positions:
            if board[r][c] == 1:
                score += 3
            elif board[r][c] == -1:
                score -= 3
        
        return score
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        empty_cells = get_empty_cells(board)
        if not empty_cells or depth == 0:
            return evaluate_position(board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for row, col in empty_cells:
                board[row][col] = 1
                eval_score = minimax(board, depth - 1, False, alpha, beta)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in empty_cells:
                board[row][col] = -1
                eval_score = minimax(board, depth - 1, True, alpha, beta)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate win
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_winner(board) == 1:
                    board[row][col] = 0
                    return (row, col)
                board[row][col] = 0
    
    # Check for blocking opponent win
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_winner(board) == -1:
                    board[row][col] = 0
                    return (row, col)
                board[row][col] = 0
    
    # Use minimax for best move
    empty_cells = get_empty_cells(board)
    
    # Adjust depth based on game state
    num_empty = len(empty_cells)
    if num_empty <= 8:
        depth = 6
    elif num_empty <= 12:
        depth = 4
    else:
        depth = 3
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for row, col in empty_cells:
        board[row][col] = 1
        score = minimax(board, depth - 1, False, float('-inf'), float('inf'))
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move
