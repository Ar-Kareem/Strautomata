
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import copy
    
    # Generate all 49 winning lines
    lines = []
    
    # Lines along each axis
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])  # along z
            lines.append([(i, 0, j), (i, 1, j), (i, 2, j)])  # along y
            lines.append([(0, i, j), (1, i, j), (2, i, j)])  # along x
    
    # Diagonals in xy planes (for each z)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Diagonals in xz planes (for each y)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Diagonals in yz planes (for each x)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def get_empty_cells(b):
        return [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if b[x][y][z] == 0]
    
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
        if winner == -1:
            return -10000
        
        score = 0
        for line in lines:
            vals = [b[x][y][z] for x, y, z in line]
            my_count = vals.count(1)
            opp_count = vals.count(-1)
            
            if opp_count == 0:
                score += [0, 1, 10, 10000][my_count]
            if my_count == 0:
                score -= [0, 1, 10, 10000][opp_count]
        
        # Bonus for center
        if b[1][1][1] == 1:
            score += 5
        elif b[1][1][1] == -1:
            score -= 5
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        winner = check_winner(b)
        if winner != 0:
            return 10000 * winner * (depth + 1), None
        
        empty = get_empty_cells(b)
        if not empty or depth == 0:
            return evaluate(b), None
        
        best_move = empty[0]
        
        if maximizing:
            max_eval = float('-inf')
            for move in empty:
                x, y, z = move
                b[x][y][z] = 1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[x][y][z] = 0
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in empty:
                x, y, z = move
                b[x][y][z] = -1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[x][y][z] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Make a mutable copy
    b = [[[board[x][y][z] for z in range(3)] for y in range(3)] for x in range(3)]
    
    empty = get_empty_cells(b)
    
    # Adjust depth based on number of empty cells
    if len(empty) > 20:
        depth = 3
    elif len(empty) > 15:
        depth = 4
    elif len(empty) > 10:
        depth = 5
    else:
        depth = 7
    
    _, best_move = minimax(b, depth, float('-inf'), float('inf'), True)
    
    return best_move
