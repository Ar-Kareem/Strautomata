
import numpy as np

def policy(board) -> str:
    """
    Amazons Policy using Minimax Search (Depth 3) with Alpha-Beta Pruning.
    Heuristic: Mobility (My Moves - Opponent Moves).
    """
    
    # Constants
    EMPTY = 0
    ME = 1
    OPP = 2
    SIZE = 6
    DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    # --- Move Generation ---
    def get_moves(bd, player):
        """Generates list of moves: ((from_r, from_c), (to_r, to_c), (arrow_r, arrow_c))"""
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if bd[r][c] == player:
                    for dr, dc in DIRS:
                        # Amazon move
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < SIZE and 0 <= nc < SIZE and bd[nr][nc] == 0:
                            # Arrow move from (nr, nc)
                            for adr, adc in DIRS:
                                ar, ac = nr + adr, nc + adc
                                while 0 <= ar < SIZE and 0 <= ac < SIZE:
                                    cell = bd[ar][ac]
                                    # 'from' (r,c) is now empty for the arrow path
                                    is_original = (ar == r and ac == c)
                                    
                                    if cell != 0 and not is_original:
                                        break
                                    
                                    # Cannot shoot arrow at own current position
                                    if not (ar == nr and ac == nc):
                                        moves.append(((r, c), (nr, nc), (ar, ac)))
                                    
                                    ar += adr
                                    ac += adc
                            nr += dr
                            nc += dc
        return moves

    def count_moves(bd, player):
        """Fast move counter (avoids list creation)"""
        count = 0
        for r in range(SIZE):
            for c in range(SIZE):
                if bd[r][c] == player:
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < SIZE and 0 <= nc < SIZE and bd[nr][nc] == 0:
                            for adr, adc in DIRS:
                                ar, ac = nr + adr, nc + adc
                                while 0 <= ar < SIZE and 0 <= ac < SIZE:
                                    cell = bd[ar][ac]
                                    is_original = (ar == r and ac == c)
                                    if cell != 0 and not is_original:
                                        break
                                    if not (ar == nr and ac == nc):
                                        count += 1
                                    ar += adr
                                    ac += adc
                            nr += dr
                            nc += dc
        return count

    # --- Evaluation ---
    def evaluate(bd):
        """Heuristic: My Mobility - Opponent Mobility. High score = good for ME."""
        my_mobility = count_moves(bd, ME)
        if my_mobility == 0:
            return -100000  # I lose
        
        opp_mobility = count_moves(bd, OPP)
        if opp_mobility == 0:
            return 100000   # I win
            
        return my_mobility - opp_mobility

    # --- Alpha-Beta Search ---
    def alphabeta(bd, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(bd)
            
        player = ME if maximizing else OPP
        moves = get_moves(bd, player)
        
        if not moves:
            # If current player cannot move, the other player wins
            return -100000 if maximizing else 100000
            
        if maximizing:
            max_eval = -float('inf')
            for (fr, fc), (tr, tc), (ar, ac) in moves:
                # Apply Move
                original_val = bd[fr][fc]
                bd[fr][fc] = EMPTY
                bd[tr][tc] = player
                bd[ar][ac] = -1
                
                eval_val = alphabeta(bd, depth - 1, alpha, beta, False)
                
                # Undo Move
                bd[ar][ac] = EMPTY
                bd[tr][tc] = EMPTY
                bd[fr][fc] = original_val
                
                if eval_val > max_eval:
                    max_eval = eval_val
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (fr, fc), (tr, tc), (ar, ac) in moves:
                # Apply Move
                original_val = bd[fr][fc]
                bd[fr][fc] = EMPTY
                bd[tr][tc] = player
                bd[ar][ac] = -1
                
                eval_val = alphabeta(bd, depth - 1, alpha, beta, True)
                
                # Undo Move
                bd[ar][ac] = EMPTY
                bd[tr][tc] = EMPTY
                bd[fr][fc] = original_val
                
                if eval_val < min_eval:
                    min_eval = eval_val
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Root Selection ---
    my_moves = get_moves(board, ME)
    
    if not my_moves:
        return ""  # Should not happen if called correctly
    
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Look ahead: My Move -> Opp Move -> My Move (Depth 3 total)
    # We are at Depth 3. We iterate my moves. 
    # For each, we call alphabeta with Depth 2 (Opponent turn).
    for (fr, fc), (tr, tc), (ar, ac) in my_moves:
        # Apply
        original_val = board[fr][fc]
        board[fr][fc] = EMPTY
        board[tr][tc] = ME
        board[ar][ac] = -1
        
        # Search (Depth 2 remaining)
        score = alphabeta(board, 2, alpha, beta, False)
        
        # Undo
        board[ar][ac] = EMPTY
        board[tr][tc] = EMPTY
        board[fr][fc] = original_val
        
        if score > best_score:
            best_score = score
            best_move = (fr, fc, tr, tc, ar, ac)
        
        alpha = max(alpha, score)
        if beta <= alpha:
            break
            
    if best_move:
        r1, c1, r2, c2, r3, c3 = best_move
        return f"{r1},{c1}:{r2},{c2}:{r3},{c3}"
        
    return ""
