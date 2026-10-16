
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the optimal move for the AI in a 4x4 Tic Tac Toe game.
    Uses Minimax with Alpha-Beta pruning and a heuristic evaluation function.
    """
    EMPTY = 0
    AI_PLAYER = 1
    OPPONENT = -1
    BOARD_SIZE = 4
    WIN_LENGTH = 4

    def is_full(b):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if b[r][c] == EMPTY:
                    return False
        return True

    def get_winner(b):
        # Check rows
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE - WIN_LENGTH + 1):
                if b[r][c] != EMPTY and all(b[r][c] == b[r][k] for k in range(c, c + WIN_LENGTH)):
                    return b[r][c]
        # Check columns
        for c in range(BOARD_SIZE):
            for r in range(BOARD_SIZE - WIN_LENGTH + 1):
                if b[r][c] != EMPTY and all(b[k][c] == b[r][c] for k in range(r, r + WIN_LENGTH)):
                    return b[r][c]
        # Check diagonal (top-left to bottom-right)
        for r in range(BOARD_SIZE - WIN_LENGTH + 1):
            for c in range(BOARD_SIZE - WIN_LENGTH + 1):
                if b[r][c] != EMPTY and all(b[r+i][c+i] == b[r][c] for i in range(WIN_LENGTH)):
                    return b[r][c]
        # Check diagonal (top-right to bottom-left)
        for r in range(BOARD_SIZE - WIN_LENGTH + 1):
            for c in range(WIN_LENGTH - 1, BOARD_SIZE):
                if b[r][c] != EMPTY and all(b[r+i][c-i] == b[r][c] for i in range(WIN_LENGTH)):
                    return b[r][c]
        return None

    def evaluate(b, player):
        """
        Heuristic evaluation of the board state.
        Positive score favors AI_PLAYER, negative favors OPPONENT.
        """
        score = 0
        
        # Weights for different line situations
        WIN_SCORE = 1000
        BLOCK_SCORE = 100
        OPEN_SCORE = 1
        
        # Check all lines (rows, cols, diags)
        lines = []
        
        # Rows
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE - WIN_LENGTH + 1):
                lines.append([b[r][k] for k in range(c, c + WIN_LENGTH)])
        
        # Cols
        for c in range(BOARD_SIZE):
            for r in range(BOARD_SIZE - WIN_LENGTH + 1):
                lines.append([b[k][c] for k in range(r, r + WIN_LENGTH)])
        
        # Diag TL-BR
        for r in range(BOARD_SIZE - WIN_LENGTH + 1):
            for c in range(BOARD_SIZE - WIN_LENGTH + 1):
                lines.append([b[r+i][c+i] for i in range(WIN_LENGTH)])
        
        # Diag TR-BL
        for r in range(BOARD_SIZE - WIN_LENGTH + 1):
            for c in range(WIN_LENGTH - 1, BOARD_SIZE):
                lines.append([b[r+i][c-i] for i in range(WIN_LENGTH)])
        
        for line in lines:
            ai_count = line.count(player)
            opp_count = line.count(-player)
            empty_count = line.count(EMPTY)
            
            if ai_count == WIN_LENGTH:
                return WIN_SCORE
            if opp_count == WIN_LENGTH:
                return -WIN_SCORE
            
            if ai_count > 0 and opp_count == 0:
                score += (ai_count * OPEN_SCORE)
            elif opp_count > 0 and ai_count == 0:
                score -= (opp_count * OPEN_SCORE)
                
        return score

    def get_valid_moves(b):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if b[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def minimax(b, depth, alpha, beta, maximizing_player):
        winner = get_winner(b)
        if winner == AI_PLAYER:
            return 100000 + depth  # Prefer faster wins
        if winner == OPPONENT:
            return -100000 - depth # Prefer slower losses
        if is_full(b) or depth == 0:
            return evaluate(b, AI_PLAYER)

        valid_moves = get_valid_moves(b)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in valid_moves:
                r, c = move
                b[r][c] = AI_PLAYER
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = EMPTY
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                r, c = move
                b[r][c] = OPPONENT
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = EMPTY
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # Main logic
    best_move = None
    best_value = -float('inf')
    depth_limit = 5  # Depth limit to ensure execution time constraints
    
    # Dynamic depth: if board is sparse, we can search deeper.
    # Count empty cells
    empty_count = sum(row.count(0) for row in board)
    if empty_count > 12: depth_limit = 3 # Early game
    elif empty_count > 8: depth_limit = 5 # Mid game
    else: depth_limit = 8 # Late game

    valid_moves = get_valid_moves(board)
    
    # Move ordering: prioritize center and existing threats
    # Center weights for 4x4 are indices 1, 2
    def move_priority(m):
        r, c = m
        score = 0
        if r in [1, 2]: score += 2
        if c in [1, 2]: score += 2
        # Check immediate win/block
        board[r][c] = AI_PLAYER
        if get_winner(board) == AI_PLAYER: score += 1000
        board[r][c] = OPPONENT
        if get_winner(board) == OPPONENT: score += 1000
        board[r][c] = 0
        return -score # For min sort

    valid_moves.sort(key=move_priority)

    for move in valid_moves:
        r, c = move
        
        # Check for immediate win first
        board[r][c] = AI_PLAYER
        if get_winner(board) == AI_PLAYER:
            return (r, c)
        board[r][c] = EMPTY
        
        # Check for immediate block
        board[r][c] = OPPONENT
        if get_winner(board) == OPPONENT:
            best_move = (r, c) # Block this move
            # Continue to see if there's a better move, but blocking is high priority
            best_value = 10000 
        board[r][c] = EMPTY

        board[r][c] = AI_PLAYER
        value = minimax(board, depth_limit, -float('inf'), float('inf'), False)
        board[r][c] = EMPTY

        if value > best_value:
            best_value = value
            best_move = move

    if best_move is None:
        # Fallback: pick first available
        return valid_moves[0]

    return best_move
