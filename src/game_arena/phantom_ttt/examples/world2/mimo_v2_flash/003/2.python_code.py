
def policy(board: list[list[int]]) -> int:
    import random
    
    # --- Configuration ---
    MAX_SIMS = 150  # Number of rollouts per move to stay within 1s
    WIN_SCORE = 1.0
    LOSE_SCORE = -1.0
    
    # --- Helper Functions ---
    
    def get_legal_moves(b: list[list[int]]) -> list[tuple[int, int]]:
        """Returns list of (r, c) where we don't have a confirmed mark."""
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] != 1:
                    moves.append((r, c))
        return moves

    def check_winner(b: list[list[int]]) -> int:
        """Checks for a win. Returns 1 (us), -1 (opp), or 0 (none/undetermined)."""
        lines = [
            [(0, 0), (0, 1), (0, 2)], [(1, 0), (1, 1), (1, 2)], [(2, 0), (2, 1), (2, 2)], # Rows
            [(0, 0), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 2), (1, 2), (2, 2)], # Cols
            [(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]  # Diagonals
        ]
        
        # Check if WE won
        for line in lines:
            if all(b[r][c] == 1 for r, c in line):
                return 1
        
        # In Phantom Tic Tac Toe, we only confirm opponent marks by attempting to move there and failing.
        # Since we don't have that history in this function call, we cannot definitively check
        # if the opponent has 3 in a row based solely on the board state (which hides their marks).
        # However, in our MCTS rollouts (simulated boards), we will simulate their marks.
        return 0

    def is_full(b: list[list[int]]) -> bool:
        return all(cell == 1 for row in b for cell in row)

    # --- Main Logic ---

    moves = get_legal_moves(board)
    if not moves:
        return (0, 0) # Fallback, shouldn't happen in valid game
    
    # 1. Immediate Win / Block Detection (Deterministic)
    # We can only definitively block if we see their setup, but we can try to win if we have 2.
    # We will implement a quick check assuming '0's *might* be empty.
    
    # We create a "probabilistic" view of the board for reasoning
    # Count confirmed 1s to estimate opponent moves
    my_marks = sum(row.count(1) for row in board)
    # Total moves = my_marks + opp_moves. Assuming roughly equal turns.
    # If we have N marks, opponent has at least N-1 or N moves.
    
    # High priority: Can we win immediately?
    # We try to imagine the board with '0's as empty.
    # If we fill a line of '0's with '1's, we win.
    for r, c in moves:
        # Hypothetical board
        temp_b = [row[:] for row in board]
        temp_b[r][c] = 1
        
        # Check if this completes a line for us
        if check_winner(temp_b) == 1:
            return (r, c)

    # 2. MCTS with Probabilistic Assumptions
    # We need to track stats for each move
    move_stats = {m: {'wins': 0, 'sims': 0} for m in moves}

    # Estimate Opponent Occupancy Probability
    # This is the core of Phantom Tic Tac Toe strategy.
    # If we have 2 marks, opponent likely has 2. If we have 3, they have 2 or 3.
    # We assume random placement for the opponent in unknown slots.
    # Let's estimate opponent count: usually equal or one less.
    opp_est_count = my_marks 
    # If it's the start of the game, opp count is 0.
    
    # Calculate probability of a '0' being occupied
    unknown_cells = 9 - my_marks
    prob_opp = 0
    if unknown_cells > 0:
        # If opponent has roughly my_marks moves, distribute them
        prob_opp = min(1.0, opp_est_count / unknown_cells)

    for _ in range(MAX_SIMS):
        # Pick a candidate move to evaluate
        candidate = random.choice(moves)
        
        # Create simulation board
        sim_board = [row[:] for row in board]
        sim_board[candidate[0]][candidate[1]] = 1 # Our move succeeds
        
        # Simulate the game state after our move
        # We need to fill in the opponent's hidden marks probabilistically
        # And then play out the rest of the game
        
        # Phase A: Reconstruct current hidden state
        # We assume '0's are empty with probability (1 - prob_opp), and occupied by opp with prob_opp
        # Note: In reality, we can't know. But for the simulation, we treat them as empty until we "discover" them.
        # To make it smarter, we will play the rollout as if we are the '1' player against a random opponent.
        
        # Rollout function
        def rollout(b_state):
            # Copy board
            r_board = [row[:] for row in b_state]
            
            # Determine whose turn it is
            # My marks count
            r_my = sum(row.count(1) for r in r_board for r in r_row)
            # Estimated opponent marks (based on the probabilistic assumption we made earlier)
            # We can just play: I play, then random 'empty' spot becomes opponent.
            
            # We play against a random opponent that prefers center, then corners, then edges
            # But the opponent might play on a cell we think is empty. If it is, it becomes theirs.
            
            # Let's define the turn order. 
            # After our move (candidate), it's opponent's turn.
            
            # Simulation loop
            while True:
                # 1. Check win (if we just played, we checked. Now check if prev move won)
                w = check_winner(r_board)
                if w == 1: return WIN_SCORE # We won
                # Note: We can't detect opponent win deterministically in simulation 
                # unless we simulate their placements explicitly.
                
                # Check full
                if is_full(r_board): return 0 # Draw
                
                # 2. Opponent Move (Random)
                # Opponent tries to place. They avoid our 1s. 
                # If they pick a cell that is currently 0, it becomes theirs (marked as occupied).
                # Since we don't track opponent marks explicitly in the board (we use 0), 
                # we can simulate them by simply claiming an empty spot.
                # However, to simulate "loss", we assume they are smart.
                
                # Find available spots for opponent (where we don't have 1)
                avail = get_legal_moves(r_board)
                if not avail: return 0
                
                # Heuristic opponent: Win if they can, Block us if we can win, else random
                # But we don't know their exact history. We just simulate them picking an empty spot.
                
                # Let's simplify: Opponent picks a random '0' cell and claims it.
                # In the board representation, this doesn't change (it stays 0), 
                # but conceptually it's now theirs.
                # To track wins, we need a shadow board for opponent or assume '0's are the enemy.
                # Let's use a shadow board for simulation.
                
                # Actually, let's use a simpler rollout for speed:
                # We treat '0's as contested. We play to fill lines. 
                # Opponent plays random.
                
                # Wait, standard approach: 
                # We simulate the *outcome* based on optimal play.
                # Let's use a quick evaluation based on line pressure.
                pass
                break # Break complex simulation for simpler heuristic below due to complexity/risk

        # --- Reverting to Heuristic-MCTS Hybrid due to Impossibility of Perfect Simulation ---
        # Since we can't know where the opponent is, we calculate a score based on:
        # 1. How many lines does this move open up for us?
        # 2. How many lines does this move block for the opponent?
        
        # Score calculation for the candidate
        score = 0
        
        # Lines passing through (r, c)
        r, c = candidate
        
        # Rows
        row_vals = sim_board[r]
        # If we have 1 and 0s, we have potential. If we have 2 1s, we win (checked earlier).
        if row_vals.count(1) == 1: 
            score += 1 # Opens a line
        
        # Cols
        col_vals = [sim_board[i][c] for i in range(3)]
        if col_vals.count(1) == 1:
            score += 1
            
        # Diagonals
        if r == c:
            diag = [sim_board[i][i] for i in range(3)]
            if diag.count(1) == 1: score += 1.5 # Diagonals are often stronger
        if r == 2 - c:
            diag = [sim_board[i][2-i] for i in range(3)]
            if diag.count(1) == 1: score += 1.5
            
        # Block potential: Are we stepping on a line where opponent has 2?
        # We can't know this. But we can check if we are stepping on a line where we have 0s.
        # If we step there, we block the opponent from ever having a full line there (if we assume they need 3).
        # Actually, in phantom, if we step on a cell, it becomes ours. So opponent can't use it.
        # So every move inherently blocks opponent lines.
        
        # Add some randomness to break ties
        score += random.random() * 0.1
        
        move_stats[candidate]['wins'] += score

    # Select best move
    best_move = None
    best_ratio = -float('inf')
    
    # Prioritize moves that won in simulation
    for m, stats in move_stats.items():
        ratio = stats['wins'] / max(stats['sims'], 1) # Not sims in this heuristic loop, just accumulation
        
        # We are actually comparing accumulated scores here because we used heuristics
        # Let's compare the accumulated 'wins' (heuristic score)
        if stats['wins'] > best_ratio:
            best_ratio = stats['wins']
            best_move = m
            
    # If we have multiple good options, or to ensure robustness, 
    # we can add a tie-breaker or fallback to standard Tic Tac Toe opening book.
    # Center -> Corners -> Edges
    
    if best_move is None:
        # Fallback to standard strategy
        # 1. Center
        if (1, 1) in moves: return (1, 1)
        # 2. Corners
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        valid_corners = [c for c in corners if c in moves]
        if valid_corners: return random.choice(valid_corners)
        # 3. Edges
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        valid_edges = [e for e in edges if e in moves]
        if valid_edges: return random.choice(valid_edges)
        
    return best_move
