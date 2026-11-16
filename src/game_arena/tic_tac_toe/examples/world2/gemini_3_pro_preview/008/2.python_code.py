
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.
    AI is 1, Opponent is -1, Empty is 0.
    """
    ME = 1
    OPP = -1
    EMPTY = 0
    START_TIME = time.time()
    TIME_LIMIT = 0.98  # Use slightly less than 1.0s to ensure return
    
    # Precomputed indices for rows, columns, and diagonals
    LINES = []
    for r in range(4): LINES.append([(r, c) for c in range(4)])
    for c in range(4): LINES.append([(r, c) for r in range(4)])
    LINES.append([(i, i) for i in range(4)])
    LINES.append([(i, 3 - i) for i in range(4)])

    # Static move ordering: Center -> Inner Edges/Corners -> Outer
    # Attempting to control the center usually prunes the tree faster.
    # Coordinates ordered by distance to center (1.5, 1.5).
    MOVE_ORDER = [
        (1, 1), (1, 2), (2, 1), (2, 2),  # Center
        (0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2), # Middle edges
        (0, 0), (0, 3), (3, 0), (3, 3)   # Corners
    ]

    def evaluate(b):
        """
        Heuristic evaluation of the board.
        Positive score favors AI (1), negative favors Opponent (-1).
        """
        score = 0
        for line in LINES:
            my_count = 0
            opp_count = 0
            for r, c in line:
                val = b[r][c]
                if val == ME:
                    my_count += 1
                elif val == OPP:
                    opp_count += 1
            
            # If line is mixed, it can't be won. Ignore.
            if my_count > 0 and opp_count > 0:
                continue
            
            # Winning/Losing conditions
            if my_count == 4: return 1000000
            if opp_count == 4: return -1000000
            
            # Heuristic weights
            if my_count > 0:
                if my_count == 3: score += 1000
                elif my_count == 2: score += 50
                elif my_count == 1: score += 5
            elif opp_count > 0:
                if opp_count == 3: score -= 1000
                elif opp_count == 2: score -= 50
                elif opp_count == 1: score -= 5
                
        return score

    def get_valid_moves(b):
        # Return empty cells sorted by static strategic importance
        return [m for m in MOVE_ORDER if b[m[0]][m[1]] == EMPTY]

    def minimax(depth, alpha, beta, is_maximizing):
        # Strict time check at node expansion forces early exit
        if time.time() - START_TIME > TIME_LIMIT:
            return None

        current_score = evaluate(board)
        
        # Terminal state check via score or Depth limit
        if abs(current_score) > 100000 or depth == 0:
            return current_score
        
        valid_moves = get_valid_moves(board)
        if not valid_moves:
            return 0  # Draw

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in valid_moves:
                board[r][c] = ME
                eval_val = minimax(depth - 1, alpha, beta, False)
                board[r][c] = EMPTY
                
                if eval_val is None: return None # Propagate timeout
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in valid_moves:
                board[r][c] = OPP
                eval_val = minimax(depth - 1, alpha, beta, True)
                board[r][c] = EMPTY
                
                if eval_val is None: return None # Propagate timeout

                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Get initial available moves
    possible_moves = get_valid_moves(board)
    if not possible_moves:
        return (0, 0)
    
    best_move = possible_moves[0]
    
    # Iterative Deepening
    # Start at depth 1 and increase until time runs out
    for depth in range(1, 17):
        if time.time() - START_TIME > TIME_LIMIT:
            break
            
        current_iter_best_move = None
        current_iter_max_val = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        iteration_completed = True
        
        for r, c in possible_moves:
            board[r][c] = ME
            val = minimax(depth - 1, alpha, beta, False)
            board[r][c] = EMPTY
            
            if val is None:
                iteration_completed = False
                break
            
            if val > current_iter_max_val:
                current_iter_max_val = val
                current_iter_best_move = (r, c)
            
            alpha = max(alpha, val)
            
            # Immediate win prune
            if val > 500000:
                return (r, c)

        if iteration_completed:
            best_move = current_iter_best_move
        else:
            # If iteration didn't finish, discard partial results (keep previous depth's best)
            break
            
    return best_move
