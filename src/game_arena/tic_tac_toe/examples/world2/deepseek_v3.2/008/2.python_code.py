
import time
import math
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Quick win or block
    rows = 4
    cols = 4
    player = 1
    opponent = -1

    # Helper to check if a line has 4 of same kind
    def check_line(line):
        if all(cell == player for cell in line):
            return player
        if all(cell == opponent for cell in line):
            return opponent
        return 0

    # Check for immediate win for player
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                # Try placing player's piece
                board[r][c] = player
                # Check all lines through (r,c)? Actually we need to check if player wins after placing.
                # Check all rows, columns, diagonals.
                # We'll reuse the winner check function.
                winner = get_winner(board)
                board[r][c] = 0
                if winner == player:
                    return (r, c)

    # Check for opponent's immediate win (block)
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                board[r][c] = opponent
                winner = get_winner(board)
                board[r][c] = 0
                if winner == opponent:
                    return (r, c)

    # If no immediate win/block, use minimax with iterative deepening
    time_limit = 0.95  # seconds
    start_time = time.time()
    best_move = None
    depth = 1
    # Initial move ordering: center cells first
    moves = get_possible_moves(board)
    if not moves:
        return (0, 0)  # shouldn't happen
    # Order moves: center (rows 1-2, cols 1-2) first, then corners, then others
    moves.sort(key=lambda pos: (
        -((1 <= pos[0] <= 2) and (1 <= pos[1] <= 2)),  # center priority
        -(pos[0] in (0, 3) and pos[1] in (0, 3)),      # corners
        -abs(pos[0] - 1.5) - abs(pos[1] - 1.5)         # closeness to center
    ))

    # We'll store the best move from previous depth
    best_move = moves[0]

    # Transposition table: key = (board_tuple, depth, maximizing), value = (score, best_move?)
    transposition = {}

    while time.time() - start_time < time_limit:
        try:
            best_score = -math.inf
            alpha = -math.inf
            beta = math.inf
            current_best = moves[0]
            for move in moves:
                r, c = move
                board[r][c] = player
                score = minimax(board, depth-1, alpha, beta, False, start_time, time_limit, transposition)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    current_best = move
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            best_move = current_best
            depth += 1
        except TimeoutError:
            # Time's up, break out of iterative deepening
            break

    return best_move

def get_possible_moves(board):
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def get_winner(board):
    # Check rows
    for r in range(4):
        row = board[r]
        if all(cell == 1 for cell in row):
            return 1
        if all(cell == -1 for cell in row):
            return -1
    # Check columns
    for c in range(4):
        col = [board[r][c] for r in range(4)]
        if all(cell == 1 for cell in col):
            return 1
        if all(cell == -1 for cell in col):
            return -1
    # Check diagonals
    diag1 = [board[i][i] for i in range(4)]
    diag2 = [board[i][3-i] for i in range(4)]
    if all(cell == 1 for cell in diag1) or all(cell == 1 for cell in diag2):
        return 1
    if all(cell == -1 for cell in diag1) or all(cell == -1 for cell in diag2):
        return -1
    return 0

def evaluate(board):
    # Heuristic evaluation for non-terminal positions
    player = 1
    opponent = -1
    score = 0
    # Rows
    for r in range(4):
        row = board[r]
        player_count = row.count(player)
        opponent_count = row.count(opponent)
        if player_count > 0 and opponent_count > 0:
            continue  # blocked line
        if player_count > 0:
            score += 10 ** (player_count - 1)
        elif opponent_count > 0:
            score -= 10 ** (opponent_count - 1)
    # Columns
    for c in range(4):
        col = [board[r][c] for r in range(4)]
        player_count = col.count(player)
        opponent_count = col.count(opponent)
        if player_count > 0 and opponent_count > 0:
            continue
        if player_count > 0:
            score += 10 ** (player_count - 1)
        elif opponent_count > 0:
            score -= 10 ** (opponent_count - 1)
    # Diagonals
    diag1 = [board[i][i] for i in range(4)]
    diag2 = [board[i][3-i] for i in range(4)]
    for diag in (diag1, diag2):
        player_count = diag.count(player)
        opponent_count = diag.count(opponent)
        if player_count > 0 and opponent_count > 0:
            continue
        if player_count > 0:
            score += 10 ** (player_count - 1)
        elif opponent_count > 0:
            score -= 10 ** (opponent_count - 1)
    return score

def minimax(board, depth, alpha, beta, maximizingPlayer, start_time, time_limit, transposition):
    # Check timeout
    if time.time() - start_time > time_limit:
        raise TimeoutError()

    # Check for terminal states
    winner = get_winner(board)
    if winner == 1:
        return 10000
    if winner == -1:
        return -10000
    # Check if board is full (draw)
    if all(board[r][c] != 0 for r in range(4) for c in range(4)):
        return 0

    if depth == 0:
        return evaluate(board)

    # Create a hashable key for transposition table
    board_tuple = tuple(tuple(row) for row in board)
    key = (board_tuple, depth, maximizingPlayer)
    if key in transposition:
        score, a, b = transposition[key]
        if a <= score <= b:
            return score
        # Otherwise, we can still use the score for pruning? Not strictly correct, but we'll ignore.

    moves = get_possible_moves(board)
    # Order moves heuristically
    moves.sort(key=lambda pos: (
        -((1 <= pos[0] <= 2) and (1 <= pos[1] <= 2)),
        -(pos[0] in (0, 3) and pos[1] in (0, 3)),
        -abs(pos[0] - 1.5) - abs(pos[1] - 1.5)
    ))

    if maximizingPlayer:
        value = -math.inf
        for move in moves:
            r, c = move
            board[r][c] = 1
            child_value = minimax(board, depth-1, alpha, beta, False, start_time, time_limit, transposition)
            board[r][c] = 0
            value = max(value, child_value)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        transposition[key] = (value, alpha, beta)
        return value
    else:
        value = math.inf
        for move in moves:
            r, c = move
            board[r][c] = -1
            child_value = minimax(board, depth-1, alpha, beta, True, start_time, time_limit, transposition)
            board[r][c] = 0
            value = min(value, child_value)
            beta = min(beta, value)
            if alpha >= beta:
                break
        transposition[key] = (value, alpha, beta)
        return value
