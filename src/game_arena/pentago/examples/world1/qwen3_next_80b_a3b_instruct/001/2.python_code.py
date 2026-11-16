
import numpy as np

def policy(you, opponent):
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you)
    opponent_arr = np.array(opponent)
    
    # Create full board state (1 for you, 2 for opponent, 0 for empty)
    board = np.zeros((6, 6), dtype=int)
    board[you_arr == 1] = 1
    board[opponent_arr == 1] = 2
    
    # Find all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empty_positions.append((r, c))
    
    # Check for immediate winning moves
    for r, c in empty_positions:
        # Try placing my marble here
        board[r][c] = 1
        
        # Check if this creates a win
        if check_win(board, 1):
            # If win, choose any valid rotation (we only need one legal move)
            # Try quad 0, R (simplest choice)
            return f"{r+1},{c+1},0,R"
        
        # Try to block opponent's immediate win
        # Temporarily put opponent's piece here to see if they win
        board[r][c] = 2
        if check_win(board, 2):
            # Block this position by placing my piece here and choose good rotation
            board[r][c] = 1
            # Score rotations to find best one after placement
            best_rot = find_best_rotation(board, r, c)
            return f"{r+1},{c+1},{best_rot[0]},{best_rot[1]}"
        # Restore board
        board[r][c] = 0
    
    # No immediate win or block, so use heuristic
    # Try placements that are central and have good connectivity
    # Score each possible placement
    
    best_move = None
    best_score = float('-inf')
    
    for r, c in empty_positions:
        # Place my piece temporarily
        board[r][c] = 1
        
        # Evaluate this placement with different rotations
        for quad in range(4):
            for direction in ['L', 'R']:
                # Apply rotation
                rotated_board = rotate_quadrant(board.copy(), quad, direction)
                
                # Score the resulting position
                score = evaluate_board(rotated_board)
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)
        
        # Restore board
        board[r][c] = 0
    
    # If no good move found, fall back to first empty position with default rotation
    if best_move is None:
        r, c = empty_positions[0]
        return f"{r+1},{c+1},0,R"
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"

def check_win(board, player):
    """Check if player has 5 or more in a row"""
    size = 6
    
    # Check horizontal
    for r in range(size):
        for c in range(size - 4):
            if all(board[r][c+i] == player for i in range(5)):
                return True
    
    # Check vertical
    for c in range(size):
        for r in range(size - 4):
            if all(board[r+i][c] == player for i in range(5)):
                return True
    
    # Check main diagonal (top-left to bottom-right)
    for r in range(size - 4):
        for c in range(size - 4):
            if all(board[r+i][c+i] == player for i in range(5)):
                return True
    
    # Check anti-diagonal (top-right to bottom-left)
    for r in range(size - 4):
        for c in range(4, size):
            if all(board[r+i][c-i] == player for i in range(5)):
                return True
    
    return False

def rotate_quadrant(board, quad, direction):
    """Rotate the specified quadrant by 90 degrees (L=anticlockwise, R=clockwise)"""
    # Create a copy of the board
    new_board = board.copy()
    
    # Define the 3x3 region for each quadrant
    quad_coords = {
        0: (slice(0, 3), slice(0, 3)),  # top-left
        1: (slice(0, 3), slice(3, 6)),  # top-right
        2: (slice(3, 6), slice(0, 3)),  # bottom-left
        3: (slice(3, 6), slice(3, 6))   # bottom-right
    }
    
    r_slice, c_slice = quad_coords[quad]
    quad_matrix = new_board[r_slice, c_slice]
    
    if direction == 'R':  # Clockwise
        # 90 degrees clockwise: row becomes column in reverse order
        rotated = np.rot90(quad_matrix, k=3)  # k=3 is equivalent to 90 clockwise
    else:  # 'L', anticlockwise
        rotated = np.rot90(quad_matrix, k=1)  # k=1 is 90 anticlockwise
    
    new_board[r_slice, c_slice] = rotated
    return new_board

