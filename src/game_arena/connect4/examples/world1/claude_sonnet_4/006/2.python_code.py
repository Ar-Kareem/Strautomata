
def policy(board: list[list[int]]) -> int:
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def make_move(board, col, player):
        # Create a copy of the board and make the move
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def check_winner(board):
        # Check horizontal, vertical, and diagonal wins
        for row in range(6):
            for col in range(7):
                if board[row][col] == 0:
                    continue
                player = board[row][col]
                
                # Check horizontal (right)
                if col <= 3:
                    if all(board[row][col + i] == player for i in range(4)):
                        return player
                
                # Check vertical (down)
                if row <= 2:
                    if all(board[row + i][col] == player for i in range(4)):
                        return player
                
                # Check diagonal (down-right)
                if row <= 2 and col <= 3:
                    if all(board[row + i][col + i] == player for i in range(4)):
                        return player
                
                # Check diagonal (down-left)
                if row <= 2 and col >= 3:
                    if all(board[row + i][col - i] == player for i in range(4)):
                        return player
        
        return 0  # No winner
    
    def count_sequences(board, player, length):
        count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonal
        
        for row in range(6):
            for col in range(7):
                for dr, dc in directions:
                    sequence_count = 0
                    empty_count = 0
                    
                    # Check if we can fit a sequence of 4 starting from this position
                    if (row + 3 * dr < 0 or row + 3 * dr >= 6 or 
                        col + 3 * dc < 0 or col + 3 * dc >= 7):
                        continue
                    
                    for i in range(4):
                        r, c = row + i * dr, col + i * dc
                        if board[r][c] == player:
                            sequence_count += 1
                        elif board[r][c] == 0:
                            empty_count += 1
                        else:  # opponent piece
                            break
                    else:  # no break occurred
                        if sequence_count == length and sequence_count + empty_count == 4:
                            count += 1
        
        return count
    
    def evaluate_board(board, player):
        winner = check_winner(board)
        if winner == player:
            return 1000
        elif winner == -player:
            return -1000
        
        score = 0
        # Count potential wins
        score += count_sequences(board, player, 3) * 50
        score += count_sequences(board, player, 2) * 10
        score += count_sequences(board, player, 1) * 2
        
        # Subtract opponent potential wins
        score -= count_sequences(board, -player, 3) * 50
        score -= count_sequences(board, -player, 2) * 10
        score -= count_sequences(board, -player, 1) * 2
        
        # Prefer center columns
        for row in range(6):
            if board[row][3] == player:
                score += 3
            elif board[row][3] == -player:
                score -= 3
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        winner = check_winner(board)
        if winner != 0:
            return (1000 if winner == player else -1000), None
        
        if depth == 0:
            return evaluate_board(board, player), None
        
        valid_moves = get_valid_moves(board)
        if not valid_moves:
            return 0, None
        
        best_move = valid_moves[0]
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                new_board = make_move(board, col, player)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, player)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for col in valid_moves:
                new_board = make_move(board, col, -player)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, player)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Main policy logic
    player = 1  # We are always player 1
    
    # Quick wins and blocks check
    valid_moves = get_valid_moves(board)
    
    # Check for immediate win
    for col in valid_moves:
        test_board = make_move(board, col, player)
        if check_winner(test_board) == player:
            return col
    
    # Check for immediate block
    for col in valid_moves:
        test_board = make_move(board, col, -player)
        if check_winner(test_board) == -player:
            return col
    
    # Use minimax for deeper analysis
    _, best_move = minimax(board, 4, float('-inf'), float('inf'), True, player)
    
    return best_move if best_move is not None else valid_moves[0]
