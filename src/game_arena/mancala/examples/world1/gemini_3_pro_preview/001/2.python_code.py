
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    TIME_LIMIT = 0.98  # Use 0.98s to be safe within the 1s limit
    
    # Constants for player identification
    P0 = 0 # "You"
    P1 = 1 # "Opponent"
    STORE0 = 6
    STORE1 = 13
    
    # Combined board state: [you (0-6), opponent (7-13)]
    # Indices 0-5 are your houses, 6 is your store.
    # Indices 7-12 are opponent houses, 13 is opponent store.
    root_board = you + opponent

    # -------------------------------------------------------------------------
    # Helper Functions
    # -------------------------------------------------------------------------

    def simulate(board_state, move_idx, player):
        """
        Executes a move on the board.
        Args:
            board_state: List of 14 integers.
            move_idx: Relative index (0-5) of the house to sow from.
            player: 0 for You, 1 for Opponent.
        Returns:
            (next_board, next_player, game_over, score_diff)
        """
        b = list(board_state)
        
        # Setup offsets based on current player
        if player == P0:
            offset = 0
            my_store = STORE0
            opp_store = STORE1
            # Range of own houses for capture check
            my_house_start, my_house_end = 0, 5
        else:
            offset = 7
            my_store = STORE1
            opp_store = STORE0
            my_house_start, my_house_end = 7, 12
            
        # Pick up seeds
        pit = offset + move_idx
        seeds = b[pit]
        b[pit] = 0
        
        # Sow seeds
        pos = pit
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == opp_store:
                continue
            b[pos] += 1
            seeds -= 1
            
        # Determine next player and check special rules
        next_player = 1 - player
        
        # Rule 1: Extra Turn (Last seed in own store)
        if pos == my_store:
            next_player = player
            
        # Rule 2: Capture (Last seed in own empty house, opposite not empty)
        # Note: b[pos] is 1 because we just placed a seed there.
        if my_house_start <= pos <= my_house_end:
            if b[pos] == 1: 
                opp_pos = 12 - pos
                if b[opp_pos] > 0:
                    captured = b[pos] + b[opp_pos]
                    b[pos] = 0
                    b[opp_pos] = 0
                    b[my_store] += captured
                    
        # Rule 3: Game End (One side empty)
        sum0 = sum(b[0:6])
        sum1 = sum(b[7:13])
        
        if sum0 == 0 or sum1 == 0:
            # Game Over: Move remaining seeds to stores
            b[STORE0] += sum0
            b[STORE1] += sum1
            # Clean board
            for i in range(6): b[i] = 0
            for i in range(7, 13): b[i] = 0
            
            # Return final score diff immediately
            return b, -1, True, (b[STORE0] - b[STORE1])
            
        return b, next_player, False, 0

    # -------------------------------------------------------------------------
    # Search Algorithm (IDDFS + Minimax)
    # -------------------------------------------------------------------------
    
    nodes_visited = 0
    
    def minimax(board, depth, alpha, beta, player):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Check time every 1024 nodes to reduce overhead
        if (nodes_visited & 1023) == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise TimeoutError

        # Leaf or Max Depth
        if depth == 0:
            return board[STORE0] - board[STORE1]
            
        # Get Legal Moves
        offset = 0 if player == P0 else 7
        legal_moves = [i for i in range(6) if board[offset + i] > 0]
        
        # If no legal moves, game should be over (handled in simulate), 
        # but as a fallback simply eval.
        if not legal_moves:
            return board[STORE0] - board[STORE1]
            
        # Move Ordering: Prioritize Extra Turns (seeds == distance to store)
        prioritized = []
        others = []
        for m in legal_moves:
            dist = 6 - m
            seeds = board[offset + m]
            # Check if lands exactly in store (simple case or looped case)
            if seeds == dist or seeds == dist + 13:
                prioritized.append(m)
            else:
                others.append(m)
        sorted_moves = prioritized + others

        if player == P0: # Maximizing
            max_eval = -float('inf')
            for m in sorted_moves:
                nb, np, over, score = simulate(board, m, player)
                
                if over:
                    val = score
                else:
                    # Extension: If extra turn, keep same depth to allow combo search
                    # Otherwise decrement
                    d_next = depth if np == player else depth - 1
                    # Safety clamp
                    if d_next < 0: d_next = 0
                    
                    val = minimax(nb, d_next, alpha, beta, np)
                
                if val > max_eval:
                    max_eval = val
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    break
            return max_eval
        else: # Minimizing
            min_eval = float('inf')
            for m in sorted_moves:
                nb, np, over, score = simulate(board, m, player)
                
                if over:
                    val = score
                else:
                    d_next = depth if np == player else depth - 1
                    if d_next < 0: d_next = 0
                    
                    val = minimax(nb, d_next, alpha, beta, np)
                
                if val < min_eval:
                    min_eval = val
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break
            return min_eval

    # -------------------------------------------------------------------------
    # Main Loop
    # -------------------------------------------------------------------------
    
    # Identify legal moves
    legal_moves = [i for i in range(6) if root_board[i] > 0]
    
    if not legal_moves:
        return 0 # Should not happen unless game over
    if len(legal_moves) == 1:
        return legal_moves[0] # Only one option
        
    best_move = legal_moves[0]
    
    try:
        # Iterative Deepening
        # We start at depth 1 and increase until time runs out.
        # Max depth 25 is practically unreachable in 1s for BFs ~4-5, but serves as a cap.
        for d in range(1, 26):
            alpha = -float('inf')
            beta = float('inf')
            current_best_in_depth = legal_moves[0]
            max_val = -float('inf')
            
            # Root formatting & Ordering
            prioritized = []
            others = []
            for m in legal_moves:
                dist = 6 - m
                seeds = root_board[m]
                if seeds == dist or seeds == dist + 13:
                    prioritized.append(m)
                else:
                    others.append(m)
            root_sorted = prioritized + others
            
            for m in root_sorted:
                nb, np, over, score = simulate(root_board, m, P0)
                
                if over:
                    val = score
                else:
                    nd = d if np == P0 else d - 1
                    val = minimax(nb, nd, alpha, beta, np)
                
                if val > max_val:
                    max_val = val
                    current_best_in_depth = m
                
                alpha = max(alpha, max_val)
                
                # Check time at root level as well
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError
            
            # If we completed this depth fully, update best_move
            best_move = current_best_in_depth
            
    except TimeoutError:
        # Time ran out, return the best move from the last fully completed depth
        pass
        
    return best_move
