
import numpy as np

def policy(board):
    np_board = np.array(board)
    
    def is_win(b, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Check diagonal (down-left to up-right)
        for r in range(3):
            for c in range(4):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # Check diagonal (down-right to up-left)
        for r in range(3, 6):
            for c in range(4):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False
    
    def simulate_move(b, p, col):
        new_board = b.copy()
        # Find the lowest available row in the column
        for row in reversed(range(6)):
            if new_board[row, col] == 0:
                new_board[row, col] = p
                return new_board
        return None  # This line is theoretically unreachable as we only pass valid moves
    
    def evaluate_board(b, player):
        my_score = 0
        opp_score = 0
        for r in range(6):
            for c in range(7):
                val = b[r, c]
                if val == 1:
                    my_score += (5 - r)  # Prefer lower rows
                elif val == -1:
                    opp_score += (5 - r)
        return my_score - opp_score if player == 1 else opp_score - my_score
    
    def minimax(b, player, depth, alpha, beta):
        # Check terminal states
        if is_win(b, 1):
            return float('inf') if player == 1 else -float('inf')
        if is_win(b, -1):
            return float('-inf') if player == 1 else float('inf')
        # Check if board is full or depth reached
        if not np.any(b == 0) or depth == 0:
            return evaluate_board(b, player)
        
        moves = [c for c in range(7) if b[5][c] == 0]
        best_score = -float('inf') if player == 1 else float('inf')
        
        for col in moves:
            new_board = simulate_move(b, player, col)
            # Check if current move leads to win
            if is_win(new_board, player):
                score = float('inf') if player == 1 else float('-inf')
            else:
                score = minimax(new_board, -player, depth - 1, alpha, beta)
            
            if player == 1:
                if score > best_score:
                    best_score = score
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                beta = min(beta, best_score)
            # Prune
            if alpha >= beta:
                break
        return best_score
    
    legal_moves = [col for col in range(7) if np.any(np_board[:, col] == 0)]
    
    # Check for immediate winning moves
    for col in legal_moves:
        new_b = simulate_move(np_board, 1, col)
        if is_win(new_b, 1):
            return col
    
    # Check for safe moves (opponent can't win next turn)
    safe_moves = []
    for col in legal_moves:
        new_board = simulate_move(np_board, 1, col)
        opp_moves = [c for c in range(7) if np.any(np_board[:, c] == 0)]
        opponent_can_win = False
        for opp_col in opp_moves:
            opp_board = simulate_move(new_board, -1, opp_col)
            if is_win(opp_board, -1):
                opponent_can_win = True
                break
        if not opponent_can_win:
            safe_moves.append(col)
    
    if safe_moves:
        best_score = -float('inf')
        best_col = safe_moves[0]
        for col in safe_moves:
            if col == col:  # To ensure we're iterating correctly in case of variable scoping issues
                new_b = simulate_move(np_board, 1, col)
                score = minimax(new_b, -1, 4, -float('inf'), float('inf'))
                if score > best_score:
                    best_score = score
                    best_col = col
        return best_col
    else:
        # All initial moves allow opponent to win next turn; choose the one with least opponent's winning moves
        best_col = legal_moves[0]
        min_opponent_score = float('inf')
        for col in legal_moves:
            new_board = simulate_move(np_board, 1, col)
            count = 0
            opp_moves = [c for c in range(7) if new_board[5][c] == 0]
            for opp_col in opp_moves:
                temp_board = simulate_move(new_board, -1, opp_col)
                if is_win(temp_board, -1):
                    count += 1
            if count < min_opponent_score:
                min_opponent_score = count
                best_col = col
        return best_col
