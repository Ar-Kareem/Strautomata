
import time
import random

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Checkers Policy Bot
    Strategy: Iterative Deepening Minimax with Alpha-Beta Pruning.
    Features: Mandatory Capture enforcement, positional heuristic, time management.
    """
    
    START_TIME = time.time()
    TIME_LIMIT = 0.95  # Buffer to ensure return within 1s
    MAX_DEPTH = 10     # Optimistic upper bound
    
    my_color = color
    opp_color = 'b' if color == 'w' else 'w'
    
    # --- Helpers ---
    
    def get_dirs(c):
        # White moves row +1 (Up), Black moves row -1 (Down)
        return [(1, -1), (1, 1)] if c == 'w' else [(-1, -1), (-1, 1)]
    
    king_dirs = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
    
    def is_valid(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_moves(a_men, a_kings, p_men, p_kings, c_color):
        """
        Generates all legal moves for c_color.
        Enforces mandatory capture rule: if captures exist, returns only captures.
        """
        moves = []
        captures = []
        
        # Fast lookup board: 1=Friendly, -1=Enemy
        board = {}
        for p in a_men: board[p] = 1
        for p in a_kings: board[p] = 1
        for p in p_men: board[p] = -1
        for p in p_kings: board[p] = -1
        
        fwd_dirs = get_dirs(c_color)
        
        # Check Men
        for r, c in a_men:
            for dr, dc in fwd_dirs:
                tr, tc = r + dr, c + dc # Target square
                if is_valid(tr, tc):
                    val = board.get((tr, tc))
                    if val is None:
                        # Empty square, simple move
                        moves.append(((r, c), (tr, tc)))
                    elif val == -1:
                        # Enemy, check jump
                        jr, jc = tr + dr, tc + dc
                        if is_valid(jr, jc) and board.get((jr, jc)) is None:
                            captures.append(((r, c), (jr, jc)))
                            
        # Check Kings
        for r, c in a_kings:
            for dr, dc in king_dirs:
                tr, tc = r + dr, c + dc
                if is_valid(tr, tc):
                    val = board.get((tr, tc))
                    if val is None:
                        moves.append(((r, c), (tr, tc)))
                    elif val == -1:
                        jr, jc = tr + dr, tc + dc
                        if is_valid(jr, jc) and board.get((jr, jc)) is None:
                            captures.append(((r, c), (jr, jc)))
                            
        if captures:
            return captures
        return moves

    def apply_move(move, a_men, a_kings, p_men, p_kings, c_color):
        """
        Returns new board state (tuples of lists) after applying a move.
        Handles piece movement, promotion, and capture removal.
        """
        frm, to = move
        fr, fc = frm
        tr, tc = to
        
        # Remove piece from source
        # Note: We create new lists to avoid mutating input (state needs to be pure for recursion)
        n_a_men = [p for p in a_men if p != frm]
        n_a_kings = [p for p in a_kings if p != frm]
        
        is_king = (frm in a_kings)
        
        # Check Promotion
        promote = False
        if not is_king:
            if c_color == 'w' and tr == 7: promote = True
            elif c_color == 'b' and tr == 0: promote = True
            
        if is_king or promote:
            n_a_kings.append(to)
        else:
            n_a_men.append(to)
            
        # Handle Capture
        n_p_men = list(p_men)
        n_p_kings = list(p_kings)
        
        if abs(fr - tr) == 2:
            # Capture happened, remove midpoint piece
            mid = ((fr + tr) // 2, (fc + tc) // 2)
            if mid in n_p_men:
                n_p_men.remove(mid)
            elif mid in n_p_kings:
                n_p_kings.remove(mid)
                
        return n_a_men, n_a_kings, n_p_men, n_p_kings

    def evaluate(mm, mk, om, ok):
        """
        Heuristic evaluation from perspective of my_color.
        """
        score = 0
        # Material weights
        score += 100 * len(mm)
        score += 250 * len(mk)
        score -= 100 * len(om)
        score -= 250 * len(ok)
        
        # Positional weights for Men
        for r, c in mm:
            # Advancement reward
            if my_color == 'w': score += r
            else: score += (7 - r)
            # Center control
            if 2 <= c <= 5 and 3 <= r <= 4: score += 5
            
        # Positional weights for Kings (Centrality)
        for r, c in mk:
             if 2 <= c <= 5: score += 3

        return score

    # --- Minimax ---

    def alphabeta(depth, alpha, beta, maximizing, mm, mk, om, ok):
        # Time check
        if time.time() - START_TIME > TIME_LIMIT:
             return evaluate(mm, mk, om, ok)
             
        if depth == 0:
            return evaluate(mm, mk, om, ok)
            
        if maximizing:
            # My Turn
            moves = get_moves(mm, mk, om, ok, my_color)
            if not moves: return -100000 # Loss
            
            val = -float('inf')
            for m in moves:
                nmm, nmk, nom, nok = apply_move(m, mm, mk, om, ok, my_color)
                # Recurse (swap turn)
                v = alphabeta(depth - 1, alpha, beta, False, nmm, nmk, nom, nok)
                val = max(val, v)
                alpha = max(alpha, val)
                if beta <= alpha: break
            return val
        else:
            # Opponent Turn
            moves = get_moves(om, ok, mm, mk, opp_color)
            if not moves: return 100000 # Win
            
            val = float('inf')
            for m in moves:
                # Apply move for opponent (nom=NewOppMan, nnm=NewMyMan)
                nom, nok, nmm, nmk = apply_move(m, om, ok, mm, mk, opp_color)
                # Recurse (swap turn)
                v = alphabeta(depth - 1, alpha, beta, True, nmm, nmk, nom, nok)
                val = min(val, v)
                beta = min(beta, val)
                if beta <= alpha: break
            return val

    # --- Main Execution ---
    
    # 1. Get initial legal moves
    legal_moves = get_moves(my_men, my_kings, opp_men, opp_kings, my_color)
    
    if not legal_moves:
        return ((0,0), (0,0)) # Should theoretically imply loss
    
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    best_move = legal_moves[0]
    
    # 2. Iterative Deepening
    for depth in range(1, MAX_DEPTH + 1):
        # If we are already running low on time, stop expanding
        if time.time() - START_TIME > 0.6: 
            break
            
        current_best = None
        current_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        # Shuffle to break ties randomly
        random.shuffle(legal_moves)
        
        for m in legal_moves:
            # Simulation
            nmm, nmk, nom, nok = apply_move(m, my_men, my_kings, opp_men, opp_kings, my_color)
            # Evaluate using AlphaBeta (Next is minimizing/opponent)
            score = alphabeta(depth - 1, alpha, beta, False, nmm, nmk, nom, nok)
            
            if score > current_score:
                current_score = score
                current_best = m
                
            alpha = max(alpha, score)
            
            # Interactive cutoff within the loop
            if time.time() - START_TIME > TIME_LIMIT:
                break
        
        if current_best and (time.time() - START_TIME <= TIME_LIMIT):
            best_move = current_best
            
    return best_move
