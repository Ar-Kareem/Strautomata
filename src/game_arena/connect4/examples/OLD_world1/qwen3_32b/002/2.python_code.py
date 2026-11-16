
import math
import random

def policy(board: list[list[int]]) -> int:
    def get_valid_locations(board):
        return [col for col in range(7) if board[0][col] == 0]
    
    def drop_piece(board, col, piece):
        new_board = [row[:] for row in board]
        for r in reversed(range(6)):
            if new_board[r][col] == 0:
                new_board[r][col] = piece
                return new_board
        return None  # Should not happen if column is valid
    
    def is_winning(board, piece):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c + i] == piece for i in range(4)):
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if all(board[r + i][c] == piece for i in range(4)):
                    return True
        # Check positive slope diagonals
        for r in range(3, 6):
            for c in range(4):
                if all(board[r - i][c + i] == piece for i in range(4)):
                    return True
        # Check negative slope diagonals
        for r in range(3):
            for c in range(4):
                if all(board[r + i][c + i] == piece for i in range(4)):
                    return True
        return False
    
    def evaluate_line(line):
        count_1 = line.count(1)
        count_neg1 = line.count(-1)
        if count_1 + count_neg1 == 4:
            if count_1 == 4:
                return 100
            elif count_neg1 == 4:
                return -100
            else:
                return 0
        if count_1 > 0 and count_neg1 > 0:
            return 0
        if count_1 > 0:
            if count_1 == 3:
                return 10
            elif count_1 == 2:
                return 3
            elif count_1 == 1:
                return 1
            else:
                return 0
        elif count_neg1 > 0:
            if count_neg1 == 3:
                return -10
            elif count_neg1 == 2:
                return -3
            elif count_neg1 == 1:
                return -1
            else:
                return 0
        else:
            return 0
    
    def score_position(board):
        score = 0
        
        # Bonus for center column
        center_column = [row[3] for row in board]
        center_count = center_column.count(1) - center_column.count(-1)
        score += center_count * 3
        
        # Evaluate horizontal lines
        for r in range(6):
            for c in range(4):
                line = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
                score += evaluate_line(line)
        
        # Evaluate vertical lines
        for c in range(7):
            for r in range(3):
                line = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
                score += evaluate_line(line)
        
        # Evaluate positive slope diagonals
        for r in range(3, 6):
            for c in range(4):
                line = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
                score += evaluate_line(line)
        
        # Evaluate negative slope diagonals
        for r in range(3):
            for c in range(4):
                line = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
                score += evaluate_line(line)
        
        return score
    
    def is_terminal_node(board):
        return is_winning(board, 1) or is_winning(board, -1) or len(get_valid_locations(board)) == 0
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_locations(board)
        is_terminal = is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning(board, 1):
                    return (1000000000, None)
                elif is_winning(board, -1):
                    return (-1000000000, None)
                else:  # Game is a draw
                    return (0, None)
            else:
                return (score_position(board), None)
        
        if maximizing_player:
            max_score = -math.inf
            best_col = random.choice(valid_moves)
            for col in valid_moves:
                new_board = drop_piece(board, col, 1)
                _, current_score = minimax(new_board, depth-1, alpha, beta, False)
                if current_score > max_score:
                    max_score = current_score
                    best_col = col
                alpha = max(alpha, current_score)
                if alpha >= beta:
                    break
            return max_score, best_col
        else:  # Minimizing player (opponent)
            min_score = math.inf
            best_col = random.choice(valid_moves)
            for col in valid_moves:
                new_board = drop_piece(board, col, -1)
                _, current_score = minimax(new_board, depth-1, alpha, beta, True)
                if current_score < min_score:
                    min_score = current_score
                    best_col = col
                beta = min(beta, current_score)
                if alpha >= beta:
                    break
            return min_score, best_col
    
    # Check for immediate win
    valid_moves = get_valid_locations(board)
    for col in valid_moves:
        temp_board = drop_piece(board, col, 1)
        if is_winning(temp_board, 1):
            return col
    
    # Check for immediate opponent win and block
    for col in valid_moves:
        temp_board = drop_piece(board, col, -1)
        if is_winning(temp_board, -1):
            return col
    
    # Perform minimax search
    _, best_col = minimax(board, depth=4, alpha=-math.inf, beta=math.inf, maximizing_player=True)
    return best_col
