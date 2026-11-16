
import random

def policy(board: list[list[int]]) -> int:
    def get_next_open_row(col, current_board):
        for r in range(5, -1, -1):  # Check from bottom up
            if current_board[r][col] == 0:
                return r
        return -1  # This case should not happen
    
    def get_valid_columns(current_board):
        valid_cols = []
        for col in range(7):
            if current_board[0][col] == 0:
                valid_cols.append(col)
        return valid_cols
    
    def is_winning(current_board, player):
        # Check rows
        for r in range(6):
            for c in range(4):
                if all(current_board[r][c + i] == player for i in range(4)):
                    return True
        # Check columns
        for c in range(7):
            for r in range(3):
                if all(current_board[r + i][c] == player for i in range(4)):
                    return True
        # Check positive slope diagonals
        for r in range(3):
            for c in range(4):
                if all(current_board[r + i][c + i] == player for i in range(4)):
                    return True
        # Check negative slope diagonals
        for r in range(3, 6):
            for c in range(4):
                if all(current_board[r - i][c + i] == player for i in range(4)):
                    return True
        return False
    
    def simulate_move(current_board, col, player):
        new_board = [row[:] for row in current_board]
        r = get_next_open_row(col, new_board)
        if r != -1:
            new_board[r][col] = player
        return new_board
    
    def score_window(window, player):
        other_piece = -1 if player == 1 else 1
        if other_piece in window:
            return 0
        count = window.count(player)
        if count == 4:
            return 100
        elif count == 3:
            return 50
        elif count == 2:
            return 10
        else:
            return 0
    
    def evaluate_board(current_board):
        score = 0
        # Center column bonus
        center_array = [row[3] for row in current_board]
        center_count = center_array.count(1)
        score += center_count * 6
        center_count_opp = center_array.count(-1)
        score -= center_count_opp * 6
        
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [current_board[r][c], current_board[r][c+1], current_board[r][c+2], current_board[r][c+3]]
                score += score_window(window, 1)
                score -= score_window(window, -1)
        
        # Vertical
        for c in range(7):
            for r in range(3):
                window = [current_board[r][c], current_board[r+1][c], current_board[r+2][c], current_board[r+3][c]]
                score += score_window(window, 1)
                score -= score_window(window, -1)
        
        # Positive slope diagonal
        for r in range(3):
            for c in range(4):
                window = [current_board[r][c], current_board[r+1][c+1], current_board[r+2][c+2], current_board[r+3][c+3]]
                score += score_window(window, 1)
                score -= score_window(window, -1)
        
        # Negative slope diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [current_board[r][c], current_board[r-1][c+1], current_board[r-2][c+2], current_board[r-3][c+3]]
                score += score_window(window, 1)
                score -= score_window(window, -1)
        
        return score
    
    def minimax(current_board, depth, alpha, beta, maximizing):
        valid_cols = get_valid_columns(current_board)
        is_terminal = is_winning(current_board, 1) or is_winning(current_board, -1)
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning(current_board, 1):
                    return (None, 1000000)
                elif is_winning(current_board, -1):
                    return (None, -1000000)
                else:  # No valid moves left (draw)
                    return (None, 0)
            else:
                return (None, evaluate_board(current_board))
        if maximizing:
            best_score = -float('inf')
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_board = simulate_move(current_board, col, 1)
                if is_winning(new_board, 1):
                    return (col, float('inf'))
                # Recursively evaluate the opponent's move
                _, score = minimax(new_board, depth-1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_col = col
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            return (best_col, best_score)
        else:
            best_score = float('inf')
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_board = simulate_move(current_board, col, -1)
                if is_winning(new_board, -1):
                    return (col, -float('inf'))
                # Recursively evaluate AI's move
                _, score = minimax(new_board, depth-1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_col = col
                beta = min(beta, best_score)
                if alpha >= beta:
                    break
            return (best_col, best_score)
    
    # Check for immediate win
    valid_cols = get_valid_columns(board)
    for col in valid_cols:
        new_b = simulate_move(board, col, 1)
        if is_winning(new_b, 1):
            return col
    # Perform minimax search for deeper steps
    best_col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return best_col
