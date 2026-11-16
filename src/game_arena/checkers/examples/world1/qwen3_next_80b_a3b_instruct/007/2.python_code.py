
import numpy as np
import time
from typing import List, Tuple, Dict, Optional

def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns the best move (from, to) for the current player given the board state.
    Implements minimax with alpha-beta pruning and heuristic evaluation.
    """
    # Convert inputs to sets for faster lookup
    my_pieces = set(my_men) | set(my_kings)
    opp_pieces = set(opp_men) | set(opp_kings)
    
    # Define direction based on color
    dir_mult = -1 if color == 'b' else 1  # Black moves down (row decreases), White moves up (row increases)
    
    # Get all legal moves with captures
    capture_moves = get_all_capture_moves(my_pieces, opp_pieces, color, dir_mult)
    
    if capture_moves:
        # Mandatory captures: choose the best capture sequence
        best_move = evaluate_capture_sequences(capture_moves, my_pieces, opp_pieces, color, dir_mult)
        return best_move
    
    # No captures available; get normal moves
    normal_moves = get_all_normal_moves(my_pieces, opp_pieces, color, dir_mult)
    
    if not normal_moves:
        # No legal moves? This shouldn't happen in valid games, but return placeholder to avoid disqualification
        return ((0, 0), (1, 1))  # Fallback (should not reach here in real play)
    
    # If no captures, use minimax to pick best normal move
    start_time = time.time()
    best_move = None
    best_score = float('-inf')
    
    # Limited depth due to time constraint; adapt depth based on remaining time
    depth = 3
    for move in normal_moves:
        if time.time() - start_time > 0.8:  # Leave buffer
            break
            
        # Simulate move
        new_my_pieces, new_opp_pieces = simulate_move(my_pieces, opp_pieces, move, color, dir_mult)
        score = minimax(new_my_pieces, new_opp_pieces, depth - 1, False, color, dir_mult, start_time, alpha=float('-inf'), beta=float('inf'))
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        # Fallback: pick first move if minimax failed
        best_move = normal_moves[0]
        
    return best_move

def get_all_capture_moves(my_pieces, opp_pieces, color, dir_mult) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Return all possible capture moves (including multi-jumps) as a list of from, to tuples."""
    capture_chains = []
    
    # Build set for fast lookup
    all_opp = opp_pieces
    all_my = my_pieces
    
    # For each of my pieces, check for capture opportunities
    for piece in my_pieces:
        # Check if piece is king
        is_king = piece in my_pieces - set([p for p in my_pieces if p[0] == 0 or p[0] == 7])  # Kings are any piece that's on last row
        if piece in my_pieces and piece in [p for p in my_pieces if (color == 'b' and p[0] == 7) or (color == 'w' and p[0] == 0)]:
            is_king = True
        else:
            is_king = piece in [p for p in my_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7))]
        
        # This is a simplified check: we'll use a helper to detect if it's king based on position and color
        is_king = piece in [p for p in my_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7))]
        
        # Actually, better way: kings are in my_kings list
        is_king = piece in [p for p in my_pieces if p in my_kings] if 'my_kings' in globals() else (color == 'b' and piece[0] == 0) or (color == 'w' and piece[0] == 7)
        
        # Correct: my_kings are given explicitly
        is_king = piece in set(my_kings)
        
        directions = []
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Regular piece: moves only in color direction
            directions = [(dir_mult, -1), (dir_mult, 1)]
        
        for dr, dc in directions:
            # First jump
            mid_r, mid_c = piece[0] + dr, piece[1] + dc
            target_r, target_c = piece[0] + 2 * dr, piece[1] + 2 * dc
            
            if 0 <= mid_r <= 7 and 0 <= mid_c <= 7 and 0 <= target_r <= 7 and 0 <= target_c <= 7:
                if (mid_r, mid_c) in all_opp and (target_r, target_c) not in all_my and (target_r, target_c) not in all_opp:
                    # Found a capture
                    capture_chains.append(((piece[0], piece[1]), (target_r, target_c)))
    
    # Now, handle multi-jump capture sequences recursively
    all_sequences = []
    for move in capture_chains:
        # Recursively expand multi-jumps
        sequences = get_multi_jump_sequences(move, my_pieces, opp_pieces, color, dir_mult)
        all_sequences.extend(sequences)
    
    # If we have multi-jump sequences, return them (since they are valid capture sequences)
    if all_sequences:
        # Return all leaf sequences of multi-jumps
        return all_sequences
    
    # Return single capture moves
    return capture_chains

