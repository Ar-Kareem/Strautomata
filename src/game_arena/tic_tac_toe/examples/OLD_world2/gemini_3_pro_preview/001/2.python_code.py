
import random

# Precompute line indices for 4x4 board to optimize checking
# This allows checking wins/scores without recreating list objects constantly
_LINES = []
# Rows
for r in range(4):
    _LINES.append([(r, c) for c in range(4)])
# Columns
for c in range(4):
    _LINES.append([(r, c) for r in range(4)])
# Diagonals
_LINES.append([(i, i) for i in range(4)])
_LINES.append([(i, 3 - i) for i in range(4)])

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.
    
    Args:
        board: 4x4 list of lists containing 0 (empty), 1 (AI), -1 (Opponent).
        
    Returns:
        (row, col) tuple coordinates (0-3).
    """
    
    ME = 1
    OPP = -1
    EMPTY = 0
    
    # --- Helper Functions ---
    
    def get_valid_moves(b):
        """Return list of (r, c) tuples for all empty spots."""
        return [(r, c) for r in range(4) for c in range(4) if b[r][c] == EMPTY]

    def is_terminal(b):
        """
        Check if the game is over.
        Returns: (is_over: bool, score: int)
        Score is extremely high for ME win, extremely low for OPP win, 0 for draw.
        """
        # Check winning lines
        for line in _LINES:
            s = 0
            for r, c in line:
                s += b[r][c]
            
            if s == 4: return True, 1000000
            if s == -4: return True, -1000000
        
        # Check for draw (no empty spots)
        for r in range(4):
            for c in range(4):
                if b[r][c] == EMPTY:
                    return False, 0
                    
        return True, 0

    def evaluate(b):
        """
        Heuristic evaluation of the board from ME's perspective.
        Called when search completes without a terminal state.
        """
        score = 0
        for line in _LINES:
            my_count = 0
            opp_count = 0
            for r, c in line:
                val = b[r][c]
                if val == ME:
                    my_count += 1
                elif val == OPP:
                    opp_count += 1
            
            # If a line has both markers, it's useless for winning
            if my_count > 0 and opp_count > 0:
                continue
            
            # Scoring Logic: 3-in-line is much better than 2, etc.
            if my_count > 0:
                if my_count == 4: return 1000000 # Should be caught by is_terminal
                if my_count == 3: score += 5000
                if my_count == 2: score += 100
                if my_count == 1: score += 10
            elif opp_count > 0:
                if opp_count == 4: return -1000000
                if opp_count == 3: score -= 5000
                if opp_count == 2: score -= 100
                if opp_count == 1: score -= 10
                
        return score

    def minimax(b, depth, alpha, beta, is_maximizing):
        """
        Minimax w/ Alpha-Beta Pruning.
        """
        is_over, score = is_terminal(b)
        if is_over:
            # Adjust score based on depth to prefer faster wins / slower losses
            if score > 0: score += depth
            if score < 0: score -= depth
            return score
        
        if depth == 0:
            return evaluate(b)
        
        moves = get_valid_moves(b)
        
        if is_maximizing:
            max_eval = -float('inf')
            for r, c in moves:
                b[r][c] = ME
                eval_val = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = EMPTY
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in moves:
                b[r][c] = OPP
                eval_val = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = EMPTY
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Strategy Logic ---
    
    valid_moves = get_valid_moves(board)
    
    # Edge case: Board full
    if not valid_moves:
        return (0, 0)

    # 1. Instant Win/Loss Check (Optimization)
    # Before running recursion, check if we can win NOW or must block NOW.
    
    # Check for Winning Move
    for r, c in valid_moves:
        board[r][c] = ME
        over, score = is_terminal(board)
        board[r][c] = EMPTY
        if over and score > 0:
            return (r, c)

    # Check for Forced Block
    for r, c in valid_moves:
        board[r][c] = OPP
        over, score = is_terminal(board)
        board[r][c] = EMPTY
        if over and score < 0:
            return (r, c)

    # 2. Determine Search Depth
    # 4x4 state space is large. Adjust depth based on remaining empty cells to fit time limits.
    empty_count = len(valid_moves)
    
    if empty_count >= 14:
        depth = 2 # Opening: fast search, rely on heuristics/center control
    elif empty_count >= 10:
        depth = 4 # Mid-game: look 4 plies ahead
    elif empty_count >= 6:
        depth = 5 # Deep mid-game
    else:
        depth = 7 # End-game: nearly solving locally

    # 3. Execute Minimax to find best move
    best_move = valid_moves[0]
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Move Ordering: Check moves near center first to improve Alpha-Beta pruning efficiency
    # Center of 4x4 is roughly (1.5, 1.5)
    valid_moves.sort(key=lambda m: abs(m[0]-1.5) + abs(m[1]-1.5))

    for r, c in valid_moves:
        board[r][c] = ME
        val = minimax(board, depth - 1, alpha, beta, False)
        board[r][c] = EMPTY
        
        if val > best_val:
            best_val = val
            best_move = (r, c)
        
        alpha = max(alpha, val)
        
    return best_move
