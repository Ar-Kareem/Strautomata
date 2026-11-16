
import time
import numpy as np

WIN_SCORE = 10000
THREE_SCORE = 100
TWO_SCORE = 10
CENTRAL_COL_BONUS = 3

# Precompute all possible winning four-in-a-row lines (horizontal, vertical, diagonal)
def generate_winning_lines(rows=6, cols=7):
    lines = []
    # horizontal
    for r in range(rows):
        for c in range(cols - 3):
            lines.append([(r, c + i) for i in range(4)])
    # vertical
    for r in range(rows - 3):
        for c in range(cols):
            lines.append([(r + i, c) for i in range(4)])
    # diagonal down-right
    for r in range(rows - 3):
        for c in range(cols - 3):
            lines.append([(r + i, c + i) for i in range(4)])
    # diagonal up-right
    for r in range(3, rows):
        for c in range(cols - 3):
            lines.append([(r - i, c + i) for i in range(4)])
    return lines

WINNING_LINES = generate_winning_lines()

def evaluate_board(board, player):
    """Heuristic score from player's perspective."""
    if player == 1:
        opponent = -1
    else:
        opponent = 1
    score = 0
    # center column preference
    center_col = 3
    for r in range(6):
        if board[r][center_col] == player:
            score += CENTRAL_COL_BONUS
        elif board[r][center_col] == opponent:
            score -= CENTRAL_COL_BONUS
    # evaluate each possible line
    for line in WINNING_LINES:
        values = [board[r][c] for r, c in line]
        p_count = values.count(player)
        o_count = values.count(opponent)
        empty_count = values.count(0)
        if p_count == 4:
            return WIN_SCORE
        if o_count == 4:
            return -WIN_SCORE
        if o_count == 0 and p_count > 0:
            if p_count == 3 and empty_count == 1:
                score += THREE_SCORE
            elif p_count == 2 and empty_count == 2:
                score += TWO_SCORE
        if p_count == 0 and o_count > 0:
            if o_count == 3 and empty_count == 1:
                score -= THREE_SCORE
            elif o_count == 2 and empty_count == 2:
                score -= TWO_SCORE
    return score

def get_valid_moves(board):
    return [c for c in range(7) if board[0][c] == 0]

def make_move(board, col, player):
    new_board = [row[:] for row in board]
    for r in reversed(range(6)):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            break
    return new_board

def minimax(board, depth, alpha, beta, maximizing, start_time, player, max_depth):
    valid_moves = get_valid_moves(board)
    opponent = -player
    # terminal or depth limit
    if depth == 0 or time.time() - start_time > 0.9 or not valid_moves:
        return evaluate_board(board, player), None
    # check immediate win for current player
    for col in valid_moves:
        temp_board = make_move(board, col, player if maximizing else opponent)
        # check if this move wins
        if abs(evaluate_board(temp_board, player)) >= WIN_SCORE // 2:
            return (WIN_SCORE, col) if maximizing else (-WIN_SCORE, col)
    if maximizing:
        max_eval = -float('inf')
        best_col = valid_moves[0]
        # move ordering: center first
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        for col in ordered_moves:
            new_board = make_move(board, col, player)
            eval_val, _ = minimax(new_board, depth - 1, alpha, beta, False, start_time, player, max_depth)
            if eval_val > max_eval:
                max_eval = eval_val
                best_col = col
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_col
    else:
        min_eval = float('inf')
        best_col = valid_moves[0]
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        for col in ordered_moves:
            new_board = make_move(board, col, opponent)
            eval_val, _ = minimax(new_board, depth - 1, alpha, beta, True, start_time, player, max_depth)
            if eval_val < min_eval:
                min_eval = eval_val
                best_col = col
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_col

def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    player = 1  # we are always player 1
    opponent = -1
    valid_moves = get_valid_moves(board)
    # if only one move, return it immediately
    if len(valid_moves) == 1:
        return valid_moves[0]
    # check for immediate win
    for col in valid_moves:
        temp_board = make_move(board, col, player)
        if evaluate_board(temp_board, player) >= WIN_SCORE // 2:
            return col
    # check for opponent's immediate win (block)
    for col in valid_moves:
        temp_board = make_move(board, col, opponent)
        if evaluate_board(temp_board, player) <= -WIN_SCORE // 2:
            return col
    # iterative deepening with time limit
    best_col = valid_moves[0]
    max_depth = 1
    while time.time() - start_time < 0.9 and max_depth <= 10:
        _, col = minimax(board, max_depth, -float('inf'), float('inf'), True, start_time, player, max_depth)
        best_col = col
        max_depth += 1
    return best_col
