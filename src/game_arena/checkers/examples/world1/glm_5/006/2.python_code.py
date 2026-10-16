
import copy

# Constants for piece values and positions
MAN_VALUE = 100
KING_VALUE = 175
DEPTH = 4

# Directions: (row_delta, col_delta)
# White moves up (+1), Black moves down (-1)
# Kings move in all 4 directions

def get_directions(color, is_king):
    """Returns possible move directions for a piece."""
    if is_king:
        return [(1, -1), (1, 1), (-1, -1), (-1, 1)]
    if color == 'w':
        return [(1, -1), (1, 1)]
    else: # color == 'b'
        return [(-1, -1), (-1, 1)]

def apply_move(state, move, turn_color):
    """
    Applies a move to the state and returns a new state dictionary.
    state = {
        'w_men': set(...), 'w_kings': set(...),
        'b_men': set(...), 'b_kings': set(...)
    }
    """
    new_state = {
        'w_men': set(state['w_men']),
        'w_kings': set(state['w_kings']),
        'b_men': set(state['b_men']),
        'b_kings': set(state['b_kings'])
    }
    
    (fr, fc), (tr, tc) = move
    
    # Identify piece
    is_king = False
    if (fr, fc) in new_state[f'{turn_color}_kings']:
        is_king = True
        new_state[f'{turn_color}_kings'].remove((fr, fc))
    elif (fr, fc) in new_state[f'{turn_color}_men']:
        new_state[f'{turn_color}_men'].remove((fr, fc))
    else:
        # Should not happen if move generation is correct
        return new_state

    # Check for capture
    if abs(tr - fr) == 2:
        cap_r, cap_c = (fr + tr) // 2, (fc + tc) // 2
        opp_color = 'b' if turn_color == 'w' else 'w'
        if (cap_r, cap_c) in new_state[f'{opp_color}_men']:
            new_state[f'{opp_color}_men'].remove((cap_r, cap_c))
        elif (cap_r, cap_c) in new_state[f'{opp_color}_kings']:
            new_state[f'{opp_color}_kings'].remove((cap_r, cap_c))
    
    # Place piece at destination, check for promotion
    promotion_row = 7 if turn_color == 'w' else 0
    if not is_king and tr == promotion_row:
        new_state[f'{turn_color}_kings'].add((tr, tc))
    else:
        target_set = 'kings' if is_king else 'men'
        new_state[f'{turn_color}_{target_set}'].add((tr, tc))
        
    return new_state

def get_legal_moves(state, turn_color):
    """Generates all legal moves for the current player. Captures are mandatory."""
    moves = []
    captures = []
    
    my_men = state[f'{turn_color}_men']
    my_kings = state[f'{turn_color}_kings']
    opp_color = 'b' if turn_color == 'w' else 'w'
    
    opp_pieces = state[f'{opp_color}_men'] | state[f'{opp_color}_kings']
    all_pieces = state['w_men'] | state['w_kings'] | state['b_men'] | state['b_kings']
    
    # Check captures for men
    for r, c in my_men:
        dirs = get_directions(turn_color, False)
        # Men capture forward only in standard checkers
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            jr, jc = r + 2*dr, c + 2*dc
            if 0 <= jr < 8 and 0 <= jc < 8:
                if (nr, nc) in opp_pieces and (jr, jc) not in all_pieces:
                    captures.append(((r, c), (jr, jc)))
                    
    # Check captures for kings
    for r, c in my_kings:
        dirs = get_directions(turn_color, True)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            jr, jc = r + 2*dr, c + 2*dc
            if 0 <= jr < 8 and 0 <= jc < 8:
                if (nr, nc) in opp_pieces and (jr, jc) not in all_pieces:
                    captures.append(((r, c), (jr, jc)))
    
    if captures:
        return captures
    
    # If no captures, generate simple moves
    # Men simple moves
    for r, c in my_men:
        dirs = get_directions(turn_color, False)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
                    
    # Kings simple moves
    for r, c in my_kings:
        dirs = get_directions(turn_color, True)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
                    
    return moves

def evaluate(state, my_color):
    """Heuristic evaluation of the board state."""
    opp_color = 'b' if my_color == 'w' else 'w'
    
    my_men = len(state[f'{my_color}_men'])
    my_kings = len(state[f'{my_color}_kings'])
    opp_men = len(state[f'{opp_color}_men'])
    opp_kings = len(state[f'{opp_color}_kings'])
    
    score = 0
    
    # Material Score
    score += (my_men - opp_men) * MAN_VALUE
    score += (my_kings - opp_kings) * KING_VALUE
    
    # Positional Score
    # 1. Advancement (Men closer to promotion)
    promotion_row = 7 if my_color == 'w' else 0
    advancement_score = 0
    for r, c in state[f'{my_color}_men']:
        dist = abs(promotion_row - r)
        advancement_score += (7 - dist) * 2 # Closer is better
        
    # 2. Center Control (Columns 2,3,4,5 are better)
    center_score = 0
    for pieces in [state[f'{my_color}_men'], state[f'{my_color}_kings']]:
        for r, c in pieces:
            if 2 <= c <= 5:
                center_score += 5
                
    # 3. Back row protection (early game)
    back_row = 0 if my_color == 'w' else 7
    if my_men + my_kings > 10: # Early game heuristic
        for r, c in state[f'{my_color}_men']:
            if r == back_row:
                center_score += 3
    
    return score + advancement_score + center_score

def minimax(state, depth, alpha, beta, maximizing_player, my_color, turn_color):
    """Minimax with Alpha-Beta pruning."""
    moves = get_legal_moves(state, turn_color)
    
    if depth == 0 or not moves:
        return evaluate(state, my_color), None
    
    best_move = None
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_state = apply_move(state, move, turn_color)
            # Note: Checkers allows multi-jump. 
            # A simplified approach assumes the turn passes after one move in the search tree, 
            # but for strict adherence, we should check if the move was a capture and if more captures are available.
            # However, implementing full multi-jump logic in minimax adds complexity.
            # We assume the engine calls policy again for subsequent jumps.
            # So we switch turn.
            
            # Switching turn
            next_turn = 'b' if turn_color == 'w' else 'w'
            eval_score, _ = minimax(new_state, depth - 1, alpha, beta, False, my_color, next_turn)
            
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
            new_state = apply_move(state, move, turn_color)
            next_turn = 'b' if turn_color == 'w' else 'w'
            eval_score, _ = minimax(new_state, depth - 1, alpha, beta, True, my_color, next_turn)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Initial state setup
    state = {
        'w_men': set(my_men) if color == 'w' else set(opp_men),
        'w_kings': set(my_kings) if color == 'w' else set(opp_kings),
        'b_men': set(opp_men) if color == 'w' else set(my_men),
        'b_kings': set(opp_kings) if color == 'w' else set(my_kings)
    }
    
    # If we are black, the initial state dictionary keys for 'b' must contain our pieces.
    if color == 'b':
        state = {
            'w_men': set(opp_men),
            'w_kings': set(opp_kings),
            'b_men': set(my_men),
            'b_kings': set(my_kings)
        }

    # Determine legal moves
    legal_moves = get_legal_moves(state, color)
    
    if not legal_moves:
        # Should not happen in a valid game state if called correctly
        return ((0,0), (0,0))
    
    # If only one move available, return it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Run Minimax
    _, best_move = minimax(state, DEPTH, float('-inf'), float('inf'), True, color, color)
    
    return best_move if best_move else legal_moves[0]
