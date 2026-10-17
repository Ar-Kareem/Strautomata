
import random

# Global constant storing all 49 winning lines (combinations of 3 coordinates)
WINNING_LINES = []

def _init_lines():
    """Generate all 49 winning lines for a 3x3x3 board."""
    # 1. Straight lines along x-axis (fixed y, z)
    for y in range(3):
        for z in range(3):
            WINNING_LINES.append([(0, y, z), (1, y, z), (2, y, z)])
            
    # 2. Straight lines along y-axis (fixed x, z)
    for x in range(3):
        for z in range(3):
            WINNING_LINES.append([(x, 0, z), (x, 1, z), (x, 2, z)])
            
    # 3. Straight lines along z-axis (fixed x, y) - Pillars
    for x in range(3):
        for y in range(3):
            WINNING_LINES.append([(x, y, 0), (x, y, 1), (x, y, 2)])
            
    # 4. 2D Diagonals on xy planes (fixed z)
    for z in range(3):
        WINNING_LINES.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        WINNING_LINES.append([(0, 2, z), (1, 1, z), (2, 0, z)])
        
    # 5. 2D Diagonals on xz planes (fixed y)
    for y in range(3):
        WINNING_LINES.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        WINNING_LINES.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
    # 6. 2D Diagonals on yz planes (fixed x)
    for x in range(3):
        WINNING_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        WINNING_LINES.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
        
    # 7. 3D Main Diagonals (corners through center)
    WINNING_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    WINNING_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    WINNING_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    WINNING_LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

_init_lines()

def get_heuristic_score(board):
    """
    Evaluates the board state from the perspective of player 1 (AI).
    Returns a score: positive for advantage, negative for disadvantage.
    """
    score = 0
    for line in WINNING_LINES:
        counts = {1: 0, -1: 0, 0: 0}
        for x, y, z in line:
            val = board[x][y][z]
            counts[val] += 1
            
        # If the line is blocked by both players, it's useless (value 0)
        if counts[1] > 0 and counts[-1] > 0:
            continue
            
        if counts[1] == 3:
            return 100000 # AI Wins
        if counts[-1] == 3:
            return -100000 # Opponent Wins
        
        # Weighted scoring: Potential to win increases exponentially
        # 2 in a row is much more valuable than 1 in a row
        score += (10 ** counts[1]) - (10 ** counts[-1])
        
    return score

def check_immediate_move(board, player_val):
    """
    Checks if 'player_val' can win in one move.
    Returns the coordinate tuple (x,y,z) if a winning move exists, else None.
    """
    target_sum = 2 * player_val
    for line in WINNING_LINES:
        empty_cells = []
        current_sum = 0
        for x, y, z in line:
            val = board[x][y][z]
            if val == 0:
                empty_cells.append((x, y, z))
            current_sum += val
        
        # If the sum of the line is 2*player (e.g., 2 for AI, -2 for Opponent)
        # and there is exactly 1 empty cell, that's the winning move.
        if current_sum == target_sum and len(empty_cells) == 1:
            return empty_cells[0]
    return None

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    score = get_heuristic_score(board)
    if abs(score) >= 100000 or depth == 0:
        return score

    # Generate all possible moves
    empty_moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_moves.append((x, y, z))
    
    if not empty_moves:
        return 0 # Draw

    # Move ordering: Prioritize moves closer to the center (1,1,1)
    # This improves pruning efficiency significantly
    empty_moves.sort(key=lambda c: abs(c[0]-1) + abs(c[1]-1) + abs(c[2]-1))

    if maximizing_player:
        max_eval = -float('inf')
        for x, y, z in empty_moves:
            board[x][y][z] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[x][y][z] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for x, y, z in empty_moves:
            board[x][y][z] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[x][y][z] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # 1. Check for immediate win
    winning_move = check_immediate_move(board, 1)
    if winning_move:
        return winning_move
        
    # 2. Check for immediate block (opponent winning)
    blocking_move = check_immediate_move(board, -1)
    if blocking_move:
        return blocking_move
        
    # 3. Count empty cells to decide depth
    empty_count = 0
    moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_count += 1
                    moves.append((x, y, z))

    # Best opening move is center
    if empty_count == 27:
        return (1, 1, 1)

    # Adaptive depth: Search deeper as the board fills up (endgame is critical)
    # Depth 4 is safe for all stages, Depth 5 for endgame
    search_depth = 4 if empty_count > 15 else 5

    best_score = -float('inf')
    best_move = None
    
    # Shuffle moves to ensure variety if scores are equal
    random.shuffle(moves)
    
    # Sort by center preference again for the root search
    moves.sort(key=lambda c: abs(c[0]-1) + abs(c[1]-1) + abs(c[2]-1))

    for x, y, z in moves:
        board[x][y][z] = 1
        score = minimax(board, search_depth, -float('inf'), float('inf'), False)
        board[x][y][z] = 0
        
        if score > best_score:
            best_score = score
            best_move = (x, y, z)

    return best_move
