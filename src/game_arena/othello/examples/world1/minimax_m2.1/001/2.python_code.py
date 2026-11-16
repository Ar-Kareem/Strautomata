
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Determine the best move for the Othello player.
    
    Args:
        you: 8x8 numpy array where you[r][c] == 1 means your disc is at (r,c)
        opponent: 8x8 numpy array where opponent[r][c] == 1 means opponent disc is at (r,c)
    
    Returns:
        A move string like "d3" or "pass" if no legal moves
    """
    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    # If no legal moves, must pass
    if not legal_moves:
        return "pass"
    
    # If only one legal move, take it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Evaluate each move and select the best
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Simulate the move
        new_you, new_opponent = simulate_move(you, opponent, move)
        
        # Evaluate the resulting position
        score = evaluate_position(new_you, new_opponent, legal_moves, move)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> list:
    """
    Generate all legal moves for the current player.
    
    Returns list of move strings like ["d3", "e5", ...]
    """
    legal_moves = []
    
    # All 8 directions: (dr, dc)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    for r in range(8):
        for c in range(8):
            # Can only place on empty squares
            if you[r][c] == 1 or opponent[r][c] == 1:
                continue
            
            # Check if this move would flip any opponent discs
            for dr, dc in directions:
                if would_flip(you, opponent, r, c, dr, dc):
                    # Convert to algebraic notation
                    move_str = chr(ord('a') + c) + str(r + 1)
                    legal_moves.append(move_str)
                    break
    
    return legal_moves


def would_flip(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """
    Check if placing a disc at (r,c) would flip any opponent discs in direction (dr,dc).
    """
    nr, nc = r + dr, c + dc
    
    # Need at least one opponent disc in this direction
    if not (0 <= nr < 8 and 0 <= nc < 8):
        return False
    
    if opponent[nr][nc] != 1:
        return False
    
    # Continue in this direction looking for our disc
    while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
        nr += dr
        nc += dc
    
    # If we found our own disc after opponent discs, this move is legal
    if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1:
        return True
    
    return False


def simulate_move(you: np.ndarray, opponent: np.ndarray, move: str) -> tuple:
    """
    Simulate placing a disc at the given move position.
    
    Returns (new_you, new_opponent) arrays after the move.
    """
    # Parse the move
    col = ord(move[0]) - ord('a')
    row = int(move[1]) - 1
    
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    # Place our disc
    new_you[row][col] = 1
    
    # All 8 directions
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    # Flip opponent discs in each direction
    for dr, dc in directions:
        if would_flip(you, opponent, row, col, dr, dc):
            # Actually flip the discs
            nr, nc = row + dr, col + dc
            while opponent[nr][nc] == 1:
                new_you[nr][nc] = 1
                new_opponent[nr][nc] = 0
                nr += dr
                nc += dc
    
    return new_you, new_opponent


def evaluate_position(you: np.ndarray, opponent: np.ndarray, 
                      current_moves: list, current_move: str) -> float:
    """
    Evaluate a board position using multiple heuristics.
    """
    # Positional weights matrix
    weights = np.array([
        [100, -50,  25,  25,  25,  25, -50, 100],
        [-50, -50,  -5,  -5,  -5,  -5, -50, -50],
        [ 25,  -5,  10,  10,  10,  10,  -5,  25],
        [ 25,  -5,  10,   5,   5,  10,  -5,  25],
        [ 25,  -5,  10,   5,   5,  10,  -5,  25],
        [ 25,  -5,  10,  10,  10,  10,  -5,  25],
        [-50, -50,  -5,  -5,  -5,  -5, -50, -50],
        [100, -50,  25,  25,  25,  25, -50, 100]
    ])
    
    # Calculate positional score
    our_positional_score = np.sum(weights * you)
    opp_positional_score = np.sum(weights * opponent)
    positional_score = our_positional_score - opp_positional_score
    
    # Count discs
    our_discs = np.sum(you)
    opp_discs = np.sum(opponent)
    total_discs = our_discs + opp_discs
    
    # Game phase detection (early, mid, late game)
    if total_discs < 20:
        # Early game: prioritize mobility and corners
        mobility_weight = 10
        disc_weight = 1
        corner_weight = 50
        positional_weight = 30
    elif total_discs < 50:
        # Mid game: balance between positional and disc count
        mobility_weight = 8
        disc_weight = 5
        corner_weight = 40
        positional_weight = 25
    else:
        # Late game: prioritize disc count
        mobility_weight = 5
        disc_weight = 15
        corner_weight = 30
        positional_weight = 20
    
    # Calculate mobility
    # Get opponent's possible moves after our move
    opp_legal_moves = get_legal_moves(opponent, you)
    our_mobility = len(current_moves)
    opp_mobility = len(opp_legal_moves)
    
    # Mobility score (positive if we have more moves)
    if our_mobility + opp_mobility > 0:
        mobility_score = (our_mobility - opp_mobility) / (our_mobility + opp_mobility) * 100
    else:
        mobility_score = 0
    
    # Corner detection and scoring
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    our_corners = sum(1 for r, c in corners if you[r][c] == 1)
    opp_corners = sum(1 for r, c in corners if opponent[r][c] == 1)
    
    # X-squares (adjacent to corners) - avoid unless necessary
    x_squares = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7),
                 (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]
    our_x_squares = sum(1 for r, c in x_squares if you[r][c] == 1)
    opp_x_squares = sum(1 for r, c in x_squares if opponent[r][c] == 1)
    
    corner_score = (our_corners - opp_corners) * 100
    x_square_score = (opp_x_squares - our_x_squares) * 30  # Negative if we occupy X-squares
    
    # Disc difference score
    disc_diff = our_discs - opp_discs
    disc_score = disc_diff * 10
    
    # Combined score
    total_score = (positional_weight * positional_score +
                   mobility_weight * mobility_score +
                   disc_weight * disc_score +
                   corner_score +
                   x_square_score)
    
    # Add a small random factor to break ties and add variety
    total_score += np.random.uniform(-1, 1)
    
    return total_score
