
import numpy as np
import time

def policy(board) -> str:
    """
    Amazons Policy for 6x6 Board
    Strategy: 1-ply Greedy Search with Territory Evaluation (BFS)
    """
    
    # Game Constants
    ME = 1
    OPP = 2
    EMPTY = 0
    ARROW = -1
    SIZE = 6
    
    # Time Management
    # Stop searching if we exceed this threshold to ensure we return safely
    TIME_LIMIT = 0.90 
    begin_time = time.time()
    
    # Movement Directions (Orthogonal + Diagonal)
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    def evaluate(current_board):
        """
        Evaluates the board state based on territory control.
        Uses BFS to find the shortest 'queen-move' distance to all cells.
        """
        # Identify queen locations
        p1_locs = []
        p2_locs = []
        for r in range(SIZE):
            for c in range(SIZE):
                val = current_board[r, c]
                if val == ME:
                    p1_locs.append((r, c))
                elif val == OPP:
                    p2_locs.append((r, c))
        
        # Helper: Multi-source BFS to calculate min moves to reach cells
        def bfs_reach(starts):
            # initialize with a high distance
            dists = np.full((SIZE, SIZE), 999, dtype=int)
            queue = list(starts)
            
            # Distance to self is 0
            for r, c in starts:
                dists[r, c] = 0
            
            head = 0
            while head < len(queue):
                r, c = queue[head]
                head += 1
                current_dist = dists[r, c]
                next_dist = current_dist + 1
                
                for dr, dc in directions:
                    cr, cc = r, c
                    while True:
                        cr += dr
                        cc += dc
                        
                        # Check bounds
                        if 0 <= cr < SIZE and 0 <= cc < SIZE:
                            # If blocked, stop sliding in this direction
                            if current_board[cr, cc] != EMPTY:
                                break
                            
                            # If we found a shorter path to this empty square
                            if dists[cr, cc] > next_dist:
                                dists[cr, cc] = next_dist
                                queue.append((cr, cc))
                            
                            # In Amazons, we continue sliding through empty squares
                            # even if we've visited them, to reach squares further down the line.
                        else:
                            break
            return dists

        # Calculate distances for both players
        dists_me = bfs_reach(p1_locs)
        dists_opp = bfs_reach(p2_locs)
        
        score = 0
        
        # Calculate territory score
        for r in range(SIZE):
            for c in range(SIZE):
                if current_board[r, c] == EMPTY:
                    d_me = dists_me[r, c]
                    d_opp = dists_opp[r, c]
                    
                    # If I can reach it faster, it's my territory
                    if d_me < d_opp:
                        # Base point for territory
                        score += 1.0 
                        # Tie-breaker: prefer closer squares slightly
                        score += 0.01 / d_me
                    elif d_opp < d_me:
                        score -= 1.0
                        score -= 0.01 / d_opp
                    # If distances are equal, it's neutral/contested (0 points)

        return score

    # Store the best move found
    best_move_str = None
    best_val = -float('inf')
    
    # Identify my pieces to generate moves
    my_pieces = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r, c] == ME:
                my_pieces.append((r, c))
    
    # --- Move Generation & Search ---
    
    # Iterate through all my Amazons
    for r_from, c_from in my_pieces:
        
        # 1. Try moving the Amazon
        for dr, dc in directions:
            r_to, c_to = r_from, c_from
            while True:
                r_to += dr
                c_to += dc
                
                # Check board boundaries
                if not (0 <= r_to < SIZE and 0 <= c_to < SIZE):
                    break
                # Check for blockers
                if board[r_to, c_to] != EMPTY:
                    break
                
                # EXECUTE MOVE (Temporarily)
                board[r_from, c_from] = EMPTY
                board[r_to, c_to] = ME
                
                # 2. Try shooting an arrow
                for adr, adc in directions:
                    r_arr, c_arr = r_to, c_to
                    while True:
                        r_arr += adr
                        c_arr += adc
                        
                        # Check bounds for arrow
                        if not (0 <= r_arr < SIZE and 0 <= c_arr < SIZE):
                            break
                        # Check blockers for arrow
                        if board[r_arr, c_arr] != EMPTY:
                            break
                        
                        # EXECUTE SHOT (Temporarily)
                        board[r_arr, c_arr] = ARROW
                        
                        # EVALUATE POSITION
                        current_val = evaluate(board)
                        
                        # Update Best Move
                        if current_val > best_val:
                            best_val = current_val
                            best_move_str = f"{r_from},{c_from}:{r_to},{c_to}:{r_arr},{c_arr}"
                        
                        # Ensure we always return something legal
                        if best_move_str is None:
                            best_move_str = f"{r_from},{c_from}:{r_to},{c_to}:{r_arr},{c_arr}"
                            best_val = current_val

                        # UNDO SHOT
                        board[r_arr, c_arr] = EMPTY
                        
                        # Check Timeout
                        if (time.time() - begin_time) > TIME_LIMIT:
                            # Undo Move and return immediately
                            board[r_to, c_to] = EMPTY
                            board[r_from, c_from] = ME
                            return best_move_str

                    # Check Timeout after inner loop
                    if (time.time() - begin_time) > TIME_LIMIT:
                        board[r_to, c_to] = EMPTY
                        board[r_from, c_from] = ME
                        return best_move_str

                # UNDO MOVE
                board[r_to, c_to] = EMPTY
                board[r_from, c_from] = ME
                
                # Check Timeout
                if (time.time() - begin_time) > TIME_LIMIT:
                    return best_move_str

    # If no move found (should imply game over, but returning strictly string)
    if best_move_str is None:
        # Construct a dummy self-loop if somehow no moves are found to satisfy return type
        # In a real game, this function wouldn't be called if no moves exist.
        return f"{my_pieces[0][0]},{my_pieces[0][1]}:{my_pieces[0][0]},{my_pieces[0][1]}:{my_pieces[0][0]},{my_pieces[0][1]}"

    return best_move_str
