
import numpy as np
from typing import List, Tuple, Optional

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    
    # Convert to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    all_my_pieces = my_men_set | my_kings_set
    all_opp_pieces = opp_men_set | opp_kings_set
    all_pieces = all_my_pieces | all_opp_pieces
    
    direction = 1 if color == 'w' else -1  # white moves up, black moves down
    
    def is_valid_square(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8 and (r + c) % 2 == 1  # dark squares only
    
    def get_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, is_white):
        """Generate all legal moves, prioritizing captures"""
        all_my = my_men_set | my_kings_set
        all_opp = opp_men_set | opp_kings_set
        all_pieces = all_my | all_opp
        
        captures = []
        normal_moves = []
        
        for piece in all_my:
            r, c = piece
            is_king = piece in my_kings_set
            
            # Directions: men move forward, kings move all 4 directions
            if is_king:
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            else:
                if is_white:
                    directions = [(1, 1), (1, -1)]
                else:
                    directions = [(-1, 1), (-1, -1)]
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if is_valid_square(nr, nc) and (nr, nc) not in all_pieces:
                    normal_moves.append(((r, c), (nr, nc)))
                
                # Check captures
                cap_r, cap_c = r + 2*dr, c + 2*dc
                mid_r, mid_c = r + dr, c + dc
                if (is_valid_square(cap_r, cap_c) and 
                    (mid_r, mid_c) in all_opp and 
                    (cap_r, cap_c) not in all_pieces):
                    captures.append(((r, c), (cap_r, cap_c)))
        
        # If captures exist, they are mandatory
        if captures:
            return captures
        return normal_moves
    
    def get_all_captures_for_piece(piece, my_men_set, my_kings_set, opp_men_set, opp_kings_set, is_white):
        """Get all captures for a specific piece (for multi-jump chains)"""
        all_my = my_men_set | my_kings_set
        all_opp = opp_men_set | opp_kings_set
        all_pieces = all_my | all_opp
        
        is_king = piece in my_kings_set
        r, c = piece
        
        if is_king:
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        else:
            if is_white:
                directions = [(1, 1), (1, -1)]
            else:
                directions = [(-1, 1), (-1, -1)]
        
        captures = []
        for dr, dc in directions:
            cap_r, cap_c = r + 2*dr, c + 2*dc
            mid_r, mid_c = r + dr, c + dc
            if (is_valid_square(cap_r, cap_c) and 
                (mid_r, mid_c) in all_opp and 
                (cap_r, cap_c) not in all_pieces):
                captures.append((cap_r, cap_c))
        return captures
    
    def apply_move(state, move):
        """Apply a move and return new state"""
        my_men, my_kings, opp_men, opp_kings, is_white = state
        my_men = set(my_men)
        my_kings = set(my_kings)
        opp_men = set(opp_men)
        opp_kings = set(opp_kings)
        
        from_pos, to_pos = move
        fr, fc = from_pos
        tr, tc = to_pos
        
        # Determine if piece is king
        is_king = from_pos in my_kings
        piece_was_man = from_pos in my_men
        
        # Remove from old position
        if is_king:
            my_kings.discard(from_pos)
        else:
            my_men.discard(from_pos)
        
        # Check if it's a capture
        if abs(tr - fr) == 2:
            # Remove captured piece
            mid_r = (fr + tr) // 2
            mid_c = (fc + tc) // 2
            if (mid_r, mid_c) in opp_kings:
                opp_kings.discard((mid_r, mid_c))
            elif (mid_r, mid_c) in opp_men:
                opp_men.discard((mid_r, mid_c))
        
        # Check for promotion
        if not is_king:
            if is_white and tr == 7:
                my_kings.add(to_pos)
            elif not is_white and tr == 0:
                my_kings.add(to_pos)
            else:
                my_men.add(to_pos)
        else:
            my_kings.add(to_pos)
        
        return (frozenset(my_men), frozenset(my_kings), 
                frozenset(opp_men), frozenset(opp_kings), is_white)
    
    def evaluate_state(state):
        """Heuristic evaluation of the board"""
        my_men, my_kings, opp_men, opp_kings, is_white = state
        
        # Material value
        men_value = 1.0
        king_value = 2.5
        
        my_material = len(my_men) * men_value + len(my_kings) * king_value
        opp_material = len(opp_men) * men_value + len(opp_kings) * king_value
        
        score = my_material - opp_material
        
        # Positional bonuses
        # Advance pieces forward
        my_pieces = my_men | my_kings
        opp_pieces = opp_men | opp_kings
        
        for (r, c) in my_pieces:
            if (r, c) in my_men:
                # Men want to advance
                if is_white:
                    score += 0.1 * r  # closer to row 7 is better
                else:
                    score += 0.1 * (7 - r)  # closer to row 0 is better
            
            # Center control
            if 2 <= c <= 5:
                score += 0.05
        
        for (r, c) in opp_pieces:
            if (r, c) in opp_men:
                if is_white:
                    score -= 0.1 * (7 - r)
                else:
                    score -= 0.1 * r
            
            if 2 <= c <= 5:
                score -= 0.05
        
        # King mobility bonus
        for (r, c) in my_kings:
            score += 0.2
        
        for (r, c) in opp_kings:
            score -= 0.2
        
        return score
    
    def get_all_moves_from_state(state):
        """Get all legal moves from a state"""
        my_men, my_kings, opp_men, opp_kings, is_white = state
        return get_all_moves(my_men, my_kings, opp_men, opp_kings, is_white)
    
    def has_captures(state):
        """Check if there are any capture moves"""
        my_men, my_kings, opp_men, opp_kings, is_white = state
        all_my = my_men | my_kings
        all_opp = opp_men | opp_kings
        all_pieces = all_my | all_opp
        
        for piece in all_my:
            r, c = piece
            is_king = piece in my_kings
            
            if is_king:
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            else:
                if is_white:
                    directions = [(1, 1), (1, -1)]
                else:
                    directions = [(-1, 1), (-1, -1)]
            
            for dr, dc in directions:
                cap_r, cap_c = r + 2*dr, c + 2*dc
                mid_r, mid_c = r + dr, c + dc
                if (is_valid_square(cap_r, cap_c) and 
                    (mid_r, mid_c) in all_opp and 
                    (cap_r, cap_c) not in all_pieces):
                    return True
        return False
    
    def minimax(state, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return evaluate_state(state), None
        
        my_men, my_kings, opp_men, opp_kings, is_white = state
        
        if maximizing:
            max_eval = -float('inf')
            best_move = None
            
            moves = get_all_moves_from_state(state)
            if not moves:
                return -1000, None  # No moves = loss
            
            # Sort moves: captures first
            capture_moves = [m for m in moves if abs(m[1][0] - m[0][0]) == 2]
            normal_moves = [m for m in moves if abs(m[1][0] - m[0][0]) == 1]
            
            # Prioritize captures
            sorted_moves = capture_moves + normal_moves
            
            for move in sorted_moves:
                new_state = apply_move(state, move)
                
                # Check for multi-jump
                if abs(move[1][0] - move[0][0]) == 2:
                    # Check if piece can capture again
                    new_my_men, new_my_kings, new_opp_men, new_opp_kings, new_is_white = new_state
                    piece_captures = get_all_captures_for_piece(
                        move[1], new_my_men, new_my_kings, 
                        new_opp_men, new_opp_kings, new_is_white
                    )
                    if piece_captures:
                        # For simplicity, we only consider single jumps in minimax
                        # Full multi-jump would be more complex
                        pass
                
                eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            
            # Swap roles for opponent's turn
            opp_state = (opp_men, opp_kings, my_men, my_kings, not is_white)
            moves = get_all_moves_from_state(opp_state)
            
            if not moves:
                return 1000, None  # Opponent has no moves = win for us
            
            capture_moves = [m for m in moves if abs(m[1][0] - m[0][0]) == 2]
            normal_moves = [m for m in moves if abs(m[1][0] - m[0][0]) == 1]
            sorted_moves = capture_moves + normal_moves
            
            for move in sorted_moves:
                new_state = apply_move(opp_state, move)
                # Swap back to our perspective
                new_opp_men, new_opp_kings, new_my_men, new_my_kings, new_is_white = new_state
                back_state = (new_my_men, new_my_kings, new_opp_men, new_opp_kings, is_white)
                
                eval_score, _ = minimax(back_state, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Choose search depth based on piece count
    total_pieces = len(all_my_pieces) + len(all_opp_pieces)
    if total_pieces <= 8:
        depth = 8
    elif total_pieces <= 12:
        depth = 6
    elif total_pieces <= 16:
        depth = 5
    elif total_pieces <= 20:
        depth = 4
    else:
        depth = 3
    
    # Initial state
    is_white = (color == 'w')
    state = (frozenset(my_men_set), frozenset(my_kings_set), 
             frozenset(opp_men_set), frozenset(opp_kings_set), is_white)
    
    # Get all legal moves for current state
    moves = get_all_moves_from_state(state)
    
    if not moves:
        # No legal moves, but we must return something
        # Return a dummy move (shouldn't happen in real game)
        for piece in all_my_pieces:
            return (piece, (0, 0))
    
    # If there's only one move, return it immediately
    if len(moves) == 1:
        return moves[0]
    
    # Run minimax
    _, best_move = minimax(state, depth, -float('inf'), float('inf'), True)
    
    if best_move is None:
        # Fallback to first available move
        return moves[0]
    
    return best_move
