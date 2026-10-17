
import numpy as np
import time

def policy(board):
    start_time = time.time()
    time_limit = 0.95
    
    # Directions: 8 neighbors (N, S, E, W, NE, NW, SE, SW)
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def get_moves(current_board, player):
        moves = []
        amazons = np.argwhere(current_board == player)
        
        for am_r, am_c in amazons:
            # Generate Amazon moves
            for dr, dc in DIRS:
                nr, nc = am_r, am_c
                while True:
                    nr += dr
                    nc += dc
                    if 0 <= nr < 6 and 0 <= nc < 6:
                        if current_board[nr, nc] == 0:
                            # Valid Amazon move (am_r, am_c) -> (nr, nc)
                            # Generate Arrow shots from (nr, nc)
                            for ar_dr, ar_dc in DIRS:
                                arr, arc = nr, nc
                                while True:
                                    arr += ar_dr
                                    arc += ar_dc
                                    if 0 <= arr < 6 and 0 <= arc < 6:
                                        # Check if arrow can pass/land
                                        # Valid if empty OR is the vacated square (am_r, am_c)
                                        if current_board[arr, arc] == 0 or (arr == am_r and arc == am_c):
                                            moves.append((am_r, am_c, nr, nc, arr, arc))
                                        else:
                                            break
                                    else:
                                        break
                        else:
                            break
                else:
                    break
        return moves

    def evaluate(current_board):
        # Heuristic: Difference in reachable squares (Territory/Mobility)
        # 1 = Player, 2 = Opponent
        my_score = 0
        opp_score = 0
        
        my_amazons = np.argwhere(current_board == 1)
        opp_amazons = np.argwhere(current_board == 2)
        
        for r, c in my_amazons:
            for dr, dc in DIRS:
                nr, nc = r, c
                while True:
                    nr += dr
                    nc += dc
                    if 0 <= nr < 6 and 0 <= nc < 6 and current_board[nr, nc] == 0:
                        my_score += 1
                    else:
                        break
                        
        for r, c in opp_amazons:
            for dr, dc in DIRS:
                nr, nc = r, c
                while True:
                    nr += dr
                    nc += dc
                    if 0 <= nr < 6 and 0 <= nc < 6 and current_board[nr, nc] == 0:
                        opp_score += 1
                    else:
                        break
                        
        return my_score - opp_score

    def apply_move(current_board, move):
        fr, fc, tr, tc, ar, ac = move
        new_board = current_board.copy()
        player = new_board[fr, fc]
        
        new_board[fr, fc] = 0
        new_board[tr, tc] = player
        new_board[ar, ac] = -1
        
        return new_board

    def minimax(current_board, depth, alpha, beta, maximizing_player):
        if time.time() - start_time > time_limit:
            raise TimeoutError
            
        if depth == 0:
            return evaluate(current_board), None
            
        player = 1 if maximizing_player else 2
        moves = get_moves(current_board, player)
        
        if not moves:
            # Terminal state: current player cannot move
            return (-10000 if maximizing_player else 10000), None
            
        # Move ordering: Sort by quick heuristic to improve pruning
        # We only sort if the number of moves is manageable to avoid overhead
        if len(moves) > 1:
             # Use a simple lambda to sort; higher score is better for Max, lower for Min
            moves.sort(key=lambda m: evaluate(apply_move(current_board, m)), reverse=maximizing_player)
        
        best_move = moves[0]
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                new_board = apply_move(current_board, move)
                eval_val, _ = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = apply_move(current_board, move)
                eval_val, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Main execution with Iterative Deepening
    best_move_found = None
    
    # We assume there is always a legal move if policy is called
    initial_moves = get_moves(board, 1)
    if initial_moves:
        best_move_found = initial_moves[0] # Fallback
        
        try:
            for depth in range(1, 5): # Search depth 1, 2, 3, 4...
                _, move = minimax(board, depth, -float('inf'), float('inf'), True)
                if move:
                    best_move_found = move
        except TimeoutError:
            pass

    if best_move_found:
        fr, fc, tr, tc, ar, ac = best_move_found
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
    else:
        # Should not be reached if game logic is correct, but return valid syntax just in case
        return "0,0:0,0:0,0"

