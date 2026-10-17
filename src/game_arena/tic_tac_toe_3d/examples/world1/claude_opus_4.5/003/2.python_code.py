
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all 49 winning lines
    lines = []
    
    # Rows, columns, pillars (27 lines)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # along z
            lines.append([(i, k, j) for k in range(3)])  # along y
            lines.append([(k, i, j) for k in range(3)])  # along x
    
    # Face diagonals (18 lines)
    for i in range(3):
        lines.append([(k, k, i) for k in range(3)])
        lines.append([(k, 2-k, i) for k in range(3)])
        lines.append([(k, i, k) for k in range(3)])
        lines.append([(k, i, 2-k) for k in range(3)])
        lines.append([(i, k, k) for k in range(3)])
        lines.append([(i, k, 2-k) for k in range(3)])
    
    # Space diagonals (4 lines)
    lines.append([(k, k, k) for k in range(3)])
    lines.append([(k, k, 2-k) for k in range(3)])
    lines.append([(k, 2-k, k) for k in range(3)])
    lines.append([(2-k, k, k) for k in range(3)])
    
    def get_empty_cells(b):
        empty = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if b[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    def check_winner(b):
        for line in lines:
            vals = [b[x][y][z] for x, y, z in line]
            if vals[0] != 0 and vals[0] == vals[1] == vals[2]:
                return vals[0]
        return 0
    
    def evaluate(b):
        winner = check_winner(b)
        if winner == 1:
            return 10000
        elif winner == -1:
            return -10000
        
        score = 0
        for line in lines:
            vals = [b[x][y][z] for x, y, z in line]
            my_count = vals.count(1)
            opp_count = vals.count(-1)
            
            if opp_count == 0:
                if my_count == 2:
                    score += 50
                elif my_count == 1:
                    score += 5
            if my_count == 0:
                if opp_count == 2:
                    score -= 50
                elif opp_count == 1:
                    score -= 5
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10000 + depth, None
        if winner == -1:
            return -10000 - depth, None
        
        empty = get_empty_cells(b)
        if not empty or depth == 0:
            return evaluate(b), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = empty[0]
            for x, y, z in empty:
                b[x][y][z] = 1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[x][y][z] = 0
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (x, y, z)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = empty[0]
            for x, y, z in empty:
                b[x][y][z] = -1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[x][y][z] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (x, y, z)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Check for immediate winning move
    empty = get_empty_cells(board)
    for x, y, z in empty:
        board[x][y][z] = 1
        if check_winner(board) == 1:
            board[x][y][z] = 0
            return (x, y, z)
        board[x][y][z] = 0
    
    # Check for blocking move
    for x, y, z in empty:
        board[x][y][z] = -1
        if check_winner(board) == -1:
            board[x][y][z] = 0
            return (x, y, z)
        board[x][y][z] = 0
    
    # Use minimax with adaptive depth
    num_empty = len(empty)
    if num_empty > 20:
        depth = 3
    elif num_empty > 15:
        depth = 4
    elif num_empty > 10:
        depth = 5
    else:
        depth = 6
    
    _, best_move = minimax(board, depth, float('-inf'), float('inf'), True)
    return best_move
