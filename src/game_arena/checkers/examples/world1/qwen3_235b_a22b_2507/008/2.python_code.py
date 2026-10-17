
import numpy as np
from typing import List, Tuple, Optional, Set

# Define board size
ROWS, COLS = 8, 8

# Direction vectors: for black (downward), white (upward), kings can move in both
def get_directions(piece: str, color: str):
    if piece == 'king':
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    elif color == 'b':
        return [(1, -1), (1, 1)]  # Black moves "up" the board (row decreases in our coord)
    else:
        return [(-1, -1), (-1, 1)]  # White moves "down" (row increases)

# Check if a square is within the board and on a dark square
def is_valid_dark_square(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS and (r + c) % 2 == 1

# Get all possible moves from a piece at (r, c)
def get_moves_from_piece(r: int, c: int, my_men: List[Tuple[int, int]], 
                        my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], 
                        opp_kings: List[Tuple[int, int]], color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]]:
    moves = []
    is_king = (r, c) in my_kings
    directions = get_directions('king' if is_king else 'man', color)
    opponent_pieces = opp_men + opp_kings
    my_pieces = my_men + my_kings
    
    for dr, dc in directions:
        nr1, nc1 = r + dr, c + dc
        if not is_valid_dark_square(nr1, nc1):
            continue
        
        # Regular move (non-capture)
        if (nr1, nc1) not in my_pieces and (nr1, nc1) not in opponent_pieces:
            moves.append(((r, c), (nr1, nc1), []))  # no captured pieces
        
        # Capture move
        elif (nr1, nc1) in opponent_pieces:
            nr2, nc2 = r + 2*dr, c + 2*dc
            if is_valid_dark_square(nr2, nc2) and (nr2, nc2) not in my_pieces and (nr2, nc2) not in opponent_pieces:
                captured = [(nr1, nc1)]
                moves.append(((r, c), (nr2, nc2), captured))
                
    # Further captures (multi-jump for kings and after capture)
    all_jumps = []
    for move in moves:
        if move[2]:  # It's a capture
            all_jumps.append(move)
    
    # Recursively expand jumps
    def expand_jumps(start, current, path, captures):
        r, c = current
        is_king_now = is_king or (r, c) in my_kings or abs(r - start[0]) >= 2  # promoted
        piece_type = 'king' if is_king_now else ('king' if (r, c) in my_kings else 'man')
        directions = get_directions(piece_type, color)
        has_further_jump = False
        for dr, dc in directions:
            nr1, nc1 = r + dr, c + dc
            if not is_valid_dark_square(nr1, nc1):
                continue
            if (nr1, nc1) in opponent_pieces and (nr1, nc1) not in captures:
                nr2, nc2 = r + 2*dr, c + 2*dc
                if is_valid_dark_square(nr2, nc2) and (nr2, nc2) not in my_pieces and (nr2, nc2) not in opponent_pieces:
                    new_captures = captures + [(nr1, nc1)]
                    new_pos = (nr2, nc2)
                    # Promote to king?
                    if not is_king_now and ((color == 'b' and nr2 == 7) or (color == 'w' and nr2 == 0)):
                        new_pos = (nr2, nc2)
                    has_further_jump = True
                    expand_jumps(start, new_pos, path + [(start, new_pos, new_captures)], new_captures)
        if not has_further_jump:
            path.append((start, current, captures))
    
    final_jumps = []
    for move in all_jumps:
        path = []
        expand_jumps(move[0], move[1], path, move[2])
        final_jumps.extend(path)
    
    # Combine non-captures and multi-jumps
    if final_jumps:
        return final_jumps
    else:
        return [m for m in moves if not m[2]]  # no capture moves

# Generate all legal moves for current player
def get_all_legal_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
                        opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
                        color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]]:
    all_moves = []
    my_pieces = my_men + my_kings
    for piece in my_pieces:
        piece_moves = get_moves_from_piece(piece[0], piece[1], my_men, my_kings, opp_men, opp_kings, color)
        all_moves.extend(piece_moves)
    
    # If any capture move exists, only return captures
    capture_moves = [m for m in all_moves if m[2]]
    if capture_moves:
        return capture_moves
    return all_moves

# Apply a move to the board state
def apply_move(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
               opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
               move: Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]], 
               color: str) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    fr, fc = move[0]
    tr, tc = move[1]
    captures = move[2]
    
    new_my_men = [p for p in my_men if p != (fr, fc)]
    new_my_kings = [p for p in my_kings if p != (fr, fc)]
    
    new_opp_men = [p for p in opp_men]
    new_opp_kings = [p for p in opp_kings]
    
    # Promote if reaching last rank
    is_king = (fr, fc) in my_kings
    if not is_king:
        if (color == 'b' and tr == 7) or (color == 'w' and tr == 0):
            new_my_kings.append((tr, tc))
        else:
            new_my_men.append((tr, tc))
    else:
        new_my_kings.append((tr, tc))
    
    # Remove captured pieces
    for cr, cc in captures:
        if (cr, cc) in new_opp_men:
            new_opp_men.remove((cr, cc))
        elif (cr, cc) in new_opp_kings:
            new_opp_kings.remove((cr, cc))
    
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

