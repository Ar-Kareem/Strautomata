
import numpy as np
import time

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Competitive Othello policy using positional strategy and limited search.
    """
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Use best move selection with time limit
    best_move = select_best_move(you, opponent, legal_moves)
    return best_move

def get_legal_moves(you, opponent):
    """Get all legal moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_legal_move(you, opponent, r, c):
                    moves.append((r, c))
    return moves

def is_legal_move(you, opponent, r, c):
    """Check if placing a disc at (r, c) is legal."""
    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        found_opponent = False
        
        while 0 <= nr < 8 and 0 <= nc < 8:
            if opponent[nr][nc] == 1:
                found_opponent = True
            elif you[nr][nc] == 1:
                if found_opponent:
                    return True
                break
            else:
                break
            nr += dr
            nc += dc
    
    return False

def make_move(you, opponent, r, c):
    """Return new board state after making a move."""
    new_you = you.copy()
    new_opp = opponent.copy()
    
    new_you[r][c] = 1
    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    for dr, dc in directions:
        flips = []
        nr, nc = r + dr, c + dc
        
        while 0 <= nr < 8 and 0 <= nc < 8:
            if new_opp[nr][nc] == 1:
                flips.append((nr, nc))
            elif new_you[nr][nc] == 1:
                for fr, fc in flips:
                    new_opp[fr][fc] = 0
                    new_you[fr][fc] = 1
                break
            else:
                break
            nr += dr
            nc += dc
    
    return new_you, new_opp

def evaluate_position(you, opponent):
    """Evaluate board position using multiple heuristics."""
    # Positional weights (corners and edges are valuable)
    weights = np.array([
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [ 10,  -5,   5,   2,   2,   5,  -5,  10],
        [  5,  -5,   2,   1,   1,   2,  -5,   5],
        [  5,  -5,   2,   1,   1,   2,  -5,   5],
        [ 10,  -5,   5,   2,   2,   5,  -5,  10],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [100, -20,  10,   5,   5,  10, -20, 100]
    ])
    
    total_discs = np.sum(you) + np.sum(opponent)
    game_stage = total_discs / 64.0
    
    # Positional score
    pos_score = np.sum(you * weights) - np.sum(opponent * weights)
    
    # Mobility (number of legal moves)
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility_score = 0
    if my_moves + opp_moves > 0:
        mobility_score = 10 * (my_moves - opp_moves)
    
    # Disc count (more important in endgame)
    disc_score = (np.sum(you) - np.sum(opponent)) * game_stage * 5
    
    # Combine scores based on game stage
    if game_stage < 0.5:  # Early game
        return pos_score + mobility_score * 2
    elif game_stage < 0.8:  # Mid game
        return pos_score + mobility_score + disc_score
    else:  # End game
        return disc_score * 3 + pos_score
    
def minimax(you, opponent, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_position(you, opponent), None
    
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        opp_moves = get_legal_moves(opponent, you)
        if not opp_moves:
            # Game over
            disc_diff = np.sum(you) - np.sum(opponent)
            return disc_diff * 1000, None
        # Pass turn
        return -minimax(opponent, you, depth - 1, -beta, -alpha, not maximizing)[0], None
    
    best_move = moves[0]
    
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_you, new_opp = make_move(you, opponent, move[0], move[1])
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_you, new_opp = make_move(you, opponent, move[0], move[1])
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def select_best_move(you, opponent, legal_moves):
    """Select the best move using minimax search."""
    total_discs = np.sum(you) + np.sum(opponent)
    
    # Adjust depth based on game stage
    if total_discs > 50:
        depth = 5  # End game - search deeper
    elif total_discs > 40:
        depth = 4
    else:
        depth = 3
    
    _, best_move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        best_move = legal_moves[0]
    
    # Convert to algebraic notation
    r, c = best_move
    return chr(ord('a') + c) + str(r + 1)
