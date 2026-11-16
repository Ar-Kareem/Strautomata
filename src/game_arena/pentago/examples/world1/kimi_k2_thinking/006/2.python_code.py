
import numpy as np

# Precompute all possible 5-in-a-row lines (as flattened indices)
def generate_all_line_indices():
    lines = []
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for r in range(6):
        for c in range(6):
            for dr, dc in directions:
                line = []
                for i in range(5):
                    nr, nc = r + i*dr, c + i*dc
                    if 0 <= nr < 6 and 0 <= nc < 6:
                        line.append(nr * 6 + nc)
                    else:
                        break
                if len(line) == 5:
                    lines.append(line)
    
    return lines

ALL_LINE_INDICES = generate_all_line_indices()

def convert_board(you, opponent):
    """Convert input arrays to numpy array with 0/1/2 values"""
    board = np.zeros((6, 6), dtype=np.int8)
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r][c] = 1
            elif opponent[r][c] == 1:
                board[r][c] = 2
    return board

def get_quadrant_coords(quad):
    """Get slice objects for a quadrant"""
    if quad == 0:
        return np.s_[0:3, 0:3]
    elif quad == 1:
        return np.s_[0:3, 3:6]
    elif quad == 2:
        return np.s_[3:6, 0:3]
    else:  # quad == 3
        return np.s_[3:6, 3:6]

def apply_move(board, move, player):
    """Apply a move to the board for the given player (1 or 2)"""
    row, col, quad, dir = move
    new_board = board.copy()
    
    # Place marble
    new_board[row, col] = player
    
    # Rotate quadrant
    quadrant_coords = get_quadrant_coords(quad)
    quadrant = new_board[quadrant_coords]
    
    if dir == 'L':
        rotated = np.rot90(quadrant, 1)  # 90 deg anticlockwise
    else:  # 'R'
        rotated = np.rot90(quadrant, -1)  # 90 deg clockwise
    
    new_board[quadrant_coords] = rotated
    
    return new_board

def check_win(board, player):
    """Check if player has 5-in-a-row"""
    flat = board.flat
    for line in ALL_LINE_INDICES:
        # Early exit optimization
        if flat[line[0]] != player:
            continue
        if all(flat[i] == player for i in line):
            return True
    return False

def generate_moves(board):
    """Generate all legal moves from current board state"""
    moves = []
    empty_cells = [(r, c) for r in range(6) for c in range(6) if board[r][c] == 0]
    
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                moves.append((r, c, quad, dir))
    
    return moves

def format_move(move):
    """Format move tuple to string with 1-indexed coordinates"""
    row, col, quad, dir = move
    return f"{row+1},{col+1},{quad},{dir}"

def evaluate_position(board):
    """Evaluate board position for player 1 (positive good for us)"""
    score = 0
    flat = board.flat
    
    for line in ALL_LINE_INDICES:
        our_count = 0
        opp_count = 0
        
        for idx in line:
            val = flat[idx]
            if val == 1:
                our_count += 1
            elif val == 2:
                opp_count += 1
        
        # Skip blocked lines
        if our_count > 0 and opp_count > 0:
            continue
        
        # Exponential scoring for our lines
        if our_count > 0:
            score += 2 ** our_count
        
        # Exponential penalty for opponent's lines
        if opp_count > 0:
            score -= 2 ** opp_count
    
    return score

def opponent_can_win_from(board):
    """
    Check if opponent can win from this board state.
    Returns True if opponent has already won or can win on their turn.
    """
    we_win = check_win(board, 1)
    opp_win = check_win(board, 2)
    
    # If opponent wins and we don't, they win
    if opp_win and not we_win:
        return True
    
    # If we win (clean or draw), opponent can't win
    if we_win:
        return False
    
    # Check if opponent can win on their turn
    for move in generate_moves(board):
        new_board = apply_move(board, move, 2)
        if check_win(new_board, 2):
            return True
    
    return False

def policy(you, opponent):
    """
    Main policy function: returns the next move as "row,col,quad,dir"
    Implements a heuristic-based Pentago strategy with win/block/evaluate phases
    """
    board = convert_board(you, opponent)
    all_moves = generate_moves(board)
    
    # Phase 1: Look for immediate clean win
    for move in all_moves:
        new_board = apply_move(board, move, 1)
        we_win = check_win(new_board, 1)
        opp_win = check_win(new_board, 2)
        
        if we_win and not opp_win:
            return format_move(move)
    
    # Phase 2: Look for move that blocks opponent's win
    if opponent_can_win_from(board):
        for our_move in all_moves:
            new_board = apply_move(board, our_move, 1)
            
            if not opponent_can_win_from(new_board):
                return format_move(our_move)
    
    # Phase 3: Find best non-losing move using heuristics
    best_move = None
    best_score = -float('inf')
    center_positions = {2, 3}
    
    for move in all_moves:
        new_board = apply_move(board, move, 1)
        
        # Skip if opponent can win from this state
        if opponent_can_win_from(new_board):
            continue
        
        # Evaluate position
        score = evaluate_position(new_board)
        
        # Bonus for center control (rows 3-4, cols 3-4)
        row, col = move[0], move[1]
        if row in center_positions and col in center_positions:
            score += 50
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        return format_move(best_move)
    
    # Phase 4: Return first legal move (should rarely happen)
    return format_move(all_moves[0])
