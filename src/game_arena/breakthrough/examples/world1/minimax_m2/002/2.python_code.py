
def get_piece_progress(pos, color):
    """Calculate the progress score for a piece based on its position and color."""
    r, c = pos
    if color == 'w':
        return r  # White pieces advance by increasing row
    else:
        return 7 - r  # Black pieces advance by decreasing row

def evaluate_board(me_set, opp_set, color):
    """Evaluate the board state from the current player's perspective."""
    score = 0
    for piece in me_set:
        r, c = piece
        if color == 'w':
            score += r  # White pieces contribute their row
        else:
            score += 7 - r  # Black pieces contribute (7 - row)
    for piece in opp_set:
        r, c = piece
        if color == 'w':
            score -= 7 - r  # Opponent black pieces are bad when close to row 0
        else:
            score -= r  # Opponent white pieces are bad when close to row 7
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return the best move for the current player."""
    me_set = set(me)
    opp_set = set(opp)
    moves = []
    
    for piece in me:
        r, c = piece
        dir = 1 if color == 'w' else -1  # Direction: white moves up, black moves down
        
        # Straight forward move
        new_r = r + dir
        new_c = c
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set and (new_r, new_c) not in opp_set:
                moves.append(((r, c), (new_r, new_c)))
        
        # Diagonal left move
        new_r = r + dir
        new_c = c - 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set:  # Cannot move onto own piece
                if (new_r, new_c) in opp_set:
                    moves.append(((r, c), (new_r, new_c)))  # Capture move
                else:
                    moves.append(((r, c), (new_r, new_c)))  # Regular move
        
        # Diagonal right move
        new_r = r + dir
        new_c = c + 1
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set:
                if (new_r, new_c) in opp_set:
                    moves.append(((r, c), (new_r, new_c)))
                else:
                    moves.append(((r, c), (new_r, new_c)))
    
    # If no moves are available, return None (should not happen in practice)
    if not moves:
        return None
    
    best_move = None
    best_score = -float('inf')
    best_progress = -float('inf')
    
    for move in moves:
        from_pos, to_pos = move
        new_me = set(me)
        new_me.discard(from_pos)
        new_me.add(to_pos)
        new_opp = set(opp)
        if to_pos in opp_set:
            new_opp.discard(to_pos)  # Remove captured piece
        
        score = evaluate_board(new_me, new_opp, color)
        progress = get_piece_progress(to_pos, color)
        
        if score > best_score:
            best_score = score
            best_move = move
            best_progress = progress
        elif score == best_score:
            if progress > best_progress:
                best_move = move
                best_progress = progress
    
    return best_move
