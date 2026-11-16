
import numpy as np

def policy(you, opponent):
    # Convert inputs to numpy arrays for easier handling
    you_board = np.array(you)
    opp_board = np.array(opponent)
    
    # Find all legal moves
    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 0 and opp_board[r][c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        legal_moves.append((r+1, c+1, quad, direction))
    
    # Try to find an immediate winning move
    for move in legal_moves:
        move_str = f"{move[0]},{move[1]},{move[2]},{move[3]}"
        new_you, new_opp = make_move(you_board.copy(), opp_board.copy(), move[0]-1, move[1]-1, move[2], move[3])
        if check_win(new_you):
            return move_str
    
    # Try to find an immediate blocking move
    for move in legal_moves:
        # Simulate opponent's move after our placement but before rotation
        temp_you = you_board.copy()
        temp_opp = opp_board.copy()
        temp_you[move[0]-1][move[1]-1] = 1  # Place our piece
        
        # Check all opponent responses
        opponent_has_win = False
        for r in range(6):
            for c in range(6):
                if temp_you[r][c] == 0 and temp_opp[r][c] == 0:
                    temp_opp[r][c] = 1
                    if check_win(temp_opp):
                        opponent_has_win = True
                    temp_opp[r][c] = 0
                    if opponent_has_win:
                        break
            if opponent_has_win:
                break
        
        if opponent_has_win:
            # If opponent has a winning response, we need to try this move to see if our rotation prevents it
            new_you, new_opp = make_move(you_board.copy(), opp_board.copy(), move[0]-1, move[1]-1, move[2], move[3])
            if check_win(new_opp): # Still a win for opponent
                continue # Not a good blocking move
            else:
                return f"{move[0]},{move[1]},{move[2]},{move[3]}"
    
    # Use minimax with alpha-beta pruning for deeper search
    best_move = legal_moves[0]
    best_value = float('-inf')
    depth = 2 # Adjustable depth for performance
    
    for move in legal_moves:
        new_you, new_opp = make_move(you_board.copy(), opp_board.copy(), move[0]-1, move[1]-1, move[2], move[3])
        value = minimax(new_opp, new_you, depth - 1, False, float('-inf'), float('inf'))  # Note the switch of roles
        if value > best_value:
            best_value = value
            best_move = move
            
    return f"{best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]}"


def make_move(you_board, opp_board, row, col, quad, direction):
    """Apply a move (place and rotate) to the board state."""
    # Place the piece
    you_board[row][col] = 1
    
    # Determine rotation boundaries
    if quad == 0:
        r_start, r_end = 0, 3
        c_start, c_end = 0, 3
    elif quad == 1:
        r_start, r_end = 0, 3
        c_start, c_end = 3, 6
    elif quad == 2:
        r_start, r_end = 3, 6
        c_start, c_end = 0, 3
    else: # quad == 3
        r_start, r_end = 3, 6
        c_start, c_end = 3, 6

    # Extract the quadrant
    you_quad = you_board[r_start:r_end, c_start:c_end].copy()
    opp_quad = opp_board[r_start:r_end, c_start:c_end].copy()

    # Rotate the quadrant
    if direction == 'L':  # Counter-clockwise
        you_board[r_start:r_end, c_start:c_end] = np.rot90(you_quad, k=1)
        opp_board[r_start:r_end, c_start:c_end] = np.rot90(opp_quad, k=1)
    else:  # Clockwise
        you_board[r_start:r_end, c_start:c_end] = np.rot90(you_quad, k=-1)
        opp_board[r_start:r_end, c_start:c_end] = np.rot90(opp_quad, k=-1)
        
    return you_board, opp_board


def check_win(board):
    """Check if the board has a winning condition (5 in a row)."""
    # Check rows
    for r in range(6):
        count = 0
        for c in range(6):
            if board[r][c] == 1:
                count += 1
                if count >= 5:
                    return True
            else:
                count = 0

    # Check columns
    for c in range(6):
        count = 0
        for r in range(6):
            if board[r][c] == 1:
                count += 1
                if count >= 5:
                    return True
            else:
                count = 0

    # Check diagonals
    for r in range(6):
        for c in range(6):
            # Diagonal down-right
            if r <= 2 and c <= 2:
                count = 0
                for i in range(5):
                    if board[r+i][c+i] == 1:
                        count += 1
                    else:
                        break
                if count == 5:
                    return True
            # Diagonal up-right
            if r >= 4 and c <= 2:
                count = 0
                for i in range(5):
                    if board[r-i][c+i] == 1:
                        count += 1
                    else:
                        break
                if count == 5:
                    return True
                    
    return False


def evaluate(you_board, opp_board):
    """Heuristic evaluation function."""
    score = 0
    
    # Simple features for evaluation
    # Count number of own pieces vs opponent pieces
    own_count = np.sum(you_board)
    opp_count = np.sum(opp_board)
    score += (own_count - opp_count) * 10
    
    # Evaluate lines of 2, 3, 4
    def count_lines(board, length):
        count = 0
        # Rows
        for r in range(6):
            for c in range(7-length):
                match = True
                empty = 0
                for i in range(length):
                    if board[r][c+i] != 1:
                        match = False
                        break
                if match:
                    # Check if ends are blocked
                    blocked_l = (c == 0 or board[r][c-1] != 0)
                    blocked_r = (c+length == 6 or board[r][c+length] != 0)
                    if not(blocked_l and blocked_r):
                        count += 1
                        
        # Cols
        for c in range(6):
            for r in range(7-length):
                match = True
                for i in range(length):
                    if board[r+i][c] != 1:
                        match = False
                        break
                if match:
                    blocked_u = (r == 0 or board[r-1][c] != 0)
                    blocked_d = (r+length == 6 or board[r+length][c] != 0)
                    if not(blocked_u and blocked_d):
                        count += 1
                        
        # Diags
        for r in range(7-length):
            for c in range(7-length):
                # Down-right
                match = True
                for i in range(length):
                    if board[r+i][c+i] != 1:
                        match = False
                        break
                if match:
                    blocked_ul = (r == 0 or c == 0 or (board[r-1][c-1] != 0))
                    blocked_dr = (r+length == 6 or c+length == 6 or (board[r+length][c+length] != 0))
                    if not(blocked_ul and blocked_dr):
                        count += 1
                        
                # Up-right
                match = True
                for i in range(length):
                    if board[r+length-1-i][c+i] != 1:
                        match = False
                        break
                if match:
                    blocked_ur = (r+length == 6 or c == 0 or (board[r+length][c-1] != 0))
                    blocked_dl = (r == 0 or c+length == 6 or (board[r-1][c+length] != 0))
                    if not(blocked_ur and blocked_dl):
                        count += 1
        return count
    
    score += count_lines(you_board, 2) * 20
    score += count_lines(you_board, 3) * 100
    score += count_lines(you_board, 4) * 10000
    
    score -= count_lines(opp_board, 2) * 20
    score -= count_lines(opp_board, 3) * 100
    score -= count_lines(opp_board, 4) * 10000
    
    # Bonus for centrality
    center_bonus = 0
    for r in range(6):
        for c in range(6):
            if you_board[r][c] == 1:
                center_bonus += 3 - abs(2.5 - r) - abs(2.5 - c)
    score += center_bonus * 5
    
    return score


def minimax(you_board, opp_board, depth, is_maximizing, alpha, beta):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or check_win(you_board) or check_win(opp_board):
        return evaluate(you_board, opp_board)
    
    if is_maximizing:
        max_eval = float('-inf')
        for r in range(6):
            for c in range(6):
                if you_board[r][c] == 0 and opp_board[r][c] == 0:
                    for quad in range(4):
                        for direction in ['L', 'R']:
                            new_you = you_board.copy()
                            new_opp = opp_board.copy()
                            new_you, new_opp = make_move(new_you, new_opp, r, c, quad, direction)
                            eval = minimax(new_opp, new_you, depth - 1, False, alpha, beta)  # Switch roles
                            max_eval = max(max_eval, eval)
                            alpha = max(alpha, eval)
                            if beta <= alpha:
                                return max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for r in range(6):
            for c in range(6):
                if you_board[r][c] == 0 and opp_board[r][c] == 0:
                    for quad in range(4):
                        for direction in ['L', 'R']:
                            new_you = you_board.copy()
                            new_opp = opp_board.copy()
                            new_opp, new_you = make_move(new_opp, new_you, r, c, quad, direction)  # Opponent places
                            eval = minimax(new_you, new_opp, depth - 1, True, alpha, beta)  # Switch roles
                            min_eval = min(min_eval, eval)
                            beta = min(beta, eval)
                            if beta <= alpha:
                                return min_eval
        return min_eval
