
import numpy as np

def drop(board, col, player):
    new_board = board.copy()
    col_empty = np.where(new_board[:, col] == 0)[0]
    if len(col_empty) == 0:
        return None
    row = col_empty[-1]
    new_board[row, col] = player
    return new_board

def legal_moves(board):
    return [c for c in range(7) if np.any(board[:, c] == 0)]

def get_winner(board):
    # horizontal
    for r in range(6):
        for c in range(4):
            if (board[r, c] == 1 and board[r, c + 1] == 1 and board[r, c + 2] == 1 and board[r, c + 3] == 1):
                return 1
            if (board[r, c] == -1 and board[r, c + 1] == -1 and board[r, c + 2] == -1 and board[r, c + 3] == -1):
                return -1
    # vertical
    for c in range(7):
        for r in range(3):
            if (board[r, c] == 1 and board[r + 1, c] == 1 and board[r + 2, c] == 1 and board[r + 3, c] == 1):
                return 1
            if (board[r, c] == -1 and board[r + 1, c] == -1 and board[r + 2, c] == -1 and board[r + 3, c] == -1):
                return -1
    # diagonal /
    for r in range(3):
        for c in range(4):
            if all(board[r + i, c + i] == 1 for i in range(4)):
                return 1
            if all(board[r + i, c + i] == -1 for i in range(4)):
                return -1
    # diagonal \
    for r in range(3):
        for c in range(3, 7):
            if all(board[r + i, c - i] == 1 for i in range(4)):
                return 1
            if all(board[r + i, c - i] == -1 for i in range(4)):
                return -1
    return 0

def is_terminal(board):
    winner = get_winner(board)
    if winner != 0:
        return True, winner
    if np.all(board != 0):
        return True, 0
    return False, 0

def count_lines(board, p):
    score = 0
    opp = -p
    # horizontal
    for r in range(6):
        for s in range(4):
            window = board[r, s:s + 4]
            my = np.sum(window == p)
            o = np.sum(window == opp)
            e = 4 - my - o
            if my == 4:
                score += 1000000
            elif my == 3 and e == 1:
                score += 10000
            elif my == 2 and e == 2:
                score += 100
            elif my == 1 and e == 3:
                score += 10
    # vertical
    for c in range(7):
        for s in range(3):
            window = board[s:s + 4, c]
            my = np.sum(window == p)
            o = np.sum(window == opp)
            e = 4 - my - o
            if my == 4:
                score += 1000000
            elif my == 3 and e == 1:
                score += 10000
            elif my == 2 and e == 2:
                score += 100
            elif my == 1 and e == 3:
                score += 10
    # diagonal /
    for sr in range(3):
        for sc in range(4):
            my = 0
            o = 0
            for i in range(4):
                cell = board[sr + i, sc + i]
                if cell == p:
                    my += 1
                elif cell == opp:
                    o += 1
            e = 4 - my - o
            if my == 4:
                score += 1000000
            elif my == 3 and e == 1:
                score += 10000
            elif my == 2 and e == 2:
                score += 100
            elif my == 1 and e == 3:
                score += 10
    # diagonal \
    for sr in range(3):
        for sc in range(3, 7):
            my = 0
            o = 0
            for i in range(4):
                cell = board[sr + i, sc - i]
                if cell == p:
                    my += 1
                elif cell == opp:
                    o += 1
            e = 4 - my - o
            if my == 4:
                score += 1000000
            elif my == 3 and e == 1:
                score += 10000
            elif my == 2 and e == 2:
                score += 100
            elif my == 1 and e == 3:
                score += 10
    return score

def heuristic(board):
    return count_lines(board, 1) - count_lines(board, -1)

def move_order(board):
    moves = legal_moves(board)
    order_cols = [3, 2, 4, 1, 5, 0, 6]
    return sorted(moves, key=order_cols.index)

def alphabeta(board, depth, alpha, beta, is_max):
    terminal, winner = is_terminal(board)
    if terminal:
        if winner == 1:
            return 1000000
        elif winner == -1:
            return -1000000
        else:
            return 0
    if depth == 0:
        return heuristic(board)
    moves = move_order(board)
    if is_max:
        max_eval = -float('inf')
        for col in moves:
            new_board = drop(board, col, 1)
            if new_board is None:
                continue
            eval_score = alphabeta(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in moves:
            new_board = drop(board, col, -1)
            if new_board is None:
                continue
            eval_score = alphabeta(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board_list: list[list[int]]) -> int:
    board = np.array(board_list, dtype=int)
    moves = legal_moves(board)
    if not moves:
        return 0  # should not happen

    # Check for immediate win
    for col in range(7):
        new_board = drop(board, col, 1)
        if new_board is not None and get_winner(new_board) == 1:
            return col

    # Root move ordering with heuristic
    move_list = []
    for col in moves:
        new_board = drop(board, col, 1)
        h = heuristic(new_board)
        move_list.append((h, col))
    move_list.sort(reverse=True)

    # Search
    DEPTH = 10
    best_score = -float('inf')
    best_col = move_list[0][1]
    for _, col in move_list:
        new_board = drop(board, col, 1)
        score = alphabeta(new_board, DEPTH, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
