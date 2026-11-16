
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
    
    def is_board_full(board):
        return all(board[i][j] != 0 for i in range(4) for j in range(4))
    
    def get_empty_positions(board):
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
            score += evaluate_line(line)
        
        # Center bonus
        center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for i, j in center_positions:
            if board[i][j] == 1:
                score += 3
            elif board[i][j] == -1:
                score -= 3
        
        return score
    
    def evaluate_line(line):
        my_count = line.count(1)
        opp_count = line.count(-1)
        empty_count = line.count(0)
        
        if opp_count > 0 and my_count > 0:
            return 0  # Mixed line, no threat
        
        if my_count == 4:
            return 1000
        elif my_count == 3 and empty_count == 1:
            return 50
        elif my_count == 2 and empty_count == 2:
            return 10
        elif my_count == 1 and empty_count == 3:
            return 1
        elif opp_count == 4:
            return -1000
        elif opp_count == 3 and empty_count == 1:
            return -100  # Block opponent win
        elif opp_count == 2 and empty_count == 2:
            return -15
        elif opp_count == 1 and empty_count == 3:
            return -2
        
        return 0
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0 or is_board_full(board) or depth == 0:
            return evaluate_position(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for i, j in get_empty_positions(board):
                board[i][j] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in get_empty_positions(board):
                board[i][j] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate win
    for i, j in get_empty_positions(board):
        board[i][j] = 1
        if check_winner(board) == 1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Check for immediate block
    for i, j in get_empty_positions(board):
        board[i][j] = -1
        if check_winner(board) == -1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Use minimax for best move
    empty_positions = get_empty_positions(board)
    
    # Adjust depth based on game state
    num_empty = len(empty_positions)
    if num_empty > 12:
        depth = 3
    elif num_empty > 8:
        depth = 4
    elif num_empty > 4:
        depth = 5
    else:
        depth = 7
    
    best_move = None
    best_score = float('-inf')
    
    for i, j in empty_positions:
        board[i][j] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move if best_move else empty_positions[0]
