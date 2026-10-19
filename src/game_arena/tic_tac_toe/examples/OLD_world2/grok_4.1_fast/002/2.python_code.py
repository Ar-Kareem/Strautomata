
def get_winner(board):
    # Check rows
    for i in range(4):
        if board[i][0] == board[i][1] == board[i][2] == board[i][3] != 0:
            return board[i][0]
    # Check columns
    for j in range(4):
        if board[0][j] == board[1][j] == board[2][j] == board[3][j] != 0:
            return board[0][j]
    # Check diagonal1
    if board[0][0] == board[1][1] == board[2][2] == board[3][3] != 0:
        return board[0][0]
    # Check diagonal2
    if board[0][3] == board[1][2] == board[2][1] == board[3][0] != 0:
        return board[0][3]
    return 0

def get_move_score(row, col):
    centers = {(1,1), (1,2), (2,1), (2,2)}
    mid_edges = {(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)}
    if (row, col) in centers:
        return 4
    elif (row, col) in mid_edges:
        return 2
    else:
        return 0

def minimax(board, player, alpha, beta):
    w = get_winner(board)
    if w != 0:
        return w

    empties = []
    is_full = True
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                is_full = False
                empties.append((i, j))
    if is_full:
        return 0

    # Order moves: high score first
    empties.sort(key=lambda m: get_move_score(m[0], m[1]), reverse=True)

    if player == 1:  # maximizing player
        max_eval = -2
        for i, j in empties:
            new_board = [row[:] for row in board]
            new_board[i][j] = 1
            eval_score = minimax(new_board, -1, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break
        return max_eval
    else:  # minimizing player
        min_eval = 2
        for i, j in empties:
            new_board = [row[:] for row in board]
            new_board[i][j] = -1
            eval_score = minimax(new_board, 1, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if alpha >= beta:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    empties = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if not empties:
        return (0, 0)  # No moves, shouldn't happen

    # Order moves: high score first
    empties.sort(key=lambda m: get_move_score(m[0], m[1]), reverse=True)

    best_score = -2
    best_move = empties[0]

    for i, j in empties:
        new_board = [row[:] for row in board]
        new_board[i][j] = 1
        score = minimax(new_board, -1, -2, 2)
        if score > best_score:
            best_score = score
            best_move = (i, j)
        if best_score == 1:
            break  # Can't do better than win
    return best_move
