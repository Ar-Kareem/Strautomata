
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Determines the next move for a 4x4 Dots and Boxes game.
    
    Args:
        horizontal: 5x5 array, 0=empty, non-zero=occupied
        vertical: 5x5 array, 0=empty, non-zero=occupied
        capture: 5x5 array, 0=empty, 1=mine, -1=opponent
        
    Returns:
        str: Move in format 'row,col,dir'
    """
    
    # Dimensions
    rows, cols = 5, 5
    
    # Helper to check if a move is legal
    def is_legal(r, c, is_h):
        if 0 <= r < rows and 0 <= c < cols:
            arr = horizontal if is_h else vertical
            return arr[r, c] == 0
        return False

    # Helper to get list of all legal moves
    def get_legal_moves():
        moves = []
        # Horizontal moves: h[r, c] connects (r,c) to (r, c+1)
        # Valid c is 0..3 for boxes, but input array allows 0..4.
        # c=4 is the right boundary.
        for r in range(rows):
            for c in range(cols):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        
        # Vertical moves: v[r, c] connects (r,c) to (r+1, c)
        # Valid r is 0..3 for boxes. r=4 is the bottom boundary.
        for r in range(rows):
            for c in range(cols):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    # Helper to simulate a move and calculate captured boxes
    def simulate_move(r, c, is_h):
        # Returns (new_h, new_v, captured_indices_list)
        # We create copies or just check logically. 
        # Since this is called repeatedly, we check logic on the fly.
        
        h_new = horizontal.copy()
        v_new = vertical.copy()
        
        if is_h:
            h_new[r, c] = 1
        else:
            v_new[r, c] = 1
            
        captured = []
        
        # Check all 4 adjacent boxes (if they exist)
        # Box coordinates (br, bc) are 0..3
        # Box top-left is (r, c). Edge h[r, c] is Top.
        if is_h:
            # Box above the edge: (r-1, c). Edge is Bottom.
            if r > 0:
                br, bc = r-1, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if all(e != 0 for e in edges):
                    captured.append((br, bc))
            # Box below the edge: (r, c). Edge is Top.
            if r < rows - 1:
                br, bc = r, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if all(e != 0 for e in edges):
                    captured.append((br, bc))
        else:
            # Box left of edge: (r, c-1). Edge is Right.
            if c > 0:
                br, bc = r, c-1
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if all(e != 0 for e in edges):
                    captured.append((br, bc))
            # Box right of edge: (r, c). Edge is Left.
            if c < cols - 1:
                br, bc = r, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if all(e != 0 for e in edges):
                    captured.append((br, bc))
                    
        return h_new, v_new, captured

    # Helper to check if a move creates a 3-box (dangerous)
    def creates_three_sided_box(r, c, is_h):
        h_new, v_new, _ = simulate_move(r, c, is_h)
        
        # Check neighbors
        if is_h:
            # Check box above (r-1, c)
            if r > 0:
                br, bc = r-1, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                # Count non-zeros
                if sum(e != 0 for e in edges) == 3:
                    return True
            # Check box below (r, c)
            if r < rows - 1:
                br, bc = r, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if sum(e != 0 for e in edges) == 3:
                    return True
        else:
            # Check box left (r, c-1)
            if c > 0:
                br, bc = r, c-1
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if sum(e != 0 for e in edges) == 3:
                    return True
            # Check box right (r, c)
            if c < cols - 1:
                br, bc = r, c
                edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
                if sum(e != 0 for e in edges) == 3:
                    return True
        return False

    # Categorize moves
    legal_moves = get_legal_moves()
    if not legal_moves:
        return "0,0,H" # Should not happen unless game over

    capturing_moves = []
    safe_moves = []
    unsafe_moves = []
    boundary_moves = []
    
    # Boundary indices: h[r, 4] and v[4, c] do not bound a 4x4 box.
    # Note: In a 4x4 box grid (indices 0..3), h[r, 4] is right boundary. v[4, c] is bottom.
    for r, c, d in legal_moves:
        if d == 'H' and c == 4:
            boundary_moves.append((r, c, d))
        elif d == 'V' and r == 4:
            boundary_moves.append((r, c, d))
        else:
            _, _, caps = simulate_move(r, c, d == 'H')
            if caps:
                capturing_moves.append((r, c, d, len(caps)))
            elif not creates_three_sided_box(r, c, d == 'H'):
                safe_moves.append((r, c, d))
            else:
                unsafe_moves.append((r, c, d))

    # 1. Prioritize Captures
    if capturing_moves:
        # Pick one with max captures
        capturing_moves.sort(key=lambda x: x[3], reverse=True)
        best = capturing_moves[0]
        return f"{best[0]},{best[1]},{best[2]}"
        
    # 2. Prioritize Safe Moves
    if safe_moves:
        # Heuristic: Try to force opponent into a position with no safe moves.
        # We perform a 1-ply lookahead on safe moves.
        # A "hard" move is one that leaves the opponent with 0 safe moves (but game not over).
        
        best_safe_moves = []
        
        # Evaluate safe moves
        for r, c, d in safe_moves:
            h_new, v_new, _ = simulate_move(r, c, d == 'H')
            
            # Count opponent's safe moves from this state
            opp_safe_count = 0
            opp_has_capture = False
            
            # Check all legal opponent moves in this hypothetical state
            # Optimization: Only check if move is safe for opponent
            # We iterate through all legal moves in the CURRENT board, 
            # but we need to check against NEW board.
            
            # Quick check: does opponent have a capture?
            for r2, c2, d2 in get_legal_moves():
                if (r2, c2, d2) == (r, c, d): continue # don't check self
                
                # Check validity in new state
                is_h2 = (d2 == 'H')
                is_legal = False
                if is_h2 and h_new[r2, c2] == 0: is_legal = True
                if not is_h2 and v_new[r2, c2] == 0: is_legal = True
                
                if is_legal:
                    # Check capture
                    cap_h, cap_v, caps = simulate_move_logic(h_new, v_new, r2, c2, is_h2)
                    if caps:
                        opp_has_capture = True
                        break 
                    
                    # Check safe
                    if not creates_three_sided_box_logic(cap_h, cap_v, r2, c2, is_h2):
                        opp_safe_count += 1
            
            if opp_has_capture:
                # If opponent can capture, that's bad (they take points and keep turn)
                # Lower priority
                score = -100
            else:
                # We want to minimize opponent's safe moves
                score = -opp_safe_count
            
            best_safe_moves.append((score, r, c, d))
            
        best_safe_moves.sort(key=lambda x: x[0])
        return f"{best_safe_moves[0][1]},{best_safe_moves[0][2]},{best_safe_moves[0][3]}"

    # 3. Boundary Moves (Free Pass)
    if boundary_moves:
        # Random boundary move is fine
        m = random.choice(boundary_moves)
        return f"{m[0]},{m[1]},{m[2]}"

    # 4. Unsafe Moves (Minimize Damage)
    if unsafe_moves:
        # Simulate opponent taking the chain
        # Find move that gives opponent fewest boxes
        min_loss = 100
        best_move = unsafe_moves[0]
        
        for r, c, d in unsafe_moves:
            # Simulate my unsafe move
            h_curr, v_curr, _ = simulate_move(r, c, d == 'H')
            
            # Opponent plays optimally (greedily captures)
            loss = 0
            while True:
                # Find all captures for opponent
                opp_captures = []
                for r2 in range(rows):
                    for c2 in range(cols):
                        # Check H
                        if h_curr[r2, c2] == 0:
                            _, _, caps = simulate_move_logic(h_curr, v_curr, r2, c2, True)
                            if caps:
                                opp_captures.append((r2, c2, True, len(caps)))
                        # Check V
                        if v_curr[r2, c2] == 0:
                            _, _, caps = simulate_move_logic(h_curr, v_curr, r2, c2, False)
                            if caps:
                                opp_captures.append((r2, c2, False, len(caps)))
                
                if not opp_captures:
                    break
                
                # Opponent takes the best capture
                opp_captures.sort(key=lambda x: x[3], reverse=True)
                best = opp_captures[0]
                loss += best[3]
                
                # Apply move
                if best[2]: # H
                    h_curr[best[0], best[1]] = 1
                else: # V
                    v_curr[best[0], best[1]] = 1
                    
            if loss < min_loss:
                min_loss = loss
                best_move = (r, c, d)
                
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Fallback
    m = legal_moves[0]
    return f"{m[0]},{m[1]},{m[2]}"

# Logic duplicates to allow passing state without recursion/global ref issues
def simulate_move_logic(h_arr, v_arr, r, c, is_h):
    h_new = h_arr.copy()
    v_new = v_arr.copy()
    
    if is_h:
        h_new[r, c] = 1
    else:
        v_new[r, c] = 1
        
    captured = []
    rows, cols = 5, 5
    
    if is_h:
        if r > 0:
            br, bc = r-1, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if all(e != 0 for e in edges): captured.append((br, bc))
        if r < rows - 1:
            br, bc = r, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if all(e != 0 for e in edges): captured.append((br, bc))
    else:
        if c > 0:
            br, bc = r, c-1
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if all(e != 0 for e in edges): captured.append((br, bc))
        if c < cols - 1:
            br, bc = r, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if all(e != 0 for e in edges): captured.append((br, bc))
            
    return h_new, v_new, captured

def creates_three_sided_box_logic(h_arr, v_arr, r, c, is_h):
    h_new, v_new, _ = simulate_move_logic(h_arr, v_arr, r, c, is_h)
    rows, cols = 5, 5
    
    if is_h:
        if r > 0:
            br, bc = r-1, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if sum(e != 0 for e in edges) == 3: return True
        if r < rows - 1:
            br, bc = r, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if sum(e != 0 for e in edges) == 3: return True
    else:
        if c > 0:
            br, bc = r, c-1
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if sum(e != 0 for e in edges) == 3: return True
        if c < cols - 1:
            br, bc = r, c
            edges = [h_new[br, bc], h_new[br+1, bc], v_new[br, bc], v_new[br+1, bc]]
            if sum(e != 0 for e in edges) == 3: return True
    return False
