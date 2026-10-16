
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board state
    board = [[None for _ in range(3)] for _ in range(3)]
    
    for prop in state:
        if prop[0] == "cell":
            row = int(prop[1]) - 1
            col = int(prop[2]) - 1
            cell_value = prop[3]
            if cell_value != "b":
                board[row][col] = cell_value
            else:
                board[row][col] = None
    
    # Find legal moves
    legal_moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] is None:
                legal_moves.append((i, j))
    
    # If no legal moves, shouldn't happen but return safe default
    if not legal_moves:
        return "mark(1,1)"
    
    # Determine opponent
    opponent = "o" if role == "x" else "x"
    
    # Check win condition
    def check_winner(b):
        # Check rows
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] and b[i][0] is not None:
                return b[i][0]
        # Check columns
        for j in range(3):
            if b[0][j] == b[1][j] == b[2][j] and b[0][j] is not None:
                return b[0][j]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] and b[0][0] is not None:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] and b[0][2] is not None:
            return b[0][2]
        return None
    
    # Minimax with alpha-beta pruning
    def minimax(b, is_maximizing, alpha, beta, depth=0):
        winner = check_winner(b)
        if winner == role:
            return 100 - depth
        elif winner == opponent:
            return -100 + depth
        
        # Check if board is full (draw)
        has_empty = any(b[i][j] is None for i in range(3) for j in range(3))
        if not has_empty:
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] is None:
                        b[i][j] = role
                        eval_score = minimax(b, False, alpha, beta, depth + 1)
                        b[i][j] = None
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            return max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] is None:
                        b[i][j] = opponent
                        eval_score = minimax(b, True, alpha, beta, depth + 1)
                        b[i][j] = None
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            return min_eval
            return min_eval
    
    # Find best move
    best_move = legal_moves[0]
    best_value = -float('inf')
    
    for move in legal_moves:
        i, j = move
        board[i][j] = role
        move_value = minimax(board, False, -float('inf'), float('inf'))
        board[i][j] = None
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    # Convert to action format
    row = best_move[0] + 1
    col = best_move[1] + 1
    return f"mark({row},{col})"
