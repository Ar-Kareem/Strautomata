
import numpy as np
import time
from collections import deque

def policy(board):
    """
    Implements a smart policy for Lines of Action using minimax with alpha-beta pruning
    and heuristic evaluation functions.
    """
    START_TIME = time.time()
    
    # Constants
    MAX_DEPTH = 4
    TIMEOUT_MARGIN = 0.1  # Leave 100ms for cleanup
    
    # Get player's pieces and opponent's pieces
    player = 1
    opponent = -1
    
    # Generate all legal moves
    legal_moves = get_all_legal_moves(board, player)
    
    # If no legal moves (shouldn't happen in normal play), return a dummy move
    if not legal_moves:
        # Find any piece and move it one square (this is fallback, shouldn't occur)
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                return f"{r},{c}:{nr},{nc}"
        # If no piece found (shouldn't happen), return arbitrary legal move
        return "0,0:0,1"
    
    # If only one legal move, return it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Use iterative deepening with alpha-beta pruning
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Set maximum depth based on remaining time
    try:
        for depth in range(2, MAX_DEPTH + 1):
            if time.time() - START_TIME > 1 - TIMEOUT_MARGIN:
                break
                
            # Alpha-beta search at current depth
            score = alpha_beta_search(board, depth, float('-inf'), float('inf'), True, player, opponent, START_TIME)
            if score > best_score:
                best_score = score
                best_move = get_best_move_from_search(board, depth, player, opponent, START_TIME)
                
            # If we're running out of time, break
            if time.time() - START_TIME > 1 - TIMEOUT_MARGIN:
                break
                
    except:
        # Fallback: choose best move based on heuristic if search fails
        best_move = get_best_heuristic_move(board, player, legal_moves)
    
    return best_move


def get_all_legal_moves(board, player):
    """
    Generate all legal moves for the current player
    """
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                # Check all 8 directions
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        # Count pieces in this line direction
                        piece_count = count_pieces_in_line(board, r, c, dr, dc)
                        if piece_count == 0:
                            continue
                            
                        # Try to move piece exactly 'piece_count' steps
                        nr, nc = r + dr * piece_count, c + dc * piece_count
                        
                        # Check if destination is on board
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            continue
                            
                        # Can't move to own piece
                        if board[nr][nc] == player:
                            continue
                            
                        # Check if path is clear (can jump over own pieces, not enemy)
                        if not is_path_clear(board, r, c, dr, dc, piece_count):
                            continue
                            
                        # Valid move
                        moves.append(f"{r},{c}:{nr},{nc}")
    
    return moves


def count_pieces_in_line(board, r, c, dr, dc):
    """
    Count total pieces (both players) in the line in direction (dr, dc) from (r,c)
    This includes pieces in both directions along the line
    """
    count = 0
    # Check in positive direction
    nr, nc = r, c
    while True:
        nr += dr
        nc += dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            break
        if board[nr][nc] != 0:
            count += 1
    
    # Check in negative direction
    nr, nc = r, c
    while True:
        nr -= dr
        nc -= dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            break
        if board[nr][nc] != 0:
            count += 1
            
    return count


def is_path_clear(board, r, c, dr, dc, steps):
    """
    Check if path from (r,c) to (r+dr*steps, c+dc*steps) is clear
    Can jump over friendly pieces, but cannot jump over enemy pieces
    """
    for step in range(1, steps):
        nr, nc = r + dr * step, c + dc * step
        if not (0 <= nr < 8 and 0 <= nc < 8):
            return False
        # If we encounter an enemy piece before the destination, move is invalid
        if board[nr][nc] == -1:
            return False
        # Friendly pieces are fine (can jump over)
        
    return True


def evaluate_board(board, player, opponent):
    """
    Heuristic evaluation function for board state
    """
    # 1. Evaluate connectivity of player's pieces
    player_connectivity = get_connectivity_score(board, player)
    
    # 2. Evaluate connectivity of opponent's pieces
    opponent_connectivity = get_connectivity_score(board, opponent)
    
    # 3. Count number of pieces
    player_pieces = np.sum(board == player)
    opponent_pieces = np.sum(board == opponent)
    
    # 4. Central control (favor pieces near center)
    center_reward = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                # Center of board is around (3.5, 3.5), so reward proximity to center
                distance_to_center = abs(r - 3.5) + abs(c - 3.5)
                center_reward += max(0, 7 - distance_to_center)
    
    # 5. Mobility - number of legal moves
    legal_moves = len(get_all_legal_moves(board, player))
    
    # 6. Potential captures
    capture_potential = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        piece_count = count_pieces_in_line(board, r, c, dr, dc)
                        if piece_count == 0:
                            continue
                        nr, nc = r + dr * piece_count, c + dc * piece_count
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == opponent:
                            capture_potential += 1
    
    # Combine scores with weights
    # Higher connectivity for player is good, for opponent is bad
    # More pieces is good, more opponent pieces is bad
    # Central control is good
    # More mobility is good
    # Capture potential is good
    
    score = (
        player_connectivity * 10 +
        -opponent_connectivity * 8 +
        (player_pieces - opponent_pieces) * 5 +
        center_reward * 1.5 +
        legal_moves * 2 +
        capture_potential * 3
    )
    
    return score


