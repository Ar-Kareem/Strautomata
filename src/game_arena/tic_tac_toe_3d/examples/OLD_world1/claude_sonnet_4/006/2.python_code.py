
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_winning_lines():
        lines = []
        
        # Lines within each z-plane
        for z in range(3):
            # Rows
            for x in range(3):
                lines.append([(x, y, z) for y in range(3)])
            # Columns
            for y in range(3):
                lines.append([(x, y, z) for x in range(3)])
            # Diagonals within plane
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Lines through z-axis
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Diagonals through z-axis
        for z_dir in range(3):
            # Main diagonals
            lines.append([(i, i, z_dir) for i in range(3)])
            lines.append([(i, 2-i, z_dir) for i in range(3)])
        
        # Space diagonals (4 total)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    def check_winner(board):
        lines = get_winning_lines()
        for line in lines:
            values = [board[x][y][z] for x, y, z in line]
            if all(v == 1 for v in values):
                return 1
            elif all(v == -1 for v in values):
                return -1
        return 0
    
    def is_board_full(board):
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        return False
        return True
    
    def get_empty_cells(board):
        empty = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    def evaluate_position(board):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        lines = get_winning_lines()
        score = 0
        
        for line in lines:
            values = [board[x][y][z] for x, y, z in line]
            player_count = sum(1 for v in values if v == 1)
            opponent_count = sum(1 for v in values if v == -1)
            
            if opponent_count == 0:
                score += player_count ** 2
            elif player_count == 0:
                score -= opponent_count ** 2
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        if is_board_full(board) or depth == 0:
            return evaluate_position(board)
        
        empty_cells = get_empty_cells(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for x, y, z in empty_cells:
                board[x][y][z] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[x][y][z] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for x, y, z in empty_cells:
                board[x][y][z] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[x][y][z] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def position_value(x, y, z):
        # Center positions are generally better
        center_distance = abs(x - 1) + abs(y - 1) + abs(z - 1)
        return 6 - center_distance
    
    # Check for immediate win
    empty_cells = get_empty_cells(board)
    for x, y, z in empty_cells:
        board[x][y][z] = 1
        if check_winner(board) == 1:
            board[x][y][z] = 0
            return (x, y, z)
        board[x][y][z] = 0
    
    # Check for blocking opponent win
    for x, y, z in empty_cells:
        board[x][y][z] = -1
        if check_winner(board) == -1:
            board[x][y][z] = 0
            return (x, y, z)
        board[x][y][z] = 0
    
    # Use minimax for best move
    best_move = None
    best_score = float('-inf')
    depth = min(6, len(empty_cells))
    
    for x, y, z in empty_cells:
        board[x][y][z] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        # Add position bonus for tie-breaking
        score += position_value(x, y, z) * 0.1
        board[x][y][z] = 0
        
        if score > best_score:
            best_score = score
            best_move = (x, y, z)
    
    return best_move if best_move else empty_cells[0]
