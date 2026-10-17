
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows
        for row in b:
            if all(x == 1 for x in row):
                return 1
            if all(x == -1 for x in row):
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
    
    def count_line_score(line, player):
        if any(x == -player for x in line):
            return 0
        count = sum(1 for x in line if x == player)
        if count == 4:
            return 1000
        elif count == 3:
            return 50
        elif count == 2:
            return 10
        elif count == 1:
            return 1
        return 0
    
    def evaluate_board(b):
        winner = check_winner(b)
        if winner != 0:
            return winner * 1000
        
        score = 0
        
        # Evaluate rows
        for row in b:
            score += count_line_score(row, 1)
            score -= count_line_score(row, -1)
        
        # Evaluate columns
        for col in range(4):
            column = [b[row][col] for row in range(4)]
            score += count_line_score(column, 1)
            score -= count_line_score(column, -1)
        
        # Evaluate diagonals
        main_diag = [b[i][i] for i in range(4)]
        anti_diag = [b[i][3-i] for i in range(4)]
        score += count_line_score(main_diag, 1)
        score -= count_line_score(main_diag, -1)
        score += count_line_score(anti_diag, 1)
        score -= count_line_score(anti_diag, -1)
        
        # Center preference
        center_positions = [(1,1), (1,2), (2,1), (2,2)]
        for r, c in center_positions:
            if b[r][c] == 1:
                score += 3
            elif b[r][c] == -1:
                score -= 3
        
        return score
    
    def get_empty_cells(b):
        return [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
    
    def minimax(b, depth, alpha, beta, maximizing_player):
        winner = check_winner(b)
        if winner != 0:
            return winner * 1000
        
        empty_cells = get_empty_cells(b)
        if not empty_cells or depth == 0:
            return evaluate_board(b)
        
        if maximizing_player:
            max_eval = float('-inf')
            for r, c in empty_cells:
                b[r][c] = 1
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                b[r][c] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate winning moves
    empty_cells = get_empty_cells(board)
    for r, c in empty_cells:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # Check for immediate blocking moves
    for r, c in empty_cells:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # Use minimax for best move
    best_score = float('-inf')
    best_move = empty_cells[0]
    
    # Adaptive depth based on game state
    empty_count = len(empty_cells)
    if empty_count <= 6:
        depth = 8
    elif empty_count <= 10:
        depth = 6
    else:
        depth = 4
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, depth, float('-inf'), float('inf'), False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
