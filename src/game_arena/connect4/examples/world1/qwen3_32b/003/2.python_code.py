
def get_valid_moves(board):
    return [col for col in range(7) if board[0][col] == 0]


def get_next_open_row(board, col):
    for r in reversed(range(6)):
        if board[r][col] == 0:
            return r
    return None


def winning_move(board, player):
    # Horizontal
    for r in range(6):
        for c in range(4):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Vertical
    for c in range(7):
        for r in range(3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Positive diagonal
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Negative diagonal
    for r in range(3, 6):
        for c in range(4):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False


def is_terminal_node(board):
    return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_moves(board)) == 0


def evaluate_line(line, player):
    opponent = -player
    if opponent in line:
        return 0
    count = line.count(player)
    if count == 0:
        return 0
    empty = line.count(0)
    if count == 4:
        return 1000
    elif count == 3 and empty == 1:
        return 100
    elif count == 2 and empty == 2:
        return 10
    elif count == 1 and empty == 3:
        return 1
    return 0


def score_position(board):
    our_score = 0
    their_score = 0

    # Horizontal
    for r in range(6):
        for c in range(4):
            line = [board[r][c + i] for i in range(4)]
            our_score += evaluate_line(line, 1)
            their_score += evaluate_line(line, -1)

    # Vertical
    for c in range(7):
        for r in range(3):
            line = [board[r + i][c] for i in range(4)]
            our_score += evaluate_line(line, 1)
            their_score += evaluate_line(line, -1)

    # Positive diagonal
    for r in range(3):
        for c in range(4):
            line = [board[r + i][c + i] for i in range(4)]
            our_score += evaluate_line(line, 1)
            their_score += evaluate_line(line, -1)

    # Negative diagonal
    for r in range(3, 6):
        for c in range(4):
            line = [board[r - i][c + i] for i in range(4)]
            our_score += evaluate_line(line, 1)
            their_score += evaluate_line(line, -1)

    return our_score - their_score


def minimax(board, depth, alpha, beta, is_maximizing):
    valid_moves = get_valid_moves(board)
    terminal = is_terminal_node(board)
    if depth == 0 or terminal:
        if terminal:
            if winning_move(board, 1):
                return (100000, None)
            elif winning_move(board, -1):
                return (-100000, None)
            else:  # Draw
                return (0, None)
        else:
            return (score_position(board), None)

    if is_maximizing:
        max_score = -float('inf')
        best_col = valid_moves[0]
        for col in valid_moves:
            copy_board = [row[:] for row in board]
            row = get_next_open_row(copy_board, col)
            copy_board[row][col] = 1
            new_score, _ = minimax(copy_board, depth - 1, alpha, beta, False)
            if new_score > max_score:
                max_score = new_score
                best_col = col
            alpha = max(alpha, new_score)
            if beta <= alpha:
                break
        return (max_score, best_col)
    else:
        min_score = float('inf')
        best_col = valid_moves[0]
        for col in valid_moves:
            copy_board = [row[:] for row in board]
            row = get_next_open_row(copy_board, col)
            copy_board[row][col] = -1
            new_score, _ = minimax(copy_board, depth - 1, alpha, beta, True)
            if new_score < min_score:
                min_score = new_score
                best_col = col
            beta = min(beta, new_score)
            if beta <= alpha:
                break
        return (min_score, best_col)


def policy(board: list[list[int]]) -> int:
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0  # Should not happen according to rules

    # Check for immediate win
    for move in valid_moves:
        copy_board = [row[:] for row in board]
        row = get_next_open_row(copy_board, move)
        copy_board[row][move] = 1
        if winning_move(copy_board, 1):
            return move

    # Check for opponent's immediate win
    for move in valid_moves:
        copy_board = [row[:] for row in board]
        row = get_next_open_row(copy_board, move)
        copy_board[row][move] = -1
        if winning_move(copy_board, -1):
            return move

    # Minimax decision with depth 4
    best_score = -float('inf')
    best_move = valid_moves[0]
    depth = 4
    for move in valid_moves:
        copy_board = [row[:] for row in board]
        row = get_next_open_row(copy_board, move)
        copy_board[row][move] = 1
        score, _ = minimax(copy_board, depth - 1, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
