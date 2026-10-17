
import numpy as np
import random
import time

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_possible_moves():
        moves = []
        for row in range(5):
            for col in range(5):
                if row < 4 and horizontal[row, col] == 0:  # Horizontal edge
                    moves.append((row, col, 'H'))
                if col < 4 and vertical[row, col] == 0:  # Vertical edge
                    moves.append((row, col, 'V'))
        return moves

    def is_box_complete(row, col, new_horizontal, new_vertical):
        # Check if box at (row, col) is complete
        if (row >= 4 or col >= 4):
            return False
        return (new_horizontal[row, col] != 0 and 
                new_horizontal[row+1, col] != 0 and 
                new_vertical[row, col] != 0 and 
                new_vertical[row, col+1] != 0)

    def get_new_state(row, col, direction, h_state, v_state, c_state, player):
        new_h = h_state.copy()
        new_v = v_state.copy()
        new_c = c_state.copy()
        if direction == 'H':
            new_h[row, col] = player
        else:  # V
            new_v[row, col] = player

        # Check if any boxes are completed by this move
        completed_boxes = 0
        if direction == 'H':
            # Can complete boxes above and below
            if row > 0 and is_box_complete(row-1, col, new_h, new_v):
                new_c[row-1, col] = player
                completed_boxes += 1
            if row < 4 and is_box_complete(row, col, new_h, new_v):
                new_c[row, col] = player
                completed_boxes += 1
        else:  # V
            # Can complete boxes to left and right
            if col > 0 and is_box_complete(row, col-1, new_h, new_v):
                new_c[row, col-1] = player
                completed_boxes += 1
            if col < 4 and is_box_complete(row, col, new_h, new_v):
                new_c[row, col] = player
                completed_boxes += 1

        return new_h, new_v, new_c, completed_boxes

    def evaluate_state(h_state, v_state, c_state, player):
        # Simple heuristic: count player's boxes vs opponent's boxes
        player_boxes = np.sum(c_state == player)
        opponent_boxes = np.sum(c_state == -player)
        return player_boxes - opponent_boxes

    def minimax(h_state, v_state, c_state, player, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_state(h_state, v_state, c_state, player), None

        possible_moves = get_possible_moves()

        # Prune by avoiding moves that create a 3-side box opportunity for opponent
        moves_without_threesides = []
        for move in possible_moves:
            row, col, direction = move
            new_h, new_v, dummy_c, dummy_boxes = get_new_state(row, col, direction, h_state, v_state, c_state, player)
            # Check if this move could create a box with 3 sides for the opponent
            if direction == 'H':
                # For H edge, check boxes above and below
                box_above = (row > 0 and new_h[row-1, col] and new_v[row-1, col] and new_v[row-1, col+1])
                box_below = (row < 4 and new_h[row+1, col] and new_v[row, col] and new_v[row, col+1])
                if box_above or box_below:
                    # Potential 3 sides, avoid if possible
                    moves_without_threesides.append(move)
            else:  # V
                # For V edge, check boxes left and right  
                box_left = (col > 0 and new_v[row, col-1] and new_h[row, col-1] and new_h[row+1, col-1])
                box_right = (col < 4 and new_v[row, col+1] and new_h[row, col+1] and new_h[row+1, col+1])
                if box_left or box_right:
                    moves_without_threesides.append(move)

        if moves_without_threesides:
            possible_moves = moves_without_threesides

        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            for move in possible_moves:
                row, col, direction = move
                new_h, new_v, new_c, boxes = get_new_state(row, col, direction, h_state, v_state, c_state, player)
                if boxes > 0:
                    # Player continues playing, maximize the same player 
                    eval_score, _ = minimax(new_h, new_v, new_c, player, depth-1, alpha, beta, True)
                else:
                    # Switch to opponent
                    eval_score, _ = minimax(new_h, new_v, new_c, -player, depth-1, alpha, beta, False)
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
            for move in possible_moves:
                row, col, direction = move
                new_h, new_v, new_c, boxes = get_new_state(row, col, direction, h_state, v_state, c_state, player)
                if boxes > 0:
                    # Opponent continues, same min player
                    eval_score, _ = minimax(new_h, new_v, new_c, player, depth-1, alpha, beta, True)
                else:
                    # Switch to opponent
                    eval_score, _ = minimax(new_h, new_v, new_c, -player, depth-1, alpha, beta, False)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Get all possible moves
    all_moves = get_possible_moves()
    
    # Filter out moves that give opponent an easy scoring opportunity
    safe_moves = []
    for move in all_moves:
        row, col, direction = move
        # Check if this would create a three-side box that could be completed by opponent
        can_create = False
        if direction == 'H':
            if row > 0 or row < 4:
                can_create = True
        else: # V
            if col > 0 or col < 4:
                can_create = True
                
        if can_create:
            safe_moves.append(move)
    
    # If no safe moves, go with all moves
    if not safe_moves:
        safe_moves = all_moves

    # If no moves left, return a random one to avoid errors
    if not safe_moves:
        move = random.choice(all_moves) if all_moves else (0, 0, 'H')
        return f"{move[0]},{move[1]},{move[2]}"

    # Try to maximize score with minimax (depth 3)
    try:
        _, best_move = minimax(horizontal, vertical, capture, 1, 3, float('-inf'), float('inf'), True)
        if best_move is None:
            best_move = random.choice(safe_moves)
    except:
        # fallback to choosing a random safe move  
        best_move = random.choice(safe_moves)
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
