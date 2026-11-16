
import sys

def policy(board: list[list[int]]) -> int:
    """
    AI Policy for Connect 4 using Alpha-Beta Pruning.
    """
    
    # Helper to check for a win
    def check_win(b, player):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # Vertical
        for r in range(3):
            for c in range(7):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Diagonal /
        for r in range(3):
            for c in range(4):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # Diagonal \
        for r in range(3, 6):
            for c in range(4):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False

    # Helper to get valid moves (non-full columns)
    def get_valid_moves(b):
        moves = []
        for c in range(7):
            if b[0][c] == 0:
                moves.append(c)
        return moves

    # Helper to drop a disc
    def get_next_row(b, col):
        for r in range(5, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    # Evaluation function
    def evaluate_window(window, piece):
        opp_piece = -1 if piece == 1 else 1
        score = 0
        count_piece = window.count(piece)
        count_empty = window.count(0)
        count_opp = window.count(opp_piece)

        if count_piece == 4:
            score += 10000
        elif count_piece == 3 and count_empty == 1:
            score += 100
        elif count_piece == 2 and count_empty == 2:
            score += 10
        
        # Blocking opponent
        if count_opp == 3 and count_empty == 1:
            score -= 80 # Strong penalty if opponent is about to win
            
        return score

    def score_position(b, piece):
        score = 0
        
        # Center column preference
        center_array = [b[r][3] for r in range(6)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Horizontal
        for r in range(6):
            row_array = b[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Vertical
        for c in range(7):
            col_array = [b[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Positive Diagonal
        for r in range(3):
            for c in range(4):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Negative Diagonal
        for r in range(3):
            for c in range(4):
                window = [b[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    # Minimax with Alpha-Beta Pruning
    def minimax(b, depth, alpha, beta, maximizingPlayer):
        valid_moves = get_valid_moves(b)
        is_terminal = check_win(b, 1) or check_win(b, -1) or len(valid_moves) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(b, 1):
                    return (None, 100000000000000)
                elif check_win(b, -1):
                    return (None, -100000000000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(b, 1))

        # Move ordering: Center columns first
        valid_moves.sort(key=lambda x: abs(x - 3))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_moves[0]
            for col in valid_moves:
                r = get_next_row(b, col)
                temp_b = [row[:] for row in b] # Copy board
                temp_b[r][col] = 1
                new_score = minimax(temp_b, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = valid_moves[0]
            for col in valid_moves:
                r = get_next_row(b, col)
                temp_b = [row[:] for row in b] # Copy board
                temp_b[r][col] = -1
                new_score = minimax(temp_b, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # 1. Check for Immediate Win
    valid_moves = get_valid_moves(board)
    for col in valid_moves:
        r = get_next_row(board, col)
        temp_b = [row[:] for row in board]
        temp_b[r][col] = 1
        if check_win(temp_b, 1):
            return col

    # 2. Check for Immediate Block (Opponent Win)
    for col in valid_moves:
        r = get_next_row(board, col)
        temp_b = [row[:] for row in board]
        temp_b[r][col] = -1
        if check_win(temp_b, -1):
            return col

    # 3. Run Minimax Search (Depth 5 is a good balance for 1s limit in Python)
    best_move, _ = minimax(board, 5, -float('inf'), float('inf'), True)
    
    return best_move
