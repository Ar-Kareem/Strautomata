
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy using Iterative Deepening Minimax with Alpha-Beta pruning.
    
    Args:
        you: list of 7 integers [h0, h1, m.., h5, store] representing your side.
        opponent: list of 7 integers [h0, ..., h5, store] representing opponent's side.
        
    Returns:
        int: Index of the house (0-5) to move from.
    """
    start_time = time.time()
    TIME_LIMIT = 0.98  # Seconds

    # --- Helper Functions ---

    def get_final_score(p1_board, p2_board):
        """Calculates final score assuming game is over (clearing board)."""
        # Remaining seeds on board go to owner's store
        s1 = p1_board[6] + sum(p1_board[:6])
        s2 = p2_board[6] + sum(p2_board[:6])
        return s1 - s2

    def evaluate(p1_board, p2_board):
        """Heuristic evaluation: Difference in total seeds held."""
        # Seeds in store + seeds on board are the total material.
        # This steers the AI to maximize material advantage.
        s1 = p1_board[6] + sum(p1_board[:6])
        s2 = p2_board[6] + sum(p2_board[:6])
        return s1 - s2

    def simulate(p1, p2, move_idx):
        """
        Simulate a move.
        Returns: (new_p1, new_p2, repeat_turn)
        """
        # Copy boards
        my_side = p1[:]
        op_side = p2[:]
        
        seeds = my_side[move_idx]
        my_side[move_idx] = 0
        
        # Sowing path logic
        # Indices 0-5: My houses
        # Index 6: My store
        # Indices 7-12: Opponent houses (op_side[0]..op_side[5])
        pos = move_idx
        
        while seeds > 0:
            pos = (pos + 1) % 13
            if pos < 6:
                my_side[pos] += 1
            elif pos == 6:
                my_side[6] += 1
            else: # 7 <= pos <= 12
                # Map 7..12 back to opponent 0..5
                op_side[pos - 7] += 1
            seeds -= 1
            
        repeat_turn = (pos == 6)
        
        # Capture Rule:
        # If last seed lands in my empty house (0-5) and opposite house is not empty
        # Note: 'pos' is the index where the last seed landed.
        # If my_side[pos] == 1, it means it was previously 0 (since we just added 1).
        if 0 <= pos <= 5 and my_side[pos] == 1:
            # Calculate opposite index
            # Visual alignment: My 0 is opposite Opp 5 (index 12 in full circle? No)
            # Standard Kalah opposites: i and (5-i)
            opp_idx = 5 - pos
            if op_side[opp_idx] > 0:
                # Capture own seed + opponent's seeds
                captured_amount = 1 + op_side[opp_idx]
                my_side[6] += captured_amount
                my_side[pos] = 0
                op_side[opp_idx] = 0
        
        return my_side, op_side, repeat_turn

    # --- Search Logic ---

    nodes_visited = 0

    def minimax(p1, p2, depth, alpha, beta):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Check time periodically (every 256 nodes)
        if nodes_visited & 0xFF == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise TimeoutError

        # Check Game Over
        # Game ends if either side has no seeds in houses
        p1_empty = (sum(p1[:6]) == 0)
        p2_empty = (sum(p2[:6]) == 0)
        
        if p1_empty or p2_empty:
            return get_final_score(p1, p2)

        if depth <= 0:
            return evaluate(p1, p2)

        # Generate Valid Moves
        moves = [i for i, s in enumerate(p1[:6]) if s > 0]
        
        # Move Ordering for Pruning
        # 1. Moves that grant an extra turn
        # 2. Regular moves ordered right-to-left (often better in Mancala)
        priority = []
        normal = []
        for m in moves:
            seeds = p1[m]
            dist_to_store = 6 - m
            # Check if lands exactly in store
            # Logic: exact fit OR wraps around (13 seeds loop) and fits
            if seeds == dist_to_store or (seeds > 13 and (seeds - dist_to_store) % 13 == 0):
                priority.append(m)
            else:
                normal.append(m)
        
        normal.sort(reverse=True)
        ordered_moves = priority + normal

        best_val = -float('inf')

        for m in ordered_moves:
            next_p1, next_p2, again = simulate(p1, p2, m)
            
            if again:
                # Same player moves again.
                # We do not decrement depth to ensure we don't explore infinite chains shallowly,
                # though strictly speaking depth usually refers to ply. 
                # Keeping depth same or decrementing is a design choice. 
                # Decrementing ensures termination in fixed time, but extra turns are instant.
                # Given time limit, treating extra turn as same search node level works well.
                # But to avoid blowing up on long chains, we can decrement. 
                # Let's keep depth for extra turn to play perfectly in endgames.
                val = minimax(next_p1, next_p2, depth, alpha, beta)
            else:
                # Opponent's turn: minimize their result (which is negative of our result)
                val = -minimax(next_p2, next_p1, depth - 1, -beta, -alpha)
            
            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        
        return best_val

    # --- Iterative Deepening Execution ---

    possible_moves = [i for i, s in enumerate(you[:6]) if s > 0]
    if not possible_moves:
        return 0 # Should not happen per rules
    if len(possible_moves) == 1:
        return possible_moves[0]

    best_move = possible_moves[0]
    
    try:
        # Depth 1 to N
        # N chosen to be high enough that time limit usually triggers first
        for d in range(1, 25):
            # Sort moves using basic heuristic or previous iteration best
            
            # Basic ordering
            priority = []
            normal = []
            for m in possible_moves:
                seeds = you[m]
                dist = 6 - m
                if seeds == dist or (seeds > 13 and (seeds - dist) % 13 == 0):
                    priority.append(m)
                else:
                    normal.append(m)
            normal.sort(reverse=True)
            candidate_ordering = priority + normal
            
            # Put previous best move first (Principal Variation)
            if best_move in candidate_ordering:
                candidate_ordering.remove(best_move)
                candidate_ordering.insert(0, best_move)
            
            current_iter_best_val = -float('inf')
            current_iter_best_move = candidate_ordering[0]
            alpha = -float('inf')
            beta = float('inf')
            
            for m in candidate_ordering:
                ny, no, again = simulate(you, opponent, m)
                
                if again:
                    val = minimax(ny, no, d, alpha, beta)
                else:
                    val = -minimax(no, ny, d - 1, -beta, -alpha)
                
                if val > current_iter_best_val:
                    current_iter_best_val = val
                    current_iter_best_move = m
                
                alpha = max(alpha, val)
                
                # Check time at root level as well
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

            # Update best move only after completing full search for this depth
            best_move = current_iter_best_move
            
    except TimeoutError:
        # Time runs out, return best move found in previous fully completed depth
        pass

    return best_move
