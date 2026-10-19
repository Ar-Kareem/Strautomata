
import itertools

# Precompute all 49 winning lines for 3x3x3 board
WINNING_LINES = []

# Lines within each layer (z constant)
for z in range(3):
    # rows (y constant)
    for y in range(3):
        WINNING_LINES.append([(x, y, z) for x in range(3)])
    # columns (x constant)
    for x in range(3):
        WINNING_LINES.append([(x, y, z) for y in range(3)])
    # two diagonals within layer
    WINNING_LINES.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    WINNING_LINES.append([(2, 0, z), (1, 1, z), (0, 2, z)])

# Vertical lines (x,y constant, z varies)
for x in range(3):
    for y in range(3):
        WINNING_LINES.append([(x, y, z) for z in range(3)])

# Space diagonals (4 main diagonals through the center)
WINNING_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
WINNING_LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
WINNING_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
WINNING_LINES.append([(2, 2, 0), (1, 1, 1), (0, 0, 2)])

# Face diagonals (for each constant x)
for x in range(3):
    WINNING_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    WINNING_LINES.append([(x, 2, 0), (x, 1, 1), (x, 0, 2)])
# Face diagonals (for each constant y)
for y in range(3):
    WINNING_LINES.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    WINNING_LINES.append([(2, y, 0), (1, y, 1), (0, y, 2)])

def check_winner(board):
    """Return 1 if we win, -1 if opponent wins, 0 otherwise."""
    for line in WINNING_LINES:
        a, b, c = line
        v1 = board[a[0]][a[1]][a[2]]
        v2 = board[b[0]][b[1]][b[2]]
        v3 = board[c[0]][c[1]][c[2]]
        if v1 == v2 == v3:
            if v1 == 1:
                return 1
            if v1 == -1:
                return -1
    return 0

def is_full(board):
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return False
    return True

def evaluate(board):
    """Heuristic evaluation of board from our perspective."""
    score = 0
    for line in WINNING_LINES:
        counts = {1: 0, -1: 0, 0: 0}
        for (x, y, z) in line:
            val = board[x][y][z]
            counts[val] += 1
        if counts[1] == 3:
            score += 100000
        elif counts[-1] == 3:
            score -= 100000
        else:
            if counts[-1] == 0:
                # only our marks and empties
                score += 10 ** counts[1]
            elif counts[1] == 0:
                # only opponent marks and empties
                score -= 10 ** counts[-1]
            # else both present, line is blocked
    # center bonus
    if board[1][1][1] == 1:
        score += 5
    elif board[1][1][1] == -1:
        score -= 5
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner != 0:
        return winner * 1000000
    if is_full(board):
        return 0
    if depth == 0:
        return evaluate(board)

    if maximizing_player:
        max_eval = -float('inf')
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        board[x][y][z] = 1
                        eval = minimax(board, depth - 1, alpha, beta, False)
                        board[x][y][z] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        board[x][y][z] = -1
                        eval = minimax(board, depth - 1, alpha, beta, True)
                        board[x][y][z] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    # First, check for immediate winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    board[x][y][z] = 1
                    if check_winner(board) == 1:
                        board[x][y][z] = 0
                        return (x, y, z)
                    board[x][y][z] = 0
    # Second, check for opponent's immediate winning move and block
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    board[x][y][z] = -1
                    if check_winner(board) == -1:
                        board[x][y][z] = 0
                        return (x, y, z)
                    board[x][y][z] = 0

    # Otherwise, run minimax with depth 3 to choose best move
    best_move = None
    best_val = -float('inf')
    depth = 3
    # If there are few empty cells, increase depth to look until end
    empty_count = sum(1 for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0)
    if empty_count <= 5:
        depth = empty_count  # search to terminal

    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    board[x][y][z] = 1
                    val = minimax(board, depth - 1, -float('inf'), float('inf'), False)
                    board[x][y][z] = 0
                    if val > best_val:
                        best_val = val
                        best_move = (x, y, z)
    # Fallback: just pick first empty cell (should never happen)
    if best_move is None:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        return (x, y, z)
    return best_move
