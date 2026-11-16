
import copy
import random
import math
import sys

# Set recursion limit a bit higher to be safe
sys.setrecursionlimit(10000)

def evaluate(board):
    """Return a heuristic score for the given board."""
    score = 0

    # Horizontal lines
    for row in range(6):
        for col_start in range(4):
            total = sum(board[row][col_start:col_start + 4])
            score += total

    # Vertical lines
    for col in range(7):
        for row_start in range(3):
            total = sum(board[row_start + i][col] for i in range(4))
            score += total

    # Diagonal left‑down (NW‑SE)
    for row in range(3):
        for col in range(4):
            total = sum(board[row + i][col + i] for i in range(4))
            score += total

    # Diagonal right‑down (NE‑SW)
    for row in range(3):
        for col in range(3, 7):
            total = sum(board[row + i][col - i] for i in range(4))
            score += total

    # Column heuristic – favour columns with my discs and punish opponent domination
    for col in range(7):
        own = sum(board[r][col] == 1 for r in range(6))
        opp = sum(board[r][col] == -1 for r in range(6))
        empty = 6 - own - opp
        # Weight heavily: own disc gets +10, opponent disc gets -10, empty cell +1
        score += (own * 10) - (opp * 10) + empty

    return score

def check_win(board, disc=1):
    """Return True if `disc` (1 for me, -1 for opponent) has formed a line of four."""
    # Horizontal
    for row in range(6):
        for col_start in range(4):
            if sum(board[row][col_start:col_start + 4]) == disc * 4:
                return True
    # Vertical
    for col in range(7):
        for row_start in range(3):
            if sum(board[row_start + i][col] for i in range(4)) == disc * 4:
                return True
    # Diagonal left‑down
    for row in range(3):
        for col in range(4):
            if sum(board[row + i][col + i] for i in range(4)) == disc * 4:
                return True
    # Diagonal right‑down
    for row in range(3):
        for col in range(3, 7):
            if sum(board[row + i][col - i] for i in range(4)) == disc * 4:
                return True
    return False

def has_moves(board):
    """Return list of columns that are not full."""
    return [col for col in range(7) if any(board[row][col] == 0 for row in range(5, -1, -1))]

def find_row(board, col):
    """Return the lowest (bottom) row index where column `col` is empty."""
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return None   # column is full

def copy_board(board):
    """Deep‑copy the 6×7 board."""
    return [row[:] for row in board]

def apply_move(board, col, disc):
    """Place `disc` (1 for me, -1 for opponent) into column `col`."""
    row = find_row(board, col)
    new = copy_board(board)
    new[row][col] = disc
    return new

def minimax(board, depth, alpha, beta, maximizing_player):
    """Depth‑limited minimax with alpha‑beta pruning."""
    if depth == 0 or not has_moves(board):
        return evaluate(board), None

    if maximizing_player:   # my turn
        best_score = -float('inf')
        best_move = None
        moves = sorted(has_moves(board))   # deterministic tie‑break
        for col in moves:
            new_board = apply_move(board, col, disc=-1)   # opponent's move
            score = minimax(new_board, depth - 1, alpha, beta, False)[0]
            if score > best_score:
                best_score = score
                best_move = col
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best_score, best_move

    else:                    # opponent's turn
        best_score = float('inf')
        best_move = None
        moves = sorted(has_moves(board))
        for col in moves:
            new_board = apply_move(board, col, disc=1)    # my move
            score = minimax(new_board, depth - 1, alpha, beta, True)[0]
            if score < best_score:
                best_score = score
                best_move = col
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move

def policy(board):
    """Main entry point: return the column index of the next move."""
    # 1️⃣ Immediate win?
    for col in has_moves(board):
        new_board = apply_move(board, col, disc=1)
        if check_win(new_board):
            return col

    # 2️⃣ Block opponent's immediate win?
    opponent_disc = -1
    for col in has_moves(board):
        new_board = apply_move(board, col, disc=opponent_disc)
        if check_win(new_board, disc=opponent_disc):
            return col

    # 3️⃣ Decide depth based on remaining moves (max 5‑6 plies is enough)
    total_empty = sum(cell == 0 for row in board for cell in row)
    max_moves = total_empty // 2   # two moves per pair
    depth_limit = min(6, max_moves)

    # 4️⃣ Run minimax with early termination if a win is found
    best_score, best_col = minimax(board, depth_limit, -float('inf'), float('inf'), True)
    return best_col