def get_multi_jump_sequences(initial_move, my_pieces, opp_pieces, color, dir_mult) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Recursively get all possible multi-jump sequences."""
    # This is a simplified version: we'll simulate the board after the first jump
    from_square, to_square = initial_move
    my_set = set(my_pieces)
    opp_set = set(opp_pieces)
    
    # Remove captured piece and move piece
    mid_row = (from_square[0] + to_square[0]) // 2
    mid_col = (from_square[1] + to_square[1]) // 2
    capture_square = (mid_row, mid_col)
    
    # Remove captured opponent piece
    new_opp = opp_set - {capture_square}
    new_my = my_set - {from_square} | {to_square}
    
    # Check if the moved piece is now a king
    is_king = to_square in set(my_kings) or (color == 'b' and to_square[0] == 0) or (color == 'w' and to_square[0] == 7)
    if not is_king and to_square in set(my_men):
        is_king = False
    else:
        is_king = True
    # Correct: use the actual my_kings list
    if to_square in set(my_kings):
        is_king = True
    elif color == 'b' and to_square[0] == 0:
        is_king = True
    elif color == 'w' and to_square[0] == 7:
        is_king = True
    else:
        is_king = to_square in set(my_kings)
    
    # Check for further captures
    further_captures = []
    directions = []
    if is_king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        directions = [(dir_mult, -1), (dir_mult, 1)]
    
    for dr, dc in directions:
        mid_r = to_square[0] + dr
        mid_c = to_square[1] + dc
        target_r = to_square[0] + 2 * dr
        target_c = to_square[1] + 2 * dc
        
        if 0 <= mid_r <= 7 and 0 <= mid_c <= 7 and 0 <= target_r <= 7 and 0 <= target_c <= 7:
            if (mid_r, mid_c) in new_opp and (target_r, target_c) not in new_my and (target_r, target_c) not in new_opp:
                # Another capture possible
                further_captures.append(((to_square[0], to_square[1]), (target_r, target_c)))
    
    if not further_captures:
        # If no further captures, this is a complete sequence
        return [initial_move]  # Returning just the original move as the complete sequence
    
    all_sequences = []
    for next_move in further_captures:
        # Recursively get full sequence
        combo = get_multi_jump_sequences(next_move, new_my, new_opp, color, dir_mult)
        # Prepend initial move to each sub-sequence
        for seq in combo:
            if isinstance(seq, tuple) and len(seq) == 2 and isinstance(seq[0], tuple):
                # It's a single move, so make a list of two moves
                complete_seq = [initial_move, seq]
                all_sequences.append(complete_seq)
            else:
                # It's a sequence, prepend initial move
                complete_seq = [initial_move] + seq
                all_sequences.append(complete_seq)
    
    # If we have sequences, return them, else return empty
    if not all_sequences:
        return [initial_move]
    
    # Flatten and return the full sequences
    return all_sequences

def get_all_normal_moves(my_pieces, opp_pieces, color, dir_mult) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Return all possible non-capture moves."""
    moves = []
    for piece in my_pieces:
        is_king = piece in [p for p in my_kings]
        
        directions = []
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(dir_mult, -1), (dir_mult, 1)]
        
        for dr, dc in directions:
            new_r, new_c = piece[0] + dr, piece[1] + dc
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                # Only dark squares are playable: square is dark if (row+col) % 2 == 1
                if (new_r + new_c) % 2 == 1:  # dark squares
                    if (new_r, new_c) not in my_pieces and (new_r, new_c) not in opp_pieces:
                        moves.append((piece, (new_r, new_c)))
    
    return moves

