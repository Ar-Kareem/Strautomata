
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello Policy implementing a weighted board heuristic with shallow lookahead.
    """
    
    # 8x8 Weighted Board Map
    # Corners are high value (100), adjacent squares are negative (-50) to avoid traps.
    # Edges are positive (20), center is moderate (5).
    weights = np.array([
        [100, -50, 20, 10, 10, 20, -50, 100],
        [-50, -50,  5,  5,  5,  5, -50, -50],
        [ 20,   5, 15,  5,  5, 15,   5,  20],
        [ 10,   5,  5,  5,  5,  5,   5,  10],
        [ 10,   5,  5,  5,  5,  5,   5,  10],
        [ 20,   5, 15,  5,  5, 15,   5,  20],
        [-50, -50,  5,  5,  5,  5, -50, -50],
        [100, -50, 20, 10, 10, 20, -50, 100]
    ], dtype=np.float32)

    # Directions for checking flips (8 neighbors)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    def is_valid(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_flips(board, opponent_board, r, c):
        """Returns a list of (r, c) that would be flipped by placing a disc at (r, c)."""
        if board[r, c] != 0 or opponent_board[r, c] != 0:
            return []
        
        flips = []
        for dr, dc in directions:
            temp_flips = []
            cr, cc = r + dr, c + dc
            while is_valid(cr, cc) and opponent_board[cr, cc] == 1:
                temp_flips.append((cr, cc))
                cr += dr
                cc += dc
            if is_valid(cr, cc) and board[cr, cc] == 1 and temp_flips:
                flips.extend(temp_flips)
        return flips

    def get_legal_moves(board, opponent_board):
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r, c] == 0 and opponent_board[r, c] == 0:
                    flips = get_flips(board, opponent_board, r, c)
                    if flips:
                        moves.append(((r, c), flips))
        return moves

    def evaluate_board(my_board, opp_board):
        """Heuristic evaluation function."""
        score = np.sum(my_board * weights) - np.sum(opp_board * weights)
        
        # Mobility Bonus: Count legal moves for self and opponent
        # High mobility is good, low opponent mobility is good.
        my_mobility = len(get_legal_moves(my_board, opp_board))
        # Swap boards to get opponent mobility relative to current state
        opp_mobility = len(get_legal_moves(opp_board, my_board))
        
        mobility_score = (my_mobility - opp_mobility) * 2.0
        return score + mobility_score

    # 1. Get all legal moves for the current player
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"

    # 2. Evaluate moves
    best_score = -float('inf')
    best_move = legal_moves[0][0]  # Default to first move

    # Pre-calculate total discs for potential tie-breaking or endgame logic
    total_discs = np.sum(you) + np.sum(opponent)
    
    # If we are in late game, switch to strict disc counting
    use_disc_count = total_discs > 50

    for (r, c), flips in legal_moves:
        # Immediate move simulation
        temp_you = you.copy()
        temp_opp = opponent.copy()
        
        temp_you[r, c] = 1
        temp_opp[r, c] = 0 # Ensure empty
        for fr, fc in flips:
            temp_you[fr, fc] = 1
            temp_opp[fr, fc] = 0
            
        # Calculate Score
        if use_disc_count:
            # Late game: maximize disc difference
            current_score = np.sum(temp_you) - np.sum(temp_opp)
        else:
            # Early/Mid game: Heuristic + Lookahead
            current_score = evaluate_board(temp_you, temp_opp)
            
            # Shallow Lookahead (Minimax depth 1 for opponent response)
            # Check if the opponent has a devastating reply (e.g., takes a corner)
            # or maximizes their score.
            opponent_moves = get_legal_moves(temp_opp, temp_you)
            if opponent_moves:
                # Find the best opponent response score
                best_opp_score = -float('inf')
                for (or_, oc_), oflips in opponent_moves:
                    sim_opp = temp_opp.copy()
                    sim_you = temp_you.copy()
                    sim_opp[or_, oc_] = 1
                    sim_you[or_, oc_] = 0
                    for ofr, ofc in oflips:
                        sim_opp[ofr, ofc] = 1
                        sim_you[ofr, ofc] = 0
                    
                    # Evaluate opponent state
                    opp_response_val = evaluate_board(sim_opp, sim_you)
                    if opp_response_val > best_opp_score:
                        best_opp_score = opp_response_val
                
                # Penalize current move if opponent gets a very good response
                # We want to maximize (MyScore - OpponentPotentialScore)
                current_score -= best_opp_score * 0.8
            else:
                # If opponent has no moves, this is a very good move (skips their turn)
                current_score += 50.0
        
        # Tie-breaking: Prefer center/edges if scores are close, or simply move order
        # We add a tiny weight to prefer moves closer to the center to stabilize sorting
        center_dist = (3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5))
        current_score += center_dist * 0.01

        if current_score > best_score:
            best_score = current_score
            best_move = (r, c)

    # Convert to algebraic notation
    r, c = best_move
    col = chr(ord('a') + c)
    row = str(r + 1)
    return col + row
