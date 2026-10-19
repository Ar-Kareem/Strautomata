
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning
    """
    
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def drop_piece(board, col, player):
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def check_winner(board):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if board[row][col] != 0:
                    if all(board[row][col + i] == board[row][col] for i in range(4)):
                        return board[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if board[row][col] != 0:
                    if all(board[row + i][col] == board[row][col] for i in range(4)):
                        return board[row][col]
        
        # Check diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if board[row][col] != 0:
                    if all(board[row + i][col + i] == board[row][col] for i in range(4)):
                        return board[row][col]
        
        # Check diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                if board[row][col] != 0:
                    if all(board[row + i][col - i] == board[row][col] for i in range(4)):
                        return board[row][col]
        
        return 0
    
    def is_terminal(board):
        return check_winner(board) != 0 or len(get_valid_moves(board)) == 0
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 10
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 2
        
        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 80
        elif window.count(opponent) == 2 and window.count(0) == 2:
            score -= 3
        
        return score
    
    def evaluate_position(board, player):
        score = 0
        
        # Center column preference
        center_array = [board[row][3] for row in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Horizontal
        for row in range(6):
            for col in range(4):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for col in range(7):
            for row in range(3):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Positive diagonal
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Negative diagonal
        for row in range(3):
            for col in range(3, 7):
                window = [board[row + i][col - i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        valid_moves = get_valid_moves(board)
        is_terminal_node = is_terminal(board)
        
        if depth == 0 or is_terminal_node:
            if is_terminal_node:
                winner = check_winner(board)
                if winner == player:
                    return None, 100000000000001
                elif winner == -player:
                    return None, -100000000000001
                else:  # Game is over, no more valid moves
                    return None, 0
            else:  # Depth is zero
                return None, evaluate_position(board, player)
        
        if maximizing_player:
            value = float('-inf')
            column = valid_moves[0] if valid_moves else 0
            for col in valid_moves:
                new_board = drop_piece(board, col, player)
                new_score = minimax(new_board, depth - 1, alpha, beta, False, player)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return column, value
        
        else:  # Minimizing player
            value = float('inf')
            column = valid_moves[0] if valid_moves else 0
            for col in valid_moves:
                new_board = drop_piece(board, col, -player)
                new_score = minimax(new_board, depth - 1, alpha, beta, True, player)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return column, value
    
    # Check for immediate winning move
    valid_moves = get_valid_moves(board)
    for col in valid_moves:
        test_board = drop_piece(board, col, 1)
        if check_winner(test_board) == 1:
            return col
    
    # Check for immediate blocking move
    for col in valid_moves:
        test_board = drop_piece(board, col, -1)
        if check_winner(test_board) == -1:
            return col
    
    # Use minimax for best move
    col, minimax_score = minimax(board, 5, float('-inf'), float('inf'), True, 1)
    return col
