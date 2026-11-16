
import numpy as np

# Constants
BOARD_SIZE = 8
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Corner and edge weights for evaluation
CORNER_WEIGHT = 1000
EDGE_WEIGHT = 500
MOBILITY_WEIGHT = 10
STABILITY_WEIGHT = -20

def get_legal_moves(you: np.ndarray, opponent: np.ndarray):
    """Get all legal moves for the current player."""
    legal_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_valid_move(you, opponent, r, c):
                    legal_moves.append((r, c))
    return legal_moves

def is_valid_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int):
    """Check if placing a disc at (r, c) is valid."""
    for dr, dc in DIRECTIONS:
        if check_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def check_direction(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int):
    """Check if placing a disc at (r, c) flips discs in direction (dr, dc)."""
    r += dr
    c += dc
    found_opponent = False
    
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        if opponent[r][c] == 1:
            found_opponent = True
        elif you[r][c] == 1:
            return found_opponent
        else:
            return False
        r += dr
        c += dc
    
    return False

def make_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int):
    """Make a move and return new board states."""
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    new_you[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        if check_direction(you, opponent, r, c, dr, dc):
            rr, cc = r + dr, c + dc
            while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and new_opponent[rr][cc] == 1:
                new_opponent[rr][cc] = 0
                new_you[rr][cc] = 1
                rr += dr
                cc += dc
    
    return new_you, new_opponent

def evaluate(you: np.ndarray, opponent: np.ndarray):
    """Evaluate the board state."""
    score = 0
    
    # Corner control
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for r, c in corners:
        if you[r][c] == 1:
            score += CORNER_WEIGHT
        elif opponent[r][c] == 1:
            score -= CORNER_WEIGHT
    
    # Edge control
    for r in [0, 7]:
        for c in range(1, 7):
            if you[r][c] == 1:
                score += EDGE_WEIGHT
            elif opponent[r][c] == 1:
                score -= EDGE_WEIGHT
    for c in [0, 7]:
        for r in range(1, 7):
            if you[r][c] == 1:
                score += EDGE_WEIGHT
            elif opponent[r][c] == 1:
                score -= EDGE_WEIGHT
    
    # Mobility
    my_moves = len(get_legal_moves(you, opponent))
    opponent_moves = len(get_legal_moves(opponent, you))
    score += MOBILITY_WEIGHT * (my_moves - opponent_moves)
    
    # Disc count
    my_discs = np.sum(you)
    opponent_discs = np.sum(opponent)
    score += (my_discs - opponent_discs)
    
    return score

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool):
    """Minimax algorithm with alpha-beta pruning."""
    if depth == 0:
        return evaluate(you, opponent)
    
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        # Pass if no legal moves
        return minimax(opponent, you, depth - 1, alpha, beta, not maximizing)
    
    if maximizing:
        max_eval = float('-inf')
        for r, c in legal_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            eval_score = minimax(new_opponent, new_you, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in legal_moves:
            new_opponent, new_you = make_move(opponent, you, r, c)
            eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function that determines the best move."""
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Determine search depth based on available time and game stage
    discs_on_board = np.sum(you) + np.sum(opponent)
    if discs_on_board < 30:
        depth = 6
    elif discs_on_board < 50:
        depth = 4
    else:
        depth = 8
    
    # Use minimax to find the best move
    best_move = None
    best_value = float('-inf')
    
    for r, c in legal_moves:
        new_you, new_opponent = make_move(you, opponent, r, c)
        move_value = minimax(new_opponent, new_you, depth - 1, float('-inf'), float('inf'), False)
        
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
    
    if best_move is None:
        return "pass"
    
    r, c = best_move
    return chr(ord('a') + c) + str(r + 1)
