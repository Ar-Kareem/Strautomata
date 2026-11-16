
def policy(board: list[list[int]]) -> tuple[int, int]:
    def evaluate(board):
        # Check rows and columns for a win
        for i in range(4):
            if abs(sum(board[i])) == 4:  # current player wins
                return 1
            if abs(sum(board[j][i] for j in range(4))) == 4:  # opponent wins
                return -1
        
        # Check diagonals
        if abs(sum(board[i][i] for i in range(4))) == 4:  # current player wins
            return 1
        if abs(sum(board[i][3 - i] for i in range(4))) == 4:  # opponent wins
            return -1

        # Check for empty spaces
        if any(0 in row for row in board):
            return 0  # game still ongoing
        
        return 0  # draw

    def minimax(board, depth, is_maximizing):
        score = evaluate(board)
        
        # If the game is over return the score
        if score != 0:
            return score
        
        if is_maximizing:
            best_score = -float('inf')
            for i in range(4):
                for j in range(4):
                    if board[i][j] == 0:  # empty space
                        board[i][j] = 1  # maximize for us
                        best_score = max(best_score, minimax(board, depth + 1, False))
                        board[i][j] = 0  # undo move
            return best_score
        else:
            best_score = float('inf')
            for i in range(4):
                for j in range(4):
                    if board[i][j] == 0:  # empty space
                        board[i][j] = -1  # minimize for opponent
                        best_score = min(best_score, minimax(board, depth + 1, True))
                        board[i][j] = 0  # undo move
            return best_score

    best_move = (-1, -1)
    best_value = -float('inf')

    # Check all possible moves to find the best one
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # empty space
                board[i][j] = 1  # make the move
                move_value = minimax(board, 0, False)
                board[i][j] = 0  # undo move
                
                if move_value > best_value:
                    best_move = (i, j)
                    best_value = move_value

    return best_move
