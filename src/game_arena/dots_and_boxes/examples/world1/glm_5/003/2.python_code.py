
import numpy as np
import time

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Constants
    ROWS, COLS = 5, 5
    BOX_ROWS, BOX_COLS = 4, 4
    TIME_LIMIT = 0.90 # Seconds
    
    start_time = time.time()
    deadline = start_time + TIME_LIMIT

    # Helper to count filled sides of a box
    def count_sides(h, v, r, c):
        s = 0
        if h[r, c] != 0: s += 1
        if h[r+1, c] != 0: s += 1
        if v[r, c] != 0: s += 1
        if v[r, c+1] != 0: s += 1
        return s

    # Identify legal moves and categorize them
    def get_moves(h, v):
        capture_moves = []
        other_moves = []
        
        # Horizontal moves
        for r in range(ROWS):
            for c in range(COLS - 1):
                if h[r, c] == 0:
                    is_capture = False
                    # Check box above (if exists)
                    if r > 0:
                        if count_sides(h, v, r-1, c) == 3:
                            is_capture = True
                    # Check box below (if exists)
                    if r < BOX_ROWS:
                        if count_sides(h, v, r, c) == 3:
                            is_capture = True
                    
                    if is_capture:
                        capture_moves.append((r, c, 'H'))
                    else:
                        other_moves.append((r, c, 'H'))
                        
        # Vertical moves
        for r in range(ROWS - 1):
            for c in range(COLS):
                if v[r, c] == 0:
                    is_capture = False
                    # Check box left (if exists)
                    if c > 0:
                        if count_sides(h, v, r, c-1) == 3:
                            is_capture = True
                    # Check box right (if exists)
                    if c < BOX_COLS:
                        if count_sides(h, v, r, c) == 3:
                            is_capture = True
                            
                    if is_capture:
                        capture_moves.append((r, c, 'V'))
                    else:
                        other_moves.append((r, c, 'V'))
        
        # Order other_moves: safe moves first (moves that don't create a 3-side box)
        safe_moves = []
        risky_moves = []
        for move in other_moves:
            r, c, d = move
            creates_trap = False
            if d == 'H':
                if r > 0 and count_sides(h, v, r-1, c) == 2: creates_trap = True
                if r < BOX_ROWS and count_sides(h, v, r, c) == 2: creates_trap = True
            else: # 'V'
                if c > 0 and count_sides(h, v, r, c-1) == 2: creates_trap = True
                if c < BOX_COLS and count_sides(h, v, r, c) == 2: creates_trap = True
            
            if creates_trap:
                risky_moves.append(move)
            else:
                safe_moves.append(move)
                
        # If capture moves exist, we usually must take them.
        # If not, we prefer safe moves.
        if capture_moves:
            return capture_moves
        return safe_moves + risky_moves

    def get_score(cap):
        return np.sum(cap == 1) - np.sum(cap == -1)

    def minimax(h, v, cap, depth, alpha, beta, maximizing_player, deadline_ref):
        # Timeout check
        if time.time() > deadline_ref:
            return get_score(cap), None, True
            
        # Terminal state check
        if np.sum(cap != 0) == BOX_ROWS * BOX_COLS:
            return get_score(cap), None, False
            
        if depth == 0:
            return get_score(cap), None, False

        moves = get_moves(h, v)
        if not moves:
            return get_score(cap), None, False

        best_move = moves[0]
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                r, c, d = move
                
                # Apply move
                changes = [] # Store changes to revert
                if d == 'H':
                    changes.append((h, r, c, h[r,c]))
                    h[r, c] = 1
                else:
                    changes.append((v, r, c, v[r,c]))
                    v[r, c] = 1
                
                # Check captures
                captured = 0
                # Determine affected boxes
                boxes_to_check = []
                if d == 'H':
                    if r > 0: boxes_to_check.append((r-1, c))
                    if r < BOX_ROWS: boxes_to_check.append((r, c))
                else:
                    if c > 0: boxes_to_check.append((r, c-1))
                    if c < BOX_COLS: boxes_to_check.append((r, c))
                
                for br, bc in boxes_to_check:
                    if count_sides(h, v, br, bc) == 4 and cap[br, bc] == 0:
                        changes.append((cap, br, bc, cap[br,bc]))
                        cap[br, bc] = 1
                        captured += 1
                
                # Recursive call
                # If captured > 0, player continues (maximizing), else turn switches
                next_player = maximizing_player if captured > 0 else not maximizing_player
                
                # Check timeout immediately after move application but before deep recursion
                if time.time() > deadline_ref:
                    # Revert before returning
                    for arr, r_i, c_i, val in reversed(changes):
                        arr[r_i, c_i] = val
                    return get_score(cap), move, True

                eval_score, _, timed_out = minimax(h, v, cap, depth - 1, alpha, beta, next_player, deadline_ref)
                
                # Revert move
                for arr, r_i, c_i, val in reversed(changes):
                    arr[r_i, c_i] = val
                    
                if timed_out:
                    return eval_score, move, True
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move, False
        else:
            # Minimizing player
            min_eval = float('inf')
            for move in moves:
                r, c, d = move
                
                changes = []
                if d == 'H':
                    changes.append((h, r, c, h[r,c]))
                    h[r, c] = -1
                else:
                    changes.append((v, r, c, v[r,c]))
                    v[r, c] = -1
                
                captured = 0
                boxes_to_check = []
                if d == 'H':
                    if r > 0: boxes_to_check.append((r-1, c))
                    if r < BOX_ROWS: boxes_to_check.append((r, c))
                else:
                    if c > 0: boxes_to_check.append((r, c-1))
                    if c < BOX_COLS: boxes_to_check.append((r, c))
                
                for br, bc in boxes_to_check:
                    if count_sides(h, v, br, bc) == 4 and cap[br, bc] == 0:
                        changes.append((cap, br, bc, cap[br,bc]))
                        cap[br, bc] = -1
                        captured += 1
                
                next_player = maximizing_player if captured > 0 else not maximizing_player
                
                if time.time() > deadline_ref:
                    for arr, r_i, c_i, val in reversed(changes):
                        arr[r_i, c_i] = val
                    return get_score(cap), move, True

                eval_score, _, timed_out = minimax(h, v, cap, depth - 1, alpha, beta, next_player, deadline_ref)
                
                for arr, r_i, c_i, val in reversed(changes):
                    arr[r_i, c_i] = val
                    
                if timed_out:
                    return eval_score, move, True
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move, False

    # Iterative Deepening Loop
    best_move_found = None
    moves = get_moves(horizontal, vertical)
    if moves:
        best_move_found = moves[0] # Default fallback

    # Max depth for 4x4 box grid (16 boxes, 40 lines) can be up to 40, but time limits us.
    for depth in range(1, 42):
        current_time = time.time()
        if current_time > deadline - 0.1: # Reserve some buffer
            break
        
        score, move, timed_out = minimax(horizontal, vertical, capture, depth, -float('inf'), float('inf'), True, deadline)
        
        if move:
            best_move_found = move
        
        if timed_out:
            break

    if best_move_found:
        return f"{best_move_found[0]},{best_move_found[1]},{best_move_found[2]}"
    
    # Fallback (should theoretically not be reached if logic is correct)
    if moves:
        return f"{moves[0][0]},{moves[0][1]},{moves[0][2]}"
    return "0,0,H"

