
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def check_winner(b):
        # Check rows, columns, and diagonals for a winner
        for i in range(3):
            # Check rows and columns in every z-level
            for j in range(3):
                if (abs(sum(b[i][j])) == 3 or abs(sum(b[i][k] for k in range(3))) == 3 or 
                    abs(sum(b[k][j] for k in range(3))) == 3):
                    return b[i][j]
                
            # Check diagonals in every z-level
            if (abs(b[i][0][0] + b[i][1][1] + b[i][2][2]) == 3 or 
                abs(b[i][0][2] + b[i][1][1] + b[i][2][0]) == 3):
                return b[i][1][1]
        
        # Check z-level columns and their diagonals
        for j in range(3):
            for k in range(3):
                if abs(b[0][j][k] + b[1][j][k] + b[2][j][k]) == 3:
                    return b[0][j][k]
                
        for d in range(3):
            if (abs(b[0][0][d] + b[1][1][d] + b[2][2][d]) == 3 or 
                abs(b[0][2][d] + b[1][1][d] + b[2][0][d]) == 3):
                return b[1][1][d]
        
        return 0  # No winner

    def minimax(b, depth, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth  # AI win
        elif winner == -1:
            return depth - 10  # Opponent win
        elif all(all(all(cell != 0 for cell in row) for row in plane) for plane in b):
            return 0  # Draw

        if is_maximizing:
            best_score = -float('inf')
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        if b[x][y][z] == 0:
                            b[x][y][z] = 1  # AI move
                            score = minimax(b, depth + 1, False)
                            b[x][y][z] = 0  # Undo move
                            best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for x in range(3):
                for y in range(3):
                    for z in range(3):
                        if b[x][y][z] == 0:
                            b[x][y][z] = -1  # Opponent move
                            score = minimax(b, depth + 1, True)
                            b[x][y][z] = 0  # Undo move
                            best_score = min(score, best_score)
            return best_score

    best_move = (-1, -1, -1)
    best_value = -float('inf')

    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:  # Only consider empty cells
                    board[x][y][z] = 1  # Try the move
                    move_value = minimax(board, 0, False)
                    board[x][y][z] = 0  # Undo move
                    if move_value > best_value:
                        best_value = move_value
                        best_move = (x, y, z)

    return best_move
