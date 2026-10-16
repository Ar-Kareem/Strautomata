
import math

# Constants representing players and empty cells
ME = 1
OPPONENT = -1
EMPTY = 0

def check_win(board, player):
    """
    Checks if the specified player has won the game.
    Returns True if the player has 4 in a row, column, or diagonal.
    """
    # Check rows
    for r in range(4):
        if all(board[r][c] == player for c in range(4)):
            return True
    # Check columns
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3-i] == player for i in range(4)):
        return True
    return False

def evaluate_board(board):
    """
    Heuristic evaluation function for non-terminal states.
    Scores the board based on the number of consecutive pieces in potential lines.
    """
    score = 0
    lines = []
    
    # Rows
    for r in range(4):
        lines.append(board[r])
    # Columns
    for c in range(4):
        lines.append([board[r][c] for r in range(4)])
    # Diagonals
    lines.append([board[i][i] for i in range(4)])
    lines.append([board[i][3-i] for i in range(4)])
    
    for line in lines:
        count_me = line.count(ME)
        count_opp = line.count(OPPONENT)
        
        # If both players are in the line, it is blocked and worthless
        if count_me > 0 and count_opp > 0:
            continue
            
        # Exponential scoring to prioritize completing lines
        if count_me > 0:
            score += 10 ** count_me
        if count_opp > 0:
            score -= 10 ** count_opp
            
    return score

def get_ordered_moves(board):
    """
    Returns a list of empty cells (row, col) ordered by strategic value:
    Center -> Corners -> Edges.
    """
    centers = [(1,1), (1,2), (2,1), (2,2)]
    corners = [(0,0), (0,3), (3,0), (3,3)]
    edges = [(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    
    moves = []
    for r, c in centers:
        if board[r][c] == EMPTY:
            moves.append((r, c))
    for r, c in corners:
        if board[r][c] == EMPTY:
            moves.append((r, c))
    for r, c in edges:
        if board[r][c] == EMPTY:
            moves.append((r, c))
            
    return moves

def minimax(board, depth, alpha, beta, is_maximizing):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Terminal state checks
    if check_win(board, ME):
        return 1000000
    if check_win(board, OPPONENT):
        return -1000000
    
    # Check for draw (board full)
    is_full = True
    for r in range(4):
        for c in range(4):
            if board[r][c] == EMPTY:
                is_full = False
                break
        if not is_full:
            break
    if is_full:
        return 0
        
    # Depth limit reached: use heuristic
    if depth == 0:
        return evaluate_board(board)
        
    moves = get_ordered_moves(board)
    
    if is_maximizing:
        max_eval = -math.inf
        for r, c in moves:
            board[r][c] = ME
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = EMPTY
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in moves:
            board[r][c] = OPPONENT
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = EMPTY
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """
    Main policy function to determine the next move.
    """
    # Optimization: First move should be center
    empty_count = sum(row.count(EMPTY) for row in board)
    if empty_count == 16:
        return (1, 1)
    
    best_score = -math.inf
    best_move = None
    moves = get_ordered_moves(board)
    
    # Adjust search depth based on game stage
    # Early/Mid game: Depth 4
    # Late game: Depth increases to ensure perfect play
    depth = 4
    if empty_count < 8:
        depth = 6
    if empty_count < 5:
        depth = 10
        
    for r, c in moves:
        board[r][c] = ME
        score = minimax(board, depth, -math.inf, math.inf, False)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move
