
import math
import random

# Main policy function required by the arena
def policy(you, opponent) -> str:
    # Build combined board: 1 = us, -1 = opponent, 0 = empty
    board = [[0 for _ in range(6)] for _ in range(6)]
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r][c] = 1
            elif opponent[r][c] == 1:
                board[r][c] = -1

    move = choose_best_move(board)
    if move is None:
        # Fallback: choose any legal move
        empties = get_empty_cells(board)
        r, c = empties[0]
        move = (r, c, 0, 'L')
    r, c, q, d = move
    return f"{r+1},{c+1},{q},{d}"


# -------- Game Logic --------

def get_empty_cells(board):
    empties = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empties.append((r, c))
    return empties

def rotate_quadrant(board, quad, direction):
    r0 = 0 if quad < 2 else 3
    c0 = 0 if quad % 2 == 0 else 3
    temp = [[board[r0+i][c0+j] for j in range(3)] for i in range(3)]
    if direction == 'R':
        new = [[temp[2-j][i] for j in range(3)] for i in range(3)]
    else:
        new = [[temp[j][2-i] for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            board[r0+i][c0+j] = new[i][j]

def apply_move(board, r, c, quad, direction, player):
    new_board = [row[:] for row in board]
    new_board[r][c] = player
    rotate_quadrant(new_board, quad, direction)
    return new_board

def has_five(board, player):
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for r in range(6):
        for c in range(6):
            if board[r][c] != player:
                continue
            for dr, dc in directions:
                cnt = 1
                nr, nc = r+dr, c+dc
                while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == player:
                    cnt += 1
                    if cnt >= 5:
                        return True
                    nr += dr
                    nc += dc
    return False

def terminal_score(board):
    win1 = has_five(board, 1)
    win2 = has_five(board, -1)
    if win1 and win2:
        return 0
    if win1:
        return 100000
    if win2:
        return -100000
    # full board
    full = True
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                full = False
                break
        if not full:
            break
    if full:
        return 0
    return None

def evaluate(board):
    # Heuristic based on 5-length sequences
    score = 0
    weights = [0, 1, 10, 100, 1000, 10000]
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for r in range(6):
        for c in range(6):
            for dr, dc in directions:
                r_end = r + 4*dr
                c_end = c + 4*dc
                if 0 <= r_end < 6 and 0 <= c_end < 6:
                    count1 = 0
                    count2 = 0
                    for i in range(5):
                        v = board[r+i*dr][c+i*dc]
                        if v == 1:
                            count1 += 1
                        elif v == -1:
                            count2 += 1
                    if count1 > 0 and count2 > 0:
                        continue
                    if count1 > 0:
                        score += weights[count1]
                    elif count2 > 0:
                        score -= weights[count2]
    return score

def generate_moves(board):
    empties = get_empty_cells(board)
    moves = []
    for (r, c) in empties:
        for quad in range(4):
            moves.append((r, c, quad, 'L'))
            moves.append((r, c, quad, 'R'))
    return moves

def choose_best_move(board):
    moves = generate_moves(board)
    if not moves:
        return None

    # First, check immediate winning move
    for move in moves:
        r, c, q, d = move
        b1 = apply_move(board, r, c, q, d, 1)
        term = terminal_score(b1)
        if term == 100000:
            return move

    best_val = -math.inf
    best_move = None

    for move in moves:
        r, c, q, d = move
        b1 = apply_move(board, r, c, q, d, 1)
        term = terminal_score(b1)
        if term is not None:
            val = term
        else:
            val = opponent_best(b1)
        if val > best_val:
            best_val = val
            best_move = move

    return best_move

def opponent_best(board):
    moves = generate_moves(board)
    if not moves:
        return evaluate(board)

    best = math.inf
    for move in moves:
        r, c, q, d = move
        b2 = apply_move(board, r, c, q, d, -1)
        term = terminal_score(b2)
        if term is not None:
            val = term
        else:
            val = evaluate(b2)
        if val < best:
            best = val
        if best <= -100000:
            break
    return best
