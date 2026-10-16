
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows, columns, and diagonals for 4 in a row
        for i in range(4):
            # Check rows
            if abs(sum(board[i])) == 4:
                return board[i][0]
            # Check columns
            col_sum = sum(board[j][i] for j in range(4))
            if abs(col_sum) == 4:
                return board[0][i]
        
        # Check diagonals
        diag1_sum = sum(board[i][i] for i in range(4))
        if abs(diag1_sum) == 4:
            return board[0][0]
        
        diag2_sum = sum(board[i][3-i] for i in range(4))
        if abs(diag2_sum) == 4:
            return board[0][3]
        
        return 0
    
    def get_empty_positions(board):
        positions = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    positions.append((i, j))
        return positions
    
    def evaluate_board(board):
        winner = check_winner(board)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        
        score = 0
        # Evaluate all possible lines (rows, columns, diagonals)
        lines = []
        
        # Rows and columns
        for i in range(4):
            lines.append([board[i][j] for j in range(4)])  # row
            lines.append([board[j][i] for j in range(4)])  # column
        
        # Diagonals
        lines.append([board[i][i] for i in range(4)])
        lines.append([board[i][3-i] for i in range(4)])
        
        for line in lines:
            score += evaluate_line(line)
        
        return score
    
    def evaluate_line(line):
        score = 0
        my_count = line.count(1)
        opp_count = line.count(-1)
        
        # If both players have pieces in the line, it's neutral
        if my_count > 0 and opp_count > 0:
            return 0
        
        # Score based on how many pieces we have in the line
        if my_count == 3:
            score += 50
        elif my_count == 2:
            score += 10
        elif my_count == 1:
            score += 1
        
        # Penalty for opponent pieces
        if opp_count == 3:
            score -= 50
        elif opp_count == 2:
            score -= 10
        elif opp_count == 1:
            score -= 1
        
        return score
    
    def can_win_next_move(board, player):
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    board[i][j] = player
                    if check_winner(board) == player:
                        board[i][j] = 0
                        return (i, j)
                    board[i][j] = 0
        return None
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0 or depth == 0:
            return evaluate_board(board)
        
        empty_positions = get_empty_positions(board)
        if not empty_positions:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for row, col in empty_positions:
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
            for row, col in empty_positions:
                board[row][col] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Main strategy
    
    # 1. Check if we can win immediately
    winning_move = can_win_next_move(board, 1)
    if winning_move:
        return winning_move
    
    # 2. Check if we need to block opponent from winning
    blocking_move = can_win_next_move(board, -1)
    if blocking_move:
        return blocking_move
    
    # 3. Use minimax to find the best move
    empty_positions = get_empty_positions(board)
    
    # Adjust depth based on number of empty positions to stay within time limit
    if len(empty_positions) > 10:
        depth = 3
    elif len(empty_positions) > 6:
        depth = 4
    else:
        depth = 6
    
    best_move = None
    best_value = float('-inf')
    
    for row, col in empty_positions:
        board[row][col] = 1
        move_value = minimax(board, depth, float('-inf'), float('inf'), False)
        board[row][col] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = (row, col)
    
    # If no move found (shouldn't happen), take first available
    if best_move is None:
        return empty_positions[0]
    
    return best_move
