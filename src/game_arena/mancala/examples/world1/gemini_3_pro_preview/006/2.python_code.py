
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy using Iterative Deepening Minimax with Alpha-Beta pruning.
    
    State Representation:
    A list of 14 integers:
    Indices 0-5: Current player's houses.
    Index 6: Current player's store.
    Indices 7-12: Opponent's houses.
    Index 13: Opponent's store.
    """
    
    # Timing constraints
    start_time = time.time()
    TIME_LIMIT = 0.95  # Seconds, leaving a small buffer
    
    # Initial board setup from input
    board = you + opponent
    
    # Exception to break out of recursion on timeout
    class SearchTimeout(Exception):
        pass

    def do_move(b: list[int], move_idx: int):
        """
        Simulates a move on the board.
        Returns: (new_board, extra_turn, game_over)
        """
        # Create a copy of the board
        nb = b[:]
        
        seeds = nb[move_idx]
        nb[move_idx] = 0
        
        pos = move_idx
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == 13: # Skip opponent's store
                continue
            nb[pos] += 1
            seeds -= 1
            
        # Check special rules based on where the last seed landed (pos)
        extra_turn = (pos == 6)
        
        # Capture Rule:
        # 1. Landed in own house (0-5)
        # 2. That house now has exactly 1 seed (meaning it was empty before this drop)
        # 3. The opposite house (12 - pos) has seeds
        if 0 <= pos <= 5 and nb[pos] == 1:
            opp_idx = 12 - pos
            if nb[opp_idx] > 0:
                captured_amount = nb[pos] + nb[opp_idx]
                nb[pos] = 0
                nb[opp_idx] = 0
                nb[6] += captured_amount
        
        # Game Over Check
        # The game ends if either side (0-5 or 7-12) is entirely empty.
        side1_empty = all(x == 0 for x in nb[0:6])
        side2_empty = all(x == 0 for x in nb[7:13])
        
        if side1_empty or side2_empty:
            # Move all remaining seeds to respective stores
            s1 = sum(nb[0:6])
            s2 = sum(nb[7:13])
            nb[6] += s1
            nb[13] += s2
            # Clear houses
            for i in range(6): nb[i] = 0
            for i in range(7, 13): nb[i] = 0
            return nb, extra_turn, True
            
        return nb, extra_turn, False

    def flip_board(b: list[int]) -> list[int]:
        """
        Rotates the board 180 degrees so the opponent becomes the current player.
        Old 7-12 become 0-5, Old 13 becomes 6, etc.
        """
        return b[7:14] + b[0:7]

    def heuristic(b: list[int]) -> int:
        """
        Evaluates the board state for the current player.
        Primary metric: Store difference.
        """
        return b[6] - b[13]

    # Global node counter for periodic time checks
    nodes_visited = 0

    def negamax(b: list[int], depth: int, alpha: float, beta: float) -> float:
        nonlocal nodes_visited
        nodes_visited += 1
        
        # periodic time check (every 1024 nodes)
        if nodes_visited & 1023 == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise SearchTimeout()

        moves = [i for i in range(6) if b[i] > 0]
        
        # If no moves are possible, it implies game over logic should have triggered.
        # However, checking 'over' inside the loop handles standard game end.
        # If moves list is empty here, we treat it as terminal.
        if not moves:
            return heuristic(b) * 10000

        # Base case
        if depth == 0:
            return heuristic(b)

        # Move Ordering: Simple heuristic to try better moves first
        # Reverse order (5 to 0) is often a good heuristic for Kalah
        moves.sort(reverse=True)

        best_score = -float('inf')

        for m in moves:
            nb, extra, over = do_move(b, m)
            
            if over:
                # Terminal node: heavily weight winning board states
                score = (nb[6] - nb[13]) * 10000 
            else:
                if extra:
                    # Same player moves again; depth is typically not reduced 
                    # significantly for extra turns to analyze the full sequence,
                    # but we rely on iterative deepening to limit execution.
                    score = negamax(nb, depth, alpha, beta)
                else:
                    # Switch turn: negate the opponent's score
                    score = -negamax(flip_board(nb), depth - 1, -beta, -alpha)

            if score > best_score:
                best_score = score
            
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break # Beta Cutoff
        
        return best_score

    # Main Iterative Deepening Loop
    
    # Identify legal moves
    legal_moves = [i for i in range(6) if board[i] > 0]
    
    # We assume policy is never called with no legal moves per spec,
    # but safe fallback just in case.
    if not legal_moves:
        return 0

    # Initial sorting of legal moves by a 1-ply simulation score
    # to improve alpha-beta efficiency at the root.
    def root_sort_key(m):
        sim_b, extra, over = do_move(board, m)
        score = sim_b[6] - sim_b[13]
        if extra: score += 10 # heuristic bonus for extra turn
        if over: score += 1000 # prefer winning immediately
        return score

    legal_moves.sort(key=root_sort_key, reverse=True)
    
    best_move = legal_moves[0]
    
    try:
        max_depth = 1
        # Loop until timeout breaks execution
        while True:
            alpha = -float('inf')
            beta = float('inf')
            current_best_val = -float('inf')
            current_best_move_in_depth = best_move
            
            # Reorder: Try the best move from previous depth first (Principal Variation)
            search_order = [best_move] + [m for m in legal_moves if m != best_move]
            
            for m in search_order:
                nb, extra, over = do_move(board, m)
                
                if over:
                    val = (nb[6] - nb[13]) * 10000
                else:
                    if extra:
                        val = negamax(nb, max_depth, alpha, beta)
                    else:
                        val = -negamax(flip_board(nb), max_depth - 1, -beta, -alpha)
                
                if val > current_best_val:
                    current_best_val = val
                    current_best_move_in_depth = m
                
                alpha = max(alpha, current_best_val)
                # No beta cutoff at root
            
            best_move = current_best_move_in_depth
            max_depth += 1
            
            # Safety break for very fast shallow games to avoid huge depth overhead
            if max_depth > 30: 
                break
                
    except SearchTimeout:
        # Time limit reached, return the best move found in the last fully completed depth
        pass

    return best_move
