
import sys

# Constants for evaluation
PIECE_VAL = 100
KING_VAL = 200  # Kings are significantly more valuable
ADVANCE_VAL = 5  # Bonus for advancing towards promotion
CENTER_VAL = 3   # Bonus for controlling center columns

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Main policy function that returns the best move for the current state.
    Uses Minimax with Alpha-Beta pruning.
    """
    # Convert lists to sets of tuples for efficient operations
    initial_state = (
        set(tuple(p) for p in my_men), 
        set(tuple(p) for p in my_kings), 
        set(tuple(p) for p in opp_men), 
        set(tuple(p) for p in opp_kings)
    )
    
    # Depth of the search tree (adjust based on time constraints/complexity)
    # Depth 5 is usually safe within 1 second for Checkers.
    search_depth = 5
    
    valid_moves = get_all_valid_moves(initial_state, color)
    
    # If no moves, return a default (should not happen in a valid game)
    if not valid_moves:
        return ((0, 0), (0, 0))

    # Optimization: If only one legal move, return it immediately
    if len(valid_moves) == 1:
        return (valid_moves[0][0], valid_moves[0][-1])

    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Iterate through moves to find the best one using Minimax
    for move in valid_moves:
        new_state = apply_move(initial_state, move, color)
        # Start Minimax recursion (minimizing opponent's turn)
        score = minimax(new_state, search_depth - 1, alpha, beta, False, color, get_opponent_color(color))
        
        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, score)
        
    if best_move:
        return (best_move[0], best_move[-1])
    else:
        # Fallback
        return (valid_moves[0][0], valid_moves[0][-1])

def minimax(state, depth, alpha, beta, maximizing_player, my_color, current_turn_color):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Terminal condition: depth limit reached
    if depth == 0:
        return evaluate(state, my_color)
    
    moves = get_all_valid_moves(state, current_turn_color)
    
    # Terminal condition: no moves left (loss)
    if not moves:
        return -float('inf') if maximizing_player else float('inf')

    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            new_state = apply_move(state, move, current_turn_color)
            eval_val = minimax(new_state, depth - 1, alpha, beta, False, my_color, get_opponent_color(current_turn_color))
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_state = apply_move(state, move, current_turn_color)
            eval_val = minimax(new_state, depth - 1, alpha, beta, True, my_color, get_opponent_color(current_turn_color))
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def evaluate(state, my_color):
    """
    Evaluates the board state.
    Higher score is better for 'my_color'.
    """
    my_men, my_kings, opp_men, opp_kings = state
    
    # 1. Material Score
    score = 0
    score += len(my_men) * PIECE_VAL
    score += len(my_kings) * KING_VAL
    score -= len(opp_men) * PIECE_VAL
    score -= len(opp_kings) * KING_VAL
    
    # 2. Positional Score: Advancement (Men closer to promotion)
    for r, c in my_men:
        if my_color == 'w':
            score += r * ADVANCE_VAL
        else:
            score += (7 - r) * ADVANCE_VAL
            
    for r, c in opp_men:
        if my_color == 'w': # Opponent is 'b', moving down
            score -= (7 - r) * ADVANCE_VAL
        else: # Opponent is 'w', moving up
            score -= r * ADVANCE_VAL
            
    # 3. Center Control (Columns 2, 3, 4, 5)
    for r, c in my_men | my_kings:
        if 2 <= c <= 5:
            score += CENTER_VAL
    for r, c in opp_men | opp_kings:
        if 2 <= c <= 5:
            score -= CENTER_VAL
            
    return score

def get_opponent_color(color):
    return 'w' if color == 'b' else 'b'

def apply_move(state, move, color):
    """
    Applies a move (or sequence of jumps) to the state.
    Returns the new state.
    """
    my_men = set(state[0])
    my_kings = set(state[1])
    opp_men = set(state[2])
    opp_kings = set(state[3])
    
    start = move[0]
    end = move[-1]
    
    is_king = start in my_kings
    
    # Remove piece from start
    if is_king:
        my_kings.remove(start)
    else:
        my_men.remove(start)
        
    # Handle captures (intermediate jumps)
    for i in range(len(move) - 1):
        r1, c1 = move[i]
        r2, c2 = move[i+1]
        cap_r = (r1 + r2) // 2
        cap_c = (c1 + c2) // 2
        
        if (cap_r, cap_c) in opp_men: opp_men.remove((cap_r, cap_c))
        elif (cap_r, cap_c) in opp_kings: opp_kings.remove((cap_r, cap_c))
            
    # Add piece to destination (check for promotion)
    promotion = False
    if not is_king:
        if (color == 'w' and end[0] == 7) or (color == 'b' and end[0] == 0):
            promotion = True
            
    if is_king or promotion:
        my_kings.add(end)
    else:
        my_men.add(end)
        
    return (my_men, my_kings, opp_men, opp_kings)

def get_all_valid_moves(state, color):
    """
    Generates all valid moves. Captures are mandatory.
    """
    my_men, my_kings, opp_men, opp_kings = state
    all_pieces = my_men | my_kings | opp_men | opp_kings
    opp_pieces = opp_men | opp_kings
    
    captures = []
    
    # Check captures for Men
    for piece in my_men:
        captures.extend(get_piece_captures(piece, False, all_pieces, opp_pieces, color))
    
    # Check captures for Kings
    for piece in my_kings:
        captures.extend(get_piece_captures(piece, True, all_pieces, opp_pieces, color))
        
    if captures:
        return captures
        
    # No captures, generate simple moves
    moves = []
    for piece in my_men:
        moves.extend(get_simple_moves(piece, False, all_pieces, color))
    for piece in my_kings:
        moves.extend(get_simple_moves(piece, True, all_pieces, color))
        
    return moves

def get_simple_moves(pos, is_king, all_pieces, color):
    r, c = pos
    moves = []
    directions = []
    
    if color == 'w':
        directions.append((1, -1))
        directions.append((1, 1))
        if is_king:
            directions.append((-1, -1))
            directions.append((-1, 1))
    else: # 'b'
        directions.append((-1, -1))
        directions.append((-1, 1))
        if is_king:
            directions.append((1, -1))
            directions.append((1, 1))
            
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if (nr, nc) not in all_pieces:
                moves.append([(r, c), (nr, nc)])
    return moves

def get_piece_captures(start_pos, is_king, all_pieces_initial, opp_pieces_initial, color):
    """
    Finds all capture sequences (multi-jumps) for a specific piece.
    Uses a stack for DFS to find all paths.
    Handles promotion logic (turn ends upon promotion).
    """
    paths = []
    # Stack element: (current_pos, occupied_squares, opponent_squares, path_history)
    stack = [(start_pos, set(all_pieces_initial), set(opp_pieces_initial), [start_pos])]
    
    while stack:
        pos, occupied, opponents, path = stack.pop()
        
        r, c = pos
        found_jump = False
        
        # Determine movement directions
        dirs = []
        if is_king:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'w': dirs = [(1, -1), (1, 1)]
            else: dirs = [(-1, -1), (-1, 1)]
            
        for dr, dc in dirs:
            cap_r, cap_c = r + dr, c + dc
            lan_r, lan_c = r + 2*dr, c + 2*dc
            
            if 0 <= lan_r < 8 and 0 <= lan_c < 8:
                # Check if there is an opponent to jump over
                if (cap_r, cap_c) in opponents:
                    # Check if landing square is empty
                    if (lan_r, lan_c) not in occupied:
                        found_jump = True
                        
                        # Create new state for this branch
                        new_occupied = set(occupied)
                        new_occupied.remove((cap_r, cap_c)) # Remove captured piece
                        new_occupied.remove(pos)            # Move piece from current
                        new_occupied.add((lan_r, lan_c))    # Move piece to landing
                        
                        new_opponents = set(opponents)
                        new_opponents.remove((cap_r, cap_c))
                        
                        new_path = path + [(lan_r, lan_c)]
                        
                        # Check for promotion
                        # Standard rule: Turn ends immediately upon promotion
                        promoted = False
                        if not is_king:
                            if (color == 'w' and lan_r == 7) or (color == 'b' and lan_r == 0):
                                promoted = True
                        
                        if promoted:
                            paths.append(new_path)
                        else:
                            # Continue searching for jumps from the new position
                            stack.append(((lan_r, lan_c), new_occupied, new_opponents, new_path))
                            
        # If we finished processing a node and found no further jumps, record path if it's a capture sequence
        if not found_jump and len(path) > 1:
            paths.append(path)
            
    return paths
