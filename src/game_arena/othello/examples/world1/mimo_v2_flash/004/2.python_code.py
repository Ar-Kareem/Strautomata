
import numpy as np

# Precomputed corner positions and safety zones
CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
# Edges are rows 0 and 7, cols 0 and 7
# C-squares are (0,1), (1,0), (1,1), (0,6), (1,6), (1,7), (6,0), (6,1), (7,1), (6,6), (6,7), (7,6)
# X-squares are (1,1), (1,6), (6,1), (6,6)

# Weights for the evaluation function
# Heavily prioritize corners, avoid X-squares early, favor edges/mobility
POSITION_WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
], dtype=np.float32)

# Directions for checking flips: (dr, dc)
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def get_valid_moves(you: np.ndarray, opponent: np.ndarray) -> list:
    """Returns a list of valid (r, c) moves."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r, c] == 1 or opponent[r, c] == 1:
                continue
            # Check each direction
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if opponent[nr, nc] == 0:
                    continue
                # Walk the line
                while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 1:
                    nr += dr
                    nc += dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc] == 1:
                        moves.append((r, c))
                        break
                else:
                    continue
                break
    return moves

def apply_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int):
    """Simulates a move and returns new boards (you, opponent) after flipping."""
    # We need to copy to not modify original state
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    new_you[r, c] = 1
    
    for dr, dc in DIRS:
        # Collect discs to flip in this direction
        to_flip = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent[nr, nc] == 1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and new_you[nr, nc] == 1 and to_flip:
            for fr, fc in to_flip:
                new_you[fr, fc] = 1
                new_opponent[fr, fc] = 0
                
    return new_you, new_opponent

def evaluate(you: np.ndarray, opponent: np.ndarray) -> float:
    """Heuristic evaluation function."""
    # 1. Positional Score
    pos_score = 0.0
    you_coords = np.argwhere(you == 1)
    opp_coords = np.argwhere(opponent == 1)
    
    for r, c in you_coords:
        pos_score += POSITION_WEIGHTS[r, c]
    for r, c in opp_coords:
        pos_score -= POSITION_WEIGHTS[r, c]
        
    # 2. Mobility (Number of valid moves)
    # This is crucial for avoiding being stuck
    my_moves = len(get_valid_moves(you, opponent))
    
    # Temporarily swap to get opponent's mobility
    # Note: opponent is currently the one who just moved, or we are simulating
    # In Minimax, the recursion alternates. 
    # Here we calculate relative mobility to the current state.
    # Let's check how many moves the opponent WOULD have if they played from here.
    opp_moves = len(get_valid_moves(opponent, you))
    
    mobility_score = 0.0
    if my_moves + opp_moves != 0:
        mobility_score = 10 * (my_moves - opp_moves)
        
    # 3. Frontier Discs (Discs adjacent to empty squares) -> Bad
    frontier_score = 0.0
    my_frontier = 0
    opp_frontier = 0
    
    # Optimization: Iterate over non-empty cells
    for r in range(8):
        for c in range(8):
            if you[r, c] == 1:
                # Check neighbors for emptiness
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc] == 0 and opponent[nr, nc] == 0:
                        my_frontier += 1
                        break
            elif opponent[r, c] == 1:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc] == 0 and opponent[nr, nc] == 0:
                        opp_frontier += 1
                        break
                        
    frontier_score = -5 * (my_frontier - opp_frontier)
    
    total_score = pos_score + mobility_score + frontier_score
    return total_score

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool, game_count: int) -> tuple:
    """Minimax algorithm with Alpha-Beta pruning."""
    # Terminal conditions: depth limit or no moves for either player
    # If game over (no moves for current player), return static evaluation
    # Note: We need to detect if THIS state is terminal.
    # The function is called from the perspective of the player whose turn it is.
    # So if maximizing_player is True, it is 'you's turn.
    
    current_player = you if maximizing_player else opponent
    other_player = opponent if maximizing_player else you
    
    valid_moves = get_valid_moves(current_player, other_player)
    
    # If no moves, check if game over
    if not valid_moves:
        # Check if opponent also has no moves (Game Over)
        opp_valid_moves = get_valid_moves(other_player, current_player)
        if not opp_valid_moves:
            # Game over. Return score based on disk count
            my_count = np.sum(you)
            opp_count = np.sum(opponent)
            if my_count > opp_count:
                return 10000 + my_count, None # Large win
            elif my_count < opp_count:
                return -10000 - opp_count, None # Large loss
            else:
                return 0, None # Draw
        else:
            # Pass turn. We lose a turn.
            # In Minimax, passing means we simulate the opponent playing from the exact same board state.
            # But wait, the board state doesn't change when passing.
            # We just swap turns.
            return minimax(you, opponent, depth - 1, alpha, beta, not maximizing_player, game_count)

    # Leaf node (depth 0) or dynamic depth cut?
    # Using a fixed depth is safer for strict 1s limit, but we want the best move.
    # Let's add a very simple quiescence or just use depth.
    if depth <= 0:
        return evaluate(you, opponent), None

    # Initialize best move
    best_move = None
    
    if maximizing_player:
        max_eval = -float('inf')
        for r, c in valid_moves:
            # Apply move
            next_you, next_opp = apply_move(you, opponent, r, c)
            # Recursive call
            eval_score, _ = minimax(next_you, next_opp, depth - 1, alpha, beta, False, game_count)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Beta cutoff
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for r, c in valid_moves:
            # Apply move (swap roles for opponent)
            # Note: apply_move expects 'you' as the mover. 
            # Here the mover is the opponent.
            next_opp, next_you = apply_move(opponent, you, r, c)
            
            eval_score, _ = minimax(next_you, next_opp, depth - 1, alpha, beta, True, game_count)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Alpha cutoff
        return min_eval, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # 1. Get all valid moves
    moves = get_valid_moves(you, opponent)
    
    if not moves:
        return "pass"
        
    # 2. Check for immediate corner capture
    for r, c in moves:
        if (r, c) in CORNERS:
            return f"{chr(ord('a') + c)}{r + 1}"
            
    # 3. Heuristic: Avoid moves that allow opponent to take corners
    # We will filter out moves that are "obvious" blunders.
    # A blunder is a move that immediately opens a corner for the opponent.
    # e.g., placing at (0,1) when (0,0) is empty is often bad unless (0,0) is yours.
    safe_moves = []
    dangerous_moves = []
    
    # If corners are open, specific squares near them are bad
    # (0,1), (1,0), (1,1) bad if (0,0) open
    # (0,6), (1,6), (1,7) bad if (0,7) open
    # etc.
    
    for r, c in moves:
        is_dangerous = False
        
        # Top-Left
        if (0,0) not in CORNERS: # Check if corner is empty
             # Actually, check if corner is empty
             if opponent[0,0] == 0 and you[0,0] == 0:
                 if (r == 0 and c == 1) or (r == 1 and c == 0) or (r == 1 and c == 1):
                     is_dangerous = True
                     
        # Top-Right
        if opponent[0,7] == 0 and you[0,7] == 0:
            if (r == 0 and c == 6) or (r == 1 and c == 7) or (r == 1 and c == 6):
                is_dangerous = True
                
        # Bottom-Left
        if opponent[7,0] == 0 and you[7,0] == 0:
            if (r == 7 and c == 1) or (r == 6 and c == 0) or (r == 6 and c == 1):
                is_dangerous = True
                
        # Bottom-Right
        if opponent[7,7] == 0 and you[7,7] == 0:
            if (r == 7 and c == 6) or (r == 6 and c == 7) or (r == 6 and c == 6):
                is_dangerous = True
                
        if is_dangerous:
            dangerous_moves.append((r, c))
        else:
            safe_moves.append((r, c))
            
    # If we have safe moves, prefer them. If only dangerous, we must play one.
    candidates = safe_moves if safe_moves else moves
    
    # 4. Minimax search
    # Adjust depth based on board fill. 
    # Early game (low count) -> faster/heuristic. Mid game -> deeper. End game -> very deep (perfect play).
    my_count = np.sum(you)
    opp_count = np.sum(opponent)
    total_discs = my_count + opp_count
    
    # Dynamic depth: 
    # 0-10: Depth 3
    # 10-40: Depth 4
    # 40-58: Depth 5 (or 6 if fast)
    # 58+: Perfect play is ideal, but depth 6+ is risky in 1s.
    
    depth = 3
    if total_discs > 40:
        depth = 4
    if total_discs > 52:
        depth = 5
        
    # Optimization: If only one move, just play it
    if len(candidates) == 1:
        r, c = candidates[0]
        return f"{chr(ord('a') + c)}{r + 1}"
    
    # Run Minimax on candidates
    best_score = -float('inf')
    best_move = candidates[0]
    
    # We iterate manually to find the best move using minimax at root
    # The root node is maximizing, and we want the move leading to the best state.
    # We perform 1 ply (evaluate opponent's response) using minimax.
    
    for r, c in candidates:
        # Apply move
        next_you, next_opp = apply_move(you, opponent, r, c)
        
        # Start Minimax recursion (depth-1 remaining)
        # It is now opponent's turn, so maximizing_player=False
        score, _ = minimax(next_you, next_opp, depth - 1, -float('inf'), float('inf'), False, total_discs)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # Convert to string
    return f"{chr(ord('a') + best_move[1])}{best_move[0] + 1}"
