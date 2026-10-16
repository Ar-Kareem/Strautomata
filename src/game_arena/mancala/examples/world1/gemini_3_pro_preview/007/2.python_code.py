
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah-6 move selection policy using Iterative Deepening Minimax with Alpha-Beta pruning.
    
    Args:
        you: List of 7 integers [h0, h1, h2, h3, h4, h5, store] representing your side.
        opponent: List of 7 integers [h0, h1, h2, h3, h4, h5, store] representing opponent side.
        
    Returns:
        int: Index 0-5 representing the chosen house to move from.
    """
    
    # Constants and limits
    TIME_LIMIT = 0.92  # Seconds (leave buffer)
    MAX_DEPTH = 50     # Depth cap (unlikely to be reached in 1s)
    MY_STORE_IDX = 6
    OPP_STORE_IDX = 13
    
    start_time = time.time()
    
    # Internal board representation: 14 integers
    # Indices 0-5: My houses
    # Index 6: My store
    # Indices 7-12: Opponent houses (mapped from opponent 0-5)
    # Index 13: Opponent store
    initial_board = you + opponent
    
    # --- Helper Functions ---

    def get_legal_moves(board, player):
        """Returns list of valid move indices for the given player (0=Me, 1=Opp)."""
        moves = []
        offset = 0 if player == 0 else 7
        for i in range(6):
            if board[offset + i] > 0:
                moves.append(offset + i)
        return moves

    def do_move(board, move_idx, player):
        """
        Executes a move on the board.
        Returns: (new_board_list, extra_turn_boolean)
        """
        new_board = list(board)
        seeds = new_board[move_idx]
        new_board[move_idx] = 0
        
        ptr = move_idx
        my_store = MY_STORE_IDX if player == 0 else OPP_STORE_IDX
        opp_store = OPP_STORE_IDX if player == 0 else MY_STORE_IDX
        
        # Sowing seeds
        while seeds > 0:
            ptr = (ptr + 1) % 14
            if ptr == opp_store:
                continue
            new_board[ptr] += 1
            seeds -= 1
            
        extra_turn = (ptr == my_store)
        
        # Capture Logic
        # Capture happens if last seed lands in own empty house and opposite house has seeds.
        # Note: 'ptr' is the index where the last seed landed.
        if not extra_turn:
            is_own_side = (0 <= ptr <= 5) if player == 0 else (7 <= ptr <= 12)
            # Check consistency: rule says 'was empty'.
            # Since we just added 1, current count must be 1.
            if is_own_side and new_board[ptr] == 1:
                # Calculate opposite pit index: 0->12, 1->11 ... i -> 12-i
                opposite_idx = 12 - ptr
                if new_board[opposite_idx] > 0:
                    capture_amount = new_board[ptr] + new_board[opposite_idx]
                    new_board[ptr] = 0
                    new_board[opposite_idx] = 0
                    new_board[my_store] += capture_amount
                    
        return new_board, extra_turn

    def evaluate(board):
        """Heuristic evaluation of the board state from perspective of player 0."""
        # Weighted score: Banked seeds are worth more than seeds on board.
        # Score = 2 * (MyStore - OppStore) + (MySeedsOnBoard - OppSeedsOnBoard)
        s1 = sum(board[0:6])
        s2 = sum(board[7:13])
        
        score_diff = board[MY_STORE_IDX] - board[OPP_STORE_IDX]
        material_diff = s1 - s2
        
        return 2 * score_diff + material_diff

    def final_score(board):
        """Calculates exact score difference when game ends."""
        # Game end rule: Other player captures their remaining seeds.
        s1 = sum(board[0:6])
        s2 = sum(board[7:13])
        
        # Effectively, everyone keeps their side + store
        my_total = board[MY_STORE_IDX] + s1
        opp_total = board[OPP_STORE_IDX] + s2
        
        return my_total - opp_total

    # --- Search Context ---
    nodes_visited = 0
    timeout_flag = False

    def minimax(board, depth, alpha, beta, maximizing):
        nonlocal nodes_visited, timeout_flag
        nodes_visited += 1
        
        # Periodic time check
        if nodes_visited & 255 == 0:
            if time.time() - start_time > TIME_LIMIT:
                timeout_flag = True
                return 0

        # Check for game over (one side empty)
        s1 = sum(board[0:6])
        s2 = sum(board[7:13])
        if s1 == 0 or s2 == 0:
            # End of game score
            return final_score(board) * (1000) # Scale up terminal states to prefer winning

        if depth == 0:
            return evaluate(board)

        player = 0 if maximizing else 1
        moves = get_legal_moves(board, player)
        
        # Move Ordering: Prioritize moves that grant extra turns or likely captures
        # Simple heuristic: if seeds == distance to store, it's an extra turn.
        move_priorities = []
        target_store = MY_STORE_IDX if player == 0 else OPP_STORE_IDX
        
        for m in moves:
            seeds = board[m]
            dist = (target_store - m) % 14
            # Extra turn if seeds % 13 == dist (handling wraps) and seeds >= dist
            # Actually simple check: last seed lands in store.
            # dist is seeds needed to reach store exactly.
            is_extra = (seeds % 13 == dist) 
            # Note: seeds % 13 == 0 means 13, 26... but dist to store is never 0 (min 1).
            
            # Sort Key: (Is Extra Turn, Number of Seeds)
            move_priorities.append((1 if is_extra else 0, seeds, m))
        
        # Sort descending
        move_priorities.sort(key=lambda x: (x[0], x[1]), reverse=True)
        sorted_indices = [x[2] for x in move_priorities]

        if maximizing:
            value = -float('inf')
            for m in sorted_indices:
                next_bd, extra = do_move(board, m, 0)
                
                # If extra turn, continue search at SAME depth (or extend),
                # but to ensure we don't loop forever or blow up time, treat carefully.
                # Standard practice: same depth.
                if extra:
                    val = minimax(next_bd, depth, alpha, beta, True)
                else:
                    val = minimax(next_bd, depth - 1, alpha, beta, False)
                
                if timeout_flag: return 0
                
                value = max(value, val)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for m in sorted_indices:
                next_bd, extra = do_move(board, m, 1)
                
                if extra:
                    val = minimax(next_bd, depth, alpha, beta, False)
                else:
                    val = minimax(next_bd, depth - 1, alpha, beta, True)
                
                if timeout_flag: return 0
                
                value = min(value, val)
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    # --- Main Iterative Deepening Loop ---
    
    valid_moves = get_legal_moves(initial_board, 0)
    
    # Fallback if no moves (should be handled by game runner, but strictly needed)
    if not valid_moves:
        return 0 
        
    best_move = valid_moves[0]
    
    # Initial sort for root moves
    root_moves_data = []
    for m in valid_moves:
        seeds = initial_board[m]
        dist = (MY_STORE_IDX - m)
        is_extra = (seeds % 13 == dist)
        root_moves_data.append((is_extra, seeds, m))
    root_moves_data.sort(key=lambda x: (x[0], x[1]), reverse=True)
    root_search_order = [x[2] for x in root_moves_data]

    # Iterative Deepening
    for d in range(1, MAX_DEPTH + 1):
        alpha = -float('inf')
        beta = float('inf')
        current_best_val = -float('inf')
        current_best_move = best_move # Keep previous best as fallback
        
        # Explicit expansion of root to track best move
        fail = False
        for m in root_search_order:
            next_bd, extra = do_move(initial_board, m, 0)
            
            if extra:
                val = minimax(next_bd, d, alpha, beta, True)
            else:
                val = minimax(next_bd, d - 1, alpha, beta, False)
            
            if timeout_flag:
                fail = True
                break
            
            if val > current_best_val:
                current_best_val = val
                current_best_move = m
            
            alpha = max(alpha, current_best_val)
            # Beta cut-off not applicable at root max node (it is the root)
            
        if fail:
            break
            
        best_move = current_best_move
        
        # If we found a winning mate score, we can stop early?
        # In Kalah, scores vary, difficult to detect 'mate' without exact bounds.
        # Just use time.

    return best_move
