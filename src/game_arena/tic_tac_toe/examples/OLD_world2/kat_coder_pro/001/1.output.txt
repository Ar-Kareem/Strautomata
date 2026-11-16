import numpy as np
from collections import defaultdict
import random

def policy(board):
    BOARD_SIZE = 4
    EMPTY, ME, OP = 0, 1, -1

    def is_win(state):
        # Check rows
        for r in range(BOARD_SIZE):
            if abs(sum(state[r])) == BOARD_SIZE:
                return state[r][0]
        # Check cols
        for c in range(BOARD_SIZE):
            if abs(sum(state[r][c] for r in range(BOARD_SIZE))) == BOARD_SIZE:
                return state[0][c]
        # Check diags
        if abs(sum(state[i][i] for i in range(BOARD_SIZE))) == BOARD_SIZE:
            return state[0][0]
        if abs(sum(state[i][BOARD_SIZE-1-i] for i in range(BOARD_SIZE))) == BOARD_SIZE:
            return state[0][BOARD_SIZE-1]
        return None

    def is_full(state):
        return all(cell != EMPTY for row in state for cell in row)

    def has_won(state, player):
        return is_win(state) == player

    def is_valid_move(state, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and state[r][c] == EMPTY

    def get_valid_moves(state):
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if state[r][c] == EMPTY]

    def evaluate(state):
        # Simple heuristic: count of my marks minus opponent marks in potential lines
        score = 0
        lines = []

        # rows
        for r in range(BOARD_SIZE):
            lines.append([state[r][c] for c in range(BOARD_SIZE)])
        # cols
        for c in range(BOARD_SIZE):
            lines.append([state[r][c] for r in range(BOARD_SIZE)])
        # diags
        lines.append([state[i][i] for i in range(BOARD_SIZE)])
        lines.append([state[i][BOARD_SIZE-1-i] for i in range(BOARD_SIZE)])

        for line in lines:
            my_count = sum(1 for x in line if x == ME)
            op_count = sum(1 for x in line if x == OP)
            if op_count == 0:
                score += my_count ** 2
            elif my_count == 0 and op_count > 0:
                score -= op_count ** 2
        return score

    def alphabeta(state, depth, alpha, beta, maximizing_player):
        winner = is_win(state)
        if winner is not None:
            return winner * 1000 + depth, None
        if is_full(state) or depth == 0:
            return evaluate(state), None

        if maximizing_player:
            max_eval = -float('inf')
            best_move = None
            for r, c in get_valid_moves(state):
                state[r][c] = ME
                eval_score, _ = alphabeta(state, depth - 1, alpha, beta, False)
                state[r][c] = EMPTY
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for r, c in get_valid_moves(state):
                state[r][c] = OP
                eval_score, _ = alphabeta(state, depth - 1, alpha, beta, True)
                state[r][c] = EMPTY
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    board_np = np.array(board)
    valid_moves = get_valid_moves(board_np)
    if not valid_moves:
        return (0, 0)

    # Immediate win
    for r, c in valid_moves:
        board_np[r][c] = ME
        if has_won(board_np, ME):
            board_np[r][c] = EMPTY
            return (r, c)
        board_np[r][c] = EMPTY

    # Block immediate opponent win
    for r, c in valid_moves:
        board_np[r][c] = OP
        if has_won(board_np, OP):
            board_np[r][c] = EMPTY
            return (r, c)
        board_np[r][c] = EMPTY

    # Minimax with alpha-beta pruning
    _, move = alphabeta(board_np, depth=6, alpha=-float('inf'), beta=float('inf'), maximizing_player=True)
    if move is not None:
        return move

    # Fallback to random
    return random.choice(valid_moves)