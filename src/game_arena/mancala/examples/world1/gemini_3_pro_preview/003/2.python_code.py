
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy.
    Uses Iterative Deepening Minimax with Alpha-Beta pruning within a 1-second time limit.
    """
    
    # -------------------------------------------------------------------------
    # CONFIG & CONSTANTS
    # -------------------------------------------------------------------------
    START_TIME = time.time()
    TIME_LIMIT = 0.98  # Safety buffer (20ms)
    
    # Board Indices
    # Player (Me): Houses 0-5, Store 6
    # Opponent:    Houses 7-12, Store 13
    IDX_STORE_ME = 6
    IDX_STORE_OPP = 13
    BOARD_SIZE = 14
    
    # Create internal board representation
    # We use a tuple for the board to enable potential caching (though distinct states are many)
    initial_board = tuple(you + opponent)
    
    # -------------------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------------------
    
    def get_legal_moves(board_tuple, player):
        """Returns list of indices where the player has seeds."""
        if player == 0:
            return [i for i in range(6) if board_tuple[i] > 0]
        else:
            return [i for i in range(7, 13) if board_tuple[i] > 0]

    def make_move(board_tuple, move_idx, player):
        """
        Simulates a move.
        Returns: (next_board_tuple, next_player, game_over_flag)
        """
        b = list(board_tuple)
        seeds = b[move_idx]
        b[move_idx] = 0
        
        pos = move_idx
        
        # Distribute seeds
        while seeds > 0:
            pos = (pos + 1) % BOARD_SIZE
            
            # Skip opponent's store
            if player == 0 and pos == IDX_STORE_OPP:
                continue
            if player == 1 and pos == IDX_STORE_ME:
                continue
            
            b[pos] += 1
            seeds -= 1
            
        # Check Special Rules based on where the last seed landed
        # pos is the location of the last seed
        extra_turn = False
        
        # 1. Extra Move Rule: Last seed in own store
        if player == 0:
            if pos == IDX_STORE_ME:
                extra_turn = True
        else:
            if pos == IDX_STORE_OPP:
                extra_turn = True
                
        # 2. Capture Rule: Last seed in own empty house & opposite valid
        # Note: b[pos] == 1 means it was 0 before this placement
        did_capture = False
        if not extra_turn:
            # Capture only applies if landing in own field
            if player == 0:
                if 0 <= pos <= 5 and b[pos] == 1:
                    # Opposite index rule: 0->12 (5), 1->11 (4), ..., i -> 12-i
                    opp_idx = 12 - pos
                    if b[opp_idx] > 0:
                        loot = b[pos] + b[opp_idx]
                        b[pos] = 0
                        b[opp_idx] = 0
                        b[IDX_STORE_ME] += loot
                        did_capture = True
            else:
                if 7 <= pos <= 12 and b[pos] == 1:
                    opp_idx = 12 - pos
                    if b[opp_idx] > 0:
                        loot = b[pos] + b[opp_idx]
                        b[pos] = 0
                        b[opp_idx] = 0
                        b[IDX_STORE_OPP] += loot
                        did_capture = True
        
        # 3. Game Over Check (One side empty)
        # If one side is empty, game ends immediately.
        # Remaining seeds on the other side are captured by that player.
        me_empty = (sum(b[0:6]) == 0)
        opp_empty = (sum(b[7:13]) == 0)
        
        if me_empty or opp_empty:
            rem_me = sum(b[0:6])
            rem_opp = sum(b[7:13])
            
            b[IDX_STORE_ME] += rem_me
            b[IDX_STORE_OPP] += rem_opp
            
            # Clear board for cleanliness
            for i in range(6): b[i] = 0
            for i in range(7, 13): b[i] = 0
            
            return tuple(b), -1, True
            
        next_player = player if extra_turn else (1 - player)
        return tuple(b), next_player, False

    def evaluate(board_tuple):
        """Heuristic evaluation: My Score - Opponent Score."""
        return board_tuple[IDX_STORE_ME] - board_tuple[IDX_STORE_OPP]
    
    # -------------------------------------------------------------------------
    # SEARCH ENGINE
    # -------------------------------------------------------------------------
    nodes_visited = 0
    
    def minimax(board_tuple, depth, alpha, beta, player):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Periodically check time to reduce syscall overhead
        if nodes_visited & 127 == 0:
            if time.time() - START_TIME > TIME_LIMIT:
                raise TimeoutError
        
        # Base case: depth limit (unless handled by make_move returning game_over)
        if depth <= 0:
            return evaluate(board_tuple)
        
        moves = get_legal_moves(board_tuple, player)
        
        # If no legal moves, game should be over (handled in previous step), 
        # but as a fallback check:
        if not moves:
            return evaluate(board_tuple)
            
        # Move ordering logic could go here, but omitted for speed in deep recursion.
        # Rely on initial sorting in the root.
        
        if player == 0: # Maximizer
            value = -float('inf')
            for move in moves:
                next_b, next_p, game_over = make_move(board_tuple, move, player)
                
                if game_over:
                    val = evaluate(next_b)
                else:
                    # Logic: Extra turns do not decrement depth to allow searching full sequences.
                    # Standard turns decrement depth.
                    new_depth = depth if (next_p == player) else (depth - 1)
                    val = minimax(next_b, new_depth, alpha, beta, next_p)
                
                if val > value:
                    value = val
                alpha = max(alpha, value)
                if value >= beta:
                    break
            return value
        
        else: # Minimizer
            value = float('inf')
            for move in moves:
                next_b, next_p, game_over = make_move(board_tuple, move, player)
                
                if game_over:
                    val = evaluate(next_b)
                else:
                    new_depth = depth if (next_p == player) else (depth - 1)
                    val = minimax(next_b, new_depth, alpha, beta, next_p)
                
                if val < value:
                    value = val
                beta = min(beta, value)
                if value <= alpha:
                    break
            return value

    # -------------------------------------------------------------------------
    # MAIN LOOP (IDDFS)
    # -------------------------------------------------------------------------
    legal_moves = get_legal_moves(initial_board, 0)
    
    # Trivial cases/Sanity check
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    # Heuristic Move Ordering for Root
    # We prefer moves that:
    # 1. Grant an extra turn immediately.
    # 2. Result in a capture or large score increase.
    # 3. Are closer to the store (conventional heuristic).
    ordered_moves = []
    
    for m in legal_moves:
        next_b, next_p, game_over = make_move(initial_board, m, 0)
        
        score_gain = next_b[IDX_STORE_ME] - initial_board[IDX_STORE_ME]
        is_extra = (next_p == 0 and not game_over)
        
        # Priority Weighting
        weight = 0
        if is_extra: weight += 10000
        weight += score_gain * 10
        weight += m # Tie-breaker: prefer moves closer to store? (indices 0-5)
        
        ordered_moves.append((weight, m))
        
    # Sort descending weight
    ordered_moves.sort(key=lambda x: x[0], reverse=True)
    root_moves = [x[1] for x in ordered_moves]
    
    best_move = root_moves[0]
    
    try:
        current_depth = 1
        # IDDFS Loop
        while True:
            alpha = -float('inf')
            beta = float('inf')
            iteration_best_move = root_moves[0]
            iteration_best_val = -float('inf')
            
            for move in root_moves:
                next_b, next_p, game_over = make_move(initial_board, move, 0)
                
                if game_over:
                    val = evaluate(next_b)
                else:
                    d_next = current_depth if (next_p == 0) else (current_depth - 1)
                    val = minimax(next_b, d_next, alpha, beta, next_p)
                
                if val > iteration_best_val:
                    iteration_best_val = val
                    iteration_best_move = move
                    
                alpha = max(alpha, val)
            
            # If we completed the depth without timeout, update global best
            best_move = iteration_best_move
            current_depth += 1
            
            # Depth cap to prevent extremely long search on simple boards
            if current_depth > 20: 
                break
                
    except TimeoutError:
        # Time ran out, return the best move from the last fully completed depth
        pass
        
    return best_move