def evaluate_board(board):
    """Evaluate the board position. Higher score is better for player 1 (us)."""
    score = 0
    
    # Check for our potential wins
    our_pieces = np.where(board == 1, 1, 0)
    opponent_pieces = np.where(board == 2, 1, 0)
    
    # Count potential 4-in-a-row opportunities (almost wins)
    def count_patterns(board_arr, player):
        count = 0
        size = 6
        
        # Horizontal
        for r in range(size):
            for c in range(size - 3):
                window = board_arr[r, c:c+4]
                if np.sum(window) == 3 and np.sum((board[r, c:c+4] == player)) == 3:
                    # 3 of our pieces with one empty
                    empty_pos = np.sum(board[r, c:c+4] == 0)
                    if empty_pos == 1:
                        count += 1
        
        # Vertical
        for c in range(size):
            for r in range(size - 3):
                window = board_arr[r:r+4, c]
                if np.sum(window) == 3 and np.sum((board[r:r+4, c] == player)) == 3:
                    empty_pos = np.sum(board[r:r+4, c] == 0)
                    if empty_pos == 1:
                        count += 1
        
        # Main diagonal
        for r in range(size - 3):
            for c in range(size - 3):
                window = np.array([board_arr[r+i, c+i] for i in range(4)])
                if np.sum(window) == 3 and np.sum((board[r:r+4, c:c+4].diagonal() == player)) == 3:
                    empty_pos = np.sum(board[r:r+4, c:c+4].diagonal() == 0)
                    if empty_pos == 1:
                        count += 1
        
        # Anti-diagonal
        for r in range(size - 3):
            for c in range(3, size):
                window = np.array([board_arr[r+i, c-i] for i in range(4)])
                if np.sum(window) == 3 and np.sum((board[r:r+4, c-3:c+1].flat[::7] == player)) == 3:
                    # Extract anti-diagonal elements correctly
                    anti_diag = np.array([board[r+i, c-i] for i in range(4)])
                    empty_pos = np.sum(anti_diag == 0)
                    if empty_pos == 1:
                        count += 1
        
        return count
    
    # We get points for potential wins, lose points for opponent's potential wins
    our_potentials = count_patterns(our_pieces, 1)
    opp_potentials = count_patterns(opponent_pieces, 2)
    
    score += our_potentials * 10
    score -= opp_potentials * 9  # Slightly less than ours to prioritize offense
    
    # Edge bonus for central positions
    center_positions = [(1,1), (1,2), (2,1), (2,2), (3,3), (3,4), (4,3), (4,4)]
    for r, c in center_positions:
        if board[r, c] == 1:
            score += 2
        elif board[r, c] == 2:
            score -= 1
    
    # Control of center quadrants
    center_quads = [(0, 0), (0, 2), (2, 0), (2, 2)]  # Centers of quadrants
    for qr, qc in center_quads:
        if board[qr, qc] == 1:
            score += 1
        if board[qr, qc] == 2:
            score -= 1
    
    # Count total pieces (slight preference for having more)
    our_count = np.sum(board == 1)
    opp_count = np.sum(board == 2)
    score += (our_count - opp_count) * 0.5
    
    return score

def find_best_rotation(board, placement_row, placement_col):
    """Find the best rotation after placing a marble at (placement_row, placement_col)"""
    best_quad = 0
    best_dir = 'R'
    best_score = float('-inf')
    
    # Try all combinations of quadrant rotations
    for quad in range(4):
        for direction in ['L', 'R']:
            # Create a copy and apply the placement and rotation
            test_board = board.copy()
            test_board[placement_row, placement_col] = 1
            
            # Apply rotation
            rotated_board = rotate_quadrant(test_board, quad, direction)
            
            # Evaluate
            score = evaluate_board(rotated_board)
            
            if score > best_score:
                best_score = score
                best_quad = quad
                best_dir = direction
    
    return best_quad, best_dir
