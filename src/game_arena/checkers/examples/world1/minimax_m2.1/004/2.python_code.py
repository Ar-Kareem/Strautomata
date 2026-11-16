
import time
import sys
sys.setrecursionlimit(10000)

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    
    # Convert to tuples for immutability
    state = (tuple(my_men), tuple(my_kings), tuple(opp_men), tuple(opp_kings), color)
    
    # Define positional tables
    man_table_white = [
        [0, 50, 50, 50, 50, 50, 50, 0],
        [50, 100, 100, 100, 100, 100, 100, 50],
        [50, 100, 200, 200, 200, 200, 100, 50],
        [50, 100, 200, 300, 300, 200, 100, 50],
        [50, 100, 200, 300, 300, 200, 100, 50],
        [50, 100, 200, 200, 200, 200, 100, 50],
        [50, 100, 100, 100, 100, 100, 100, 50],
        [0, 50, 50, 50, 50, 50, 50, 0]
    ]
    
    king_table = [
        [0, 5, 10, 15, 15, 10, 5, 0],
        [5, 10, 20, 25, 25, 20, 10, 5],
        [10, 20, 30, 35, 35, 30, 20, 10],
        [15, 25, 35, 40, 40, 35, 25, 15],
        [15, 25, 35, 40, 40, 35, 25, 15],
        [10, 20, 30, 35, 35, 30, 20, 10],
        [5, 10, 20, 25, 25, 20, 10, 5],
        [0, 5, 10, 15, 15, 10, 5, 0]
    ]
    
    # Create man table for black by flipping white table
    man_table_black = [row[::-1] for row in man_table_white[::-1]]
    
    def opposite(color):
        return 'b' if color == 'w' else 'w'
    
    def generate_moves(state):
        our_men, our_kings, their_men, their_kings, turn = state
        
        # Build board representation
        board = [[None]*8 for _ in range(8)]
        for (r,c) in our_men:
            board[r][c] = 'our_man'
        for (r,c) in our_kings:
            board[r][c] = 'our_king'
        for (r,c) in their_men:
            board[r][c] = 'their_man'
        for (r,c) in their_kings:
            board[r][c] = 'their_king'
        
        # Directions for movement
        if turn == 'w':
            man_dirs = [(1, -1), (1, 1)]
            king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            man_dirs = [(-1, -1), (-1, 1)]
            king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        simple_moves = []
        capture_moves = []
        
        # Generate moves for men
        for (r,c) in our_men:
            for dr, dc in man_dirs:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < 8 and 0 <= c2 < 8:
                    if board[r2][c2] is None:
                        simple_moves.append(((r, c), (r2, c2)))
                    elif board[r2][c2].startswith('their'):
                        r3, c3 = r + 2*dr, c + 2*dc
                        if 0 <= r3 < 8 and 0 <= c3 < 8 and board[r3][c3] is None:
                            capture_moves.append(((r, c), (r3, c3)))
        
        # Generate moves for kings
        for (r,c) in our_kings:
            for dr, dc in king_dirs:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < 8 and 0 <= c2 < 8:
                    if board[r2][c2] is None:
                        simple_moves.append(((r, c), (r2, c2)))
                    elif board[r2][c2].startswith('their'):
                        r3, c3 = r + 2*dr, c + 2*dc
                        if 0 <= r3 < 8 and 0 <= c3 < 8 and board[r3][c3] is None:
                            capture_moves.append(((r, c), (r3, c3)))
        
        # Return capture moves if available, else simple moves
        if capture_moves:
            return capture_moves
        return simple_moves
    
    def apply_move(state, move):
        our_men, our_kings, their_men, their_kings, turn = state
        (start_r, start_c), (end_r, end_c) = move
        
        # Create new sets for our pieces
        new_our_men = set(our_men)
        new_our_kings = set(our_kings)
        new_their_men = set(their_men)
        new_their_kings = set(their_kings)
        
        # Check if it's a capture move
        if abs(start_r - end_r) == 2 and abs(start_c - end_c) == 2:
            captured_r = (start_r + end_r) // 2
            captured_c = (start_c + end_c) // 2
            captured_piece = (captured_r, captured_c)
            
            # Remove captured piece
            if captured_piece in new_their_men:
                new_their_men.remove(captured_piece)
            else:
                new_their_kings.remove(captured_piece)
        
        # Move our piece
        if (start_r, start_c) in new_our_men:
            new_our_men.remove((start_r, start_c))
            
            # Check for promotion
            if (turn == 'w' and end_r == 7) or (turn == 'b' and end_r == 0):
                new_our_kings.add((end_r, end_c))
            else:
                new_our_men.add((end_r, end_c))
        else:
            new_our_kings.remove((start_r, start_c))
            new_our_kings.add((end_r, end_c))
        
        # Create new state with swapped roles
        new_state = (tuple(new_their_men), tuple(new_their_kings), 
                    tuple(new_our_men), tuple(new_our_kings), opposite(turn))
        return new_state
    
    def evaluate(state):
        our_men, our_kings, their_men, their_kings, turn = state
        
        # Choose appropriate man table
        man_table = man_table_white if turn == 'w' else man_table_black
        
        score = 0
        
        # Evaluate our pieces
        for (r, c) in our_men:
            score += 100 + man_table[r][c]
        for (r, c) in our_kings:
            score += 300 + king_table[r][c]
        
        # Evaluate opponent pieces (subtract from score)
        for (r, c) in their_men:
            score -= 100 + man_table[r][c]
        for (r, c) in their_kings:
            score -= 300 + king_table[r][c]
        
        return score
    
    def minimax(state, depth, alpha, beta, maximizing_player):
        # Check for terminal state or depth limit
        if depth == 0:
            return evaluate(state)
        
        moves = generate_moves(state)
        if not moves:
            # No moves available - lose
            return -10000 if maximizing_player else 10000
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                new_state = apply_move(state, move)
                eval = minimax(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_state = apply_move(state, move)
                eval = minimax(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Iterative deepening with time limit
    best_move = None
    best_value = -float('inf')
    depth = 1
    max_depth = 4  # Maximum depth to search
    
    while depth <= max_depth and time.time() - start_time < 0.9:
        current_best_move = None
        current_best_value = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        moves = generate_moves(state)
        for move in moves:
            if time.time() - start_time > 0.9:
                break
                
            new_state = apply_move(state, move)
            value = minimax(new_state, depth - 1, alpha, beta, False)
            
            if value > current_best_value:
                current_best_value = value
                current_best_move = move
            
            alpha = max(alpha, value)
        
        if current_best_move is not None:
            best_move = current_best_move
            best_value = current_best_value
        
        depth += 1
    
    # Fallback to simple move if no move found
    if best_move is None:
        moves = generate_moves(state)
        if moves:
            best_move = moves[0]
    
    return best_move
