
def get_winning_moves(board, player):
    winning_moves = []
    # Check rows
    for i in range(4):
        row = board[i]
        count_player = row.count(player)
        count_zero = row.count(0)
        if count_player == 3 and count_zero == 1:
            for j in range(4):
                if row[j] == 0:
                    winning_moves.append((i, j))
    # Check columns
    for j in range(4):
        col = [board[i][j] for i in range(4)]
        count_player = col.count(player)
        count_zero = col.count(0)
        if count_player == 3 and count_zero == 1:
            for i in range(4):
                if board[i][j] == 0:
                    winning_moves.append((i, j))
    # Check main diagonal
    diag = [board[i][i] for i in range(4)]
    count_player = diag.count(player)
    count_zero = diag.count(0)
    if count_player == 3 and count_zero == 1:
        for i in range(4):
            if board[i][i] == 0:
                winning_moves.append((i, i))
    # Check anti-diagonal
    anti_diag = [board[i][3-i] for i in range(4)]
    count_player = anti_diag.count(player)
    count_zero = anti_diag.count(0)
    if count_player == 3 and count_zero == 1:
        for i in range(4):
            if board[i][3-i] == 0:
                winning_moves.append((i, 3-i))
    return winning_moves

def check_winner(board):
    # Check rows
    for i in range(4):
        if all(board[i][j] == 1 for j in range(4)):
            return 1
        if all(board[i][j] == -1 for j in range(4)):
            return -1
    # Check columns
    for j in range(4):
        if all(board[i][j] == 1 for i in range(4)):
            return 1
        if all(board[i][j] == -1 for i in range(4)):
            return -1
    # Check main diagonal
    if all(board[i][i] == 1 for i in range(4)):
        return 1
    if all(board[i][i] == -1 for i in range(4)):
        return -1
    # Check anti-diagonal
    if all(board[i][3-i] == 1 for i in range(4)):
        return 1
    if all(board[i][3-i] == -1 for i in range(4)):
        return -1
    # Check if board full
    if all(board[i][j] != 0 for i in range(4) for j in range(4)):
        return 0  # draw
    return None

def policy(board):
    # Check for immediate win
    immediate_wins = get_winning_moves(board, 1)
    if immediate_wins:
        return immediate_wins[0]
    
    # Check for immediate block
    immediate_blocks = get_winning_moves(board, -1)
    if immediate_blocks:
        return immediate_blocks[0]
    
    # Use minimax algorithm with alpha-beta pruning and caching
    cache = {}
    
    def get_board_key(board):
        return tuple(board[i][j] for i in range(4) for j in range(4))
    
    def minimax(board, player, alpha, beta):
        key = (get_board_key(board), player)
        if key in cache:
            return cache[key]
        
        winner = check_winner(board)
        if winner is not None:
            cache[key] = (winner, None)
            return cache[key]
        
        moves = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    moves.append((i, j))
        
        if not moves:
            value = 0
            best_move = None
            cache[key] = (value, best_move)
            return cache[key]
        
        if player == 1:  # Maximize
            best_value = -2
            best_move = None
            for move in moves:
                new_board = [row[:] for row in board]  # Deep copy
                new_board[move[0]][move[1]] = player
                value, next_move = minimax(new_board, -player, alpha, beta)
                if value > best_value:
                    best_value = value
                    best_move = move
                if value >= beta:
                    break
                alpha = max(alpha, value)
            cache[key] = (best_value, best_move)
            return cache[key]
        else:  # player == -1, minimize
            best_value = 2
            best_move = None
            for move in moves:
                new_board = [row[:] for row in board]
                new_board[move[0]][move[1]] = player
                value, next_move = minimax(new_board, 1, alpha, beta)
                if value < best_value:
                    best_value = value
                    best_move = move
                if value <= alpha:
                    break
                beta = min(beta, value)
            cache[key] = (best_value, best_move)
            return cache[key]
    
    best_value, best_move = minimax(board, 1, -2, 2)
    return best_move
