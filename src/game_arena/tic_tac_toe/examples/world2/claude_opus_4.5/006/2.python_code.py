
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows
        for row in b:
            if sum(row) == 4:
                return 1
            if sum(row) == -4:
                return -1
        
        # Check columns
        for col in range(4):
            total = sum(b[row][col] for row in range(4))
            if total == 4:
                return 1
            if total == -4:
                return -1
        
        # Check main diagonal
        diag = sum(b[i][i] for i in range(4))
        if diag == 4:
            return 1
        if diag == -4:
            return -1
        
        # Check anti-diagonal
        anti_diag = sum(b[i][3-i] for i in range(4))
        if anti_diag == 4:
            return 1
        if anti_diag == -4:
            return -1
        
        return 0
    
    def get_empty_cells(b):
        return [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
    
    def evaluate_move(b, r, c):
        # Heuristic to prioritize center and strategic positions
        score = 0
        # Center positions are valuable
        if r in [1, 2] and c in [1, 2]:
            score += 2
        # Corners
        if (r, c) in [(0,0), (0,3), (3,0), (3,3)]:
            score += 1
        return score
    
    def minimax(b, depth, alpha, beta, is_maximizing, max_depth):
        winner = check_winner(b)
        if winner == 1:
            return 1000 - depth, None
        if winner == -1:
            return -1000 + depth, None
        
        empty = get_empty_cells(b)
        if not empty:
            return 0, None
        
        if depth >= max_depth:
            # Simple heuristic evaluation
            return heuristic_eval(b), None
        
        # Sort moves by heuristic for better pruning
        empty.sort(key=lambda x: -evaluate_move(b, x[0], x[1]))
        
        if is_maximizing:
            best_score = -float('inf')
            best_move = empty[0]
            for r, c in empty:
                b[r][c] = 1
                score, _ = minimax(b, depth + 1, alpha, beta, False, max_depth)
                b[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = float('inf')
            best_move = empty[0]
            for r, c in empty:
                b[r][c] = -1
                score, _ = minimax(b, depth + 1, alpha, beta, True, max_depth)
                b[r][c] = 0
                if score < best_score:
                    best_score = score
                    best_move = (r, c)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return best_score, best_move
    
    def heuristic_eval(b):
        score = 0
        lines = []
        # Rows
        for row in b:
            lines.append(row)
        # Columns
        for col in range(4):
            lines.append([b[row][col] for row in range(4)])
        # Diagonals
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        
        for line in lines:
            s = sum(line)
            zeros = line.count(0)
            if s == 3 and zeros == 1:
                score += 50
            elif s == -3 and zeros == 1:
                score -= 50
            elif s == 2 and zeros == 2:
                score += 10
            elif s == -2 and zeros == 2:
                score -= 10
        return score
    
    # Make a copy to avoid modifying the input
    board_copy = [row[:] for row in board]
    
    # Determine search depth based on empty cells
    empty_count = len(get_empty_cells(board_copy))
    if empty_count <= 8:
        max_depth = 16  # Can search to end
    elif empty_count <= 10:
        max_depth = 10
    else:
        max_depth = 8
    
    _, move = minimax(board_copy, 0, -float('inf'), float('inf'), True, max_depth)
    
    if move is None:
        # Fallback: return first empty cell
        empty = get_empty_cells(board)
        if empty:
            return empty[0]
    
    return move
