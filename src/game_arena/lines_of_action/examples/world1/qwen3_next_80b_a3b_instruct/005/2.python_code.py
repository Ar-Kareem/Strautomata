
import numpy as np
import time
from collections import deque

def policy(board):
    """
    Implements a strategic minimax policy with alpha-beta pruning for Lines of Action.
    Returns a legal move as a string in format "from_row,from_col:to_row,to_col"
    """
    start_time = time.time()
    
    # Convert board to numpy array for efficient operations
    board = np.array(board, dtype=np.int8)
    
    # Get current player (always 1 for us)
    player = 1
    opponent = -1
    
    # Get all legal moves for current player
    legal_moves = get_all_legal_moves(board, player)
    
    # If no legal moves (shouldn't happen in normal play), return a dummy move
    if len(legal_moves) == 0:
        # Find any piece and move it to an adjacent empty spot as fallback
        for r in range(8):
            for c in range(8):
                if board[r, c] == player:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == 0:
                                return f"{r},{c}:{nr},{nc}"
        # If even this fails, just return first possible
        return "0,0:0,0"
    
    # If only one legal move, return it immediately
    if len(legal_moves) == 1:
        r1, c1, r2, c2 = legal_moves[0]
        return f"{r1},{c1}:{r2},{c2}"
    
    # Estimate available time for search (leave buffer for cleanup)
    available_time = 0.9  # seconds
    
    # Use iterative deepening to maximize search depth within time limit
    max_depth = 2
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Try deeper searches if time permits
    for depth in range(2, 6):  # Maximum depth 5
        if time.time() - start_time > available_time * 0.8:  # Leave room for final processing
            break
            
        score, move = minimax(board, depth, player, opponent, start_time, available_time, alpha=float('-inf'), beta=float('inf'), best_move=best_move)
        
        if move is not None and score > best_score:
            best_score = score
            best_move = move
    
    r1, c1, r2, c2 = best_move
    return f"{r1},{c1}:{r2},{c2}"


def get_all_legal_moves(board, player):
    """
    Get all legal moves for the given player on the board.
    Returns list of tuples: (from_row, from_col, to_row, to_col)
    """
    moves = []
    
    # For each piece of the player
    for r in range(8):
        for c in range(8):
            if board[r, c] == player:
                # Check all 8 directions
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        
                        # Count pieces in this direction
                        line_count = count_pieces_in_direction(board, r, c, dr, dc)
                        
                        # Can't move 0 squares
                        if line_count == 0:
                            continue
                        
                        # Try to move exactly line_count squares in this direction
                        nr, nc = r + dr * line_count, c + dc * line_count
                        
                        # Check if destination is within bounds
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            continue
                        
                        # Check if we can land there (can capture opponent or move to empty)
                        if board[nr, nc] == opponent or board[nr, nc] == 0:
                            # Check path isn't blocked by opponent pieces
                            if not is_path_clear(board, r, c, dr, dc, line_count):
                                continue
                            
                            moves.append((r, c, nr, nc))
    
    return moves


def count_pieces_in_direction(board, r, c, dr, dc):
    """
    Count total pieces (both players) in the line starting from (r,c) in direction (dr,dc)
    Includes the starting piece itself.
    """
    count = 0
    current_r, current_c = r, c
    
    while 0 <= current_r < 8 and 0 <= current_c < 8:
        if board[current_r, current_c] != 0:
            count += 1
        current_r += dr
        current_c += dc
        
        # Stop when we hit the edge
        if not (0 <= current_r < 8 and 0 <= current_c < 8):
            break
    
    return count


def is_path_clear(board, start_r, start_c, dr, dc, distance):
    """
    Check if the path from (start_r, start_c) to the destination (distance away) is clear.
    Can jump over friendly pieces but not enemy pieces.
    """
    for i in range(1, distance):  # Check intermediate squares
        r, c = start_r + dr * i, start_c + dc * i
        if not (0 <= r < 8 and 0 <= c < 8):
            return False
        if board[r, c] == -1:  # Encountered opponent piece before destination
            return False
        # Friendly pieces (1) or empty (0) are okay to jump over
        # Note: We'll land on the destination in the move, that's handled separately
    
    return True