# Evaluate board state
def evaluate(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
             opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
             color: str) -> float:
    score = 0.0
    
    # Piece values
    MAN_VALUE = 1.0
    KING_VALUE = 1.5
    
    # Positional weights: favor center and advancement
    center_weight = np.array([
        [0, 0.1, 0.2, 0.3, 0.3, 0.2, 0.1, 0],
        [0, 0.2, 0.3, 0.4, 0.4, 0.3, 0.2, 0],
        [0, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0],
        [0, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0],
        [0, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0],
        [0, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0],
        [0, 0.2, 0.3, 0.4, 0.4, 0.3, 0.2, 0],
        [0, 0.1, 0.2, 0.3, 0.3, 0.2, 0.1, 0]
    ])
    
    # For black: higher rows are better
    # For white: lower rows are better
    row_weight_black = np.array([[i/7 for _ in range(8)] for i in range(8)])
    row_weight_white = np.array([[(7-i)/7 for _ in range(8)] for i in range(8)])
    
    for r, c in my_men:
        score += MAN_VALUE
        score += center_weight[r][c] * 0.1
        if color == 'b':
            score += row_weight_black[r][c] * 0.1
        else:
            score += row_weight_white[r][c] * 0.1
    
    for r, c in my_kings:
        score += KING_VALUE
        score += center_weight[r][c] * 0.1
    
    for r, c in opp_men:
        score -= MAN_VALUE
        if color == 'b':
            score -= row_weight_white[r][c] * 0.1  # Opponent's advancement
        else:
            score -= row_weight_black[r][c] * 0.1
        score -= center_weight[r][c] * 0.1
    
    for r, c in opp_kings:
        score -= KING_VALUE
        score -= center_weight[r][c] * 0.1
    
    return score

# Quiescence search to handle unstable positions
def quiescence(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
               opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
               color: str, alpha: float, beta: float) -> float:
    stand_pat = evaluate(my_men, my_kings, opp_men, opp_kings, color)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Only consider capture moves in quiescence
    all_moves = get_all_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    capture_moves = [m for m in all_moves if m[2]]
    
    if not capture_moves:
        return stand_pat

    for move in capture_moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, move, color)
        opp_color = 'w' if color == 'b' else 'b'
        score = -quiescence(new_opp_men, new_opp_kings, new_my_men, new_my_kings,
                            opp_color, -beta, -alpha)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

# Minimax with alpha-beta pruning
def minimax(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
            opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
            color: str, depth: int, alpha: float, beta: float, 
            maximizing: bool) -> float:
    if depth == 0:
        return quiescence(my_men, my_kings, opp_men, opp_kings, color, alpha, beta)
    
    all_moves = get_all_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not all_moves:
        return -1000 if maximizing else 1000
    
    # Move ordering: captures first
    all_moves.sort(key=lambda m: len(m[2]), reverse=True)
    
    best_value = -np.inf if maximizing else np.inf
    for move in all_moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, move, color)
        opp_color = 'w' if color == 'b' else 'b'
        value = minimax(new_opp_men, new_opp_kings, new_my_men, new_my_kings,
                        opp_color, depth - 1, alpha, beta, not maximizing)
        if maximizing:
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if alpha >= beta:
                break
        else:
            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
    return best_value

# Main policy function
def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Get all legal moves
    legal_moves = get_all_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not legal_moves:
        # Fallback: should not happen if game is over, but return something
        piece = my_men[0] if my_men else my_kings[0]
        return (piece[0], piece[1]), (piece[0], piece[1])  # same square
    
    # If only one move, return it
    if len(legal_moves) == 1:
        return legal_moves[0][0], legal_moves[0][1]
    
    # Sort moves: captures first
    legal_moves.sort(key=lambda m: len(m[2]), reverse=True)
    
    # Choose depth based on number of pieces to stay under 1 second
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if total_pieces > 16:
        max_depth = 4
    elif total_pieces > 10:
        max_depth = 5
    else:
        max_depth = 6
    
    best_move = legal_moves[0]
    best_value = -np.inf
    
    for move in legal_moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, move, color)
        opp_color = 'w' if color == 'b' else 'b'
        value = minimax(new_opp_men, new_opp_kings, new_my_men, new_my_kings,
                        opp_color, max_depth - 1, -np.inf, np.inf, False)
        if value > best_value:
            best_value = value
            best_move = move
    
    # Return the first two elements: from and to
    return best_move[0], best_move[1]
