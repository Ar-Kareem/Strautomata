
import numpy as np
import time
from typing import List, Tuple, Optional, Set

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert inputs to sets for fast lookups
    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)
    all_opp = opp_men | opp_kings
    all_my = my_men | my_kings

    # Direction mapping based on color
    if color == 'b':
        my_directions = [(-1, -1), (-1, 1)]  # black moves up (row decreases)
        opp_directions = [(1, -1), (1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        promotion_row = 7
    else:
        my_directions = [(1, -1), (1, 1)]   # white moves down (row increases)
        opp_directions = [(-1, -1), (-1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        promotion_row = 0

    def is_dark_square(r: int, c: int) -> bool:
        return (r + c) % 2 == 1

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def get_captures(men, kings, opp_pieces) -> List[Tuple[Tuple[int,int], Tuple[int,int], Set[Tuple[int,int]], Set[Tuple[int,int]], Set[Tuple[int,int]], Set[Tuple[int,int]]]]:
        """Return list of all possible capture sequences as (from, to, new_men, new_kings, new_opp, removed_opps)"""
        captures = []
        directions = king_directions if color == 'b' else king_directions  # same for both now
        all_pieces = men | kings
        all_opp = opp_pieces

        for r, c in all_pieces:
            is_king = (r, c) in kings
            dirs = king_directions if is_king else (my_directions if color == 'b' else my_directions)
            for dr, dc in dirs:
                mid_r, mid_c = r + dr, c + dc
                new_r, new_c = r + 2*dr, c + 2*dc
                if (in_bounds(mid_r, mid_c) and (mid_r, mid_c) in all_opp and
                    in_bounds(new_r, new_c) and (new_r, new_c) not in all_pieces and
                    is_dark_square(new_r, new_c)):
                    # This is a valid capture
                    new_men = men.copy()
                    new_kings = kings.copy()
                    new_opp = all_opp.copy()
                    removed_opp = {(mid_r, mid_c)}
                    
                    # Remove captured piece
                    new_opp.discard((mid_r, mid_c))
                    
                    # Move piece
                    new_men.discard((r, c))
                    new_kings.discard((r, c))
                    # Promote if reaching back rank
                    if not is_king and new_r == promotion_row:
                        new_kings.add((new_r, new_c))
                    else:
                        if is_king:
                            new_kings.add((new_r, new_c))
                        else:
                            new_men.add((new_r, new_c))
                    
                    captures.append(((r, c), (new_r, new_c), new_men, new_kings, new_opp, removed_opp))
        return captures

    def get_moves(men, kings, opp_pieces) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
        """Return all legal non-capture moves"""
        moves = []
        directions = king_directions if color == 'b' else king_directions
        all_pieces = men | kings
        all_opp = opp_pieces

        for r, c in all_pieces:
            is_king = (r, c) in kings
            dirs = king_directions if is_king else (my_directions if color == 'b' else my_directions)
            for dr, dc in dirs:
                new_r, new_c = r + dr, c + dc
                if (in_bounds(new_r, new_c) and (new_r, new_c) not in all_pieces and
                    (new_r, new_c) not in all_opp and is_dark_square(new_r, new_c)):
                    moves.append(((r, c), (new_r, new_c)))
        return moves

    def has_capture(men, kings, opp_pieces) -> bool:
        return len(get_captures(men, kings, opp_pieces)) > 0

    def apply_move_sequence(from_pos, moves_list):
        """Apply a sequence of moves, return final position"""
        r, c = from_pos
        for dr, dc in moves_list:
            r, c = r + dr, c + dc
        return (r, c)

    def expand_capture_sequence(from_piece, current_pos, men, kings, opp_pieces, path, jumped, is_king):
        """Recursively expand a capture sequence"""
        sequences = []
        r, c = current_pos
        dirs = king_directions if is_king else my_directions if color == 'b' else [(1, -1), (1, 1)]
        
        extended = False
        for dr, dc in dirs:
            mid_r, mid_c = r + dr, c + dc
            new_r, new_c = r + 2*dr, c + 2*dc
            mid_pos = (mid_r, mid_c)
            new_pos = (new_r, new_c)
            if (in_bounds(mid_r, mid_c) and mid_pos in opp_pieces and mid_pos not in jumped and
                in_bounds(new_r, new_c) and new_pos not in men and new_pos not in kings and
                is_dark_square(new_r, new_c)):
                extended = True
                new_jumped = jumped | {mid_pos}
                new_path = path + [(2*dr, 2*dc)]
                # Promote during capture if reaching back rank
                becomes_king = (not is_king) and new_r == promotion_row
                sequences += expand_capture_sequence(from_piece, new_pos, men, kings, opp_pieces, new_path, new_jumped, becomes_king or is_king)
        
        if not extended:
            # No more captures, this sequence ends
            if len(path) > 1:  # more than one jump
                final_pos = apply_move_sequence(from_piece, path)
                sequences.append((from_piece, final_pos, path))
        return sequences

    def get_all_capture_sequences(men, kings, opp_pieces) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
        """Return all multi-jump capture sequences"""
        sequences = []
        all_pieces = men | kings
        
        for piece in all_pieces:
            r, c = piece
            is_king = piece in kings
            dirs = king_directions if is_king else my_directions if color == 'b' else [(1, -1), (1, 1)]
            for dr, dc in dirs:
                mid_r, mid_c = r + dr, c + dc
                new_r, new_c = r + 2*dr, c + 2*dc
                if (in_bounds(mid_r, mid_c) and (mid_r, mid_c) in opp_pieces and
                    in_bounds(new_r, new_c) and (new_r, new_c) not in all_pieces and
                    is_dark_square(new_r, new_c)):
                    # Found a starting jump
                    becomes_king = (not is_king) and new_r == promotion_row
                    new_king_status = becomes_king or is_king
                    seq = expand_capture_sequence(piece, (new_r, new_c), men, kings, opp_pieces, [(2*dr, 2*dc)], {(mid_r, mid_c)}, new_king_status)
                    sequences.extend(seq)
        
        # Also include single jumps if no multi-jump exists
        if not sequences:
            basic_captures = get_captures(men, kings, opp_pieces)
            for (fr, fc), (tr, tc), _, _, _, _ in basic_captures:
                sequences.append(((fr, fc), (tr, tc)))
        
        # Convert to move format
        result = []
        for start, end, _ in sequences:
            result.append((start, end))
        return result

    # Piece square table - encourage center control and king promotion
    pst = np.array([
        [ 0,  5,  0,  5,  0,  5,  0,  5],
        [ 5,  1,  5,  1,  5,  1,  5,  1],
        [ 0,  5,  0,  5,  0,  5,  0,  5],
        [ 5,  1,  5,  1,  5,  1,  5,  1],
        [ 1,  5,  1,  5,  1,  5,  1,  5],
        [ 5,  0,  5,  0,  5,  0,  5,  0],
        [ 0,  5,  0,  5,  0,  5,  0,  5],
        [ 5,  0,  5,  0,  5,  0,  5,  0]
    ])

    # If we are white, flip the table vertically
    if color == 'w':
        pst = pst[::-1]

    def evaluate() -> float:
        """Evaluate the current board state"""
        score = 0
        
        # Piece values
        score += 100 * len(my_men)
        score += 300 * len(my_kings)
        score -= 100 * len(opp_men)
        score -= 300 * len(opp_kings)
        
        # Positional scoring
        for r, c in my_men:
            if in_bounds(r, c):
                score += pst[r, c]
        for r, c in my_kings:
            if in_bounds(r, c):
                score += pst[r, c] * 0.5  # kings already have high base value
        
        # Mobility bonus
        if not has_capture(my_men, my_kings, all_opp):
            moves = get_moves(my_men, my_kings, all_opp)
            score += len(moves) * 5
        
        # Penalize having pieces stuck at back
        back_row = 7 if color == 'b' else 0
        for r, c in my_men:
            if r == back_row and color == 'w':
                score -= 10
            if r == back_row and color == 'b':
                score -= 10
                
        return score

    def minimax(men, kings, opp_m, opp_k, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth == 0 or (len(men) + len(kings) == 0):
            return evaluate() if maximizing else -evaluate()

        my_all = men | kings
        opp_all = opp_m | opp_k
        all_pieces = my_all | opp_all

        if maximizing:
            max_eval = float('-inf')
            # Check for captures
            captures = get_all_capture_sequences(men, kings, opp_all)
            if captures:
                for from_pos, to_pos in captures:
                    # Simple capture simulation
                    new_men = men.copy()
                    new_kings = kings.copy()
                    new_opp_m = opp_m.copy()
                    new_opp_k = opp_k.copy()
                    
                    piece = (from_pos[0], from_pos[1])
                    is_king = piece in kings
                    # Find captured piece
                    dr = (to_pos[0] - from_pos[0]) // (abs(to_pos[0] - from_pos[0]) if to_pos[0] != from_pos[0] else 1)
                    dc = (to_pos[1] - from_pos[1]) // (abs(to_pos[1] - from_pos[1]) if to_pos[1] != from_pos[1] else 1)
                    mid_r, mid_c = from_pos[0] + dr, from_pos[1] + dc
                    mid = (mid_r, mid_c)
                    
                    # Remove from current
                    new_men.discard(piece)
                    new_kings.discard(piece)
                    
                    # Add to new position
                    if not is_king and to_pos[0] == promotion_row:
                        new_kings.add(to_pos)
                    else:
                        if is_king:
                            new_kings.add(to_pos)
                        else:
                            new_men.add(to_pos)
                    
                    # Remove captured
                    if mid in new_opp_m:
                        new_opp_m.discard(mid)
                    elif mid in new_opp_k:
                        new_opp_k.discard(mid)
                    
                    # Recursively evaluate, but don't alternate turn until non-capture
                    eval_score = minimax(new_men, new_kings, new_opp_m, new_opp_k, depth - 1, alpha, beta, True)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            else:
                # Regular moves
                moves = get_moves(men, kings, opp_all)
                if not moves:
                    return float('-inf')  # No moves means loss
                
                for from_pos, to_pos in moves:
                    new_men = men.copy()
                    new_kings = kings.copy()
                    
                    piece = (from_pos[0], from_pos[1])
                    is_king = piece in kings
                    new_men.discard(piece)
                    new_kings.discard(piece)
                    
                    if not is_king and to_pos[0] == promotion_row:
                        new_kings.add(to_pos)
                    else:
                        if is_king:
                            new_kings.add(to_pos)
                        else:
                            new_men.add(to_pos)
                    
                    eval_score = minimax(opp_m, opp_k, new_men, new_kings, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                        
            return max_eval
        else:
            # Opponent's turn (minimizing)
            min_eval = float('inf')
            # Assume opponent has captures?
            opp_captures = get_all_capture_sequences(opp_m, opp_k, my_all)
            if opp_captures:
                for from_pos, to_pos in opp_captures:
                    new_opp_m = opp_m.copy()
                    new_opp_k = opp_k.copy()
                    new_men = men.copy()
                    new_kings = kings.copy()
                    
                    piece = (from_pos[0], from_pos[1])
                    is_king = piece in opp_kings
                    dr = (to_pos[0] - from_pos[0]) // max(1, abs(to_pos[0] - from_pos[0]))
                    dc = (to_pos[1] - from_pos[1]) // max(1, abs(to_pos[1] - from_pos[1]))
                    mid_r, mid_c = from_pos[0] + dr, from_pos[1] + dc
                    mid = (mid_r, mid_c)
                    
                    new_opp_m.discard(piece)
                    new_opp_k.discard(piece)
                    
                    if not is_king and to_pos[0] == (0 if color == 'b' else 7):
                        new_opp_k.add(to_pos)
                    else:
                        if is_king:
                            new_opp_k.add(to_pos)
                        else:
                            new_opp_m.add(to_pos)
                    
                    if mid in new_men:
                        new_men.discard(mid)
                    elif mid in new_kings:
                        new_kings.discard(mid)
                    
                    eval_score = minimax(new_men, new_kings, new_opp_m, new_opp_k, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            else:
                # Opponent regular moves
                opp_moves = get_moves(opp_m, opp_k, my_all)
                if not opp_moves:
                    return float('inf')  # Win
                
                for from_pos, to_pos in opp_moves:
                    new_opp_m = opp_m.copy()
                    new_opp_k = opp_k.copy()
                    
                    piece = (from_pos[0], from_pos[1])
                    is_king = piece in opp_k
                    new_opp_m.discard(piece)
                    new_opp_k.discard(piece)
                    
                    prom_row_opp = 0 if color == 'b' else 7
                    if not is_king and to_pos[0] == prom_row_opp:
                        new_opp_k.add(to_pos)
                    else:
                        if is_king:
                            new_opp_k.add(to_pos)
                        else:
                            new_opp_m.add(to_pos)
                    
                    eval_score = minimax(men, kings, new_opp_m, new_opp_k, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                        
            return min_eval

    # Start timing
    start_time = time.time()

    # First, check for mandatory captures
    all_opp = opp_men | opp_kings
    capture_moves = get_all_capture_sequences(my_men, my_kings, all_opp)
    if capture_moves:
        best_move = capture_moves[0]
        best_value = float('-inf')
        
        for move in capture_moves:
            from_pos, to_pos = move
            new_men = my_men.copy()
            new_kings = my_kings.copy()
            
            piece = from_pos
            is_king = piece in my_kings
            # Find captured piece
            dr = (to_pos[0] - from_pos[0]) // max(1, abs(to_pos[0] - from_pos[0]))
            dc = (to_pos[1] - from_pos[1]) // max(1, abs(to_pos[1] - from_pos[1]))
            mid_r, mid_c = from_pos[0] + dr, from_pos[1] + dc
            mid = (mid_r, mid_c)
            
            new_men.discard(piece)
            new_kings.discard(piece)
            
            if not is_king and to_pos[0] == promotion_row:
                new_kings.add(to_pos)
            else:
                if is_king:
                    new_kings.add(to_pos)
                else:
                    new_men.add(to_pos)
            
            # Remove captured
            new_opp_m = opp_men.copy()
            new_opp_k = opp_kings.copy()
            if mid in new_opp_m:
                new_opp_m.discard(mid)
            elif mid in new_opp_k:
                new_opp_k.discard(mid)
            
            # Evaluate this move with reduced depth minimax
            value = minimax(new_men, new_kings, new_opp_m, new_opp_k, 2, float('-inf'), float('inf'), False)
            if value > best_value:
                best_value = value
                best_move = move
                
        return best_move

    # If no captures, get regular moves
    regular_moves = get_moves(my_men, my_kings, all_opp)
    if not regular_moves:
        # Fallback: return any piece move even if illegal (should not happen)
        if my_men:
            p = next(iter(my_men))
            return (p, p)
        if my_kings:
            p = next(iter(my_kings))
            return (p, p)

    # Evaluate regular moves
    best_move = regular_moves[0]
    best_value = float('-inf')
    depth = 4  # Reduced depth for time safety

    for move in regular_moves:
        if time.time() - start_time > 0.8:
            break  # Time is running out
            
        from_pos, to_pos = move
        new_men = my_men.copy()
        new_kings = my_kings.copy()
        
        piece = from_pos
        is_king = piece in my_kings
        new_men.discard(piece)
        new_kings.discard(piece)
        
        if not is_king and to_pos[0] == promotion_row:
            new_kings.add(to_pos)
        else:
            if is_king:
                new_kings.add(to_pos)
            else:
                new_men.add(to_pos)
        
        value = minimax(opp_men, opp_kings, new_men, new_kings, depth, float('-inf'), float('inf'), False)
        if value > best_value:
            best_value = value
            best_move = move

    return best_move
