
import itertools
import math

# Precompute all winning lines (49 lines)
def generate_lines():
    directions = []
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dz == dy == dx == 0:
                    continue
                directions.append((dz, dy, dx))
    lines_set = set()
    for z in range(3):
        for y in range(3):
            for x in range(3):
                for dz, dy, dx in directions:
                    cells = []
                    for i in range(3):
                        nz = z + i * dz
                        ny = y + i * dy
                        nx = x + i * dx
                        if not (0 <= nz < 3 and 0 <= ny < 3 and 0 <= nx < 3):
                            break
                        cells.append((nz, ny, nx))
                    if len(cells) == 3:
                        lines_set.add(frozenset(cells))
    return [list(line) for line in lines_set]

ALL_LINES = generate_lines()

def get_empty_cells(board):
    """Return list of (z,y,x) tuples for empty cells."""
    empty = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty.append((z, y, x))
    return empty

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in ALL_LINES:
        values = [board[z][y][x] for (z, y, x) in line]
        if values[0] == values[1] == values[2] and values[0] != 0:
            return values[0]
    return 0

def is_full(board):
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    return False
    return True

def evaluate(board):
    """Heuristic evaluation for player 1."""
    score = 0
    for line in ALL_LINES:
        counts = {1: 0, -1: 0, 0: 0}
        for z, y, x in line:
            val = board[z][y][x]
            counts[val] += 1
        # immediate win/loss handled elsewhere
        if counts[1] == 2 and counts[0] == 1:
            score += 100
        if counts[-1] == 2 and counts[0] == 1:
            score -= 100
        if counts[1] == 1 and counts[0] == 2:
            score += 1
        if counts[-1] == 1 and counts[0] == 2:
            score -= 1
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner == 1:
        return 10000 - depth
    if winner == -1:
        return -10000 + depth
    if depth == 0 or is_full(board):
        return evaluate(board)

    empty_cells = get_empty_cells(board)
    if maximizing_player:
        max_eval = -math.inf
        for move in empty_cells:
            z, y, x = move
            board[z][y][x] = 1
            eval = minimax(board, depth - 1, alpha, beta, False)
            board[z][y][x] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in empty_cells:
            z, y, x = move
            board[z][y][x] = -1
            eval = minimax(board, depth - 1, alpha, beta, True)
            board[z][y][x] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Return (z, y, x) coordinates for the next move."""
    # 1. Immediate win?
    empty = get_empty_cells(board)
    for z, y, x in empty:
        board[z][y][x] = 1
        if check_winner(board) == 1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0

    # 2. Block opponent's immediate win?
    for z, y, x in empty:
        board[z][y][x] = -1
        if check_winner(board) == -1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0

    # 3. Choose best move using minimax with adaptive depth
    depth_limit = 4
    if len(empty) <= 6:
        depth_limit = len(empty)  # search to end if few moves left
    best_score = -math.inf
    best_move = empty[0]
    for move in empty:
        z, y, x = move
        board[z][y][x] = 1
        score = minimax(board, depth_limit - 1, -math.inf, math.inf, False)
        board[z][y][x] = 0
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
