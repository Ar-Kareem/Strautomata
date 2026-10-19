
import math

def policy(board: list[list[int]]) -> int:
    def is_valid_move(col):
        return board[0][col] == 0
    
    def get_valid_moves():
        return [col for col in range(7) if is_valid_move(col)]
    
    def make_move(new_board, col, player):
        # Create a copy of the board
        result = [row[:] for row in new_board]
        # Drop the disc
        for row in range(5, -1, -1):
            if result[row][col] == 0:
                result[row][col] = player
                break
        return result
    
    def check_winner(b):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if b[row][col] != 0 and b[row][col] == b[row][col+1] == b[row][col+2] == b[row][col+3]:
                    return b[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if b[row][col] != 0 and b[row][col] == b[row+1][col] == b[row+2][col] == b[row+3][col]:
                    return b[row][col]
        
        # Check diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if b[row][col] != 0 and b[row][col] == b[row+1][col+1] == b[row+2][col+2] == b[row+3][col+3]:
                    return b[row][col]
        
        # Check diagonal (up-right)
        for row in range(3, 6):
            for col in range(4):
                if b[row][col] != 0 and b[row][col] == b[row-1][col+1] == b[row-2][col+2] == b[row-3][col+3]:
                    return b[row][col]
        
        return 0
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        if window.count(player) == 4:
            score += 1000
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 100
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 10
        
        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 100
            
        return score
    
    def evaluate_board(b, player):
        score = 0
        
        # Score center column preference
        center_array = [b[row][3] for row in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Score horizontal
        for row in range(6):
            for col in range(4):
                window = [b[row][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score vertical
        for row in range(3):
            for col in range(7):
                window = [b[row+i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score positive diagonal
        for row in range(3):
            for col in range(4):
                window = [b[row+i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score negative diagonal
        for row in range(3, 6):
            for col in range(4):
                window = [b[row-i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
                
        return score
    
    def minimax(b, depth, alpha, beta, maximizing_player, player):
        valid_moves = get_valid_moves()
        is_terminal = check_winner(b) != 0 or len(valid_moves) == 0
        opponent = -player
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_winner(b) == player:
                    return (None, 10000000000000)
                elif check_winner(b) == opponent:
                    return (None, -10000000000000)
                else:  # Game is over, no more valid moves
                    return (None, 0)
            else:  # Depth is zero
                return (None, evaluate_board(b, player))
        
        if maximizing_player:
            value = -math.inf
            column = valid_moves[0]
            for col in valid_moves:
                new_board = make_move(b, col, player)
                new_score = minimax(new_board, depth-1, alpha, beta, False, player)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:  # Minimizing player
            value = math.inf
            column = valid_moves[0]
            for col in valid_moves:
                new_board = make_move(b, col, opponent)
                new_score = minimax(new_board, depth-1, alpha, beta, True, player)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
    
    # Determine search depth based on board state
    valid_moves_count = len(get_valid_moves())
    if valid_moves_count <= 3:
        depth = 7
    elif valid_moves_count <= 5:
        depth = 6
    else:
        depth = 5
    
    # Check for immediate winning move
    for col in get_valid_moves():
        new_board = make_move(board, col, 1)
        if check_winner(new_board) == 1:
            return col
    
    # Check for opponent's immediate winning move to block
    for col in get_valid_moves():
        new_board = make_move(board, col, -1)
        if check_winner(new_board) == -1:
            return col
    
    # Use minimax to select best move
    column, _ = minimax(board, depth, -math.inf, math.inf, True, 1)
    return column if column is not None else get_valid_moves()[0]
