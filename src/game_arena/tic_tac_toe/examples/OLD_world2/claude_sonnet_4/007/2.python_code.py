
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows
        for row in board:
            if all(cell == 1 for cell in row):
                return 1
            if all(cell == -1 for cell in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(board[row][col] == 1 for row in range(4)):
                return 1
            if all(board[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(board[i][i] == 1 for i in range(4)):
            return 1
        if all(board[i][i] == -1 for i in range(4)):
            return -1
        if all(board[i][3-i] == 1 for i in range(4)):
            return 1
        if all(board[i][3-i] == -1 for i in range(4)):
            return -1
        
        return 0
    
    def count_threats(board, player):
        threats = 0
        
        # Check rows
        for row in board:
            if row.count(player) == 3 and row.count(0) == 1:
                threats += 1
        
        # Check columns
        for col in range(4):
            column = [board[row][col] for row in range(4)]
            if column.count(player) == 3 and column.count(0) == 1:
                threats += 1
        
        # Check diagonals
        main_diag = [board[i][i] for i in range(4)]
        if main_diag.count(player) == 3 and main_diag.count(0) == 1:
            threats += 1
        
        anti_diag = [board[i][3-i] for i in range(4)]
        if anti_diag.count(player) == 3 and anti_diag.count(0) == 1:
            threats += 1
        
        return threats
    
    def evaluate_position(board):
        winner = check_winner(board)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        
        score = 0
        
        # Count immediate threats
        my_threats = count_threats(board, 1)
        opp_threats = count_threats(board, -1)
        score += my_threats * 100 - opp_threats * 100
        
        # Count potential lines (2 in a row with 2 empty)
        for row in board:
            if row.count(1) == 2 and row.count(0) == 2:
                score += 10
            if row.count(-1) == 2 and row.count(0) == 2:
                score -= 10
        
        for col in range(4):
            column = [board[row][col] for row in range(4)]
            if column.count(1) == 2 and column.count(0) == 2:
                score += 10
            if column.count(-1) == 2 and column.count(0) == 2:
                score -= 10
        
        # Diagonals
        main_diag = [board[i][i] for i in range(4)]
        if main_diag.count(1) == 2 and main_diag.count(0) == 2:
            score += 10
        if main_diag.count(-1) == 2 and main_diag.count(0) == 2:
            score -= 10
        
        anti_diag = [board[i][3-i] for i in range(4)]
        if anti_diag.count(1) == 2 and anti_diag.count(0) == 2:
            score += 10
        if anti_diag.count(-1) == 2 and anti_diag.count(0) == 2:
            score -= 10
        
        # Center control bonus
        center_positions = [(1,1), (1,2), (2,1), (2,2)]
        for r, c in center_positions:
            if board[r][c] == 1:
                score += 3
            elif board[r][c] == -1:
                score -= 3
        
        return score
    
    def get_empty_cells(board):
        return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        empty_cells = get_empty_cells(board)
        if not empty_cells or depth == 0:
            return evaluate_position(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for r, c in empty_cells:
                board[r][c] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                board[r][c] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate wins
    empty_cells = get_empty_cells(board)
    for r, c in empty_cells:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # Check for blocking opponent wins
    for r, c in empty_cells:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # Use minimax for strategic play
    best_move = None
    best_score = float('-inf')
    depth = min(6, len(empty_cells))
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move if best_move else empty_cells[0]