def get_connected_components(board, player):
    """
    Count connected components for the player using 8-directional connectivity.
    Returns the number of connected groups and the size of the largest group.
    """
    if not np.any(board == player):
        return 0, 0
    
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    max_group_size = 0
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                components += 1
                # BFS to find size of this component
                queue = deque([(r, c)])
                visited[r, c] = True
                size = 0
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    # Check 8 neighbors
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = curr_r + dr, curr_c + dc
                            if (0 <= nr < 8 and 0 <= nc < 8 and 
                                board[nr, nc] == player and not visited[nr, nc]):
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                
                max_group_size = max(max_group_size, size)
    
    return components, max_group_size


def evaluate_board(board, player, opponent):
    """
    Evaluate the board state for the current player.
    Higher score is better for the player.
    """
    # Get number of pieces for each player
    player_pieces = np.sum(board == player)
    opponent_pieces = np.sum(board == opponent)
    
    # If opponent has no pieces, we win with maximum score
    if opponent_pieces == 0:
        return 10000
    
    # If we have no pieces, we lose
    if player_pieces == 0:
        return -10000
    
    # Connectivity assessment - want to be one connected group
    player_components, player_largest = get_connected_components(board, player)
    opponent_components, opponent_largest = get_connected_components(board, opponent)
    
    # Component bonus: More connected = better
    player_connectivity_bonus = (1000 / (player_components + 1)) if player_components > 0 else 0
    opponent_connectivity_penalty = (1000 / (opponent_components + 1)) if opponent_components > 0 else 0
    
    # Center control bonus
    center_bonus = 0
    center_positions = [(3, 3), (3, 4), (4, 3), (4, 4)]
    for r, c in center_positions:
        if board[r, c] == player:
            center_bonus += 10
        elif board[r, c] == opponent:
            center_bonus -= 10
    
    # Mobility - number of legal moves
    player_moves = len(get_all_legal_moves(board, player))
    opponent_moves = len(get_all_legal_moves(board, opponent))
    mobility_bonus = (player_moves - opponent_moves) * 2
    
    # Piece count advantage
    piece_advantage = (player_pieces - opponent_pieces) * 5
    
    # Capture potential
    capture_potential = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == player:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        line_count = count_pieces_in_direction(board, r, c, dr, dc)
                        if line_count == 0:
                            continue
                        nr, nc = r + dr * line_count, c + dc * line_count
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == opponent:
                            # We can capture an opponent piece here
                            capture_potential += 50
    
    # Score calculation
    score = (
        player_connectivity_bonus - opponent_connectivity_penalty +  # Connectivity value
        center_bonus +  # Control of center
        mobility_bonus +  # Mobility advantage
        piece_advantage +  # Piece count
        capture_potential  # Potential captures
    )
    
    # Extra bonus for winning condition
    if player_components == 1 and player_pieces > 0:
        score += 500  # All pieces connected is very good
    
    # Scale for game phase: Early game weight different
    total_pieces = player_pieces + opponent_pieces
    if total_pieces > 40:  # Early game
        return score * 0.8
    elif total_pieces > 20:  # Mid game
        return score * 1.5
    else:  # End game
        return score * 2.0


def minimax(board, depth, player, opponent, start_time, available_time, alpha, beta, best_move):
    """
    Minimax algorithm with alpha-beta pruning and time management.
    Returns (score, best_move)
    """
    if time.time() - start_time > available_time * 0.8:
        return evaluate_board(board, player, opponent), best_move
    
    legal_moves = get_all_legal_moves(board, player)
    
    # If terminal state or no moves (should be rare)
    if depth == 0 or len(legal_moves) == 0:
        return evaluate_board(board, player, opponent), best_move
    
    # Sort moves: captures first, then center moves, then others
    def move_score(move):
        r1, c1, r2, c2 = move
        score = 0
        # Capture moves
        if board[r2, c2] == opponent:
            score += 1000
        # Center moves
        if (r2, c2) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
            score += 100
        return score
    
    legal_moves.sort(key=move_score, reverse=True)
    
    best_score = float('-inf')
    best_candidate_move = legal_moves[0] if legal_moves else best_move
    
    for move in legal_moves:
        r1, c1, r2, c2 = move
        
        # Apply move
        original_val = board[r2, c2]
        board[r2, c2] = player
        board[r1, c1] = 0
        
        # Recursively evaluate
        score, _ = minimax(board, depth - 1, opponent, player, start_time, available_time, -beta, -alpha, best_candidate_move)
        score = -score  # Flip score because next player is opponent
        
        # Undo move
        board[r1, c1] = player
        board[r2, c2] = original_val
        
        if score > best_score:
            best_score = score
            best_candidate_move = move
            
        # Alpha-beta pruning
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Prune
    
    return best_score, best_candidate_move
