
import math
import random
from typing import Optional

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Precompute all winning lines: each line is a list of (r,c)
    lines = []
    # rows
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    # columns
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    # diagonals
    lines.append([(i, i) for i in range(4)])  # main diag
    lines.append([(i, 3 - i) for i in range(4)])  # anti diag

    # Helper to get list of empty cells
    def empty_cells(b):
        return [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]

    # Check for winner (1, -1, or 0)
    def get_winner(b):
        for line in lines:
            values = [b[r][c] for (r, c) in line]
            if all(v == 1 for v in values):
                return 1
            if all(v == -1 for v in values):
                return -1
        return 0

    # Evaluation function
    def evaluate(b):
        score = 0
        # center bonus
        center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for r, c in center_squares:
            if b[r][c] == 1:
                score += 2
            elif b[r][c] == -1:
                score -= 2
        # line evaluation
        for line in lines:
            us = 0
            them = 0
            empty = 0
            for r, c in line:
                val = b[r][c]
                if val == 1:
                    us += 1
                elif val == -1:
                    them += 1
                else:
                    empty += 1
            if us > 0 and them > 0:
                continue  # dead line, no threat
            if us == 4:
                score += 10000
            elif them == 4:
                score -= 10000
            elif us == 3 and empty == 1:
                score += 100
            elif them == 3 and empty == 1:
                score -= 100
            elif us == 2 and empty == 2:
                score += 10
            elif them == 2 and empty == 2:
                score -= 10
            elif us == 1 and empty == 3:
                score += 1
            elif them == 1 and empty == 3:
                score -= 1
        return score

    # Minimax with alpha-beta, depth limited
    def minimax(b, depth, alpha, beta, maximizing):
        winner = get_winner(b)
        if winner != 0:
            return winner * 100000  # large number, positive for us, negative for opponent
        if depth == 0 or not empty_cells(b):
            return evaluate(b)

        if maximizing:
            value = -math.inf
            moves = empty_cells(b)
            # move ordering: maybe sort by heuristic? For simplicity, random
            random.shuffle(moves)
            for r, c in moves:
                b[r][c] = 1
                value = max(value, minimax(b, depth - 1, alpha, beta, False))
                b[r][c] = 0
                if value >= beta:
                    break
                alpha = max(alpha, value)
            return value
        else:
            value = math.inf
            moves = empty_cells(b)
            random.shuffle(moves)
            for r, c in moves:
                b[r][c] = -1
                value = min(value, minimax(b, depth - 1, alpha, beta, True))
                b[r][c] = 0
                if value <= alpha:
                    break
                beta = min(beta, value)
            return value

    # First, check immediate winning move for us
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if get_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # Then, check opponent's winning move (block)
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if get_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # No immediate win/block, run minimax with depth
    best_move = None
    best_value = -math.inf
    moves = empty_cells(board)
    if not moves:
        return (0, 0)  # should not happen if game not over
    # Shuffle to add variety
    random.shuffle(moves)
    for r, c in moves:
        board[r][c] = 1
        move_value = minimax(board, depth=4, alpha=-math.inf, beta=math.inf, maximizing=False)
        board[r][c] = 0
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
    if best_move is None:
        best_move = moves[0]
    return best_move
