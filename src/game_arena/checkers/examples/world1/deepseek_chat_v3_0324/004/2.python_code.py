
import numpy as np
from typing import List, Tuple
import time

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    
    start_time = time.time()
    
    # Combine all pieces
    my_pieces = my_men + my_kings
    opp_pieces = opp_men + opp_kings
    all_pieces = my_pieces + opp_pieces
    
    # First check for capture moves
    capture_moves = []
    for piece in my_pieces:
        captures = find_captures(piece, my_pieces, opp_pieces, color, is_king=(piece in my_kings))
        for cap in captures:
            capture_moves.append((piece, cap))
    
    if capture_moves:
        # Select the best capture sequence
        best_capture = None
        best_score = -float('inf')
        
        for move in capture_moves:
            from_pos, to_pos = move
            temp_my_men = my_men.copy()
            temp_my_kings = my_kings.copy()
            temp_opp_men = opp_men.copy()
            temp_opp_kings = opp_kings.copy()
            
            # Simulate the move and capture
            score = evaluate_capture_move(from_pos, to_pos, temp_my_men, temp_my_kings, 
                                        temp_opp_men, temp_opp_kings, color)
            
            if score > best_score:
                best_score = score
                best_capture = move
        
        if best_capture:
            # Make sure to return before time runs out
            if time.time() - start_time < 0.95:
                return best_capture
    
    # If no captures, evaluate normal moves
    normal_moves = []
    for piece in my_pieces:
        moves = find_moves(piece, my_pieces, opp_pieces, color, is_king=(piece in my_kings))
        for move in moves:
            normal_moves.append((piece, move))
    
    if not normal_moves:
        # No legal moves (shouldn't happen as opponent must have made a move)
        return ((0,0), (0,0))  # fallback
    
    # Evaluate normal moves and select best one
    best_move = None
    best_score = -float('inf')
    
    for move in normal_moves:
        from_pos, to_pos = move
        score = evaluate_normal_move(from_pos, to_pos, my_men, my_kings, opp_men, opp_kings, color)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Make sure to return before time runs out
    return best_move if best_move else normal_moves[0]

def find_captures(piece, my_pieces, opp_pieces, color, is_king=False):
    captures = []
    row, col = piece
    directions = []
    
    if is_king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        if color == 'b':  # black moves down (lower rows)
            directions = [(-1, -1), (-1, 1)]
        else:  # white moves up (higher rows)
            directions = [(1, -1), (1, 1)]
    
    for dr, dc in directions:
        # Check for adjacent opponent piece
        jump_row = row + dr
        jump_col = col + dc
        if 0 <= jump_row < 8 and 0 <= jump_col < 8:
            if (jump_row, jump_col) in opp_pieces:
                # Check landing square
                land_row = row + 2*dr
                land_col = col + 2*dc
                if 0 <= land_row < 8 and 0 <= land_col < 8:
                    if (land_row, land_col) not in my_pieces and (land_row, land_col) not in opp_pieces:
                        captures.append((land_row, land_col))
    
    return captures

def find_moves(piece, my_pieces, opp_pieces, color, is_king=False):
    moves = []
    row, col = piece
    directions = []
    
    if is_king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        if color == 'b':  # black moves down (lower rows)
            directions = [(-1, -1), (-1, 1)]
        else:  # white moves up (higher rows)
            directions = [(1, -1), (1, 1)]
    
    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if (new_row, new_col) not in my_pieces and (new_row, new_col) not in opp_pieces:
                moves.append((new_row, new_col))
    
    return moves

def evaluate_capture_move(from_pos, to_pos, my_men, my_kings, opp_men, opp_kings, color):
    score = 0
    
    # Perform the capture
    row, col = from_pos
    to_row, to_col = to_pos
    
    if from_pos in my_men:
        my_men.remove(from_pos)
    else:
        my_kings.remove(from_pos)
    
    # Add to new position (check for promotion)
    if color == 'b' and to_row == 0:
        my_kings.append(to_pos)
        score += 2  # promotion bonus
    elif color == 'w' and to_row == 7:
        my_kings.append(to_pos)
        score += 2  # promotion bonus
    else:
        my_men.append(to_pos)
    
    # Remove captured piece
    jumped_row = (row + to_row) // 2
    jumped_col = (col + to_col) // 2
    if (jumped_row, jumped_col) in opp_men:
        opp_men.remove((jumped_row, jumped_col))
        score += 1
    else:
        opp_kings.remove((jumped_row, jumped_col))
        score += 1.5  # king is more valuable
    
    # Check for additional captures
    additional_captures = find_captures(to_pos, my_men + my_kings, opp_men + opp_kings, 
                                      color, is_king=(to_pos in my_kings))
    if additional_captures:
        score += 0.5  # bonus for potential additional captures
    
    # Evaluate board state
    my_pieces = my_men + my_kings
    opp_pieces = opp_men + opp_kings
    
    # Material difference
    material = len(my_pieces) - len(opp_pieces)
    score += material * 0.5
    
    # Central control bonus
    center_bonus = 0
    for (r, c) in my_pieces:
        if 2 <= r <= 5 and 2 <= c <= 5:
            center_bonus += 0.1
    score += center_bonus
    
    return score

def evaluate_normal_move(from_pos, to_pos, my_men, my_kings, opp_men, opp_kings, color):
    score = 0
    
    # Check for promotion
    if from_pos in my_men:
        if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
            score += 2
    
    # Prefer moving towards promotion
    if color == 'b':
        score += (7 - to_pos[0]) * 0.05  # black moves down (0 is promotion row)
    else:
        score += to_pos[0] * 0.05  # white moves up (7 is promotion row)
    
    # Bonus for central positions
    if 2 <= to_pos[0] <= 5 and 2 <= to_pos[1] <= 5:
        score += 0.1
    
    # Penalty for moving to edge (could be trapped)
    if to_pos[1] == 0 or to_pos[1] == 7:
        score -= 0.1
    
    return score
