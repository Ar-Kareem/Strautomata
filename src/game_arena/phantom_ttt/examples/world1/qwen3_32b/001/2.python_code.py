
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Map numpy's 0-8 index to (row, col) coordinate system
    def action_to_coord(action):
        return (action // 3, action % 3)
    
    # Check if a player has won
    def check_win(state, player):
        # Check rows, columns, and diagonals
        for i in range(3):
            if all(state[i, j] == player for j in range(3)) or all(state[j, i] == player for j in range(3)):
                return True
        
        if all(state[i, i] == player for i in range(3)) or all(state[i, 2-i] == player for i in range(3)):
            return True
        
        return False
    
    # Count confirmed cells for each player
    confirmed_me = np.sum(board == 1)
    confirmed_opponent = np.sum(board == 2 if board.ndim == 2 else np.array([[cell == 2 for cell in row] for row in board]))
    
    # At the start of the game or when we have very few moves, use randomness to explore
    if (confirmed_me + confirmed_opponent) < 3:
        return legal_moves[0]  # action_to_coord(legal_moves[np.random.choice(len(legal_moves))])
    
    # If we have a winning move, take it
    for move in legal_moves:
        board_temp = board.copy()
        r, c = action_to_coord(move)
        
        # Assume our move is successful and check if it leads to a win
        board_temp[r, c] = 1
        if check_win(board_temp, 1):
            return move
    
    # If we can't win immediately, try to block the opponent
    for move in legal_moves:
        board_temp = board.copy()
        r, c = action_to_coord(move)
        
        # Assume the opponent's move was this one (they might be trying to win)
        board_temp[r, c] = 2
        if check_win(board_temp, 2):
            return move
    
    # If no winning/blocking move is available, use minimax with alpha-beta pruning
    best_score = -np.inf
    best_move = legal_moves[0]
    
    for move in legal_moves:
        board_temp = board.copy()
        r, c = action_to_coord(move)
        board_temp[r, c] = 1  # Assume our move was successful
        is_empty = np.sum(board == 1) == confirmed_me  # True if the board didn't change (i.e., our mark was new)
        
        if not is_empty:
            continue  # Skip this move, as the cell already contained our mark
            
        score = minimax(board_temp, 0, False, -np.inf, np.inf)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def minimax(board, depth, is_maximizer, alpha, beta, max_depth=2):
    # Check if we have a terminal state or reached max depth
    if depth == max_depth:
        return evaluate(board)
    
    # Convert board to confirmed opponent marks if it's their turn
    if is_maximizer:
        confirmed_opponent = board.copy()
        confirmed_opponent[confirmed_opponent != 2] = 0
    else:
        player = 1 if is_maximizer else 2
        if check_win(board, player):
            return 1 if is_maximizer else -1
    
    # Generate possible states based on known information
    unmarked_cells = np.where(board == 0)
    possible_actions = [3 * r + c for r, c in zip(unmarked_cells[0], unmarked_cells[1])]
    
    if is_maximizer:
        # We're trying to maximize our chances
        max_val = -np.inf
        for action in possible_actions:
            r, c = action_to_coord(action)
            
            # Assume the opponent can successfully place in any unmarked cell
            board[r, c] = 2
            if check_win(board, 2):
                board[r, c] = 0
                return -1
            
            # If the opponent might win in their next move regardless, no need to explore further
            win_possible = any(
                check_win(board, 2) 
                for action2 in possible_actions if 3 * r2 + c2 == action
                for r2, c2 in action_to_coord(action2)
                if board[r2,c2] == 0
            )
            if win_possible:
                board[r, c] = 0
                continue
            
            # Otherwise, explore the state
            val = minimax(board, depth + 1, False, alpha, beta)
            board[r, c] = 0
            alpha = max(alpha, val)
            max_val = max(max_val, val)
            if beta <= alpha:
                break
        return max_val
    
    else:
        # We're trying to minimize losses (defensive play)
        min_val = np.inf
        for action in possible_actions:
            r, c = action_to_coord(action)
            
            # Assume our placement is successful
            board[r, c] = 1
            if check_win(board, 1):
                board[r, c] = 0
                return -1
                
            # Explore the state
            val = minimax(board, depth + 1, True, alpha, beta)
            board[r, c] = 0
            beta = min(beta, val)
            min_val = min(min_val, val)
            if beta <= alpha:
                break
        return min_val

def evaluate(board):
    # Prioritize winning, blocking, and choosing the center
    if check_win(board, 1):
        return 1  # AI wins
    elif check_win(board, 2):
        return -1  # Opponent could win
    elif board[1,1] == 0 and 5 in legal_moves:
        return 0.0  # Neutral, but center is available
    elif board[1,1] == 1 and 5 in legal_moves:
        return -0.5  # Already claimed, not ideal
    else:
        # Favor positions that increase winning potential
        potential_wins = 0
        # Check for two-in-a-row for AI
        for i in range(3):
            for j in range(3):
                # Check row, column, and both diagonals
                if np.sum(board[i, :]) >= 2 or np.sum(board[:, j]) >= 2 or (i == j == 1 and np.sum(board.diagonal()) >= 2) or (i != j and np.sum(np.fliplr(board)[i, j]) >= 2 and i == j):
                    potential_wins += 1
                    
        return potential_wins