def simulate_move(my_pieces, opp_pieces, move, color, dir_mult):
    """Simulate a move and return new board state. Assumes move is legal."""
    from_square, to_square = move
    my_set = set(my_pieces)
    opp_set = set(opp_pieces)
    
    # Check if it's a capture
    mid_r = (from_square[0] + to_square[0]) // 2
    mid_c = (from_square[1] + to_square[1]) // 2
    
    # If there's an opponent piece in the middle, it's a capture
    if (mid_r, mid_c) in opp_set:
        # Capture the piece
        new_opp = opp_set - {(mid_r, mid_c)}
        new_my = (my_set - {from_square}) | {to_square}
        
        # Check for promotion to king
        is_king = (color == 'b' and to_square[0] == 0) or (color == 'w' and to_square[0] == 7)
        
        # Update king status: if it was a king, it remains a king
        if from_square in my_kings or is_king:
            # King promotion or already king
            pass
        return new_my, new_opp
    else:
        # Normal move
        new_my = (my_set - {from_square}) | {to_square}
        return new_my, opp_set  # Opponent state unchanged

def minimax(my_pieces, opp_pieces, depth, maximizing_player, color, dir_mult, start_time, alpha, beta):
    """Minimax with alpha-beta pruning."""
    if time.time() - start_time > 0.8:
        return evaluate_board(my_pieces, opp_pieces, color)
    
    if depth == 0:
        return evaluate_board(my_pieces, opp_pieces, color)
    
    is_king = lambda p: p in my_kings if maximizing_player else p in set(opp_kings)
    
    if maximizing_player:
        max_eval = float('-inf')
        capture_moves = get_all_capture_moves(my_pieces, opp_pieces, color, dir_mult)
        
        if capture_moves:
            move_list = []  # We'll evaluate capture sequences; just use the first level
            for move in capture_moves:
                if isinstance(move[0], tuple) and len(move) == 2:
                    move_list.append(move)
                else:
                    # It's a sequence; use the first move only for next state
                    move_list.append(move[0])
            moves = move_list
        else:
            moves = get_all_normal_moves(my_pieces, opp_pieces, color, dir_mult)
            
        for move in moves:
            if time.time() - start_time > 0.8:
                return max_eval
                
            new_my, new_opp = simulate_move(my_pieces, opp_pieces, move, color, dir_mult)
            eval_score = minimax(new_my, new_opp, depth - 1, False, color, dir_mult, start_time, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        # Opponent's turn (minimizing)
        # We need to reverse roles for opponent: their color is opposite
        opp_color = 'w' if color == 'b' else 'b'
        opp_dir_mult = -1 if opp_color == 'b' else 1  # since b moves down
        
        capture_moves = get_all_capture_moves(opp_pieces, my_pieces, opp_color, opp_dir_mult)
        
        if capture_moves:
            move_list = []
            for move in capture_moves:
                if isinstance(move[0], tuple) and len(move) == 2:
                    move_list.append(move)
                else:
                    move_list.append(move[0])
            moves = move_list
        else:
            moves = get_all_normal_moves(opp_pieces, my_pieces, opp_color, opp_dir_mult)
            
        for move in moves:
            if time.time() - start_time > 0.8:
                return min_eval
                
            new_opp, new_my = simulate_move(opp_pieces, my_pieces, move, opp_color, opp_dir_mult)
            eval_score = minimax(new_my, new_opp, depth - 1, True, color, dir_mult, start_time, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(my_pieces, opp_pieces, color) -> float:
    """
    Heuristic evaluation of the board.
    +10 for each regular piece, +20 for each king
    +bonus for controlling center and advanced positions
    -penalty for being vulnerable to capture
    """
    score = 0.0
    
    # Piece count score
    score += len(my_pieces) * 10
    score -= len(opp_pieces) * 10
    
    # King bonus
    my_kings_count = sum(1 for p in my_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7)))
    opp_kings_count = sum(1 for p in opp_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7)))
    
    # Actually use passed global or inferred from context
    # We don't have exact my_kings list, so infer: if piece is on opponent's back rank => king
    my_kings_inferred = [p for p in my_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7))]
    opp_kings_inferred = [p for p in opp_pieces if ((color == 'b' and p[0] == 0) or (color == 'w' and p[0] == 7))]
    
    score += len(my_kings_inferred) * 15
    score -= len(opp_kings_inferred) * 15
    
    # Mobility: count available normal moves
    # This is computationally expensive, so just approximate
    dir_mult = -1 if color == 'b' else 1
    
    my_mobility = len(get_all_normal_moves(my_pieces, opp_pieces, color, dir_mult)) * 0.5
    opp_mobility = len(get_all_normal_moves(opp_pieces, my_pieces, 'w' if color == 'b' else 'b', -dir_mult)) * 0.5
    
    score += my_mobility
    score -= opp_mobility
    
    # Position bonus: inner control and advancement
    for piece in my_pieces:
        row, col = piece
        # Center control (central 16 squares)
        center_bonus = 0
        if 2 <= row <= 5 and 2 <= col <= 5:
            center_bonus = 1.0
        # Advancement bonus (for black: row 0 is far, row 7 is back? Wait: (0,0) is bottom-left)
        # In our coord: row 0 is bottom, row 7 is top
        # Black (b) moves down -> towards row 0 (to reach opponent's row 7)
        # White (w) moves up -> towards row 7
        
        if color == 'b':  # wants to reach row 0 (opponent's side)
            advancement = row / 7.0  # 0.0 at bottom, 1.0 at top? Actually: row 0 is good for black!
            # Correction: row 0 is bottom, row 7 is top
            # For black: 0 is opponent's back rank -> goal
            # So row 0 is best for black
            advancement = (7 - row) / 7.0  # 0 at row 7 (bad), 1 at row 0 (good)
        else:  # white
            advancement = row / 7.0  # 0 at row 0 (bad), 1 at row 7 (good)
        
        score += advancement * 2.0 + center_bonus
    
    for piece in opp_pieces:
        row, col = piece
        if color == 'b':
            advancement = (7 - row) / 7.0
        else:
            advancement = row / 7.0
        score -= advancement * 2.0
        
        # Center bonus for opponent is bad
        if 2 <= row <= 5 and 2 <= col <= 5:
            score -= 1.0
    
    # Prevent crowding/edge traps: avoid being on edge unless kinged
    for piece in my_pieces:
        if piece[0] == 0 or piece[0] == 7 or piece[1] == 0 or piece[1] == 7:
            # Not a king on edge might be vulnerable
            if not ((color == 'b' and piece[0] == 0) or (color == 'w' and piece[0] == 7)):
                # It's not a king on the edge
                score -= 0.5
    
    return score

