
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_empty_cells(board):
        empty = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        empty.append((i, j, k))
        return empty
    
    def check_winner(board):
        # All possible winning lines in 3D tic-tac-toe
        lines = []
        
        # Rows (along k axis)
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])
        
        # Columns (along j axis)
        for i in range(3):
            for k in range(3):
                lines.append([(i, 0, k), (i, 1, k), (i, 2, k)])
        
        # Depths (along i axis)
        for j in range(3):
            for k in range(3):
                lines.append([(0, j, k), (1, j, k), (2, j, k)])
        
        # Face diagonals - front/back faces (i fixed)
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
        
        # Face diagonals - left/right faces (k fixed)
        for k in range(3):
            lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
            lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])
        
        # Face diagonals - top/bottom faces (j fixed)
        for j in range(3):
            lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
            lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])
        
        # Space diagonals (4 main diagonals through the cube)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
        
        for line in lines:
            values = [board[pos[0]][pos[1]][pos[2]] for pos in line]
            if values == [1, 1, 1]:
                return 1
            elif values == [-1, -1, -1]:
                return -1
        
        return 0
    
    def evaluate_line(line_values):
        if line_values.count(1) == 2 and line_values.count(0) == 1:
            return 10  # We can win
        elif line_values.count(-1) == 2 and line_values.count(0) == 1:
            return -10  # Opponent can win
        elif line_values.count(1) == 1 and line_values.count(0) == 2:
            return 1  # Potential for us
        elif line_values.count(-1) == 1 and line_values.count(0) == 2:
            return -1  # Potential for opponent
        return 0
    
    def evaluate_position(board):
        winner = check_winner(board)
        if winner == 1:
            return 100
        elif winner == -1:
            return -100
        
        score = 0
        lines = []
        
        # All winning lines (same as in check_winner)
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])
        for i in range(3):
            for k in range(3):
                lines.append([(i, 0, k), (i, 1, k), (i, 2, k)])
        for j in range(3):
            for k in range(3):
                lines.append([(0, j, k), (1, j, k), (2, j, k)])
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
        for k in range(3):
            lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
            lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])
        for j in range(3):
            lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
            lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
        
        for line in lines:
            values = [board[pos[0]][pos[1]][pos[2]] for pos in line]
            score += evaluate_line(values)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0:
            return winner * 100
        
        empty_cells = get_empty_cells(board)
        if not empty_cells or depth == 0:
            return evaluate_position(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for pos in empty_cells:
                i, j, k = pos
                board[i][j][k] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[i][j][k] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for pos in empty_cells:
                i, j, k = pos
                board[i][j][k] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[i][j][k] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    empty_cells = get_empty_cells(board)
    if not empty_cells:
        return (0, 0, 0)
    
    # Check for immediate win
    for pos in empty_cells:
        i, j, k = pos
        board[i][j][k] = 1
        if check_winner(board) == 1:
            board[i][j][k] = 0
            return pos
        board[i][j][k] = 0
    
    # Check for blocking opponent win
    for pos in empty_cells:
        i, j, k = pos
        board[i][j][k] = -1
        if check_winner(board) == -1:
            board[i][j][k] = 0
            return pos
        board[i][j][k] = 0
    
    # Use minimax for best move
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for pos in empty_cells:
        i, j, k = pos
        board[i][j][k] = 1
        score = minimax(board, min(6, len(empty_cells)), float('-inf'), float('inf'), False)
        board[i][j][k] = 0
        
        if score > best_score:
            best_score = score
            best_move = pos
    
    return best_move
