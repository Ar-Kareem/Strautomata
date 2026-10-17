
def policy(you: list[int], opponent: list[int]) -> str:
    """
    Determines the optimal move in Clobber 5x6.
    Uses endgame analysis (1v1) and mobility reduction heuristics.
    """
    # Convert to a more usable format if necessary, but list access works fine.
    # Helper to check bounds and content
    def is_opponent(r, c):
        return 0 <= r < 5 and 0 <= c < 6 and opponent[r][c] == 1

    def is_you(r, c):
        return 0 <= r < 5 and 0 <= c < 6 and you[r][c] == 1

    def count_pieces(board):
        return sum(sum(row) for row in board)

    # 1. Count pieces to understand the game phase
    my_count = count_pieces(you)
    opp_count = count_pieces(opponent)

    moves = []

    # Collect all legal moves and analyze them
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                # Check neighbors
                for dr, dc, d in [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]:
                    nr, nc = r + dr, c + dc
                    if is_opponent(nr, nc):
                        move_str = f"{r},{c},{d}"
                        moves.append((r, c, d, move_str))
                        
                        # --- Immediate Win Check ---
                        # If this move captures the last opponent piece (or leaves them with pieces but no moves)
                        # We can simulate.
                        
                        # If opp_count == 1, we definitely win by capturing it.
                        if opp_count == 1:
                            return move_str
                        
                        # Deeper check: Does this move leave opponent with NO moves?
                        # Optimization: Only check this if opp_count is small (e.g., <= 3) to save time.
                        if opp_count <= 3:
                            # Create hypothetical board states
                            new_you = [row[:] for row in you]
                            new_opp = [row[:] for row in opponent]
                            
                            # Apply move: Remove my piece, capture opponent, place my piece
                            new_you[r][c] = 0
                            new_opp[nr][nc] = 0
                            new_opp[r][c] = 0 # Just in case overlap logic (not possible in standard rules but safe)
                            new_you[nr][nc] = 1
                            
                            # Check if opponent has any moves
                            has_move = False
                            for rr in range(5):
                                for cc in range(6):
                                    if new_opp[rr][cc] == 1:
                                        if (rr > 0 and new_you[rr-1][cc] == 1) or \
                                           (rr < 4 and new_you[rr+1][cc] == 1) or \
                                           (cc > 0 and new_you[rr][cc-1] == 1) or \
                                           (cc < 5 and new_you[rr][cc+1] == 1):
                                            has_move = True
                                            break
                                if has_move: break
                            
                            if not has_move:
                                return move_str

    # --- Endgame Logic: 1 vs 1 ---
    if my_count == 1 and opp_count == 1:
        # Find positions
        my_pos = next(((r, c) for r in range(5) for c in range(6) if you[r][c] == 1), None)
        opp_pos = next(((r, c) for r in range(5) for c in range(6) if opponent[r][c] == 1), None)
        
        if my_pos and opp_pos:
            dist = abs(my_pos[0] - opp_pos[0]) + abs(my_pos[1] - opp_pos[1])
            
            # If adjacent, we simply capture (distance 1).
            if dist == 1:
                # Find the move that connects to the opponent
                for r, c, d, s in moves:
                    if (r + (-1 if d == 'U' else 1 if d == 'D' else 0), c + (1 if d == 'R' else -1 if d == 'L' else 0)) == opp_pos:
                        return s
            
            # If distance > 1:
            # If distance is ODD, we are in winning position. We must move to make distance EVEN (and minimize it).
            # If distance is EVEN, we are in losing position, but we try to prolong/move closer to "trap" opponent or force error.
            # In strict combinatorial game theory, if dist is even and no immediate trap, we lose. But we must move.
            # We prioritize moving closer (reducing Manhattan distance).
            
            best_move = None
            best_dist = 999
            
            for r, c, d, s in moves:
                # Calculate new distance if we move this way
                nr, nc = r + (-1 if d == 'U' else 1 if d == 'D' else 0), c + (1 if d == 'R' else -1 if d == 'L' else 0)
                # We move to nr, nc. Opponent is at opp_pos.
                new_dist = abs(nr - opp_pos[0]) + abs(nc - opp_pos[1])
                
                # In 1v1, we want to minimize distance (to potentially trap) unless we are forced to increase?
                # Usually reducing distance is safer in Clobber 1v1 to force the opponent into a corner.
                if new_dist < best_dist:
                    best_dist = new_dist
                    best_move = s
            
            if best_move:
                return best_move

    # --- General Heuristic (N vs N) ---
    # If we didn't find a forced win or special 1v1 case, we play a heuristic.
    # Heuristic: Prefer capturing pieces that have low mobility (degree <= 1) to "prune" the opponent.
    # If no such move, prefer moving pieces that are "pinned" or have few moves themselves?
    # Actually, standard Clobber theory suggests minimizing opponent options.
    
    candidate_moves = []
    for r, c, d, s in moves:
        # Identify the target opponent piece
        nr, nc = r + (-1 if d == 'U' else 1 if d == 'D' else 0), c + (1 if d == 'R' else -1 if d == 'L' else 0)
        
        # Calculate opponent's degree of freedom (mobility) for this piece
        opp_mobility = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            tr, tc = nr + dr, nc + dc
            if is_you(tr, tc):
                opp_mobility += 1
        
        # Lower mobility means more valuable to capture
        # Tie-breaker: Maybe prefer moves that don't expose our piece too much?
        # Let's add a simple safety check: does the move put us in danger of immediate capture?
        # We can't easily check "future" safety, but we can check if the source piece was threatened?
        
        candidate_moves.append((opp_mobility, s))
    
    if candidate_moves:
        # Sort by opp_mobility (ascending) to target weak pieces
        candidate_moves.sort(key=lambda x: x[0])
        
        # If there are multiple moves with same mobility score, pick one.
        # To avoid being too predictable, we can pick randomly or alternate, 
        # but determinism is usually preferred in coding arenas unless specific constraints.
        # Let's pick the first one sorted.
        return candidate_moves[0][1]

    # Fallback: If for some reason moves list was populated but logic failed, return first
    if moves:
        return moves[0][3]

    # If no moves found (should not happen as per constraints unless we lose, but we must return something or crash)
    # The prompt says "You must always return a legal move string". 
    # If we have no legal moves, we have lost, but we can't return a move. 
    # We return a dummy invalid move to signal loss, but the arena likely handles this.
    # However, we try to avoid this block.
    return "0,0,U" # Fallback invalid
