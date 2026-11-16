
import numpy as np

def policy(board) -> str:
    """
    Determines the next move for the Amazons game using a Minimax algorithm.
    """
    # Constants
    MY_ID = 1
    OPP_ID = 2
    BLOCKED = -1
    EMPTY = 0
    MAX_DEPTH = 2
    
    # Directions: 8 orthogonal and diagonal directions
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def get_reachable_squares(board, r, c):
        """
        Returns a list of (row, col) squares reachable from (r, c) in one queen move.
        """
        reachable = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                if board[nr, nc] == EMPTY:
                    reachable.append((nr, nc))
                    nr += dr
                    nc += dc
                else:
                    break
        return reachable

    def get_legal_moves(board, player_id):
        """
        Generates all legal moves for a player.
        Returns a list of tuples: (from_r, from_c, to_r, to_c, arrow_r, arrow_c)
        """
        moves = []
        amazons = np.argwhere(board == player_id)
        
        for amazon in amazons:
            r1, c1 = amazon
            # Get amazon destinations
            to_squares = get_reachable_squares(board, r1, c1)
            
            for r2, c2 in to_squares:
                # Simulate the amazon moving to (r2, c2) to check arrow shots
                # The square (r1, c1) becomes empty, (r2, c2) becomes occupied
                
                # We can optimize arrow generation by checking lines from (r2, c2)
                # Note: (r1, c1) is now empty, so arrows can pass through or land there.
                
                for dr, dc in DIRS:
                    ar, ac = r2 + dr, c2 + dc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        # A square is a valid arrow target if:
                        # 1. It is the vacated square (r1, c1)
                        # 2. It is empty on the current board (and not r2, c2 where we are standing, but board[r2,c2] was 0)
                        
                        # Note: board[ar, ac] reflects state BEFORE move.
                        # If (ar, ac) == (r1, c1), it is valid (vacated spot).
                        # If board[ar, ac] == EMPTY, it is valid.
                        
                        # However, we must ensure we don't shoot onto ourselves at (r2, c2) 
                        # if the loop somehow points there (impossible since we start at r2+dr).
                        # We also must ensure we don't shoot through obstacles.
                        
                        is_vacated = (ar == r1 and ac == c1)
                        is_empty = (board[ar, ac] == EMPTY)
                        
                        if is_vacated or is_empty:
                            # Valid arrow target
                            moves.append((r1, c1, r2, c2, ar, ac))
                            
                            # Continue ray
                            ar += dr
                            ac += dc
                        else:
                            # Hit an obstacle (other amazon, blocked, or other amazon's location)
                            break
                            
        return moves

    def evaluate_board(board):
        """
        Evaluates the board state based on mobility difference.
        """
        # Mobility: Count reachable squares for all amazons
        my_amazons = np.argwhere(board == MY_ID)
        opp_amazons = np.argwhere(board == OPP_ID)
        
        my_mobility = 0
        for r, c in my_amazons:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == EMPTY:
                    my_mobility += 1
                    nr += dr
                    nc += dc
                    
        opp_mobility = 0
        for r, c in opp_amazons:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == EMPTY:
                    opp_mobility += 1
                    nr += dr
                    nc += dc
                    
        return my_mobility - opp_mobility

    def minimax(board, depth, alpha, beta, maximizing_player):
        """
        Minimax with Alpha-Beta pruning.
        """
        # Terminal condition check or depth limit
        if depth == 0:
            return evaluate_board(board), None
            
        current_player = MY_ID if maximizing_player else OPP_ID
        moves = get_legal_moves(board, current_player)
        
        if not moves:
            # Current player cannot move. They lose.
            # If I cannot move, score is -Inf. If opponent cannot move, score is +Inf.
            return (float('-inf') if maximizing_player else float('inf')), None

        best_move = moves[0] # Default
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                r1, c1, r2, c2, ar, ac = move
                # Create new board state
                new_board = board.copy()
                new_board[r1, c1] = EMPTY
                new_board[r2, c2] = MY_ID
                new_board[ar, ac] = BLOCKED
                
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                
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
                r1, c1, r2, c2, ar, ac = move
                # Create new board state
                new_board = board.copy()
                new_board[r1, c1] = EMPTY
                new_board[r2, c2] = OPP_ID
                new_board[ar, ac] = BLOCKED
                
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move # Though we only care about root move usually
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Run Minimax
    # Depth 2 is chosen as a safe balance between look-ahead and time constraint (1s)
    _, best_move = minimax(board, MAX_DEPTH, float('-inf'), float('inf'), True)
    
    if best_move is None:
        # Fallback: if no moves found by minimax (shouldn't happen if logic correct), 
        # find any legal move using a simple search.
        # This block ensures we always return a string.
        moves = get_legal_moves(board, MY_ID)
        if moves:
            best_move = moves[0]
        else:
            return "0,0:0,0:0,0" # No legal moves possible

    r1, c1, r2, c2, ar, ac = best_move
    return f"{r1},{c1}:{r2},{c2}:{ar},{ac}"
