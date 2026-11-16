
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for player 1 (me) in a 3x3 Tic Tac Toe game using Minimax.
    board: 3x3 list of lists where 0 is empty, 1 is me, -1 is opponent.
    Returns: A tuple (row, col).
    """
    
    # Constants
    ME = 1
    OPPONENT = -1
    EMPTY = 0
    
    # Work on a copy to avoid checking or modifying the external list reference
    grid = [row[:] for row in board]

    def get_outcome(b):
        """
        Checks the board state.
        Returns ME (1) if I win, OPPONENT (-1) if opponent wins,
        0 if draw, and None if ongoing.
        """
        # Rows
        for row in b:
            s = sum(row)
            if s == 3: return ME
            if s == -3: return OPPONENT
        
        # Columns
        for c in range(3):
            s = b[0][c] + b[1][c] + b[2][c]
            if s == 3: return ME
            if s == -3: return OPPONENT
            
        # Diagonals
        d1 = b[0][0] + b[1][1] + b[2][2]
        if d1 == 3: return ME
        if d1 == -3: return OPPONENT
        
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d2 == 3: return ME
        if d2 == -3: return OPPONENT
        
        # Check for empty spots to distinguish Draw vs Ongoing
        for r in range(3):
            for c in range(3):
                if b[r][c] == EMPTY:
                    return None
        
        return 0

    def minimax(b, depth, alpha, beta, is_maximizing):
        """
        Recursive Minimax with Alpha-Beta pruning.
        """
        outcome = get_outcome(b)
        if outcome is not None:
            if outcome == ME:
                return 10 - depth  # Prefer winning sooner
            elif outcome == OPPONENT:
                return depth - 10  # Prefer losing later
            else:
                return 0
        
        if is_maximizing:
            max_eval = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == EMPTY:
                        b[r][c] = ME
                        eval_score = minimax(b, depth + 1, alpha, beta, False)
                        b[r][c] = EMPTY # Backtrack
                        
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == EMPTY:
                        b[r][c] = OPPONENT
                        eval_score = minimax(b, depth + 1, alpha, beta, True)
                        b[r][c] = EMPTY # Backtrack
                        
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval

    # Identify valid moves
    possible_moves = []
    for r in range(3):
        for c in range(3):
            if grid[r][c] == EMPTY:
                possible_moves.append((r, c))
    
    # Heuristic sorting: Check Center -> Corners -> Edges
    # This ensures that if scores are equal (e.g. at start), we pick the strategic best.
    priority_order = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    possible_moves.sort(key=lambda m: priority_order.index(m) if m in priority_order else 99)

    best_move = None
    best_score = -math.inf
    
    for (r, c) in possible_moves:
        grid[r][c] = ME
        # Call minimax for the resulting state (opponent's turn next)
        score = minimax(grid, 0, -math.inf, math.inf, False)
        grid[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
            # Optimization: If we found a guaranteed immediate win, take it.
            if best_score == 10:
                break
                
    # Fallback if board is full (should not happen based on prompt)
    if best_move is None and possible_moves:
        best_move = possible_moves[0]
        
    return best_move if best_move else (0, 0)
