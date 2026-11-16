
import time
from typing import List, Tuple, Set, Optional

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.9  # Leave some buffer
    
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    direction = -1 if color == 'b' else 1  # b moves down (decreasing row), w moves up
    
    def get_all_moves(men: Set, kings: Set, opp_m: Set, opp_k: Set, dir: int):
        captures = []
        simple_moves = []
        all_opp = opp_m | opp_k
        all_pieces = men | kings | all_opp
        
        # Check for captures first (mandatory)
        for piece in men | kings:
            is_king = piece in kings
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(dir, -1), (dir, 1)]
            
            for dr, dc in dirs:
                mid_r, mid_c = piece[0] + dr, piece[1] + dc
                end_r, end_c = piece[0] + 2*dr, piece[1] + 2*dc
                
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    if (mid_r, mid_c) in all_opp and (end_r, end_c) not in all_pieces:
                        captures.append((piece, (end_r, end_c)))
        
        if captures:
            return captures, True
        
        # Simple moves
        for piece in men | kings:
            is_king = piece in kings
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(dir, -1), (dir, 1)]
            
            for dr, dc in dirs:
                new_r, new_c = piece[0] + dr, piece[1] + dc
                if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in all_pieces:
                    simple_moves.append((piece, (new_r, new_c)))
        
        return simple_moves, False
    
    def evaluate(men: Set, kings: Set, opp_m: Set, opp_k: Set, dir: int) -> float:
        score = 0
        # Material
        score += len(men) * 100 + len(kings) * 150
        score -= len(opp_m) * 100 + len(opp_k) * 150
        
        # Positional bonuses
        for r, c in men:
            # Advancement
            if dir == 1:  # white moves up
                score += r * 5
            else:  # black moves down
                score += (7 - r) * 5
            # Center control
            score += (3.5 - abs(c - 3.5)) * 2
        
        for r, c in kings:
            score += (3.5 - abs(c - 3.5)) * 3
            score += (3.5 - abs(r - 3.5)) * 3
        
        for r, c in opp_m:
            if dir == 1:
                score -= (7 - r) * 5
            else:
                score -= r * 5
            score -= (3.5 - abs(c - 3.5)) * 2
        
        for r, c in opp_k:
            score -= (3.5 - abs(c - 3.5)) * 3
            score -= (3.5 - abs(r - 3.5)) * 3
        
        return score
    
    def apply_move(men: Set, kings: Set, opp_m: Set, opp_k: Set, move, dir: int, is_capture: bool):
        frm, to = move
        new_men = set(men)
        new_kings = set(kings)
        new_opp_m = set(opp_m)
        new_opp_k = set(opp_k)
        
        is_king = frm in kings
        
        if is_king:
            new_kings.remove(frm)
            new_kings.add(to)
        else:
            new_men.remove(frm)
            # Check promotion
            if (dir == 1 and to[0] == 7) or (dir == -1 and to[0] == 0):
                new_kings.add(to)
            else:
                new_men.add(to)
        
        if is_capture:
            mid = ((frm[0] + to[0]) // 2, (frm[1] + to[1]) // 2)
            new_opp_m.discard(mid)
            new_opp_k.discard(mid)
        
        return new_men, new_kings, new_opp_m, new_opp_k
    
    def minimax(men, kings, opp_m, opp_k, dir, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(men, kings, opp_m, opp_k, dir), None
        
        moves, is_capture = get_all_moves(men, kings, opp_m, opp_k, dir)
        
        if not moves or depth == 0:
            return evaluate(men, kings, opp_m, opp_k, dir), None
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                nm, nk, nom, nok = apply_move(men, kings, opp_m, opp_k, move, dir, is_capture)
                eval_score, _ = minimax(nom, nok, nm, nk, -dir, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                nm, nk, nom, nok = apply_move(men, kings, opp_m, opp_k, move, dir, is_capture)
                eval_score, _ = minimax(nom, nok, nm, nk, -dir, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Get legal moves first
    moves, _ = get_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction)
    
    if not moves:
        # No legal moves - return something (shouldn't happen if game is valid)
        for p in my_men_set | my_kings_set:
            return (p, p)
    
    if len(moves) == 1:
        return moves[0]
    
    # Iterative deepening
    best_move = moves[0]
    for depth in range(1, 10):
        if time.time() - start_time > time_limit * 0.8:
            break
        _, move = minimax(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction, depth, float('-inf'), float('inf'), True)
        if move:
            best_move = move
    
    return best_move
