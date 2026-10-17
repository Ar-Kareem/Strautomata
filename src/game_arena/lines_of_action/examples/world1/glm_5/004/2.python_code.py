
import numpy as np

def policy(board):
    """
    Calculates the best move for the current player (1) using Minimax with Alpha-Beta pruning.
    """
    # Ensure board is a numpy array for efficient operations
    if isinstance(board, list):
        board = np.array(board, dtype=int)
    
    player = 1
    best_move = None
    
    # Get all legal moves for the current player
    moves = get_legal_moves(board, player)
    
    if not moves:
        # Fallback, should not happen in a valid game state if moves exist
        return "0,0:0,0"

    # If only one move is available, return it immediately
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}"

    # Perform minimax search
    # We use a depth of 3 to stay within the 1-second time limit comfortably
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for move in moves:
        new_board = apply_move(board, move, player)
        
        # Check for immediate win
        if check_win(new_board, player):
            return f"{move[0]},{move[1]}:{move[2]},{move[3]}"
            
        score = minimax(new_board, 3, alpha, beta, False, player)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def minimax(board, depth, alpha, beta, is_maximizing, player):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Check for terminal states (win/loss)
    if check_win(board, player):
        return 100000
    if check_win(board, -player):
        return -100000
        
    if depth == 0:
        return evaluate(board, player)
        
    current_player = player if is_maximizing else -player
    moves = get_legal_moves(board, current_player)
    
    if not moves:
        # If a player has no moves, they typically lose in LOA
        return -100000 if is_maximizing else 100000

    if is_maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            eval_val = minimax(new_board, depth - 1, alpha, beta, False, player)
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            eval_val = minimax(new_board, depth - 1, alpha, beta, True, player)
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def evaluate(board, player):
    """
    Evaluates the board state.
    Higher scores are better for 'player'.
    """
    my_components = count_components(board, player)
    opp_components = count_components(board, -player)
    
    # Primary heuristic: Minimize own components, maximize opponent components
    # Score = (Opponent Components - My Components) * Weight
    # We want My Components to be small (ideally 1)
    # We want Opponent Components to be large (fragmented)
    score = (opp_components - my_components) * 100
    
    # Secondary heuristic: Centralization
    # Pieces closer to the center are generally more flexible
    my_pieces = np.argwhere(board == player)
    opp_pieces = np.argwhere(board == -player)
    
    center = 3.5
    my_dist = 0
    for r, c in my_pieces:
        my_dist += abs(r - center) + abs(c - center)
    
    opp_dist = 0
    for r, c in opp_pieces:
        opp_dist += abs(r - center) + abs(c - center)
        
    # Lower distance is better, so we subtract it
    score -= my_dist * 2
    score += opp_dist * 2
    
    return score

def check_win(board, player):
    """
    Checks if the specified player has connected all their pieces.
    """
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return False # No pieces, shouldn't happen normally
    if len(pieces) == 1:
        return True

    # BFS to count connected pieces
    visited = set()
    queue = [tuple(pieces[0])]
    visited.add(tuple(pieces[0]))
    count = 1
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr, nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    count += 1
                    
    return count == len(pieces)

def count_components(board, player):
    """
    Counts the number of connected components for a player.
    """
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return 0
    if len(pieces) == 1:
        return 1
        
    visited = set()
    components = 0
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for p in pieces:
        p_tuple = tuple(p)
        if p_tuple not in visited:
            components += 1
            queue = [p_tuple]
            visited.add(p_tuple)
            while queue:
                r, c = queue.pop(0)
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if board[nr, nc] == player and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
    return components

def get_legal_moves(board, player):
    """
    Generates all legal moves for the given player.
    """
    moves = []
    pieces = np.argwhere(board == player)
    
    # Pre-calculate flipped board for anti-diagonals
    board_flipped = np.fliplr(board)
    
    for r, c in pieces:
        # Check Row
        count_row = np.sum(board[r, :] != 0)
        # Move Left
        target_c = c - count_row
        if 0 <= target_c < 8:
            if is_path_clear(board, r, c, r, target_c, player):
                moves.append((r, c, r, target_c))
        # Move Right
        target_c = c + count_row
        if 0 <= target_c < 8:
            if is_path_clear(board, r, c, r, target_c, player):
                moves.append((r, c, r, target_c))
                
        # Check Column
        count_col = np.sum(board[:, c] != 0)
        # Move Up
        target_r = r - count_col
        if 0 <= target_r < 8:
            if is_path_clear(board, r, c, target_r, c, player):
                moves.append((r, c, target_r, c))
        # Move Down
        target_r = r + count_col
        if 0 <= target_r < 8:
            if is_path_clear(board, r, c, target_r, c, player):
                moves.append((r, c, target_r, c))
                
        # Check Diagonal 1 (Top-Left to Bottom-Right)
        # indices satisfy r-c = const
        offset1 = c - r
        diag1 = np.diag(board, offset1)
        count_d1 = np.sum(diag1 != 0)
        
        # Move Top-Left
        tr, tc = r - count_d1, c - count_d1
        if 0 <= tr < 8 and 0 <= tc < 8:
            if is_path_clear(board, r, c, tr, tc, player):
                moves.append((r, c, tr, tc))
        # Move Bottom-Right
        tr, tc = r + count_d1, c + count_d1
        if 0 <= tr < 8 and 0 <= tc < 8:
            if is_path_clear(board, r, c, tr, tc, player):
                moves.append((r, c, tr, tc))
                
        # Check Diagonal 2 (Top-Right to Bottom-Left)
        # indices satisfy r+c = const
        # This corresponds to anti-diagonal.
        # Offset for fliplr board: col_flipped - row = (7-c) - r = 7 - (r+c)
        offset2 = 7 - (r + c)
        diag2 = np.diag(board_flipped, offset2)
        count_d2 = np.sum(diag2 != 0)
        
        # Move Top-Right (r decreases, c increases)
        tr, tc = r - count_d2, c + count_d2
        if 0 <= tr < 8 and 0 <= tc < 8:
            if is_path_clear(board, r, c, tr, tc, player):
                moves.append((r, c, tr, tc))
        # Move Bottom-Left (r increases, c decreases)
        tr, tc = r + count_d2, c - count_d2
        if 0 <= tr < 8 and 0 <= tc < 8:
            if is_path_clear(board, r, c, tr, tc, player):
                moves.append((r, c, tr, tc))
                
    return moves

def is_path_clear(board, r1, c1, r2, c2, player):
    """
    Checks if a move from (r1,c1) to (r2,c2) is valid.
    1. Path must not contain enemy pieces (jumping over friendly is allowed).
    2. Destination must not contain friendly piece.
    """
    # Check destination
    if board[r2, c2] == player:
        return False
        
    dr = np.sign(r2 - r1)
    dc = np.sign(c2 - c1)
    
    steps = max(abs(r2 - r1), abs(c2 - c1))
    
    curr_r, curr_c = r1 + dr, c1 + dc
    for _ in range(steps - 1):
        # If we encounter an enemy piece along the path, the move is blocked
        if board[curr_r, curr_c] == -player:
            return False
        curr_r += dr
        curr_c += dc
        
    return True

def apply_move(board, move, player):
    """
    Applies a move and returns the new board state.
    """
    new_board = board.copy()
    r1, c1, r2, c2 = move
    new_board[r1, c1] = 0
    new_board[r2, c2] = player
    return new_board
