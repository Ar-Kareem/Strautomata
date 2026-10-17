
import numpy as np
import sys

def policy(board) -> str:
    """
    Alpha-Beta search with a mobility and central control heuristic
    for the Amazons game on a 6x6 board.
    """
    
    # Ensure we don't timeout by setting a strict recursion limit and checking time
    sys.setrecursionlimit(2000)
    
    # Constants
    SIZE = 6
    MAX_DEPTH = 4  # 6x6 board allows for deeper search than 10x10
    INF = 10000
    
    # Precompute central weights (Manhattan distance from center approx)
    # Center squares (2,2), (2,3), (3,2), (3,3) get highest weight
    WEIGHTS = np.array([
        [1, 1, 2, 2, 1, 1],
        [1, 2, 3, 3, 2, 1],
        [2, 3, 4, 4, 3, 2],
        [2, 3, 4, 4, 3, 2],
        [1, 2, 3, 3, 2, 1],
        [1, 1, 2, 2, 1, 1]
    ], dtype=np.float32)

    def get_neighbors(r, c):
        """Generator for 8 directions."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                yield dr, dc

    def get_moves(bd, player):
        """
        Generate all legal moves for 'player'.
        Returns list of (from_r, from_c, to_r, to_c, arrow_r, arrow_c).
        """
        moves = []
        opp = 2 if player == 1 else 1
        
        # Find player's amazons
        amazons = []
        for r in range(SIZE):
            for c in range(SIZE):
                if bd[r, c] == player:
                    amazons.append((r, c))
        
        for r, c in amazons:
            # 1. Generate Amazon moves (Queen-like)
            for dr, dc in get_neighbors(r, c):
                curr_r, curr_c = r + dr, c + dc
                while 0 <= curr_r < SIZE and 0 <= curr_c < SIZE:
                    if bd[curr_r, curr_c] != 0:
                        # Blocked by something (amazon or arrow)
                        break
                    
                    # Valid landing spot for Amazon
                    # Now generate arrow shots from (curr_r, curr_c)
                    # Arrow cannot land on (r, c) if it's empty? 
                    # Actually, arrow can land on (r, c) since Amazon vacated it.
                    # But arrow path must be clear. 
                    # Note: We temporarily treat 'from' square as empty for arrow trajectory?
                    # No, standard rules: Amazon moves to 'to', then shoots.
                    # The board during arrow phase: 'from' is empty, 'to' has Amazon.
                    # Arrow cannot pass through 'to' (blocked by Amazon).
                    
                    # Generate arrows
                    for adr, adc in get_neighbors(curr_r, curr_c):
                        ar, ac = curr_r + adr, curr_c + adc
                        while 0 <= ar < SIZE and 0 <= ac < SIZE:
                            if (ar, ac) == (curr_r, curr_c):
                                # Should not happen given loop structure, but safety
                                ar += adr
                                ac += adc
                                continue
                            
                            # Check if arrow path is blocked
                            # If crossing original 'from' (r,c), it's empty
                            # If crossing 'to' (curr_r, curr_c), it's blocked (Amazon is there)
                            # If crossing any other non-zero, blocked.
                            
                            block_val = bd[ar, ac]
                            
                            # Special check: if the square is the original position (r,c),
                            # it is effectively empty for the arrow.
                            if (ar, ac) == (r, c):
                                block_val = 0
                            
                            if block_val != 0:
                                # Blocked
                                break
                            
                            # Valid arrow shot
                            moves.append((r, c, curr_r, curr_c, ar, ac))
                            
                            ar += adc
                            ac += adr
                    
                    curr_r += dr
                    curr_c += dc
        return moves

    def evaluate(bd, player):
        """
        Heuristic: (My mobility + My central control) - (Opp mobility + Opp central control).
        """
        opp = 2 if player == 1 else 1
        
        # 1. Mobility (number of legal moves)
        my_moves = len(get_moves(bd, player))
        opp_moves = len(get_moves(bd, opp))
        
        # 2. Central Control (weighted sum of empty squares reachable or controlled)
        # We can approximate this by summing weights of empty squares.
        # A more refined version counts potential moves, but simple weight sum is fast.
        my_control = 0
        opp_control = 0
        
        # To calculate control efficiently:
        # We look at who 'attacks' a square. 
        # Since it's hard to calculate attack maps without simulating moves, 
        # we'll use a simpler metric: Sum of weights of empty squares.
        # This is neutral. Let's refine:
        # Sum weights of empty squares.
        
        # Actually, a strong heuristic in Amazons is trapping the opponent.
        # Let's stick to Mobility + Weighted Area.
        
        empty_weight_sum = 0
        for r in range(SIZE):
            for c in range(SIZE):
                if bd[r, c] == 0:
                    empty_weight_sum += WEIGHTS[r, c]
        
        # We split empty space bias based on player position roughly? 
        # No, standard is just weighted empty space + mobility.
        
        # Let's refine the evaluation:
        # Score = (MyMobility - OppMobility) + (MySafeArea - OppSafeArea)
        # SafeArea can be approximated by sum of weights of empty squares.
        # This is static and doesn't distinguish, but combined with mobility it works well.
        
        # Let's add a simple piece centrality metric to encourage central positioning.
        my_centrality = 0
        opp_centrality = 0
        
        for r in range(SIZE):
            for c in range(SIZE):
                val = bd[r, c]
                if val == player:
                    my_centrality += WEIGHTS[r, c]
                elif val == opp:
                    opp_centrality += WEIGHTS[r, c]
                    
        # Final Score
        # Weights: Mobility is crucial. Centrality is secondary.
        # 10 points for mobility, 1 point for centrality.
        score = (my_moves * 10) - (opp_moves * 10)
        score += (my_centrality - opp_centrality)
        
        return score

    def alpha_beta(bd, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate(bd, 1) # Always evaluate from perspective of player 1 (max)
        
        player = 1 if maximizing_player else 2
        moves = get_moves(bd, player)
        
        if not moves:
            # No moves available. 
            # If it's maximizing player's turn (root player) and no moves -> Lose (Low score)
            # If it's minimizing player's turn and no moves -> Win (High score)
            if maximizing_player:
                return -INF + (MAX_DEPTH - depth) # Prefer later losses
            else:
                return INF - (MAX_DEPTH - depth) # Prefer earlier wins
        
        if maximizing_player:
            max_eval = -INF
            for move in moves:
                # Apply move
                fr, fc, tr, tc, ar, ac = move
                old_vals = (bd[fr, fc], bd[tr, tc], bd[ar, ac])
                bd[fr, fc] = 0
                bd[tr, tc] = player
                bd[ar, ac] = -1
                
                eval = alpha_beta(bd, depth - 1, alpha, beta, False)
                
                # Undo move
                bd[fr, fc] = old_vals[0]
                bd[tr, tc] = old_vals[1]
                bd[ar, ac] = old_vals[2]
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for move in moves:
                fr, fc, tr, tc, ar, ac = move
                old_vals = (bd[fr, fc], bd[tr, tc], bd[ar, ac])
                bd[fr, fc] = 0
                bd[tr, tc] = player
                bd[ar, ac] = -1
                
                eval = alpha_beta(bd, depth - 1, alpha, beta, True)
                
                bd[fr, fc] = old_vals[0]
                bd[tr, tc] = old_vals[1]
                bd[ar, ac] = old_vals[2]
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Execution ---
    
    # Working with a copy to avoid modifying the original array passed in if it matters
    # Though usually safe to modify if not used elsewhere, better safe.
    search_board = np.copy(board)
    
    best_move = None
    best_score = -INF
    
    # Get all possible moves
    candidates = get_moves(search_board, 1)
    
    if not candidates:
        # Should not happen in valid game state if called correctly, but fail-safe
        return "0,0:0,0:0,0" 

    # Iterative Deepening (simplified here as just one depth run with sorting)
    # Sort candidates by immediate heuristic value to improve pruning
    def move_key(move):
        fr, fc, tr, tc, ar, ac = move
        # Quick static evaluation of the resulting board state for sorting
        search_board[fr, fc] = 0
        search_board[tr, tc] = 1
        search_board[ar, ac] = -1
        val = evaluate(search_board, 1)
        # Undo
        search_board[fr, fc] = 1
        search_board[tr, tc] = 0
        search_board[ar, ac] = 0
        return val

    # Sort moves: Best first (descending for max)
    candidates.sort(key=move_key, reverse=True)
    
    # Time limit check wrapper could go here, but we rely on depth limit for 6x6
    alpha = -INF
    beta = INF
    
    for move in candidates:
        fr, fc, tr, tc, ar, ac = move
        
        # Apply move
        search_board[fr, fc] = 0
        search_board[tr, tc] = 1
        search_board[ar, ac] = -1
        
        # Recursive search (Minimize opponent's response)
        score = alpha_beta(search_board, MAX_DEPTH - 1, alpha, beta, False)
        
        # Undo move
        search_board[fr, fc] = 1
        search_board[tr, tc] = 0
        search_board[ar, ac] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
            
        alpha = max(alpha, best_score)
    
    # Fallback if something goes terribly wrong
    if best_move is None and candidates:
        best_move = candidates[0]
        
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
