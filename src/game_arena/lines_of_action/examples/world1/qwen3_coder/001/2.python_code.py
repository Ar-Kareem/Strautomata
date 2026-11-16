
import numpy as np
from collections import deque

def policy(board) -> str:
    # Convert board to numpy array for easier handling
    board_array = np.array(board)
    
    # Find all my pieces
    my_pieces = []
    for i in range(8):
        for j in range(8):
            if board_array[i][j] == 1:
                my_pieces.append((i, j))
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(board_array, my_pieces)
    
    if not legal_moves:
        # Should not happen in a real game, but just in case
        return "0,0:0,1"  # Dummy move
    
    # Evaluate each move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(board_array, move, my_pieces)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def generate_legal_moves(board, my_pieces):
    moves = []
    for piece in my_pieces:
        row, col = piece
        # Count pieces in all 8 directions
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dr, dc in directions:
            # Count total pieces in this line
            count = count_pieces_in_line(board, row, col, dr, dc)
            
            # Calculate destination
            new_row = row + dr * count
            new_col = col + dc * count
            
            # Check if destination is valid
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                # Can't capture own piece
                if board[new_row][new_col] != 1:
                    moves.append(((row, col), (new_row, new_col)))
    
    return moves

def count_pieces_in_line(board, row, col, dr, dc):
    count = 0
    
    # Count in positive direction
    r, c = row, col
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r][c] != 0:
            count += 1
        r += dr
        c += dc
    
    # Count in negative direction (excluding starting position)
    r, c = row - dr, col - dc
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r][c] != 0:
            count += 1
        r -= dr
        c -= dc
    
    return count

def evaluate_move(board, move, my_pieces):
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # Create a new board state after the move
    new_board = board.copy()
    new_board[to_row][to_col] = 1
    new_board[from_row][from_col] = 0
    
    # Evaluate various factors
    score = 0
    
    # 1. Distance between pieces - prefer moves that bring pieces closer
    new_pieces = [(r, c) if (r, c) != (from_row, from_col) else (to_row, to_col) for r, c in my_pieces]
    score += evaluate_connectivity(new_board, new_pieces)
    
    # 2. Capture bonus
    if board[to_row][to_col] == -1:
        score += 10
    
    # 3. Avoid isolating pieces
    score += evaluate_isolation(new_board, new_pieces, to_pos)
    
    # 4. Central control - pieces closer to center are generally better
    score += evaluate_center_control(to_pos)
    
    # 5. Safety of moved piece
    score += evaluate_safety(new_board, to_pos)
    
    return score

def evaluate_connectivity(board, pieces):
    # Simple measure: sum of inverse distances between pieces
    if len(pieces) < 2:
        return 0
    
    total_distance = 0
    for i in range(len(pieces)):
        for j in range(i+1, len(pieces)):
            r1, c1 = pieces[i]
            r2, c2 = pieces[j]
            distance = max(abs(r1-r2), abs(c1-c2))  # Chebyshev distance
            total_distance += distance
    
    # Lower total distance is better, so we negate it
    return -total_distance * 2

def evaluate_isolation(board, pieces, moved_piece):
    # Check if a move isolates a piece
    row, col = moved_piece
    isolation_penalty = 0
    
    # Check 8 surrounding squares for friendly pieces
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    neighbors = 0
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1:
            neighbors += 1
    
    # If a piece has no neighbors after move, it's very bad
    if neighbors == 0:
        isolation_penalty -= 20
    
    return isolation_penalty

def evaluate_center_control(pos):
    # Prefer center positions
    row, col = pos
    center_row, center_col = 3.5, 3.5
    distance_from_center = abs(row - center_row) + abs(col - center_col)
    # Higher score for being closer to center
    return -(distance_from_center - 7)  # Normalize so center=0, corners=-7

def evaluate_safety(board, pos):
    # Simple measure - check if piece can be captured next turn
    row, col = pos
    safety = 0
    
    # For each direction, see if opponent can capture this piece
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        # Count pieces in this line from this position
        count = count_pieces_in_line(board, row, col, dr, dc)
        # Check if opponent can move that distance in either direction
        check_row1, check_col1 = row + dr * count, col + dc * count
        check_row2, check_col2 = row - dr * count, col - dc * count
        
        if 0 <= check_row1 < 8 and 0 <= check_col1 < 8 and board[check_row1][check_col1] == -1:
            safety -= 5
        if 0 <= check_row2 < 8 and 0 <= check_col2 < 8 and board[check_row2][check_col2] == -1:
            safety -= 5
    
    return safety

def format_move(move):
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    return f"{from_row},{from_col}:{to_row},{to_col}"
