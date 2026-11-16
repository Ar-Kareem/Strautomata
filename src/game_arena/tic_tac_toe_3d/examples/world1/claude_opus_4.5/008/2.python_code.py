
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import copy
    
    # Generate all winning lines
    lines = []
    
    # Rows (along x)
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    
    # Columns (along y)
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    
    # Pillars (along z)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Face diagonals in xy-planes
    for z in range(3):
        lines.append([(i, i, z) for i in range(3)])
        lines.append([(i, 2-i, z) for i in range(3)])
    
    # Face diagonals in xz-planes
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])
        lines.append([(i, y, 2-i) for i in range(3)])
    
    # Face diagonals in yz-planes
    for x in range(3):
        lines.append([(x, i, i) for i in range(3)])
        lines.append([(x, i, 2-i) for i in range(3)])
    
    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(2-i, i, i) for i in range(3)])
    
    def get_cell(b, pos):
        return b[pos[0]][pos[1]][pos[2]]
    
    def set_cell(b, pos, val):
        b[pos[0]][pos[1]][pos[2]] = val
    
    def check_winner(b):
        for line in lines:
            s = sum(get_cell(b, p) for p in line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0
    
    def get_empty_cells(b):
        cells = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if b[x][y][z] == 0:
                        cells.append((x, y, z))
        return cells
    
    def evaluate(b):
        score = 0
        for line in lines:
            vals = [get_cell(b, p) for p in line]
            s = sum(vals)
            zeros = vals.count(0)
            if s == 3:
                return 10000
            if s == -3:
                return -10000
            if s == 2 and zeros == 1:
                score += 100
            if s == -2 and zeros == 1:
                score -= 100
            if s == 1 and zeros == 2:
                score += 10
            if s == -1 and zeros == 2:
                score -= 10
        # Center bonus
        if b[1][1][1] == 1:
            score += 50
        elif b[1][1][1] == -1:
            score -= 50
        return score
    
    def minimax(b, depth, alpha, beta, is_max):
        winner = check_winner(b)
        if winner == 1:
            return 10000 + depth
        if winner == -1:
            return -10000 - depth
        
        empty = get_empty_cells(b)
        if not empty or depth == 0:
            return evaluate(b)
        
        if is_max:
            max_eval = float('-inf')
            for pos in empty:
                b_copy = copy.deepcopy(b)
                set_cell(b_copy, pos, 1)
                eval_score = minimax(b_copy, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for pos in empty:
                b_copy = copy.deepcopy(b)
                set_cell(b_copy, pos, -1)
                eval_score = minimax(b_copy, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    empty_cells = get_empty_cells(board)
    
    # Check for immediate win
    for pos in empty_cells:
        b_copy = copy.deepcopy(board)
        set_cell(b_copy, pos, 1)
        if check_winner(b_copy) == 1:
            return pos
    
    # Check for immediate block
    for pos in empty_cells:
        b_copy = copy.deepcopy(board)
        set_cell(b_copy, pos, -1)
        if check_winner(b_copy) == -1:
            return pos
    
    # Use minimax for best move
    depth = 4 if len(empty_cells) > 15 else 6
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for pos in empty_cells:
        b_copy = copy.deepcopy(board)
        set_cell(b_copy, pos, 1)
        score = minimax(b_copy, depth, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = pos
    
    return best_move
