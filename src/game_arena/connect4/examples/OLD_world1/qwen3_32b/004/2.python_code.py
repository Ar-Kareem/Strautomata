```python
def policy(board: list[list[int]]) -> int:
    def is_valid_move(current_board, col):
        for row in range(6):
            if current_board[row][col] == 0:
                return True
        return False

    def drop_disc(current_board, col, player):
        new_board = [row[:] for row in current_board]
        for row in reversed(range(6)):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return new_board  # Should not reach here if valid move

    def is_win(current_board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (current_board[row][col] == player and
                    current_board[row][col+1] == player and
                    current_board[row][col+2] == player and
                    current_board[row][col+3] == player):
                    return True
        # Check vertical
        for col in range(7):
            for row in range(3):
                if (current_board[row][col] == player and
                    current_board[row+1][col] == player and
                    current_board[row+2][col] == player and
                    current_board[row+3][col] == player):
                    return True
        # Check positive slope diagonal
        for row in range(3):
            for col in range(4):
                if (current_board[row][col] == player and
                    current_board[row+1][col+1] == player and
                    current_board[row+2][col+2] == player and
                    current_board[row+3][col+3] == player):
                    return True
        # Check negative slope diagonal
        for row in range(3):
            for col in range(3, 7):
                if (current_board[row][col] == player and
                    current_board[row+1][col-1] == player and
                    current_board[row+2][col-2] == player and
                    current_board[row+3][col-3] == player):
                    return True
        return False

    def evaluate_board(current_board):
        score = 0
        center_col = 3
        center_count = sum(1 for row in current_board if row[center_col] == 1) - sum(1 for row in current_board if row[center_col] == -1)
        score += center_count * 3

        # Horizontal lines
        for row in range(6):
            for col in range(4):
                line = [current_board[row][col], current_board[row][col+1], current_board[row][col+2], current_board[row][col+3]]
                my_count = line.count(1)
                opp_count = line.count(-1)
                if opp_count == 0:
                    if my_count == 4:
                        score += 1000
                    elif my_count == 3:
                        score += 100
                    elif my_count == 2:
                        score += 10
                    elif my_count == 1:
                        score += 1
                if my_count == 0:
                    if opp_count == 4:
                        score -= 1000
                    elif opp_count == 3:
                        score -= 100
                    elif opp_count == 2:
                        score -= 10
                    elif opp_count == 1:
                        score -= 1

        # Vertical lines
        for col in range(7):
            for row in range(3):
                line = [current_board[row][col], current_board[row+1][col], current_board[row+2][col], current_board[row+3][col]]
                my_count = line.count(1)
                opp_count = line.count(-1)
                if opp_count == 0:
                    if my_count == 4:
                        score += 1000
                    elif my_count == 3:
                        score += 100
                    elif my_count == 2:
                        score += 10
                    elif my_count == 1:
                        score += 1
                if my_count == 0:
                    if opp_count == 4:
                        score -= 1000
                    elif opp_count == 3:
                        score -= 100
                    elif opp_count == 2:
                        score -= 10
                    elif opp_count == 1:
                        score -= 1

        # Positive slope diagonals
        for row in range(3):
            for col in range(4):
                line = [current_board[row][col], current_board[row+1][col+1], current_board[row+2][col+2], current_board[row+3][col+3]]
                my_count = line.count(1)
                opp_count = line.count(-1)
                if opp_count == 0:
                    if my_count == 4:
                        score += 1000
                    elif my_count == 3:
                        score += 100
                    elif my_count == 2:
                        score += 10
                    elif my_count == 1:
                        score += 1
                if my_count == 0:
                    if opp_count == 4:
                        score -= 1000
                    elif opp_count == 3:
                        score -= 100
                    elif opp_count == 2:
                        score -= 10
                    elif opp_count == 1:
                        score -= 1

        # Negative slope diagonals
        for row in range(3):
            for col in range(3, 7):
                line = [current_board[row][col], current_board[row+1][col-1], current_board[row+2][col-2], current_board[row+3][col-3]]
                my_count = line.count(1)
                opp_count = line.count(-1)
                if opp_count == 0:
                    if my_count == 4:
                        score += 1000
                    elif my_count == 3:
                        score += 100
                    elif my_count == 2:
                        score += 10
                    elif my_count == 1:
                        score += 1
                if my_count == 0:
                    if opp_count == 4:
                        score -= 1000
                    elif opp_count == 3:
                        score -= 100
                    elif opp_count == 2:
                        score -= 10
                    elif opp_count == 1:
                        score -= 1
        return score

    def minimax(current_board, depth, alpha, beta, maximizing_player):
        if depth == 0 or is_win(current_board, 1) or is_win(current_board, -1):
            return evaluate_board(current_board)

        if maximizing_player:
            max_eval = -float('inf')
            for col in range(7):
                if is_valid_move(current_board, col):
                    new_board = drop_disc(current_board, col, 1)
                    eval = minimax(new_board, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for col in range(7):
                if is_valid_move(current_board, col):
                    new_board = drop_disc(current_board, col, -1)
                    eval = minimax(new_board, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval

    # Check for immediate win
    for col in range(7):
        if is_valid_move(board, col):
            new_board = drop_disc(board, col, 1)
            if is_win(new_board, 1):
                return col

    # Block opponent's immediate win
    for col in range(7):
        if is_valid_move(board, col):
            new_board = drop_disc(board, col, -1)
            if is_win(new_board, -1):
                return col

    # Use minimax to choose best move
    best_score = -float('inf')
    best_col = 0
    for col in range