def evaluate_capture_sequences(capture_sequences, my_pieces, opp_pieces, color, dir_mult):
    """Choose the best capture sequence among multiple. Prioritize: most captures, promote to king, safety."""
    best_sequence = capture_sequences[0]
    best_score = -1e6
    
    for seq in capture_sequences:
        # For multi-jump sequences, we may have a list of moves; we only care about the entire chain result
        if isinstance(seq[0], tuple) and len(seq) == 2:
            # Single capture
            from_sq, to_sq = seq
            captured = 1
            promotes = (color == 'b' and to_sq[0] == 0) or (color == 'w' and to_sq[0] == 7)
            score = captured * 10 + (1 if promotes else 0) * 5
        else:
            # It's a sequence: list of moves
            captured = len(seq)
            # Check if the final position promotes
            last_move = seq[-1]
            to_sq = last_move[1]
            promotes = (color == 'b' and to_sq[0] == 0) or (color == 'w' and to_sq[0] == 7)
            score = captured * 10 + (1 if promotes else 0) * 5
        
        # Prefer king promotion
        if score > best_score:
            best_score = score
            best_sequence = seq
    
    # Return the very first move of the sequence for single jump, or return the full first step
    if isinstance(best_sequence[0], tuple) and len(best_sequence) == 2:
        return best_sequence
    else:
        # Return the first move of the sequence
        return best_sequence[0]
