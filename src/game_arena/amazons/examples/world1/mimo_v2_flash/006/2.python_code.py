
import numpy as np
import time

def policy(board):
    # Constants
    PLAYER = 1
    OPPONENT = 2
    EMPTY = 0
    BLOCKED = -1
    ROWS, COLS = 6, 6
    MAX_DEPTH = 6  # Initial depth for iterative deepening
    TIME_LIMIT = 0.9  # Seconds
    
    start_time = time.time()
    
    # --- Helper Functions ---
    
    def get_amazons(brd, player):
        return list(zip(*np.where(brd == player)))

    def get_moves(brd, player):
        moves = []
        amazons = get_amazons(brd, player)
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        
        for r, c in amazons:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                while 0 <= nr < ROWS and 0 <= nc < COLS:
                    if brd[nr, nc] != EMPTY:
                        # Cannot land on or jump over anything
                        break
                    
                    # Found a valid landing spot for the amazon
                    # Now generate arrow shots from this new position
                    arrow_moves = []
                    
                    # Temporarily update board for arrow generation
                    # (Vacate original position, occupy new position)
                    # Optimization: Just mark the path as blocked for arrow generation
                    
                    for adr, adc in directions:
                        ar, ac = nr + adr, nc + adc
                        while 0 <= ar < ROWS and 0 <= ac < COLS:
                            # Check if arrow hits a block
                            # It cannot hit the original amazon position if that path was open? 
                            # No, original position is now empty.
                            # It cannot hit the new amazon position.
                            if (ar == nr and ac == nc) or brd[ar, ac] != EMPTY:
                                if not (ar == r and ac == c): # Can shoot back to start if it was empty (it is now)
                                    break 
                            
                            # If we are at the original position, we can jump over it because it's empty now
                            if ar == r and ac == c:
                                ar, ac = ar + adr, ac + adc
                                continue
                                
                            # Valid arrow spot
                            moves.append(((r, c), (nr, nc), (ar, ac)))
                            
                            ar, ac = ar + adr, ac + adc
                    
                    nr, nc = nr + dr, nc + dc
        return moves

    def evaluate(brd, player):
        # Simple heuristic: Mobility + Territory
        # 1. Mobility
        my_moves = len(get_moves(brd, player))
        opp_moves = len(get_moves(brd, OPPONENT if player == PLAYER else PLAYER))
        
        # 2. Territory (Flood fill approximation)
        # We simulate whose territory each empty square belongs to
        # This is expensive, so we might limit it or use a simpler proxy.
        # A simple proxy is count of empty squares reachable by simple DFS without jumping?
        # Or just count empty squares connected to player vs opponent.
        
        my_terr = 0
        opp_terr = 0
        
        # Let's use a simplified reachable count or just basic center control
        # For speed on 6x6, full territory scan is feasible.
        visited = np.zeros_like(brd, dtype=bool)
        empty_squares = np.sum(brd == EMPTY)
        
        # Fast heuristic: Difference in moves is often very indicative
        # Weighting mobility heavily because Amazons is a blocking game
        score = (my_moves - opp_moves) * 10
        
        # Center control
        center_r, center_c = 2.5, 2.5
        my_amazons = get_amazons(brd, player)
        opp_amazons = get_amazons(brd, OPPONENT if player == PLAYER else PLAYER)
        
        my_dist = sum((r - center_r)**2 + (c - center_c)**2 for r, c in my_amazons)
        opp_dist = sum((r - center_r)**2 + (c - center_c)**2 for r, c in opp_amazons)
        
        score += (opp_dist - my_dist) * 2 # Closer to center is better
        
        # Late game: if few moves left, mobility is critical
        # If we have moves and they don't, we win.
        
        return score

    def alpha_beta(brd, depth, alpha, beta, maximizing_player, player):
        # Check time
        if time.time() - start_time > TIME_LIMIT:
            return None, 0 # Timeout signal

        if depth == 0:
            return None, evaluate(brd, player)

        current_player = player if maximizing_player else (OPPONENT if player == PLAYER else PLAYER)
        
        # Check for terminal state (no moves)
        moves = get_moves(brd, current_player)
        if not moves:
            # No moves means loss for current player
            # Return a very low score for maximizing player (current turn)
            # If it's opponent's turn and they have no moves, we win (high score)
            score = -10000 if maximizing_player else 10000
            return None, score

        # Move ordering: sort by simple heuristic to improve pruning
        # We can estimate move quality by looking at immediate mobility reduction
        def move_key(m):
            # A simple key: potential to reduce opponent space?
            # Or just center proximity of landing
            _, (to_r, to_c), _ = m
            dist = abs(to_r - 2.5) + abs(to_c - 2.5)
            return -dist # Prefer center

        moves.sort(key=move_key)

        best_move = moves[0]
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                # Apply Move
                new_board = brd.copy()
                fr, fc = move[0]
                tr, tc = move[1]
                ar, ac = move[2]
                
                new_board[fr, fc] = EMPTY
                new_board[tr, tc] = current_player
                new_board[ar, ac] = BLOCKED
                
                _, eval_val = alpha_beta(new_board, depth - 1, alpha, beta, False, player)
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
                
                if time.time() - start_time > TIME_LIMIT:
                    return best_move, max_eval
                    
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = brd.copy()
                fr, fc = move[0]
                tr, tc = move[1]
                ar, ac = move[2]
                
                new_board[fr, fc] = EMPTY
                new_board[tr, tc] = current_player
                new_board[ar, ac] = BLOCKED
                
                _, eval_val = alpha_beta(new_board, depth - 1, alpha, beta, True, player)
                
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
                
                if time.time() - start_time > TIME_LIMIT:
                    return best_move, min_eval
                    
            return best_move, min_eval

    # --- Main Execution ---
    
    # Iterative Deepening
    best_move_found = None
    # Get initial moves to ensure we have something
    initial_moves = get_moves(board, PLAYER)
    if not initial_moves:
        # Should not happen if called correctly, but safe fallback
        return "0,0:0,0:0,0" 

    best_move_found = initial_moves[0] # Default to first move

    # Start search
    for depth in range(1, MAX_DEPTH + 1):
        if time.time() - start_time > TIME_LIMIT:
            break
            
        move, score = alpha_beta(board, depth, -float('inf'), float('inf'), True, PLAYER)
        
        if move is not None:
            best_move_found = move
        else:
            break # Timeout occurred
            
    # Format output
    fr, fc = best_move_found[0]
    tr, tc = best_move_found[1]
    ar, ac = best_move_found[2]
    
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
