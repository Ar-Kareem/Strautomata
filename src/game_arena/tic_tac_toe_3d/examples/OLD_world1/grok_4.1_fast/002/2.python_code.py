
def has_won(board, player):
    # Orthogonal lines
    # Along x (fix z, y)
    for z in range(3):
        for y in range(3):
            if board[z][y][0] == player and board[z][y][1] == player and board[z][y][2] == player:
                return True
    # Along y (fix z, x)
    for z in range(3):
        for x in range(3):
            if board[z][0][x] == player and board[z][1][x] == player and board[z][2][x] == player:
                return True
    # Along z (fix y, x)
    for y in range(3):
        for x in range(3):
            if board[0][y][x] == player and board[1][y][x] == player and board[2][y][x] == player:
                return True
    # Plane diagonals in xy-planes (fix z)
    for z in range(3):
        if board[z][0][0] == player and board[z][1][1] == player and board[z][2][2] == player:
            return True
        if board[z][0][2] == player and board[z][1][1] == player and board[z][2][0] == player:
            return True
    # Plane diagonals in xz-planes (fix y)
    for y in range(3):
        if board[0][y][0] == player and board[1][y][1] == player and board[2][y][2] == player:
            return True
        if board[0][y][2] == player and board[1][y][1] == player and board[2][y][0] == player:
            return True
    # Plane diagonals in yz-planes (fix x)
    for x in range(3):
        if board[0][0][x] == player and board[1][1][x] == player and board[2][2][x] == player:
            return True
        if board[0][2][x] == player and board[1][1][x] == player and board[2][0][x] == player:
            return True
    # Space diagonals
    if board[0][0][0] == player and board[1][1][1] == player and board[2][2][2] == player:
        return True
    if board[0][0][2] == player and board[1][1][1] == player and board[2][2][0] == player:
        return True
    if board[0][2][0] == player and board[1][1][1] == player and board[2][0][2] == player:
        return True
    if board[0][2][2] == player and board[1][1][1] == player and board[2][0][0] == player:
        return True
    return False

def check_winner(board):
    if has_won(board, 1):
        return 1
    if has_won(board, -1):
        return -1
    return 0

def get_moves(board):
    return [(z, y, x) for z in range(3) for y in range(3) for x in range(3) if board[z][y][x] == 0]

def minimax(board, player, alpha, beta):
    score = check_winner(board)
    if score != 0:
        return score
    moves = get_moves(board)
    if not moves:
        return 0
    # Sort moves: center first
    def move_key(m):
        z, y, x = m
        return -(abs(z - 1) + abs(y - 1) + abs(x - 1))
    moves.sort(key=move_key)
    if player == 1:
        max_score = -2
        for z, y, x in moves:
            board[z][y][x] = 1
            score = minimax(board, -1, alpha, beta)
            board[z][y][x] = 0
            if score > max_score:
                max_score = score
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = 2
        for z, y, x in moves:
            board[z][y][x] = -1
            score = minimax(board, 1, alpha, beta)
            board[z][y][x] = 0
            if score < min_score:
                min_score = score
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    moves = get_moves(board)
    if not moves:
        return (0, 0, 0)  # Should not happen
    # Sort moves for root: center first
    def move_key(m):
        z, y, x = m
        return -(abs(z - 1) + abs(y - 1) + abs(x - 1))
    moves.sort(key=move_key)
    best_score = -2
    best_move = moves[0]
    for move in moves:
        z, y, x = move
        board[z][y][x] = 1
        score = minimax(board, -1, -2, 2)
        board[z][y][x] = 0
        if score > best_score:
            best_score = score
            best_move = (z, y, x)
        # Early stop if perfect score
        if best_score == 1:
            break
    return best_move
