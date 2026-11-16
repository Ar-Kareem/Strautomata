
import sys
import time

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic Tac Toe AI Policy.
    Uses Minimax with Alpha-Beta pruning to find the optimal move.
    """

    # Convert the board to a flat list of (value, coords) for easier processing
    cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                cells.append(((i, j, k), board[i][j][k]))

    empty_cells = [c for c in cells if c[1] == 0]
    
    # If the board is empty, return the center (1, 1, 1)
    if len(empty_cells) == 27:
        return (1, 1, 1)

    # --- Helper Functions ---

    def get_lines():
        """Generate all 49 winning lines (18 rows, 18 cols, 3 pillars, 4 main diags, 4 anti-diags)"""
        lines = []
        
        # Rows and Columns (Fixed i, j, k combinations)
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)]) # Rows
                lines.append([(i, k, j) for k in range(3)]) # Cols (varied k)
        
        # Pillars (Fixed k, varying i, j)
        for k in range(3):
            for j in range(3):
                lines.append([(i, j, k) for i in range(3)]) 
            for i in range(3):
                lines.append([(i, j, k) for j in range(3)])

        # 3D Diagonals (Across the cube)
        # Main diagonals of the cube
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

        # Planar diagonals (existing from 2D logic but spread across 3D)
        # We missed some planar diagonals in the first loops (e.g. k fixed, i varies, j varies)
        for k in range(3):
            lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
            lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])
        
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])

        for j in range(3):
            lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
            lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])

        return lines

    WIN_LINES = get_lines()

    def get_winner(b):
        """Check if there is a winner on board b"""
        for line in WIN_LINES:
            vals = [b[i][j][k] for i, j, k in line]
            s = sum(vals)
            if s == 3: return 1   # AI Wins
            if s == -3: return -1 # Opponent Wins
        return 0

    def is_terminal(b):
        w = get_winner(b)
        if w != 0: return True
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if b[i][j][k] == 0:
                        return False
        return True

    # Evaluation function
    def evaluate(b):
        w = get_winner(b)
        if w == 1: return 100
        if w == -1: return -100
        
        # Heuristic: Count potential lines
        # This helps distinguish between draws and losses in non-terminal nodes
        score = 0
        for line in WIN_LINES:
            vals = [b[i][j][k] for i, j, k in line]
            ai_count = vals.count(1)
            opp_count = vals.count(-1)
            empty_count = vals.count(0)
            
            if ai_count > 0 and opp_count == 0:
                score += (2 ** ai_count) * empty_count
            elif opp_count > 0 and ai_count == 0:
                score -= (2 ** opp_count) * empty_count
                
        return score

    # Minimax with Alpha-Beta Pruning
    def minimax(b, depth, alpha, beta, is_maximizing):
        if is_terminal(b):
            w = get_winner(b)
            if w == 1: return 100 + depth  # Prefer faster wins
            if w == -1: return -100 - depth # Prefer slower losses
            return 0 # Draw

        # Limit depth for performance if game is long
        # The board is small, full search is possible, but we prune aggressively.
        if depth >= 9: 
             return evaluate(b)

        if is_maximizing:
            max_eval = -float('inf')
            # Heuristic ordering: Center -> Corners -> Edges
            # This speeds up alpha-beta pruning significantly
            ordered_moves = []
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if b[i][j][k] == 0:
                            dist = abs(i-1) + abs(j-1) + abs(k-1) # Distance from center (0 to 3)
                            ordered_moves.append((dist, (i, j, k)))
            
            ordered_moves.sort(key=lambda x: x[0]) # Sort by closeness to center
            
            for _, (i, j, k) in ordered_moves:
                b[i][j][k] = 1
                eval = minimax(b, depth + 1, alpha, beta, False)
                b[i][j][k] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            ordered_moves = []
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if b[i][j][k] == 0:
                            dist = abs(i-1) + abs(j-1) + abs(k-1)
                            ordered_moves.append((dist, (i, j, k)))
            
            ordered_moves.sort(key=lambda x: x[0])

            for _, (i, j, k) in ordered_moves:
                b[i][j][k] = -1
                eval = minimax(b, depth + 1, alpha, beta, True)
                b[i][j][k] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # --- Move Selection ---
    
    best_score = -float('inf')
    best_move = None
    
    # Copy board to a mutable list for simulation
    # (Assuming input is list of lists of lists, we can modify it in place if we revert changes, 
    # but passing a copy is safer if we weren't using in-place recursion).
    # Since we modify in-place during recursion and revert, we can reuse the 'board' object or create a deep copy.
    # To be safe with the API, let's operate on the passed board in the recursion (reverting changes).
    
    # 1. Immediate Win / Block Check (Fast path)
    # We can do this to save time on simple moves, but Minimax covers it.
    
    # 2. Minimax Search
    # Determine valid moves
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    dist = abs(i-1) + abs(j-1) + abs(k-1)
                    moves.append((dist, (i, j, k)))
    
    # Sort moves to check center and corners first
    moves.sort(key=lambda x: x[0])

    for _, (i, j, k) in moves:
        board[i][j][k] = 1 # Make move
        score = minimax(board, 0, -float('inf'), float('inf'), False)
        board[i][j][k] = 0 # Undo move
        
        if score > best_score:
            best_score = score
            best_move = (i, j, k)

    # Fallback (should not happen unless board is full)
    if best_move is None:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)

    return best_move
