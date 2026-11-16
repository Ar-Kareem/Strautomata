
import random

def on_board(r, c):
    """Check if (r, c) is within the board."""
    return 0 <= r <= 7 and 0 <= c <= 7

def get_piece_moves(r, c, is_king, color, my_pieces, opp_pieces):
    """
    Get all moves (regular and captures) for a piece at (r, c).
    Returns (moves, captures) where each is a list of ((fr, fc), (tr, tc)).
    """
    moves = []
    captures = []
    
    if is_king:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    elif color == 'b':  # Black moves downward (to lower row values)
        directions = [(-1, -1), (-1, 1)]
    else:  # White moves upward (to higher row values)
        directions = [(1, -1), (1, 1)]
    
    for dr, dc in directions:
        # Regular move
        nr, nc = r + dr, c + dc
        if on_board(nr, nc) and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
            moves.append(((r, c), (nr, nc)))
        
        # Capture move
        jr, jc = r + 2 * dr, c + 2 * dc
        if on_board(jr, jc) and (jr, jc) not in my_pieces and (jr, jc) not in opp_pieces:
            mr, mc = r + dr, c + dc
            if (mr, mc) in opp_pieces:
                captures.append(((r, c), (jr, jc)))
    
    return moves, captures

def get_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Get all legal moves, respecting the mandatory capture rule."""
    my_pieces = set(my_men) | set(my_kings)
    opp_pieces = set(opp_men) | set(opp_kings)
    
    all_moves = []
    all_captures = []
    
    for r, c in my_men:
        moves, captures = get_piece_moves(r, c, False, color, my_pieces, opp_pieces)
        all_moves.extend(moves)
        all_captures.extend(captures)
    
    for r, c in my_kings:
        moves, captures = get_piece_moves(r, c, True, color, my_pieces, opp_pieces)
        all_moves.extend(moves)
        all_captures.extend(captures)
    
    return all_captures if all_captures else all_moves

def apply_move(move, my_men, my_kings, opp_men, opp_kings, color):
    """Apply a move and return the new state."""
    (fr, fc), (tr, tc) = move
    
    new_my_men = list(my_men)
    new_my_kings = list(my_kings)
    new_opp_men = list(opp_men)
    new_opp_kings = list(opp_kings)
    
    is_king = (fr, fc) in my_kings
    
    if is_king:
        new_my_kings.remove((fr, fc))
    else:
        new_my_men.remove((fr, fc))
    
    promoted = False
    if not is_king:
        if (color == 'w' and tr == 7) or (color == 'b' and tr == 0):
            promoted = True
    
    if promoted:
        new_my_kings.append((tr, tc))
    elif is_king:
        new_my_kings.append((tr, tc))
    else:
        new_my_men.append((tr, tc))
    
    if abs(tr - fr) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        if (mr, mc) in new_opp_men:
            new_opp_men.remove((mr, mc))
        else:
            new_opp_kings.remove((mr, mc))
    
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

def evaluate(my_men, my_kings, opp_men, opp_kings):
    """Static position evaluation from my_pieces' perspective."""
    my_material = len(my_men) + 3 * len(my_kings)
    opp_material = len(opp_men) + 3 * len(opp_kings)
    return my_material - opp_material

def minimax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta):
    """Negamax search with alpha-beta pruning."""
    if depth == 0:
        return evaluate(my_men, my_kings, opp_men, opp_kings)
    
    moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not moves:
        return -1000
    
    best_score = float('-inf')
    for move in moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            move, my_men, my_kings, opp_men, opp_kings, color)
        opp_color = 'b' if color == 'w' else 'w'
        score = -minimax(new_opp_men, new_opp_kings, new_my_men, new_my_kings, 
                        opp_color, depth - 1, -beta, -alpha)
        best_score = max(best_score, score)
        alpha = max(alpha, score)
        if beta <= alpha:
            break
    return best_score

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """Return the best move for the current player."""
    moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not moves:
        return ((0, 0), (0, 0))
    
    best_move = moves[0]
    best_score = float('-inf')
    
    for move in moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            move, my_men, my_kings, opp_men, opp_kings, color)
        opp_color = 'b' if color == 'w' else 'w'
        score = -minimax(new_opp_men, new_opp_kings, new_my_men, new_my_kings, 
                        opp_color, 3, float('-inf'), float('inf'))
        score += random.random() * 0.05
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
