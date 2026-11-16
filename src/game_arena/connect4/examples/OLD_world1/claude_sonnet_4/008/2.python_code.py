
def policy(board: list[list[int]]) -> int:
    rows, cols = 6, 7
    
    def is_valid_move(col):
        return board[0][col] == 0
    
    def get_next_row(col):
        for row in range(rows - 1, -1, -1):
            if board[row][col] == 0:
                return row
        return -1
    
    def check_win(board, row, col, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
                count += 1
                r, c = r + dr, c + dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 4:
                return True
        return False
    
    def evaluate_position(board):
        score = 0
        
        # Evaluate all possible 4-in-a-row windows
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for row in range(rows):
            for col in range(cols):
                for dr, dc in directions:
                    window = []
                    for i in range(4):
                        r, c = row + i * dr, col + i * dc
                        if 0 <= r < rows and 0 <= c < cols:
                            window.append(board[r][c])
                        else:
                            break
                    
                    if len(window) == 4:
                        score += evaluate_window(window)
        
        return score
    
    def evaluate_window(window):
        score = 0
        my_count = window.count(1)
        opp_count = window.count(-1)
        empty_count = window.count(0)
        
        if my_count == 4:
            score += 100
        elif my_count == 3 and empty_count == 1:
            score += 10
        elif my_count == 2 and empty_count == 2:
            score += 2
        
        if opp_count == 4:
            score -= 100
        elif opp_count == 3 and empty_count == 1:
            score -= 80
        elif opp_count == 2 and empty_count == 2:
            score -= 2
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing):
        valid_moves = [col for col in range(cols) if is_valid_move(col)]
        
        # Check terminal conditions
        is_terminal = True
        for col in range(cols):
            if is_valid_move(col):
                row = get_next_row(col)
                # Simulate move for current player
                board[row][col] = 1 if maximizing else -1
                if check_win(board, row, col, 1 if maximizing else -1):
                    board[row][col] = 0  # Undo move
                    return 1000000 if maximizing else -1000000
                board[row][col] = 0  # Undo move
                is_terminal = False
        
        if is_terminal or depth == 0:
            return evaluate_position(board)
        
        if maximizing:
            max_eval = float('-inf')
            for col in valid_moves:
                row = get_next_row(col)
                board[row][col] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                row = get_next_row(col)
                board[row][col] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate winning move
    for col in range(cols):
        if is_valid_move(col):
            row = get_next_row(col)
            board[row][col] = 1
            if check_win(board, row, col, 1):
                board[row][col] = 0
                return col
            board[row][col] = 0
    
    # Check for blocking opponent's winning move
    for col in range(cols):
        if is_valid_move(col):
            row = get_next_row(col)
            board[row][col] = -1
            if check_win(board, row, col, -1):
                board[row][col] = 0
                return col
            board[row][col] = 0
    
    # Use minimax for best move
    best_score = float('-inf')
    best_col = 3  # Default to center
    
    for col in range(cols):
        if is_valid_move(col):
            row = get_next_row(col)
            board[row][col] = 1
            score = minimax(board, 6, float('-inf'), float('inf'), False)
            board[row][col] = 0
            
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