def get_connectivity_score(board, player):
    """
    Use BFS to find connectivity of player's pieces
    Returns a score based on how connected the pieces are
    Better score = more connected components
    """
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    player_positions = []
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                player_positions.append((r, c))
    
    # If no pieces, return 0
    if len(player_positions) == 0:
        return 0
    
    # Count connected components
    for r, c in player_positions:
        if not visited[r][c]:
            components += 1
            # BFS to mark connected pieces
            queue = deque([(r, c)])
            visited[r][c] = True
            
            while queue:
                curr_r, curr_c = queue.popleft()
                # Check all 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = curr_r + dr, curr_c + dc
                        if (0 <= nr < 8 and 0 <= nc < 8 and 
                            board[nr][nc] == player and 
                            not visited[nr][nc]):
                            visited[nr][nc] = True
                            queue.append((nr, nc))
    
    # Connective score: higher when fewer components
    # Perfect connectivity = 1 component -> score = 10
    # Each additional component reduces score
    if components == 1:
        return 10
    else:
        return 10 - (components - 1) * 1.5


def get_best_heuristic_move(board, player, legal_moves):
    """
    Choose the best move among legal moves using heuristic evaluation
    """
    best_score = float('-inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        # Parse move
        from_str, to_str = move.split(':')
        from_r, from_c = map(int, from_str.split(','))
        to_r, to_c = map(int, to_str.split(','))
        
        # Make temporary move
        board_copy = np.array(board)
        board_copy[to_r][to_c] = board[from_r][from_c]
        board_copy[from_r][from_c] = 0
        
        # Evaluate
        score = evaluate_board(board_copy, player, -player)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def alpha_beta_search(board, depth, alpha, beta, maximizing_player, player, opponent, start_time):
    """
    Minimax with alpha-beta pruning
    """
    if time.time() - start_time > 1 - 0.1:
        return evaluate_board(board, player, opponent)
    
    legal_moves = get_all_legal_moves(board, player)
    if depth == 0 or len(legal_moves) == 0:
        return evaluate_board(board, player, opponent)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            # Make move
            from_pos, to_pos = move.split(':')
            from_r, from_c = map(int, from_pos.split(','))
            to_r, to_c = map(int, to_pos.split(','))
            
            board_copy = np.array(board)
            board_copy[to_r][to_c] = player
            board_copy[from_r][from_c] = 0
            
            # Recursively search
            eval_score = alpha_beta_search(board_copy, depth - 1, alpha, beta, False, player, opponent, start_time)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break  # Beta cutoff
                
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            # Make move
            from_pos, to_pos = move.split(':')
            from_r, from_c = map(int, from_pos.split(','))
            to_r, to_c = map(int, to_pos.split(','))
            
            board_copy = np.array(board)
            board_copy[to_r][to_c] = opponent
            board_copy[from_r][from_c] = 0
            
            # Recursively search
            eval_score = alpha_beta_search(board_copy, depth - 1, alpha, beta, True, player, opponent, start_time)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break  # Alpha cutoff
                
        return min_eval


def get_best_move_from_search(board, depth, player, opponent, start_time):
    """
    Get the best move by performing the alpha-beta search and returning the top move
    """
    legal_moves = get_all_legal_moves(board, player)
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        if time.time() - start_time > 1 - 0.1:
            break
            
        # Make move
        from_pos, to_pos = move.split(':')
        from_r, from_c = map(int, from_pos.split(','))
        to_r, to_c = map(int, to_pos.split(','))
        
        board_copy = np.array(board)
        board_copy[to_r][to_c] = player
        board_copy[from_r][from_c] = 0
        
        # Evaluate the resulting position
        score = alpha_beta_search(board_copy, depth - 1, float('-inf'), float('inf'), False, player, opponent, start_time)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
