
def get_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))
    return moves

def check_win(board, player):
    # Check rows
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
    # Check columns
    for j in range(3):
        if board[0][j] == player and board[1][j] == player and board[2][j] == player:
            return True
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def evaluate(board):
    if check_win(board, 1):
        return 1
    elif check_win(board, -1):
        return -1
    else:
        # Check if board is full
        if all(board[i][j] != 0 for i in range(3) for j in range(3)):
            return 0
        else:
            return None

def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = get_moves(board)
    if not moves:
        return (0, 0)  # Should not happen, but return arbitrary if no moves

    # Cache for memoization
    cache = {}

    def minimax_score(board_state, is_maximizing):
        board_tuple = tuple(tuple(row) for row in board_state)
        key = (board_tuple, is_maximizing)
        if key in cache:
            return cache[key]

        score = evaluate(board_state)
        if score is not None:
            cache[key] = score
            return score

        current_moves = get_moves(board_state)
        if not current_moves:
            cache[key] = 0
            return 0

        piece = 1 if is_maximizing else -1
        best_score = float('-inf') if is_maximizing else float('inf')

        for move in current_moves:
            i, j = move
            new_board = [row[:] for row in board_state]  # Deep copy
            new_board[i][j] = piece
            score = minimax_score(new_board, not is_maximizing)
            if is_maximizing:
                if score > best_score:
                    best_score = score
            else:
                if score < best_score:
                    best_score = score

        cache[key] = best_score
        return best_score

    best_move = None
    best_score = float('-inf')

    for move in moves:
        i, j = move
        new_board = [row[:] for row in board]
        new_board[i][j] = 1  # My move
        score = minimax_score(new_board, is_maximizing=False)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
