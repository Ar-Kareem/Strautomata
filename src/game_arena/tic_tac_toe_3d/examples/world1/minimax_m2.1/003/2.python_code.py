
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Precompute winning lines for efficiency
    lines = []
    
    # Lines parallel to x-axis
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    
    # Lines parallel to y-axis
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    
    # Lines parallel to z-axis
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Face diagonals in xy-planes (fixed z)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Face diagonals in xz-planes (fixed y)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Face diagonals in yz-planes (fixed x)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def evaluate_board(board_state):
        score = 0
        for line in lines:
            count_1 = 0
            count_neg1 = 0
            count_0 = 0
            for (i, j, k) in line:
                if board_state[i][j][k] == 1:
                    count_1 += 1
                elif board_state[i][j][k] == -1:
                    count_neg1 += 1
                else:
                    count_0 += 1
            if count_1 == 3:
                score += 100
            if count_neg1 == 3:
                score -= 100
            if count_1 == 2 and count_0 == 1:
                score += 10
            if count_neg1 == 2 and count_0 == 1:
                score -= 10
            if count_1 == 1 and count_0 == 2:
                score += 1
            if count_neg1 == 1 and count_0 == 2:
                score -= 1
        return score
    
    def get_empty_cells(board_state):
        empty = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board_state[i][j][k] == 0:
                        empty.append((i, j, k))
        return empty
    
    def minimax(board_state, depth, alpha, beta, is_maximizing):
        empty_cells = get_empty_cells(board_state)
        
        # Terminal check: if no moves or depth reached, evaluate
        if not empty_cells or depth == 0:
            return evaluate_board(board_state), None
        
        if is_maximizing:
            best_score = -float('inf')
            best_move = None
            for move in empty_cells:
                i, j, k = move
                board_state[i][j][k] = 1
                score, _ = minimax(board_state, depth - 1, alpha, beta, False)
                board_state[i][j][k] = 0  # Undo move
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = float('inf')
            best_move = None
            for move in empty_cells:
                i, j, k = move
                board_state[i][j][k] = -1
                score, _ = minimax(board_state, depth - 1, alpha, beta, True)
                board_state[i][j][k] = 0  # Undo move
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
    
    # Use depth 2 for minimax
    _, best_move = minimax(board, 2, -float('inf'), float('inf'), True)
    return best_move
