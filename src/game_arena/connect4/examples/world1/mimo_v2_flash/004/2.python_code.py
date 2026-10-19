
import numpy as np
import sys

# Increase recursion limit to handle deeper searches if necessary, 
# though our depth will be relatively small.
sys.setrecursionlimit(2000)

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI using Alpha-Beta Pruning with a heuristic evaluation function.
    """
    # Convert board to numpy array for easier manipulation, or keep as list of lists.
    # The input is already a list of lists.
    
    # Determine the current player (1) and opponent (-1).
    # In the provided board state, 1 is the current player.
    player = 1
    opponent = -1

    # Helper function to check for a winner
    def check_winner(b, piece):
        # Check horizontal locations
        for c in range(4):
            for r in range(6):
                if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                    return True
        # Check vertical locations
        for c in range(7):
            for r in range(3):
                if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                    return True
        # Check positively sloped diagonals
        for c in range(4):
            for r in range(3):
                if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                    return True
        # Check negatively sloped diagonals
        for c in range(4):
            for r in range(3, 6):
                if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                    return True
        return False

    # Helper to get valid locations
    def get_valid_locations(b):
        valid = []
        for col in range(7):
            if b[0][col] == 0: # Check top row
                valid.append(col)
        return valid

    # Helper to find the next open row in a column
    def get_next_open_row(b, col):
        for r in range(5, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    # Evaluation function
    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        
        count_piece = window.count(piece)
        count_empty = window.count(0)
        count_opp = window.count(opp_piece)

        if count_piece == 4:
            score += 100000 # Immediate win
        elif count_piece == 3 and count_empty == 1:
            score += 100 # Strong potential
        elif count_piece == 2 and count_empty == 2:
            score += 10 # Moderate potential

        if count_opp == 3 and count_empty == 1:
            score -= 80 # Block opponent's strong threat

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
                score += evaluate_window(list(window), piece)

        # Vertical
        for c in range(7):
            col_array = [b[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(list(window), piece)

        # Positive Sloped Diagonal
        for r in range(3):
            for c in range(4):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Negative Sloped Diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [b[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    # Minimax with Alpha-Beta Pruning
    def minimax(b, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(b)
        
        # Check terminal nodes (wins)
        if check_winner(b, player):
            return (None, 100000000000000)
        if check_winner(b, opponent):
            return (None, -100000000000000)
        if not valid_locations:
            return (None, 0)
        if depth == 0:
            return (None, score_position(b, player))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_locations[0]
            # Move ordering: Center columns first for better pruning
            valid_locations.sort(key=lambda x: abs(x - 3))
            
            for col in valid_locations:
                row = get_next_open_row(b, col)
                temp_b = [r[:] for r in b] # Deep copy
                temp_b[row][col] = player
                new_score = minimax(temp_b, depth - 1, alpha, beta, False)[1]
                
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = valid_locations[0]
            valid_locations.sort(key=lambda x: abs(x - 3))
            
            for col in valid_locations:
                row = get_next_open_row(b, col)
                temp_b = [r[:] for r in b]
                temp_b[row][col] = opponent
                new_score = minimax(temp_b, depth - 1, alpha, beta, True)[1]
                
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Main execution
    # 1. Check for immediate win
    valid_cols = get_valid_locations(board)
    for col in valid_cols:
        row = get_next_open_row(board, col)
        # Simulate move
        board[row][col] = 1
        if check_winner(board, 1):
            board[row][col] = 0 # Undo move (though the environment likely resets)
            return col
        board[row][col] = 0 # Undo

    # 2. Check for immediate block (opponent winning next move)
    for col in valid_cols:
        row = get_next_open_row(board, col)
        board[row][col] = -1
        if check_winner(board, -1):
            board[row][col] = 0
            return col
        board[row][col] = 0

    # 3. Lookahead with Alpha-Beta
    # Depth 5 is usually safe for 1 second on a 3GHz CPU for Connect 4
    best_move, _ = minimax(board, 5, -float('inf'), float('inf'), True)
    
    # Fallback if something goes wrong (should not happen on a non-full board)
    if best_move is None and valid_cols:
        return valid_cols[0]
        
    return best_move
