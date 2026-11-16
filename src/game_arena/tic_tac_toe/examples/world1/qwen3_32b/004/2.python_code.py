
def policy(board: list[list[int]]) -> tuple[int, int]:
    def to_tuple(b):
        return tuple(tuple(row) for row in b)
    
    memo = {}

    def check_winner(b):
        for row in b:
            if row[0] != 0 and row[0] == row[1] == row[2]:
                return row[0]
        for c in range(3):
            if b[0][c] != 0 and b[0][c] == b[1][c] == b[2][c]:
                return b[0][c]
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2]:
            return b[0][0]
        if b[0][2] != 0 and b[0][2] == b[1][1] == b[2][0]:
            return b[1][1]
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return None
        return 0

    def minimax(current_board, is_maximizing):
        board_key = to_tuple(current_board)
        if board_key in memo:
            return memo[board_key]

        winner = check_winner(current_board)
        if winner is not None:
            memo[board_key] = ((None, None), winner)
            return (None, None), winner

        possible_moves = [(r, c) for r in range(3) for c in range(3) if current_board[r][c] == 0]

        if is_maximizing:
            best_score = -float('inf')
            best_move = (None, None)
            for r, c in possible_moves:
                new_board = [row[:] for row in current_board]
                new_board[r][c] = 1
                move, score = minimax(new_board, is_maximizing=False)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
            memo[to_tuple(current_board)] = (best_move, best_score)
            return best_move, best_score
        else:
            best_score = float('inf')
            best_move = (None, None)
            for r, c in possible_moves:
                new_board = [row[:] for row in current_board]
                new_board[r][c] = -1
                move, score = minimax(new_board, is_maximizing=True)
                if score < best_score:
                    best_score = score
                    best_move = (r, c)
            memo[to_tuple(current_board)] = (best_move, best_score)
            return best_move, best_score
    
    best_move, _ = minimax(board, is_maximizing=True)
    return best_move
