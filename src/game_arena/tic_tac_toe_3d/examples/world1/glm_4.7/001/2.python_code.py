
import math
import random

# Precompute all 49 winning lines in a 3x3x3 cube.
# A line is a list of 3 coordinates (x, y, z).
LINES = []
directions = [
    (1, 0, 0), (0, 1, 0), (0, 0, 1),       # Axes
    (1, 1, 0), (1, -1, 0),                 # XY diagonals
    (1, 0, 1), (1, 0, -1),                 # XZ diagonals
    (0, 1, 1), (0, 1, -1),                 # YZ diagonals
    (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1) # 3D diagonals
]

line_set = set()
for x in range(3):
    for y in range(3):
        for z in range(3):
            for dx, dy, dz in directions:
                # To avoid duplicates, we only consider directions that form a valid line 
                # starting from (x,y,z) moving forward.
                # Actually, the simplest way to get unique lines is to check all 3 points
                # and normalize (sort) them, then put in a set.
                coords = []
                valid = True
                for k in range(3):
                    nx, ny, nz = x + k * dx, y + k * dy, z + k * dz
                    if not (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3):
                        valid = False
                        break
                    coords.append((nx, ny, nz))
                
                if valid:
                    # Sort coordinates to ensure uniqueness regardless of direction
                    line_set.add(tuple(sorted(coords)))

LINES = [list(line) for line in line_set]

def evaluate(board):
    """
    Evaluates the board state.
    Returns a score: positive for AI (1), negative for Opponent (-1).
    Large positive/negative for wins.
    """
    score = 0
    for line in LINES:
        line_sum = 0
        has_zero = False
        for (x, y, z) in line:
            val = board[x][y][z]
            line_sum += val
            if val == 0:
                has_zero = True
        
        # Logic:
        # Sum 3: Win for AI
        # Sum 2: AI has 2, Opp has 0 (implies 1 empty) -> Strong threat
        # Sum 1: AI has 1, Opp has 0 (implies 2 empty) OR AI 2, Opp 1 (blocked) -> but sum logic handles blocks automatically
        # If sum is 1, it could be (1,0,0) [Good] or (1,1,-1) [Bad]. 
        # Since we iterate all lines, (1,0,0) is potential.
        
        if line_sum == 3:
            return 100000 # AI Wins
        if line_sum == -3:
            return -100000 # Opponent Wins
        
        # Count open lines
        if line_sum == 2: # Two 1s and one 0
            score += 100
        elif line_sum == 1 and has_zero: # One 1 and two 0s (or 1, 0, -1 which is 0 sum)
            # We only want to count lines that are not already blocked by opponent
            # Sum 1 implies no -1 present. (1+1-1=1, but that's blocked).
            # So sum 1 means strictly positive pieces or empty.
            if -1 not in [board[x][y][z] for x,y,z in line]:
                 score += 10
        elif line_sum == -2: # Two -1s and one 0
            score -= 100
        elif line_sum == -1 and has_zero:
             if 1 not in [board[x][y][z] for x,y,z in line]:
                 score -= 10
                 
    return score

def check_win(board, player):
    """Quick check if a player has won."""
    p_val = 1 if player == 1 else -1
    for line in LINES:
        if all(board[x][y][z] == p_val for (x, y, z) in line):
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move using Minimax with Alpha-Beta pruning.
    """
    
    # Get available moves
    available_moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    available_moves.append((x, y, z))
    
    if not available_moves:
        return (0, 0, 0) # Should not happen in valid game state

    # Heuristic: Prioritize center and corners
    # Distance to center (1,1,1)
    def dist_to_center(move):
        return abs(move[0] - 1) + abs(move[1] - 1) + abs(move[2] - 1)
    
    # Sort moves: center first, then corners (dist 3), then edges (dist 2)...
    # Actually dist 0 (center) is best.
    # Dist 1 (face centers) are usually weak.
    # Dist 2 (edges) weak.
    # Dist 3 (corners) strong.
    # Let's just sort by closeness to center.
    available_moves.sort(key=dist_to_center)

    # Special Case: First move
    if len(available_moves) == 27:
        return (1, 1, 1)

    # Minimax with Alpha-Beta Pruning
    # Depth limit depends on remaining moves to ensure speed.
    # 3x3x3 is small, but let's be careful.
    remaining = len(available_moves)
    max_depth = 6
    if remaining < 10: 
        max_depth = 10 # Search deeper near endgame
    
    alpha = -math.inf
    beta = math.inf
    best_score = -math.inf
    best_move = available_moves[0]

    # Iterate moves
    for move in available_moves:
        x, y, z = move
        board[x][y][z] = 1 # AI makes move
        
        # Call minimax for opponent's turn (minimizing player)
        score = minimax(board, max_depth - 1, alpha, beta, False)
        
        board[x][y][z] = 0 # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
        
        # Alpha update
        if score > alpha:
            alpha = score
        
        # Optimization: If we found a winning move (score 100000), take it immediately
        if score >= 100000:
            break

    return best_move

def minimax(board, depth, alpha, beta, is_maximizing):
    """
    Recursive minimax function.
    """
    # Terminal states
    if check_win(board, 1):
        return 100000 + depth # Prefer sooner wins
    if check_win(board, -1):
        return -100000 - depth # Prefer later losses
        
    if depth == 0:
        return evaluate(board)
    
    # Check for draw (full board)
    # (Optimization: we pass remaining moves count or check global, but simple check here is okay)
    # Actually, checking full board is O(27). 
    # Let's rely on depth==0 and win checks.
    # If no win and depth 0, we return heuristic.
    
    # Get moves
    moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    moves.append((x, y, z))
    
    if not moves:
        return 0 # Draw
    
    # Simple sorting for efficiency: center-ish first
    def dist(m): return abs(m[0]-1) + abs(m[1]-1) + abs(m[2]-1)
    moves.sort(key=dist)

    if is_maximizing:
        max_eval = -math.inf
        for move in moves:
            x, y, z = move
            board[x][y][z] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[x][y][z] = 0
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            x, y, z = move
            board[x][y][z] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[x][y][z] = 0
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
