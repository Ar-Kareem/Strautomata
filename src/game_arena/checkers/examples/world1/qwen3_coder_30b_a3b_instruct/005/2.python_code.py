
import numpy as np
from typing import List, Tuple, Set, Dict
import time

# Constants
BOARD_SIZE = 8
EMPTY = 0
BLACK_MAN = 1
WHITE_MAN = 2
BLACK_KING = 3
WHITE_KING = 4

# Direction vectors for regular pieces (row_delta, col_delta)
BLACK_DIRECTIONS = [(-1, -1), (-1, 1)]  # Up-left, Up-right
WHITE_DIRECTIONS = [(1, -1), (1, 1)]    # Down-left, Down-right

# King directions (both directions)
KING_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

# Precomputed dark squares (valid playable positions)
DARK_SQUARES = set()
for row in range(BOARD_SIZE):
    for col in range(BOARD_SIZE):
        if (row + col) % 2 == 1:  # Dark squares for standard checkerboard
            DARK_SQUARES.add((row, col))

def is_valid_position(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def get_piece_type(row, col, my_men, my_kings, opp_men, opp_kings):
    """Get the piece type at a position"""
    pos = (row, col)
    if pos in my_men:
        return BLACK_MAN if pos[0] < 4 else WHITE_MAN
    elif pos in my_kings:
        return BLACK_KING if pos[0] < 4 else WHITE_KING
    elif pos in opp_men:
        return BLACK_MAN if pos[0] < 4 else WHITE_MAN
    elif pos in opp_kings:
        return BLACK_KING if pos[0] < 4 else WHITE_KING
    return EMPTY

def get_capturing_moves(from_row, from_col, my_men, my_kings, opp_men, opp_kings, color):
    """Generate all capturing moves from a position"""
    moves = []
    piece = get_piece_type(from_row, from_col, my_men, my_kings, opp_men, opp_kings)
    
    if piece == EMPTY:
        return []
        
    # Determine directions based on piece type and color
    directions = []
    if piece in (BLACK_MAN, BLACK_KING):
        if piece == BLACK_MAN:
            directions = BLACK_DIRECTIONS
        else:
            directions = KING_DIRECTIONS
    elif piece in (WHITE_MAN, WHITE_KING):
        if piece == WHITE_MAN:
            directions = WHITE_DIRECTIONS
        else:
            directions = KING_DIRECTIONS
            
    for drow, dcol in directions:
        # Check for capture in this direction
        cap_row, cap_col = from_row + 2 * drow, from_col + 2 * dcol
        jump_row, jump_col = from_row + drow, from_col + dcol
        
        # Verify jump position is valid and contains opponent piece
        if is_valid_position(cap_row, cap_col) and (cap_row, cap_col) not in my_men and (cap_row, cap_col) not in my_kings:
            if is_valid_position(jump_row, jump_col):
                # Check if there's an opponent piece to jump over
                jump_pos = (jump_row, jump_col)
                if jump_pos in opp_men or jump_pos in opp_kings:
                    # Finally verify capture square is empty
                    if cap_row in range(BOARD_SIZE) and cap_col in range(BOARD_SIZE):
                        cap_pos = (cap_row, cap_col)
                        if cap_pos not in my_men and cap_pos not in my_kings and cap_pos not in opp_men and cap_pos not in opp_kings:
                            moves.append(((from_row, from_col), (cap_row, cap_col)))
    
    return moves

def get_all_captures(my_men, my_kings, opp_men, opp_kings, color):
    """Get all capture moves for the current player"""
    captures = []
    for row, col in my_men:
        captures.extend(get_capturing_moves(row, col, my_men, my_kings, opp_men, opp_kings, color))
    for row, col in my_kings:
        captures.extend(get_capturing_moves(row, col, my_men, my_kings, opp_men, opp_kings, color))
    return captures

def get_regular_moves(from_row, from_col, my_men, my_kings, opp_men, opp_kings, color):
    """Generate all regular moves (non-capture) from a position"""
    moves = []
    piece = get_piece_type(from_row, from_col, my_men, my_kings, opp_men, opp_kings)
    
    if piece == EMPTY:
        return []
        
    # Determine directions based on piece type and color
    directions = []
    if piece in (BLACK_MAN, BLACK_KING):
        if piece == BLACK_MAN:
            directions = BLACK_DIRECTIONS
        else:
            directions = KING_DIRECTIONS
    elif piece in (WHITE_MAN, WHITE_KING):
        if piece == WHITE_MAN:
            directions = WHITE_DIRECTIONS
        else:
            directions = KING_DIRECTIONS
            
    for drow, dcol in directions:
        to_row, to_col = from_row + drow, from_col + dcol
        
        # Check that destination is valid and empty
        if is_valid_position(to_row, to_col):
            dest_pos = (to_row, to_col)
            if (dest_pos not in my_men and dest_pos not in my_kings and 
                dest_pos not in opp_men and dest_pos not in opp_kings):
                moves.append(((from_row, from_col), (to_row, to_col)))
                
    return moves

def get_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Get all legal moves (captures have priority)"""
    # First check for captures
    captures = get_all_captures(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        return captures
    
    # If no captures, generate regular moves
    moves = []
    for row, col in my_men:
        moves.extend(get_regular_moves(row, col, my_men, my_kings, opp_men, opp_kings, color))
    for row, col in my_kings:
        moves.extend(get_regular_moves(row, col, my_men, my_kings, opp_men, opp_kings, color))
    
    return moves

def calculate_mobility_score(my_men, my_kings, opp_men, opp_kings, color):
    """Calculate mobility advantage"""
    my_moves = len(get_all_moves(my_men, my_kings, opp_men, opp_kings, color))
    opp_moves = len(get_all_moves(opp_men, opp_kings, my_men, my_kings, 'b' if color == 'w' else 'w'))
    return my_moves - opp_moves

def calculate_king_advantage(my_men, my_kings, opp_men, opp_kings, color):
    """Calculate king advantage"""
    my_king_count = len(my_kings)
    opp_king_count = len(opp_kings)
    return my_king_count - opp_king_count

def calculate_center_control(my_men, my_kings, opp_men, opp_kings, color):
    """Calculate center control (center squares are more valuable)"""
    center_squares = [(3,3), (3,4), (4,3), (4,4)]
    
    my_center = 0
    opp_center = 0
    
    for row, col in my_men:
        if (row, col) in center_squares:
            my_center += 1
            
    for row, col in my_kings:
        if (row, col) in center_squares:
            my_center += 1
            
    for row, col in opp_men:
        if (row, col) in center_squares:
            opp_center += 1
            
    for row, col in opp_kings:
        if (row, col) in center_squares:
            opp_center += 1
            
    return my_center - opp_center

def evaluate_board(my_men, my_kings, opp_men, opp_kings, color):
    """Evaluate a board position"""
    # Piece count advantage
    my_piece_count = len(my_men) + len(my_kings) * 2  # Kings worth more
    opp_piece_count = len(opp_men) + len(opp_kings) * 2
    
    piece_advantage = my_piece_count - opp_piece_count
    
    # King advantage
    king_advantage = calculate_king_advantage(my_men, my_kings, opp_men, opp_kings, color)
    
    # Mobility
    mobility_score = calculate_mobility_score(my_men, my_kings, opp_men, opp_kings, color)
    
    # Center control
    center_control = calculate_center_control(my_men, my_kings, opp_men, opp_kings, color)
    
    # Simple positional score
    positional_score = 0
    # Slight preference for advancing kings
    for row, col in my_kings:
        if color == 'b':
            positional_score += row  # Prefer lower rows
        else:
            positional_score += (BOARD_SIZE - 1 - row)  # Prefer higher rows
            
    # Slight preference for advancing men
    for row, col in my_men:
        if color == 'b':
            positional_score += row  # Prefer lower rows
        else:
            positional_score += (BOARD_SIZE - 1 - row)  # Prefer higher rows
    
    # Weighted evaluation
    score = (piece_advantage * 10 +
             king_advantage * 5 +
             mobility_score * 2 +
             center_control * 3 +
             positional_score * 0.1)
    
    return score

def is_capture_move(move):
    """Check if move is a capture"""
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    return abs(from_row - to_row) == 2

def minimax(board_state, depth, alpha, beta, maximizing_player, color, move_stack):
    """Minimax with alpha-beta pruning"""
    my_men, my_kings, opp_men, opp_kings = board_state
    
    # Limit depth to avoid timeout
    if depth <= 0:
        return evaluate_board(my_men, my_kings, opp_men, opp_kings, color)
    
    # Check if terminal state (game over)
    if not my_men and not my_kings:
        return float('-inf') if maximizing_player else float('inf')  # Loss for current player
    if not opp_men and not opp_kings:
        return float('inf') if maximizing_player else float('-inf')  # Win for current player
    
    # Get all moves for current player
    possible_moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not possible_moves:
        return float('-inf') if maximizing_player else float('inf')  # No moves, loss
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in possible_moves:
            # Make the move
            new_board_state = make_move(board_state, move, color)
            evaluation = minimax(new_board_state, depth - 1, alpha, beta, False, color, move_stack + [move])
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return max_eval
    else:
        min_eval = float('inf')
        for move in possible_moves:
            # Make the move
            new_board_state = make_move(board_state, move, color)
            evaluation = minimax(new_board_state, depth - 1, alpha, beta, True, color, move_stack + [move])
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return min_eval

def make_move(board_state, move, color):
    """Make a move and return the new board state"""
    my_men, my_kings, opp_men, opp_kings = board_state
    from_row, from_col = move[0]
    to_row, to_col = move[1]
    
    # Create deep copies
    new_my_men = [pos for pos in my_men]
    new_my_kings = [pos for pos in my_kings]
    new_opp_men = [pos for pos in opp_men]
    new_opp_kings = [pos for pos in opp_kings]
    
    # Handle capture
    if abs(from_row - to_row) == 2:
        jump_row = (from_row + to_row) // 2
        jump_col = (from_col + to_col) // 2
        jumped_pos = (jump_row, jump_col)
        
        # Remove captured piece
        if jumped_pos in new_opp_men:
            new_opp_men.remove(jumped_pos)
        elif jumped_pos in new_opp_kings:
            new_opp_kings.remove(jumped_pos)
    
    # Remove from origin
    origin_pos = (from_row, from_col)
    if origin_pos in new_my_men:
        new_my_men.remove(origin_pos)
    elif origin_pos in new_my_kings:
        new_my_kings.remove(origin_pos)
    
    # Add to destination
    dest_pos = (to_row, to_col)
    piece_type = get_piece_type(from_row, from_col, my_men, my_kings, opp_men, opp_kings)
    
    if piece_type == BLACK_MAN:
        if to_row == 0:
            new_my_kings.append(dest_pos)
        else:
            new_my_men.append(dest_pos)
    elif piece_type == WHITE_MAN:
        if to_row == 7:
            new_my_kings.append(dest_pos)
        else:
            new_my_men.append(dest_pos)
    elif piece_type == BLACK_KING or piece_type == WHITE_KING:
        new_my_kings.append(dest_pos)
        
    return (new_my_men, new_my_kings, new_opp_men, new_opp_kings)

# Simple iterative deepening strategy
def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Check if there are any available moves
    all_moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    # If no moves available, return any move to avoid error
    if not all_moves:
        return (0,0), (1,1)
    
    # Sort captures first - they are mandatory
    captures = [move for move in all_moves if is_capture_move(move)]
    
    if captures:
        # Always take a capture if available
        return captures[0]
    else:
        # If no captures, prioritize moves that get closer to becoming kings
        priority_moves = []
        for move in all_moves:
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            
            # Prefer moves that advance toward promoting to king
            advance_score = 0
            if color == 'b' and to_row < from_row:
                advance_score = 1  # Moving up (toward black king row)
            elif color == 'w' and to_row > from_row:
                advance_score = 1  # Moving down (toward white king row)
                
            # Prefer center moves
            center_score = 0
            if 2 <= to_row <= 5 and 2 <= to_col <= 5:
                center_score = 1
                
            # Prefer moves that put pieces on higher rows (toward king promotion)
            row_score = 1 if to_row > from_row else 0
            
            priority = advance_score + center_score + row_score
            
            priority_moves.append((priority, move))
            
        # Sort by priority and return the best
        priority_moves.sort(key=lambda x: x[0], reverse=True)
        return priority_moves[0][1]

