
import random
import numpy as np

def get_possible_moves(board):
    n = len(board)
    moves = []
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board[z][y][x] == 0:
                    moves.append((z, y, x))
    return moves

def check_win(board, player):
    n = len(board)
    # Check rows, columns, and ranks
    for i in range(n):
        for j in range(n):
            if all(board[i][j][k] == player for k in range(n)): return True # Rank (z, y, x) fixed z,y
            if all(board[i][k][j] == player for k in range(n)): return True # Column (z, y, x) fixed z,x
            if all(board[k][i][j] == player for k in range(n)): return True # Row (z, y, x) fixed y,x

    # Check 2D diagonals on each plane
    for k in range(n):
        # XY-plane diagonals (fixed z)
        if all(board[k][i][i] == player for i in range(n)): return True
        if all(board[k][i][n - 1 - i] == player for i in range(n)): return True
        # XZ-plane diagonals (fixed y)
        if all(board[i][k][i] == player for i in range(n)): return True
        if all(board[i][k][n - 1 - i] == player for i in range(n)): return True
        # YZ-plane diagonals (fixed x)
        if all(board[i][i][k] == player for i in range(n)): return True
        if all(board[i][n - 1 - i][k] == player for i in range(n)): return True

    # Check 3D main diagonals
    if all(board[i][i][i] == player for i in range(n)): return True
    if all(board[i][i][n - 1 - i] == player for i in range(n)): return True
    if all(board[i][n - 1 - i][i] == player for i in range(n)): return True
    if all(board[n - 1 - i][i][i] == player for i in range(n)): return True

    return False

def minimax(board, depth, is_maximizing_player, alpha, beta, n):
    if check_win(board, 1):
        return 100 - depth  # Prioritize faster wins
    if check_win(board, -1):
        return -100 + depth # Opponent win is bad, less bad if it takes longer

    possible_moves = get_possible_moves(board)
    if not possible_moves or depth == 3:  # Limiting depth for performance
        return 0  # Draw or depth limit reached

    if is_maximizing_player:
        max_eval = -np.inf
        for move in possible_moves:
            z, y, x = move
            board[z][y][x] = 1
            eval = minimax(board, depth + 1, False, alpha, beta, n)
            board[z][y][x] = 0  # Undo move
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        for move in possible_moves:
            z, y, x = move
            board[z][y][x] = -1
            eval = minimax(board, depth + 1, True, alpha, beta, n)
            board[z][y][x] = 0  # Undo move
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    possible_moves = get_possible_moves(board)

    if not possible_moves:
        return None  # No moves possible (game ended in a draw)

    # Convert to a mutable list of lists for minimax
    mutable_board = [row[:] for plane in board for row in plane]
    mutable_board = [[list(col) for col in row] for row in board]

    best_move = random.choice(possible_moves)
    best_eval = -np.inf

    for move in possible_moves:
        z, y, x = move
        mutable_board[z][y][x] = 1  # Make the move for evaluation
        eval = minimax(mutable_board, 0, False, -np.inf, np.inf, n)
        mutable_board[z][y][x] = 0  # Undo the move

        if eval > best_eval:
            best_eval = eval
            best_move = move
        elif eval == best_eval:
            # If evaluations are equal, prefer a move that might lead to a quicker win
            # or is more central (heuristic, can be refined)
            # For now, just keep the first one found or random if equal
            if random.random() < 0.5: # 50% chance to pick a new equivalent move
                best_move = move

    return best_move

