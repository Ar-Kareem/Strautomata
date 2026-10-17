
import numpy as np
import time
import sys

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello Policy using Iterative Deepening Alpha-Beta Search
    with positional heuristics and dynamic time management.
    """
    
    # --- Configuration & Weights ---
    MAX_DEPTH = 10
    INF = 10**9
    
    # 8x8 positional weights ( corners are most valuable )
    # C-squares (c, d, e, f 3-6) are often dangerous early on.
    WEIGHTS = np.array([
        [100, -20, 10,  5,  5, 10, -20, 100],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [ 10,  -2, -1, -1, -1, -1,  -2,  10],
        [  5,  -2, -1, -1, -1, -1,  -2,   5],
        [  5,  -2, -1, -1, -1, -1,  -2,   5],
        [ 10,  -2, -1, -1, -1, -1,  -2,  10],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [100, -20, 10,  5,  5, 10, -20, 100]
    ], dtype=np.float32)

    # Directions: N, NE, E, SE, S, SW, W, NW
    DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

    # --- Helper Functions ---

    def get_legal_moves(board_me: np.ndarray, board_opp: np.ndarray) -> list:
        moves = []
        empties = np.where((board_me == 0) & (board_opp == 0))
        # Heuristic: Prefer checking center squares first to establish cutoffs
        # But simply iterating is usually fine for 64 max.
        for r, c in zip(empties[0], empties[1]):
            if is_valid_move(board_me, board_opp, r, c):
                moves.append((r, c))
        return moves

    def is_valid_move(board_me: np.ndarray, board_opp: np.ndarray, r: int, c: int) -> bool:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board_opp[nr, nc] == 1:
                nr += dr
                nc += dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if board_me[nr, nc] == 1:
                        return True
                    if board_opp[nr, nc] == 0:
                        break
                    nr += dr
                    nc += dc
        return False

    def make_move(board_me: np.ndarray, board_opp: np.ndarray, r: int, c: int):
        # Creates new boards with the move applied
        new_me = board_me.copy()
        new_opp = board_opp.copy()
        
        new_me[r, c] = 1
        
        # Flip discs
        for dr, dc in DIRS:
            discs_to_flip = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8 and new_opp[nr, nc] == 1:
                discs_to_flip.append((nr, nc))
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and new_me[nr, nc] == 1:
                for fr, fc in discs_to_flip:
                    new_me[fr, fc] = 1
                    new_opp[fr, fc] = 0
        
        return new_me, new_opp

    def evaluate(board_me: np.ndarray, board_opp: np.ndarray, moves_me: int, moves_opp: int) -> float:
        # Static evaluation function
        score = 0
        
        # 1. Positional Score (Weighted Sum)
        score += np.sum(WEIGHTS * board_me)
        score -= np.sum(WEIGHTS * board_opp)
        
        # 2. Mobility (Very important early game)
        # Encourage moves that reduce opponent mobility
        if moves_me + moves_opp > 0:
            score += 10 * (moves_me - moves_opp)
        
        # 3. Disc Parity (Endgame priority)
        # Count difference normalized by total discs to emphasize importance in endgame
        total_discs = np.sum(board_me) + np.sum(board_opp)
        if total_discs > 50: # Late game
            score += 20 * (np.sum(board_me) - np.sum(board_opp))
        
        return score

    # --- Search Algorithms ---

    def order_moves(moves, board_me, board_opp):
        # Sort moves based on positional weight (corners first)
        return sorted(moves, key=lambda m: WEIGHTS[m[0], m[1]], reverse=True)

    def alpha_beta(board_me, board_opp, depth, alpha, beta, maximizing_player):
        moves = get_legal_moves(board_me, board_opp)
        
        # Game over or leaf node
        if depth == 0 or not moves:
            if not moves:
                # Pass scenario: check if opponent also has no moves
                opp_moves = get_legal_moves(board_opp, board_me)
                if not opp_moves:
                    # Terminal state
                    score = 0
                    diff = np.sum(board_me) - np.sum(board_opp)
                    if diff > 0: score = INF + diff
                    elif diff < 0: score = -INF - diff
                    return score
                else:
                    # Pass turn (simulated)
                    return alpha_beta(board_opp, board_me, depth - 1, -beta, -alpha, True) * -1
            
            # Standard evaluation at depth limit
            return evaluate(board_me, board_opp, len(moves), len(get_legal_moves(board_opp, board_me)))

        # Move Ordering
        moves = order_moves(moves, board_me, board_opp)

        if maximizing_player:
            max_eval = -INF
            for r, c in moves:
                next_me, next_opp = make_move(board_me, board_opp, r, c)
                eval_score = alpha_beta(next_me, next_opp, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for r, c in moves:
                next_me, next_opp = make_move(board_me, board_opp, r, c)
                eval_score = alpha_beta(next_me, next_opp, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Execution Logic ---

    # 1. Get Initial Moves
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"

    # 2. Sort initial moves for the root (heuristic ordering)
    # This ensures the best move is evaluated first, aiding alpha-beta pruning
    ordered_moves = order_moves(legal_moves, you, opponent)

    # 3. Time Management (Iterative Deepening)
    # We have 1 second. We will try to reach depth 6-10 depending on branching factor.
    best_move = ordered_moves[0]
    best_score = -INF
    
    start_time = time.time()
    
    # Try increasing depths
    for depth in range(1, MAX_DEPTH + 1):
        current_best_move = best_move
        current_best_score = -INF
        
        # Alpha-Beta at root
        alpha = -INF
        beta = INF
        
        for r, c in ordered_moves:
            # Check time before starting a depth iteration or node
            if time.time() - start_time > 0.85: 
                # Break early if time is running out to return the best found so far
                break
            
            next_me, next_opp = make_move(you, opponent, r, c)
            score = alpha_beta(next_me, next_opp, depth - 1, alpha, beta, False)
            
            if score > current_best_score:
                current_best_score = score
                current_best_move = (r, c)
            
            # Pruning at root
            alpha = max(alpha, score)
            
        if current_best_score > -INF:
            best_move = current_best_move
            best_score = current_best_score
            
        # If we found a winning move or a very good move, we might stop early
        if best_score > (INF - 100):
            break
            
        # Timeout check for next loop
        if time.time() - start_time > 0.9:
            break

    # 4. Format Output
    r, c = best_move
    return f"{chr(ord('a') + c)}{r + 1}"
