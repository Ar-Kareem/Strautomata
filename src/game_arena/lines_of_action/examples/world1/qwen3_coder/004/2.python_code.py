
import numpy as np
from collections import deque

def get_piece_count(board, row, col, dr, dc):
    """Count pieces in a line starting from (row, col) in direction (dr, dc)."""
    count = 0
    r, c = row, col
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r, c] != 0:
            count += 1
        r += dr
        c += dc
    return count

def get_all_moves_for_piece(board, row, col):
    """Generate all legal moves for a piece at (row, col)."""
    if board[row, col] != 1:
        return []
    
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for dr, dc in directions:
        # Count pieces in this direction line (including opponent pieces)
        count = get_piece_count(board, row, col, dr, dc) + get_piece_count(board, row, col, -dr, -dc) - (1 if board[row, col] != 0 else 0)
        
        if count <= 0:
            continue
            
        # Calculate target position
        to_row = row + dr * count
        to_col = col + dc * count
        
        # Check if target is on board
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            continue
            
        # Check if landing on own piece
        if board[to_row, to_col] == 1:
            continue
            
        # Check if path is clear (can jump over own pieces but not capture by jumping)
        r, c = row, col
        path_clear = True
        for _ in range(count):
            r += dr
            c += dc
            # We can pass through own pieces but not stop on them before final destination
            if (r != to_row or c != to_col) and board[r, c] == 1:
                continue  # Passing through own piece is OK
            if (r != to_row or c != to_col) and board[r, c] == -1:
                path_clear = False
                break
        
        if path_clear:
            moves.append(((row, col), (to_row, to_col)))
            
    return moves

def get_all_legal_moves(board):
    """Generate all legal moves for player 1."""
    moves = []
    for row in range(8):
        for col in range(8):
            if board[row, col] == 1:
                moves.extend(get_all_moves_for_piece(board, row, col))
    return moves

def is_connected(board, player=1):
    """Check if all pieces of player are connected."""
    player_positions = np.argwhere(board == player)
    if len(player_positions) <= 1:
        return True
        
    visited = set()
    queue = deque([tuple(player_positions[0])])
    visited.add(tuple(player_positions[0]))
    connected_count = 1
    
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    while queue:
        row, col = queue.popleft()
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if (0 <= nr < 8 and 0 <= nc < 8 and 
                board[nr, nc] == player and 
                (nr, nc) not in visited):
                visited.add((nr, nc))
                queue.append((nr, nc))
                connected_count += 1
                
    return connected_count == len(player_positions)

def simulate_move(board, from_pos, to_pos):
    """Return a new board with the move applied."""
    new_board = board.copy()
    fr, fc = from_pos
    tr, tc = to_pos
    new_board[tr, tc] = new_board[fr, fc]
    new_board[fr, fc] = 0
    return new_board

def evaluate_move(board, from_pos, to_pos):
    """Evaluate a move based on multiple strategic factors."""
    new_board = simulate_move(board, from_pos, to_pos)
    
    # Check for immediate win
    if is_connected(new_board, 1):
        return 10000
    
    # Evaluate connectivity of own pieces
    player_positions = np.argwhere(new_board == 1)
    if len(player_positions) <= 1:
        connectivity = 0
    else:
        # Calculate average distance between pieces (lower is better)
        total_distance = 0
        for i in range(len(player_positions)):
            for j in range(i+1, len(player_positions)):
                d = abs(player_positions[i][0] - player_positions[j][0]) + abs(player_positions[i][1] - player_positions[j][1])
                total_distance += d
        connectivity = -total_distance / max(1, len(player_positions))
    
    # Evaluate control of center
    center_control = 0
    for r, c in player_positions:
        center_control += (3.5 - abs(3.5 - r)) + (3.5 - abs(3.5 - c))
    
    # Evaluate mobility (number of future moves)
    mobility = len(get_all_legal_moves(new_board))
    
    return connectivity + center_control*0.5 + mobility*0.3

def policy(board) -> str:
    # Convert to numpy array for easier handling
    board = np.array(board)
    
    # Get all legal moves
    moves = get_all_legal_moves(board)
    
    if not moves:
        # This should not happen in a legal game state
        return "0,0:0,0"
    
    # First, check for immediate winning moves
    for from_pos, to_pos in moves:
        new_board = simulate_move(board, from_pos, to_pos)
        if is_connected(new_board, 1):
            return f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}"
    
    # Then, check if opponent can win next turn and block
    opponent_moves = []
    for row in range(8):
        for col in range(8):
            if board[row, col] == -1:
                # Generate moves for opponent piece (considering as player 1)
                temp_board = board.copy()
                temp_board[row, col] = 1
                temp_board[temp_board == -1] = 1
                temp_board[temp_board == 1] = -1
                opponent_moves.extend(get_all_moves_for_piece(temp_board, row, col))
    
    # For each opponent move, check if it leads to opponent win
    blocking_moves = []
    for opp_from, opp_to in opponent_moves:
        # Simulate opponent move on actual board
        opp_board = board.copy()
        fr, fc = opp_from
        tr, tc = opp_to
        opp_board[tr, tc] = opp_board[fr, fc]
        opp_board[fr, fc] = 0
        
        # Check if this leads to opponent win (all their pieces connected)
        opp_board_for_check = opp_board.copy()
        opp_board_for_check[opp_board_for_check == 1] = 2  # Temp marker
        opp_board_for_check[opp_board_for_check == -1] = 1  # Make opponent player 1
        opp_board_for_check[opp_board_for_check == 2] = -1  # Make us player -1
        
        if is_connected(opp_board_for_check, 1):
            # Find our move that prevents this
            for our_move in moves:
                # For simplicity, we'll just add to blocking moves
                blocking_moves.append(our_move)
    
    # If we have blocking moves, evaluate only those
    if blocking_moves:
        moves = blocking_moves
    
    # Evaluate all remaining moves
    best_move = moves[0]
    best_score = -float('inf')
    
    for from_pos, to_pos in moves:
        score = evaluate_move(board, from_pos, to_pos)
        if score > best_score:
            best_score = score
            best_move = (from_pos, to_pos)
    
    return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
