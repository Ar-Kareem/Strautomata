
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def check_winner(board):
        n = len(board)
        
        # Check all possible lines in 3D space
        directions = []
        
        # Generate all possible direction vectors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    directions.append((dx, dy, dz))
        
        # Check each possible starting position and direction
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if board[x][y][z] == 0:
                        continue
                    
                    player = board[x][y][z]
                    
                    for dx, dy, dz in directions:
                        count = 1
                        nx, ny, nz = x + dx, y + dy, z + dz
                        
                        # Count consecutive pieces in this direction
                        while (0 <= nx < n and 0 <= ny < n and 0 <= nz < n and 
                               board[nx][ny][nz] == player):
                            count += 1
                            nx += dx
                            ny += dy
                            nz += dz
                        
                        if count >= n:
                            return player
        
        return 0
    
    def get_empty_cells(board):
        empty = []
        for x in range(len(board)):
            for y in range(len(board[0])):
                for z in range(len(board[0][0])):
                    if board[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    def evaluate_position(board, player):
        winner = check_winner(board)
        if winner == player:
            return 1000
        elif winner == -player:
            return -1000
        
        # Evaluate based on potential winning lines
        score = 0
        n = len(board)
        
        directions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    directions.append((dx, dy, dz))
        
        # Check all possible lines
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    for dx, dy, dz in directions:
                        line_score = 0
                        player_count = 0
                        opponent_count = 0
                        
                        # Check if this line is valid (stays within bounds)
                        valid_line = True
                        for i in range(n):
                            nx = x + i * dx
                            ny = y + i * dy
                            nz = z + i * dz
                            if not (0 <= nx < n and 0 <= ny < n and 0 <= nz < n):
                                valid_line = False
                                break
                        
                        if not valid_line:
                            continue
                        
                        # Count pieces in this line
                        for i in range(n):
                            nx = x + i * dx
                            ny = y + i * dy
                            nz = z + i * dz
                            
                            if board[nx][ny][nz] == player:
                                player_count += 1
                            elif board[nx][ny][nz] == -player:
                                opponent_count += 1
                        
                        # Score this line
                        if opponent_count == 0 and player_count > 0:
                            score += player_count ** 2
                        elif player_count == 0 and opponent_count > 0:
                            score -= opponent_count ** 2
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        winner = check_winner(board)
        if winner != 0:
            return winner * player * 1000
        
        empty_cells = get_empty_cells(board)
        if not empty_cells or depth == 0:
            return evaluate_position(board, player)
        
        if maximizing_player:
            max_eval = float('-inf')
            for x, y, z in empty_cells:
                board[x][y][z] = player
                eval_score = minimax(board, depth - 1, alpha, beta, False, player)
                board[x][y][z] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for x, y, z in empty_cells:
                board[x][y][z] = -player
                eval_score = minimax(board, depth - 1, alpha, beta, True, player)
                board[x][y][z] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Main logic
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen
    
    # If it's the first move, take center
    if len(empty_cells) == 27:
        return (1, 1, 1)
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    # Try each empty cell and find the best move
    for x, y, z in empty_cells:
        board[x][y][z] = 1
        score = minimax(board, 4, float('-inf'), float('inf'), False, 1)
        board[x][y][z] = 0
        
        if score > best_score:
            best_score = score
            best_move = (x, y, z)
    
    return best_move
