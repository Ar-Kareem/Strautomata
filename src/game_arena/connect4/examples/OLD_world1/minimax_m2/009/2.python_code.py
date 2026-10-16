
import math

def policy(board: list[list[int]]) -> int:
    def get_valid_columns(board):
        valid = []
        for col in range(7):
            if board[0][col] == 0:
                valid.append(col)
        return valid
    
    def get_next_open_row(board, col):
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1
    
    def winning_move(board, piece):
        for r in range(6):
            for c in range(4):
                if (board[r][c] == piece and board[r][c+1] == piece and
                    board[r][c+2] == piece and board[r][c+3] == piece):
                    return True
        for c in range(7):
            for r in range(3):
                if (board[r][c] == piece and board[r+1][c] == piece and
                    board[r+2][c] == piece and board[r+3][c] == piece):
                    return True
        for r in range(3):
            for c in range(4):
                if (board[r][c] == piece and board[r+1][c+1] == piece and
                    board[r+2][c+2] == piece and board[r+3][c+3] == piece):
                    return True
        for r in range(3):
            for c in range(3, 7):
                if (board[r][c] == piece and board[r+1][c-1] == piece and
                    board[r+2][c-2] == piece and board[r+3][c-3] == piece):
                    return True
        return False
    
    def evaluate_window(window, player):
        score = 0
        opp = -player
        count_player = window.count(player)
        count_opp = window.count(opp)
        count_empty = window.count(0)
        
        if count_player == 4:
            score += 100000
        elif count_player == 3 and count_empty == 1:
            score += 1000
        elif count_player == 2 and count_empty == 2:
            score += 100
        elif count_player == 1 and count_empty == 3:
            score += 1
            
        if count_opp == 4:
            score -= 100000
        elif count_opp == 3 and count_empty == 1:
            score -= 10000
        elif count_opp == 2 and count_empty == 2:
            score -= 100
        elif count_opp == 1 and count_empty == 3:
            score -= 1
            
        return score
    
    def score_board(board, player):
        score = 0
        center_col = 3
        center_array = [board[r][center_col] for r in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        for r in range(6):
            row = [board[r][c] for c in range(7)]
            for c in range(4):
                window = row[c:c+4]
                score += evaluate_window(window, player)
                
        for c in range(7):
            col = [board[r][c] for r in range(6)]
            for r in range(3):
                window = col[r:r+4]
                score += evaluate_window(window, player)
                
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player)
                
        for r in range(3):
            for c in range(3, 7):
                window = [board[r+i][c-i] for i in range(4)]
                score += evaluate_window(window, player)
                
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_columns = get_valid_columns(board)
        
        if winning_move(board, 1):
            return (100000000, None)
        if winning_move(board, -1):
            return (-100000000, None)
        if depth == 0 or len(valid_columns) == 0:
            return (score_board(board, 1), None)
        
        center = 3
        valid_columns.sort(key=lambda x: abs(x - center))
        
        if maximizing_player:
            max_eval = -100000000
            best_col = valid_columns[0] if valid_columns else None
            for col in valid_columns:
                new_board = [row[:] for row in board]
                row = get_next_open_row(board, col)
                if row == -1:
                    continue
                new_board[row][col] = 1
                eval_score = minimax(new_board, depth-1, alpha, beta, False)[0]
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return (max_eval, best_col)
        else:
            min_eval = 100000000
            best_col = valid_columns[0] if valid_columns else None
            for col in valid_columns:
                new_board = [row[:] for row in board]
                row = get_next_open_row(board, col)
                if row == -1:
                    continue
                new_board[row][col] = -1
                eval_score = minimax(new_board, depth-1, alpha, beta, True)[0]
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return (min_eval, best_col)
    
    depth = 4
    _, col = minimax(board, depth, -math.inf, math.inf, True)
    return col
