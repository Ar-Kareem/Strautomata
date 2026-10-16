
import math
import random
from typing import List

ROWS = 6
COLS = 7

def policy(board: List[List[int]]) -> int:
    def valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def drop_piece(b, col, piece):
        new_b = [row[:] for row in b]
        for r in range(ROWS-1, -1, -1):
            if new_b[r][col] == 0:
                new_b[r][col] = piece
                break
        return new_b

    def winning_move(b, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if all(b[r][c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS-3):
                if all(b[r+i][c] == piece for i in range(4)):
                    return True
        # Diagonal down-right
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if all(b[r+i][c+i] == piece for i in range(4)):
                    return True
        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if all(b[r-i][c+i] == piece for i in range(4)):
                    return True
        return False

    def score_window(window, piece):
        opp = -piece
        count_piece = window.count(piece)
        count_opp = window.count(opp)
        count_empty = window.count(0)
        score = 0
        if count_piece == 4:
            score += 100000
        elif count_piece == 3 and count_empty == 1:
            score += 50
        elif count_piece == 2 and count_empty == 2:
            score += 10
        if count_opp == 3 and count_empty == 1:
            score -= 80
        return score

    def evaluate(b, piece):
        score = 0
        center = [b[r][COLS//2] for r in range(ROWS)]
        score += center.count(piece) * 6

        # Horizontal
        for r in range(ROWS):
            row = b[r]
            for c in range(COLS-3):
                score += score_window(row[c:c+4], piece)

        # Vertical
        for c in range(COLS):
            col = [b[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                score += score_window(col[r:r+4], piece)

        # Diagonal down-right
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [b[r+i][c+i] for i in range(4)]
                score += score_window(window, piece)

        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = [b[r-i][c+i] for i in range(4)]
                score += score_window(window, piece)

        return score

    def terminal_node(b):
        return winning_move(b, 1) or winning_move(b, -1) or len(valid_moves(b)) == 0

    def minimax(b, depth, alpha, beta, maximizing):
        valid = valid_moves(b)
        if depth == 0 or terminal_node(b):
            if winning_move(b, 1):
                return (None, 1000000)
            elif winning_move(b, -1):
                return (None, -1000000)
            else:
                return (None, evaluate(b, 1))

        if maximizing:
            value = -math.inf
            best_col = random.choice(valid)
            for col in valid:
                new_b = drop_piece(b, col, 1)
                new_score = minimax(new_b, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = math.inf
            best_col = random.choice(valid)
            for col in valid:
                new_b = drop_piece(b, col, -1)
                new_score = minimax(new_b, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    # Immediate winning move
    for col in valid_moves(board):
        if winning_move(drop_piece(board, col, 1), 1):
            return col
    # Immediate block
    for col in valid_moves(board):
        if winning_move(drop_piece(board, col, -1), -1):
            return col

    # Minimax decision
    best_col, _ = minimax(board, 4, -math.inf, math.inf, True)
    if best_col is None or best_col not in valid_moves(board):
        # fallback: first valid
        return valid_moves(board)[0]
    return best_col
