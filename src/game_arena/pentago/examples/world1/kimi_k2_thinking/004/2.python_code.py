
import numpy as np
import random
import time

# Time limit in seconds (leave margin)
TIME_LIMIT = 0.95
_start_time = 0

def policy(you, opponent):
    """
    Pentago AI policy.
    Strategy:
    1. Win immediately if possible
    2. Block opponent's immediate win by occupying their winning cell
    3. Evaluate remaining moves with center control and line potential
    """
    global _start_time
    _start_time = time.time()
    
    # Convert to internal board representation: 1=our, -1=opponent, 0=empty
    board = np.array(you, dtype=np.int8) - np.array(opponent, dtype=np.int8)
    
    # Generate all legal moves
    moves = get_all_moves(board, 1)
    random.shuffle(moves)
    
    # 1. Check for immediate win
    for move in moves:
        if check_time():
            break
        if is_winning_move(board, move, 1):
            return format_move(move)
    
    # 2. Block opponent's immediate win
    # Find all opponent winning moves
    opp_win_moves = []
    for opp_move in get_all_moves(board, -1):
        if is_winning_move(board, opp_move, -1):
            opp_win_moves.append(opp_move)
    
    # If opponent can win, try to block by placing in their winning cell
    if opp_win_moves:
        for move in moves:
            if check_time():
                break
            r, c, _, _ = move
            # Check if this cell is part of any opponent winning move
            for ow in opp_win_moves:
                ow_r, ow_c, _, _ = ow
                if r == ow_r and c == ow_c:
                    return format_move(move)
    
    # 3. Choose best move by evaluation
    best_move = moves[0]
    best_score = -np.inf
    
    for move in moves:
        if check_time():
            break
        new_board = apply_move(board, move, 1)
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def check_time():
    """Check if time limit exceeded."""
    return time.time() - _start_time > TIME_LIMIT

def get_all_moves(board, player):
    """
    Generate all legal moves for a player.
    Returns list of (row, col, quadrant, direction) tuples.
    """
    moves = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        moves.append((r, c, quad, direction))
    return moves

def is_winning_move(board, move, player):
    """
    Check if applying move results in immediate win for player.
    Returns boolean.
    """
    new_board = apply_move(board, move, player)
    return check_win(new_board, player)

def apply_move(board, move, player):
    """
    Apply a move to the board.
    Returns new board state.
    """
    r, c, quad, direction = move
    new_board = board.copy()
    new_board[r, c] = player
    
    # Rotate the specified quadrant
    row_start = 0 if quad in [0, 1] else 3
    col_start = 0 if quad in [0, 2] else 3
    quad_slice = new_board[row_start:row_start+3, col_start:col_start+3]
    
    # Rotate left (90° CCW) or right (90° CW)
    k = 1 if direction == 'L' else 3
    new_board[row_start:row_start+3, col_start:col_start+3] = np.rot90(quad_slice, k)
    
    return new_board

def check_win(board, player):
    """
    Check if player has 5+ marbles in a row.
    Checks horizontal, vertical, and both diagonals.
    Returns boolean.
    """
    mask = (board == player).astype(np.int8)
    
    # Check horizontal lines
    for r in range(6):
        row = mask[r]
        for c in range(2):
            if row[c] + row[c+1] + row[c+2] + row[c+3] + row[c+4] == 5:
                return True
    
    # Check vertical lines
    for c in range(6):
        for r in range(2):
            if mask[r, c] + mask[r+1, c] + mask[r+2, c] + mask[r+3, c] + mask[r+4, c] == 5:
                return True
    
    # Check diagonal \ lines
    for r in range(2):
        for c in range(2):
            if (mask[r, c] + mask[r+1, c+1] + mask[r+2, c+2] + 
                mask[r+3, c+3] + mask[r+4, c+4] == 5):
                return True
    
    # Check diagonal / lines
    for r in range(2):
        for c in range(4, 6):
            if (mask[r, c] + mask[r+1, c-1] + mask[r+2, c-2] + 
                mask[r+3, c-3] + mask[r+4, c-4] == 5):
                return True
    
    return False

def evaluate(board):
    """
    Evaluate board position from player 1's perspective.
    Higher scores favor player 1.
    Uses center control and line potential.
    """
    score = 0
    
    # Center control weight matrix (higher values in center)
    center_weights = np.array([
        [1, 1, 2, 2, 1, 1],
        [1, 2, 3, 3, 2, 1],
        [2, 3, 4, 4, 3, 2],
        [2, 3, 4, 4, 3, 2],
        [1, 2, 3, 3, 2, 1],
        [1, 1, 2, 2, 1, 1]
    ], dtype=np.int8)
    
    # Apply center weights
    our_pieces = (board == 1).astype(np.int8)
    opp_pieces = (board == -1).astype(np.int8)
    score += np.sum(our_pieces * center_weights) * 10
    score -= np.sum(opp_pieces * center_weights) * 10
    
    # Evaluate all potential 5-in-a-row lines
    # Horizontal
    for r in range(6):
        for c in range(2):
            score += score_line(board[r, c:c+5])
    
    # Vertical
    for r in range(2):
        for c in range(6):
            score += score_line(board[r:r+5, c])
    
    # Diagonal \
    for r in range(2):
        for c in range(2):
            line = [board[r+i, c+i] for i in range(5)]
            score += score_line(line)
    
    # Diagonal /
    for r in range(2):
        for c in range(4, 6):
            line = [board[r+i, c-i] for i in range(5)]
            score += score_line(line)
    
    return score

def score_line(line):
    """
    Score a line of 5 cells.
    Returns:
        High positive if we have many pieces
        High negative if opponent has many pieces
        0 if blocked (both have pieces)
    """
    our_count = sum(1 for x in line if x == 1)
    opp_count = sum(1 for x in line if x == -1)
    
    # Blocked line
    if our_count > 0 and opp_count > 0:
        return 0
    
    # Winning lines
    if our_count == 5:
        return 100000
    if opp_count == 5:
        return -100000
    
    # Score potential exponentially
    if our_count > 0:
        return 10 ** our_count
    if opp_count > 0:
        return -(10 ** opp_count)
    
    return 0

def format_move(move):
    """
    Format move tuple to string: "row,col,quad,dir"
    Note: row and col are 1-indexed.
    """
    r, c, quad, direction = move
    return f"{r+1},{c+1},{quad},{direction}"
