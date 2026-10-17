
import numpy as np
import time

# --- Constants ---

# Directions (row_offset, col_offset)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

# Static weights for positional evaluation
# Corners are 100, Adjacent to corners are negative (risk of giving corner)
WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
])

class TimeoutException(Exception):
    pass

# --- Helper Functions ---

def is_on_board(r, c):
    """Check if coordinates are within the 8x8 board."""
    return 0 <= r < 8 and 0 <= c < 8

def get_legal_moves(my_board, opp_board):
    """Returns a list of (r, c) tuples for valid moves."""
    moves = []
    # Identify empty squares
    empty_rows, empty_cols = np.where((my_board == 0) & (opp_board == 0))
    for r, c in zip(empty_rows, empty_cols):
        if is_valid_move(my_board, opp_board, r, c):
            moves.append((r, c))
    return moves

def is_valid_move(my_board, opp_board, r, c):
    """Checks if a specific move is valid."""
    for dr, dc in DIRECTIONS:
        if check_flip(my_board, opp_board, r, c, dr, dc):
            return True
    return False

def check_flip(my_board, opp_board, r, c, dr, dc):
    """Checks if placing piece at r,c flips opponent pieces in direction dr,dc."""
    nr, nc = r + dr, c + dc
    if not is_on_board(nr, nc) or opp_board[nr, nc] == 0:
        return False
    
    nr += dr
    nc += dc
    while is_on_board(nr, nc):
        if my_board[nr, nc] == 1:
            return True # Closed the line
        if opp_board[nr, nc] == 0:
            return False # Empty gap
        nr += dr
        nc += dc
    return False

def make_move(my_board, opp_board, r, c):
    """Returns new (my_board, opp_board) after playing at r, c."""
    new_my = my_board.copy()
    new_opp = opp_board.copy()
    new_my[r, c] = 1
    
    for dr, dc in DIRECTIONS:
        if check_flip(my_board, opp_board, r, c, dr, dc):
            nr, nc = r + dr, c + dc
            while new_opp[nr, nc] == 1:
                new_opp[nr, nc] = 0
                new_my[nr, nc] = 1
                nr += dr
                nc += dc
    return new_my, new_opp

def evaluate(my_board, opp_board):
    """Heuristic evaluation of the board state."""
    my_count = np.sum(my_board)
    opp_count = np.sum(opp_board)
    total_discs = my_count + opp_count
    
    if total_discs == 0: return 0 

    # 1. Positional Score (Static Weights)
    pos_score = np.sum(WEIGHTS * (my_board - opp_board))
    
    # 2. Mobility (Number of legal moves)
    # Note: This is computationally expensive, but valuable. 
    # For very deep searches, this might be approximated.
    my_moves = len(get_legal_moves(my_board, opp_board))
    opp_moves = len(get_legal_moves(opp_board, my_board))
    
    if my_moves + opp_moves > 0:
        mobility = 100 * (my_moves - opp_moves) / (my_moves + opp_moves)
    else:
        mobility = 0

    # 3. Coin Parity (Stronger in endgame)
    parity = 100 * (my_count - opp_count) / total_discs

    # Phase-based weights mixture
    if total_discs < 20: 
        # Opening: Focus on Mobility and good positioning
        return pos_score + 10 * mobility
    elif total_discs <= 58:
        # Midgame: Balance
        return pos_score + 5 * mobility + 2 * parity
    else:
        # Endgame: Absolute Score matters most
        return parity * 1000

# --- Main Policy ---

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start_time = time.time()
    
    # Identify legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    # Parse format requirement: If no moves, return "pass"
    if not legal_moves:
        return "pass"
    
    # Internal Alpha-Beta Recursive Function
    def alphabeta(my_board, opp_board, depth, alpha, beta, maximizing):
        # Time check: stop recursion if we are close to timeout
        if time.time() - start_time > 0.90:
            raise TimeoutException()

        if depth == 0:
            return evaluate(my_board, opp_board)
            
        moves = get_legal_moves(my_board, opp_board)
        if not moves:
            # Must pass
            # Check if opponent also has no moves (Game Over)
            opp_moves_check = get_legal_moves(opp_board, my_board)
            if not opp_moves_check:
                diff = np.sum(my_board) - np.sum(opp_board)
                return diff * 10000 # High magnitude for win
            
            # Continue with pass: swap roles, decrement depth
            return -alphabeta(opp_board, my_board, depth - 1, -beta, -alpha, not maximizing)
        
        # Move ordering heuristic: Sort by static weights to improve pruning
        moves.sort(key=lambda m: WEIGHTS[m[0], m[1]], reverse=True)
        
        best_score = -float('inf')
        
        for r, c in moves:
            new_my, new_opp = make_move(my_board, opp_board, r, c)
            # Recursion: Swap perspective (my_board becomes opp_board for next call)
            # Negamax structure: return -alphabeta(...)
            val = -alphabeta(new_opp, new_my, depth - 1, -beta, -alpha, not maximizing)
            
            if val > best_score:
                best_score = val
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break # Prune
                
        return best_score

    # Iterative Deepening
    best_move = legal_moves[0]
    # Sorting legal moves at root for faster initial alpha-beta
    legal_moves.sort(key=lambda m: WEIGHTS[m[0], m[1]], reverse=True)
    
    try:
        # Try depths 1 through 9
        for depth in range(1, 10):
            best_move_iter = None
            best_score_iter = -float('inf')
            
            # Reset alpha/beta for root of new depth
            alpha = -float('inf')
            beta = float('inf')
            
            # Root level move loop
            for r, c in legal_moves:
                new_my, new_opp = make_move(you, opponent, r, c)
                # Call recursive search
                score = -alphabeta(new_opp, new_my, depth - 1, -beta, -alpha, False)
                
                if score > best_score_iter:
                    best_score_iter = score
                    best_move_iter = (r, c)
                
                # Update alpha at root
                alpha = max(alpha, score)
            
            # If we completed the depth without timeout, update global best_move
            if best_move_iter is not None:
                best_move = best_move_iter
                
            # Time Heuristic: 
            # If we have already used > 100ms, the next depth (approx 10x slower) will likely timeout.
            # Python constraint is 1000ms.
            if time.time() - start_time > 0.1:
                break
                
    except TimeoutException:
        pass # Return the best move found in previous fully completed ID iteration

    # Convert coordinates to algebraic format e.g., (3, 0) -> "a4"
    r, c = best_move
    return f"{chr(c + ord('a'))}{r + 1}"
