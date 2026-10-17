
import copy
import math

def is_win(board, player):
    # Check rows and columns
    for i in range(4):
        row_sum = sum(board[i])
        col_sum = sum(board[j][i] for j in range(4))
        if row_sum == 4 * player or col_sum == 4 * player:
            return True
    # Check diagonals
    diag1_sum = sum(board[i][i] for i in range(4))
    diag2_sum = sum(board[i][3 - i] for i in range(4))
    if diag1_sum == 4 * player or diag2_sum == 4 * player:
        return True
    return False

def is_full(board):
    return all(cell != 0 for row in board for cell in row)

def evaluate(board):
    score = 0
    # Check rows, columns, diagonals
    lines = []
    for i in range(4):
        lines.append(board[i])  # rows
        lines.append([board[j][i] for j in range(4)])  # columns
    lines.append([board[i][i] for i in range(4)])  # diag1
    lines.append([board[i][3 - i] for i in range(4)])  # diag2
    
    for line in lines:
        my_count = line.count(1)
        opp_count = line.count(-1)
        empty_count = line.count(0)
        if my_count == 4:
            score += 10000
        elif opp_count == 4:
            score -= 10000
        elif my_count == 3 and opp_count == 0:
            score += 100
        elif opp_count == 3 and my_count == 0:
            score -= 100
        elif my_count == 2 and opp_count == 0:
            score += 10
        elif opp_count == 2 and my_count == 0:
            score -= 10
    return score

def minimax(board, depth, maximizing, player):
    if is_win(board, 1):
        return 10000
    if is_win(board, -1):
        return -10000
    if is_full(board) or depth <= 0:
        return evaluate(board)
    
    if maximizing:
        max_eval = -math.inf
        for r, c in get_moves(board):
            new_board = make_move(board, r, c, player)
            eval = minimax(new_board, depth - 1, False, -player)
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = math.inf
        for r, c in get_moves(board):
            new_board = make_move(board, r, c, -player)
            eval = minimax(new_board, depth - 1, True, -player)
            min_eval = min(min_eval, eval)
        return min_eval

def get_moves(board):
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                yield r, c

def make_move(board, r, c, player):
    new_board = copy.deepcopy(board)
    new_board[r][c] = player
    return new_board

def policy(board):
    best_move = None
    best_score = -math.inf
    for r, c in get_moves(board):
        new_board = make_move(board, r, c, 1)
        score = minimax(new_board, 3, False, 1)  # depth 3, after my move, opponent minimizes
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move
