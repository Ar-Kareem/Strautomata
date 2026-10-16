
def policy(you: list[int], opponent: list[int]) -> int:
    # Create a deep copy of the board to simulate moves
    def simulate_move(you_board, opponent_board, move):
        # Create copies
        new_you = you_board[:]
        new_opponent = opponent_board[:]
        
        seeds = new_you[move]
        new_you[move] = 0
        
        # Distribute seeds
        current_pos = move + 1
        side = 0  # 0 = you (houses), 1 = you (store), 2 = opponent, 3 = you (houses again)
        
        for _ in range(seeds):
            if side == 0:  # your houses
                if current_pos < 6:
                    new_you[current_pos] += 1
                    current_pos += 1
                else:
                    side = 1
                    current_pos = 6
                    new_you[6] += 1
                    current_pos = 0
            elif side == 1:  # your store
                new_you[6] += 1
                side = 2
                current_pos = 0
            elif side == 2:  # opponent's houses
                if current_pos < 6:
                    new_opponent[current_pos] += 1
                    current_pos += 1
                else:
                    side = 3
                    current_pos = 0
                    new_you[current_pos] += 1
                    current_pos += 1
            else:  # back to your houses
                if current_pos < 6:
                    new_you[current_pos] += 1
                    current_pos += 1
                else:
                    side = 0
                    current_pos = 0
                    new_you[current_pos] += 1
                    current_pos += 1
        
        # Check for extra turn (last seed in your store)
        last_side = side
        last_pos = current_pos - 1 if current_pos > 0 else (5 if last_side == 0 else 5)
        
        extra_turn = False
        capture = False
        
        if last_side == 1 and last_pos == 6:
            extra_turn = True
        elif last_side == 0 and 0 <= last_pos <= 5:
            # Check for capture
            if new_you[last_pos] == 1 and you_board[last_pos] == 0:  # Was empty before
                opposite = 5 - last_pos
                if new_opponent[opposite] > 0:
                    # Capture
                    captured_seeds = 1 + new_opponent[opposite]
                    new_you[6] += captured_seeds
                    new_you[last_pos] = 0
                    new_opponent[opposite] = 0
        
        return new_you, new_opponent, extra_turn
    
    # Evaluate board position
    def evaluate_position(you_board, opponent_board):
        return you_board[6] - opponent_board[6] + (sum(you_board[:6]) - sum(opponent_board[:6])) * 0.5
    
    # Check if game ended
    def is_game_over(you_board, opponent_board):
        return sum(you_board[:6]) == 0 or sum(opponent_board[:6]) == 0
    
    # Minimax with depth limit
    def minimax(you_board, opponent_board, depth, is_maximizing, alpha, beta):
        if depth == 0 or is_game_over(you_board, opponent_board):
            return evaluate_position(you_board, opponent_board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in range(6):
                if you_board[move] > 0:
                    new_you, new_opponent, extra_turn = simulate_move(you_board, opponent_board, move)
                    if extra_turn:
                        eval_score = minimax(new_you, new_opponent, depth, True, alpha, beta)
                    else:
                        eval_score = minimax(new_you, new_opponent, depth - 1, False, alpha, beta)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for move in range(6):
                if opponent_board[move] > 0:
                    new_opponent, new_you, extra_turn = simulate_move(opponent_board, you_board, move)
                    if extra_turn:
                        eval_score = minimax(new_you, new_opponent, depth, False, alpha, beta)
                    else:
                        eval_score = minimax(new_you, new_opponent, depth - 1, True, alpha, beta)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval
    
    # Find best move
    best_move = -1
    best_value = float('-inf')
    
    # First check for immediate captures or extra turns
    for move in range(6):
        if you[move] > 0:
            new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)
            if extra_turn:
                # Extra turn is very valuable
                return move
            # Check if this creates a capture
            elif new_you[6] > you[6]:  # We captured something
                return move
    
    # If no immediate tactical moves, use minimax
    depth = 4  # Adjustable depth based on performance requirements
    
    for move in range(6):
        if you[move] > 0:
            new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)
            if extra_turn:
                value = minimax(new_you, new_opponent, depth, True, float('-inf'), float('inf'))
            else:
                value = minimax(new_you, new_opponent, depth-1, False, float('-inf'), float('inf'))
            
            if value > best_value:
                best_value = value
                best_move = move
    
    # Fallback: return first valid move if minimax didn't find anything
    if best_move == -1:
        for i in range(6):
            if you[i] > 0:
                return i
                
    return best_move
