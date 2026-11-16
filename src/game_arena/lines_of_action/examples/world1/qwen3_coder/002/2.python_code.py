
import numpy as np
from collections import deque

def policy(board) -> str:
    """
    Smart policy for Lines of Action.
    """
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(board_array, 1)
    
    if not legal_moves:
        # Should not happen in a valid game state
        return "0,0:0,1"  # Fallback move
    
    # If only one move, take it
    if len(legal_moves) == 1:
        return format_move(legal_moves[0])
    
    # Evaluate each move and pick the best
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Simulate the move
        new_board = simulate_move(board_array, move, 1)
        
        # Evaluate the resulting position
        score = evaluate_position(new_board, 1)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def count_pieces_in_line(board, row, col, direction):
    """
    Count pieces in a line in the given direction.
    Directions: (dr, dc) where dr, dc in {-1, 0, 1}
    """
    dr, dc = direction
    count = 0
    
    # Count in positive direction
    r, c = row + dr, col + dc
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r][c] != 0:
            count += 1
        r += dr
        c += dc
    
    # Count in negative direction
    r, c = row - dr, col - dc
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r][c] != 0:
            count += 1
        r -= dr
        c -= dc
    
    # Add the piece itself
    return count + 1

def is_valid_position(row, col):
    """Check if position is within board bounds."""
    return 0 <= row < 8 and 0 <= col < 8

def is_legal_move(board, from_row, from_col, to_row, to_col, player):
    """
    Check if a move is legal according to Lines of Action rules.
    """
    # Must move from a player's piece
    if board[from_row][from_col] != player:
        return False
    
    # Must move to an empty cell or opponent's piece
    if board[to_row][to_col] == player:
        return False
    
    # Calculate direction and distance
    dr = to_row - from_row
    dc = to_col - from_col
    
    # Must move in a straight line (horizontal, vertical, or diagonal)
    if dr != 0 and dc != 0 and abs(dr) != abs(dc):
        return False
    
    # Distance must be exactly the number of pieces in that line
    # Normalize direction
    if dr == 0 and dc == 0:
        return False
    
    # Normalize the direction vector
    if dr != 0:
        dr_norm = dr // abs(dr) if dr != 0 else 0
    else:
        dr_norm = 0
        
    if dc != 0:
        dc_norm = dc // abs(dc) if dc != 0 else 0
    else:
        dc_norm = 0
    
    # Count pieces in the line
    pieces_in_line = count_pieces_in_line(board, from_row, from_col, (dr_norm, dc_norm))
    
    # Check distance
    distance = max(abs(dr), abs(dc))
    if distance != pieces_in_line:
        return False
    
    # Check that we don't jump over opponent pieces
    steps = max(abs(dr), abs(dc))
    if steps == 0:
        return False
    
    # Normalize step size
    step_dr = dr // steps if dr != 0 else 0
    step_dc = dc // steps if dc != 0 else 0
    
    # Check each intermediate square
    r, c = from_row, from_col
    for _ in range(steps - 1):
        r += step_dr
        c += step_dc
        if board[r][c] == -player:  # Can't jump over opponent
            return False
    
    return True

def generate_legal_moves(board, player):
    """
    Generate all legal moves for the given player.
    """
    moves = []
    
    # Find all player pieces
    for row in range(8):
        for col in range(8):
            if board[row][col] == player:
                # Try all possible destinations
                for to_row in range(8):
                    for to_col in range(8):
                        if is_legal_move(board, row, col, to_row, to_col, player):
                            moves.append((row, col, to_row, to_col))
    
    return moves

def simulate_move(board, move, player):
    """
    Simulate a move on the board and return the new board.
    """
    from_row, from_col, to_row, to_col = move
    new_board = board.copy()
    
    # Move the piece
    new_board[to_row][to_col] = new_board[from_row][from_col]
    new_board[from_row][from_col] = 0
    
    return new_board

def count_connected_components(board, player):
    """
    Count the number of connected components for the given player.
    """
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    
    for row in range(8):
        for col in range(8):
            if board[row][col] == player and not visited[row][col]:
                # BFS to find all connected pieces
                queue = deque([(row, col)])
                visited[row][col] = True
                
                while queue:
                    r, c = queue.popleft()
                    
                    # Check all 8 directions
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < 8 and 0 <= nc < 8 and 
                                board[nr][nc] == player and not visited[nr][nc]):
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                
                components += 1
    
    return components

def calculate_piece_distances(board, player):
    """
    Calculate total distance between all pairs of player's pieces.
    """
    pieces = []
    for row in range(8):
        for col in range(8):
            if board[row][col] == player:
                pieces.append((row, col))
    
    if len(pieces) < 2:
        return 0
    
    total_distance = 0
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            r1, c1 = pieces[i]
            r2, c2 = pieces[j]
            # Manhattan distance
            total_distance += abs(r1 - r2) + abs(c1 - c2)
    
    return total_distance

def evaluate_position(board, player):
    """
    Evaluate the board position from player's perspective.
    Higher score is better.
    """
    # Number of connected components (fewer is better)
    my_components = count_connected_components(board, player)
    opponent_components = count_connected_components(board, -player)
    
    # Distance between my pieces (closer is better)
    my_distance = calculate_piece_distances(board, player)
    opponent_distance = calculate_piece_distances(board, -player)
    
    # Count pieces
    my_pieces = np.sum(board == player)
    opponent_pieces = np.sum(board == -player)
    
    # Center control (pieces closer to center are better)
    center_row, center_col = 3.5, 3.5
    my_center_distance = 0
    opponent_center_distance = 0
    
    for row in range(8):
        for col in range(8):
            if board[row][col] == player:
                my_center_distance += abs(row - center_row) + abs(col - center_col)
            elif board[row][col] == -player:
                opponent_center_distance += abs(row - center_row) + abs(col - center_col)
    
    # Evaluation function
    score = 0
    
    # Prefer fewer components for myself
    score -= my_components * 100
    
    # Prefer more components for opponent
    score += opponent_components * 50
    
    # Prefer closer pieces for myself
    score -= my_distance * 2
    
    # Prefer more spread out pieces for opponent
    score += opponent_distance
    
    # Prefer more pieces
    score += (my_pieces - opponent_pieces) * 10
    
    # Prefer center control
    score -= (my_center_distance - opponent_center_distance) * 0.5
    
    # Check for immediate win or loss
    if my_components <= 1 and opponent_components > 1:
        score += 1000  # Win condition
    elif opponent_components <= 1 and my_components > 1:
        score -= 1000  # Loss condition
    
    return score

def format_move(move):
    """
    Format move as "from_row,from_col:to_row,to_col"
    """
    from_row, from_col, to_row, to_col = move
    return f"{from_row},{from_col}:{to_row},{to_col}"
