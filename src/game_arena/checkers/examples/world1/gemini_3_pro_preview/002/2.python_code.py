
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # --- Configuration ---
    TIME_LIMIT = 0.95  # Seconds buffers
    MAX_DEPTH_LIMIT = 20
    
    # Board Values
    EMPTY = 0
    MY_MAN = 1
    MY_KING = 2
    OPP_MAN = -1
    OPP_KING = -2
    
    # Evaluation Weights
    W_MAN = 100
    W_KING = 175
    W_BACK = 15
    W_CENTER = 5
    
    start_time = time.time()
    
    # --- Board Setup ---
    board = [[0] * 8 for _ in range(8)]
    for r, c in my_men: board[r][c] = MY_MAN
    for r, c in my_kings: board[r][c] = MY_KING
    for r, c in opp_men: board[r][c] = OPP_MAN
    for r, c in opp_kings: board[r][c] = OPP_KING
    
    # Determine movement direction
    # color 'w' (White) moves UP (row + 1), 'b' (Black) moves DOWN (row - 1)
    FORWARD_ROW = 1 if color == 'w' else -1
    PROMOTE_ROW = 7 if color == 'w' else 0
    OPP_FORWARD_ROW = -1 if color == 'w' else 1
    OPP_PROMOTE_ROW = 0 if color == 'w' else 7

    # --- Helpers ---
    def on_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def evaluate(b):
        score = 0
        for r in range(8):
            for c in range(8):
                p = b[r][c]
                if p == 0: continue
                
                # Material Score
                abs_p = abs(p)
                val = W_KING if abs_p == 2 else W_MAN
                
                # Positional Bonuses
                # 1. Center Control (Middle box)
                if 2 <= c <= 5 and 3 <= r <= 4:
                    val += W_CENTER
                
                # 2. Back Rank Integrity (Guard kings)
                if p > 0: # My pieces
                    if (color == 'w' and r == 0) or (color == 'b' and r == 7):
                        val += W_BACK
                else: # Opp pieces
                    if (color == 'w' and r == 7) or (color == 'b' and r == 0):
                        val += W_BACK

                if p > 0: score += val
                else: score -= val
        return score

    # --- Move Generation ---
    # Returns list of tuples: (first_step, resulting_board)
    # first_step is ((r1,c1), (r2,c2))
    
    def get_moves(b, player): 
        # player: 1 (Me), -1 (Opp)
        is_me = (player == 1)
        
        p_man = MY_MAN if is_me else OPP_MAN
        p_king = MY_KING if is_me else OPP_KING
        
        # Determine strict forward directions for men
        if is_me:
            fwd_dirs = [(FORWARD_ROW, -1), (FORWARD_ROW, 1)]
        else:
            fwd_dirs = [(OPP_FORWARD_ROW, -1), (OPP_FORWARD_ROW, 1)]
        
        # Kings move all 4 diagonals
        king_dirs = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        
        pieces_loc = []
        for r in range(8):
            for c in range(8):
                p = b[r][c]
                if p == p_man or p == p_king:
                    pieces_loc.append((r, c))
                    
        # 1. Look for Jumps (Mandatory Capture Rule)
        all_jumps = []
        
        def find_jumps(r, c, current_board, steps_taken):
            # Recursively finds jump chains.
            p = current_board[r][c]
            is_king = (abs(p) == 2)
            dirs = king_dirs if is_king else fwd_dirs
            
            branches = []
            
            for dr, dc in dirs:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + 2*dr, c + 2*dc
                
                if on_board(land_r, land_c):
                    mid_p = current_board[mid_r][mid_c]
                    land_p = current_board[land_r][land_c]
                    
                    # Check capture condition: mid is enemy, land is empty
                    if mid_p != 0 and (p * mid_p < 0) and land_p == 0:
                        # Construct next state
                        nb = [row[:] for row in current_board]
                        nb[r][c] = 0
                        nb[mid_r][mid_c] = 0
                        nb[land_r][land_c] = p
                        
                        # Check Promotion
                        promoted = False
                        promote_r = PROMOTE_ROW if is_me else OPP_PROMOTE_ROW
                        if not is_king and land_r == promote_r:
                            nb[land_r][land_c] = p_king if is_me else -abs(p_king)
                            promoted = True
                        
                        step = ((r, c), (land_r, land_c))
                        new_chain = steps_taken + [step]
                        
                        # Terminate if promoted or recursive search yields no deeper jumps
                        if promoted:
                            branches.append((new_chain, nb))
                        else:
                            sub_results = find_jumps(land_r, land_c, nb, new_chain)
                            if sub_results:
                                branches.extend(sub_results)
                            else:
                                branches.append((new_chain, nb))
            return branches

        for r, c in pieces_loc:
            chains = find_jumps(r, c, b, [])
            for chain_steps, final_b in chains:
                all_jumps.append((chain_steps[0], final_b))
                
        if all_jumps:
            # If jumps exist, strict checkers rules forbid sliding options
            # Prioritize taking longest chains? Usually standard AI logic prefers this implicitly via evaluation,
            # but we return all valid jump starts here.
            return all_jumps

        # 2. Slides (only if no jumps)
        slides = []
        for r, c in pieces_loc:
            p = b[r][c]
            is_king = (abs(p) == 2)
            dirs = king_dirs if is_king else fwd_dirs
            
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if on_board(nr, nc) and b[nr][nc] == 0:
                    nb = [row[:] for row in b]
                    nb[r][c] = 0
                    nb[nr][nc] = p
                    
                    # Promotion
                    promote_r = PROMOTE_ROW if is_me else OPP_PROMOTE_ROW
                    if not is_king and nr == promote_r:
                        nb[nr][nc] = p_king if is_me else -abs(p_king)
                        
                    slides.append( (((r,c), (nr,nc)), nb) )
                    
        return slides

    # --- Minimax Search ---
    class TimeoutException(Exception): pass

    def alphabeta(node_board, depth, alpha, beta, maximizing_player):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutException
            
        if depth == 0:
            return evaluate(node_board)
            
        moves = get_moves(node_board, 1 if maximizing_player else -1)
        
        # Tie/Loss detection
        if not moves:
            # If current player has no moves, they lose
            return -100000 + depth if maximizing_player else 100000 - depth
            
        if maximizing_player:
            max_eval = -float('inf')
            for _, next_b in moves:
                eval_val = alphabeta(next_b, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for _, next_b in moves:
                eval_val = alphabeta(next_b, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Iterative Deepening Execution ---
    initial_moves = get_moves(board, 1)
    
    # Fallback if no moves available
    if not initial_moves:
        return ((0,0), (0,0))
    
    best_move_found = initial_moves[0][0] # Default to first valid
    
    try:
        for depth in range(1, MAX_DEPTH_LIMIT + 1):
            best_val = -float('inf')
            current_depth_best = None
            
            for step, next_b in initial_moves:
                val = alphabeta(next_b, depth - 1, -float('inf'), float('inf'), False)
                if val > best_val:
                    best_val = val
                    current_depth_best = step
            
            if current_depth_best:
                best_move_found = current_depth_best
                
            # Time check break to avoid starting a depth we can't finish
            if time.time() - start_time > 0.8:
                break
                
    except TimeoutException:
        pass # Return the best move found in previous completed depths
        
    return best_move_found
